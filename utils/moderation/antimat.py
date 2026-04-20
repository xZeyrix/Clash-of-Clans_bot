from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from typing import Callable, Dict, Any, Awaitable
from collections import OrderedDict

import asyncio
import re
from html import escape

from config import config, state

MAX_STORED_MESSAGES = 100  # Максимальное количество сохранённых сообщений для просмотра

class LimiteDict(OrderedDict):
    def __setitem__(self, key, value):
        if len(self) >= MAX_STORED_MESSAGES:
            self.popitem(last=False)
        super().__setitem__(key, value)

recently_deleted = LimiteDict()


def normalize_text(s: str) -> str:
    return re.sub(r'[^а-яёa-z]', '', s)


def normalize_cyrillic_lookalikes(s: str) -> str:
    replacements = {
        'o': 'о', 'c': 'с', 'e': 'е', 'p': 'р',
        'a': 'а', 'b': 'в', 'h': 'н', 'k': 'к',
        'm': 'м', 't': 'т', 'x': 'х', 'y': 'у',
    }
    result = s
    for lat, cyr in replacements.items():
        result = result.replace(lat, cyr)
    return result


def check_trigger_light_proximity(words: list, light_words: set, trigger_words: set, max_distance: int = 3) -> bool:
    """Проверяет, находятся ли триггер и light-слово рядом (не дальше max_distance слов)."""
    light_positions = []
    trigger_positions = []

    for i, word in enumerate(words):
        cleaned = normalize_text(word)
        normalized = normalize_cyrillic_lookalikes(cleaned)

        if normalized in light_words:
            light_positions.append(i)
        if normalized in trigger_words:
            trigger_positions.append(i)

    for light_pos in light_positions:
        for trigger_pos in trigger_positions:
            if abs(light_pos - trigger_pos) <= max_distance:
                return True

    return False


def regex_fallback_moderation(
    text: str,
    bad_words: list[str],
    long_bad_words: list[str],
    words_light: list[str],
    words_triggers: list[str],
) -> dict:
    """Локальная (без LLM) проверка на нарушение. Формат совместим с ai_moderation."""
    text = (text or "").lower()
    if not text:
        return {"violation": 0, "class": "safe", "reason": ""}

    ban = False
    words = text.split()

    for word in words:
        cleaned = normalize_text(word)
        normalized = normalize_cyrillic_lookalikes(cleaned)
        if normalized in bad_words:
            ban = True
            break

    if not ban and check_trigger_light_proximity(words, set(words_light), set(words_triggers), max_distance=3):
        ban = True

    if not ban:
        cleaned_text = normalize_text(normalize_cyrillic_lookalikes(text))
        for long_word in long_bad_words:
            if long_word in cleaned_text:
                ban = True
                break

    if ban:
        return {"violation": 1, "class": "ban", "reason": "Недопустимая лексика"}

    return {"violation": 0, "class": "safe", "reason": ""}


async def apply_moderation_result(event: Message, moderation_system, result: dict) -> bool:
    """Применяет результат модерации к сообщению. Возвращает True, если действие выполнено."""
    if not result or result.get("violation") != 1:
        return False

    user_id = event.from_user.id
    user_name = event.from_user.full_name
    reason = result.get("reason") or "Недопустимая лексика"
    cls = result.get("class")

    if cls == "warning":
        try:
            await event.delete()
        except Exception:
            pass
        message = await event.bot.send_message(
            chat_id=event.chat.id,
            text=(
                f"❗ Сообщение пользователя <a href='tg://user?id={user_id}'>{escape(user_name)}</a> было удалено\n"
                f"📋 Причина: {reason}\n"
            ),
        )
        await asyncio.sleep(10)
        try:
            await message.delete()
        except Exception:
            pass
        return True

    if cls != "ban":
        return False

    moderation_system.ban_user(user_id, reason)

    hours = moderation_system.ban_time // 3600
    minutes = (moderation_system.ban_time % 3600) // 60
    warnings = moderation_system.get_warnings_count(user_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Разблокировать", callback_data=f"unban_user:{user_id}")
    builder.button(text="🔴 Выгнать из группы", callback_data=f"kick_user:{user_id}")
    builder.button(text="✅ Оставить наказание", callback_data=f"keep_ban:{user_id}")
    builder.button(text="📩 Посмотреть сообщение", callback_data=f"view_message:{user_id}")
    builder.adjust(1)

    try:
        await event.delete()
    except Exception:
        pass

    recently_deleted[user_id] = event.text or ""
    message = await event.bot.send_message(
        chat_id=event.chat.id,
        text=(
            f"🚫 <a href='tg://user?id={user_id}'>{escape(user_name)}</a> "
            f"заблокирован на {hours}ч {minutes}м!\n"
            f"📋 Причина: {reason}\n"
            f"⚠️ Предупреждений: {warnings}"
        ),
        reply_markup=builder.as_markup()
    )
    moderation_system.set_ban_message(user_id, event.chat.id, message.message_id)
    return True

class AntiMatMiddleware(BaseMiddleware):
    """Middleware для фильтрации матов"""
    
    def __init__(self, moderation_system, bad_words: list[str], long_bad_words: list[str] = [], words_light: list[str] = [], words_triggers: list[str] = []):
        self.moderation = moderation_system
        self.bad_words = [word.lower() for word in bad_words]
        self.long_bad_words = [word.lower() for word in long_bad_words]
        self.words_light = [word.lower() for word in words_light]
        self.words_triggers = [word.lower() for word in words_triggers]
        super().__init__()
    def check_trigger_light_proximity(self, words: list, light_words: set, trigger_words: set, max_distance: int = 3) -> bool:
        return check_trigger_light_proximity(words, light_words, trigger_words, max_distance)
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.chat.id != config.talk_chat_id or not state.ai_enabled:
            return await handler(event, data)

        user_id = event.from_user.id
        
        # ========== ПРОВЕРКА БАНА ДОЛЖНА БЫТЬ ПЕРВОЙ ==========
        is_banned, time_left = self.moderation.is_banned(user_id)
        
        # ← ЕСЛИ РАЗБАН ПРОИЗОШЁЛ - УДАЛЯЕМ СООБЩЕНИЕ
        if not is_banned and user_id in self.moderation.ban_messages:
            await self.moderation.delete_ban_message(user_id, event.bot)

        if is_banned:
            reason = self.moderation.get_ban_reason(user_id)
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            seconds = time_left % 60
            
            try:
                await event.delete()  # Удаляем сообщение
            except:
                pass
            
            message = await event.answer(
                f"🚫 Вы заблокированы!\n"
                f"📋 Причина: {reason}\n"
                f"⏱️ Осталось: {hours}ч {minutes}м {seconds}с"
            )
            await asyncio.sleep(3)  # Удаляем уведомление через 3 секунды
            try:
                await message.delete()
            except:
                pass
            return  # ← ВАЖНО! Не вызываем handler
        
        # Проверяем только текстовые сообщения
        if not event.text:
            return await handler(event, data)
        
        # Основная модерация перенесена в AICheckMessage.
        # Здесь оставляем только проверку активного бана и пропуск дальше.
        return await handler(event, data)