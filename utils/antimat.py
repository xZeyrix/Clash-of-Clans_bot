from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable, Dict, Any, Awaitable
import asyncio
import re
from collections import OrderedDict
from config import TALK_CHAT_ID

MAX_STORED_MESSAGES = 100  # Максимальное количество сохранённых сообщений для просмотра

class LimiteDict(OrderedDict):
    def __setitem__(self, key, value):
        if len(self) >= MAX_STORED_MESSAGES:
            self.popitem(last=False)
        super().__setitem__(key, value)

recently_deleted = LimiteDict()

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
        """
        Проверяет, находятся ли триггер и light-слово рядом (не дальше max_distance слов)
        """
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
        
        light_positions = []
        trigger_positions = []
        
        for i, word in enumerate(words):
            cleaned = normalize_text(word)
            normalized = normalize_cyrillic_lookalikes(cleaned)
            
            if normalized in light_words:
                light_positions.append(i)
            if normalized in trigger_words:
                trigger_positions.append(i)
        
        # Проверяем расстояние между любыми парами
        for light_pos in light_positions:
            for trigger_pos in trigger_positions:
                if abs(light_pos - trigger_pos) <= max_distance:
                    return True
        
        return False
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.chat.id != TALK_CHAT_ID:
            return await handler(event, data)

        user_id = event.from_user.id
        
        # ========== ПРОВЕРКА БАНА ДОЛЖНА БЫТЬ ПЕРВОЙ ==========
        is_banned, time_left = self.moderation.is_banned(user_id)
        
        # ← ЕСЛИ РАЗБАН ПРОИЗОШЁЛ - УДАЛЯЕМ СООБЩЕНИЕ
        if not is_banned and user_id in self.moderation.ban_messages:
            await self.moderation.delete_ban_message(user_id, event.bot)

        if is_banned:
            reason = self.moderation.get_ban_reason(user_id)
            minutes = time_left // 60
            seconds = time_left % 60
            
            try:
                await event.delete()  # Удаляем сообщение
            except:
                pass
            
            message = await event.answer(
                f"🚫 Вы заблокированы!\n"
                f"📋 Причина: {reason}\n"
                f"⏱️ Осталось: {minutes}м {seconds}с"
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
        
        text = event.text.lower()
        
        # Считаем количество вхождений каждого слова
        total_bad_words = 0
        
        # Функция для нормализации текста (удаление спецсимволов и цифр)
        def normalize_text(s):
            return re.sub(r'[^а-яёa-z]', '', s)
        
        # Функция для замены кириллицы, похожей на латиницу
        def normalize_cyrillic_lookalikes(s):
            # Заменяем похожие символы: о->о, с->с, е->е и т.д.
            replacements = {
                'o': 'о',  # латинское O на кириллицу О
                'c': 'с',  # латинское C на кириллицу С
                'e': 'е',  # латинское E на кириллицу Е
                'p': 'р',  # латинское P на кириллицу Р
                'a': 'а',  # латинское A на кириллицу А
                'b': 'в',  # латинское B на кириллицу В
                'h': 'н',  # латинское H на кириллицу Н
                'k': 'к',  # латинское K на кириллицу К
                'm': 'м',  # латинское M на кириллицу М
                't': 'т',  # латинское T на кириллицу Т
                'x': 'х',  # латинское X на кириллицу Х
                'y': 'у',  # латинское Y на кириллицу У
            }
            result = s
            for lat, cyr in replacements.items():
                result = result.replace(lat, cyr)
            return result
    
        # Проверяем каждое слово
        words = text.split()
        
        for word in words:
            # Очищаем слово от спецсимволов
            cleaned = normalize_text(word)
            normalized = normalize_cyrillic_lookalikes(cleaned)
            # Проверка 1: с заменой похожих символов
            if normalized in self.bad_words:
                total_bad_words += 1
        # Проверка 2: потенциальные связки слов
        if self.check_trigger_light_proximity(words, set(self.words_light), set(self.words_triggers), max_distance=3):
            total_bad_words += 1
        # Проверка 3: длинные фразы
        for long_word in self.long_bad_words:
            cleaned_text = normalize_text(normalize_cyrillic_lookalikes(text))
            if long_word in cleaned_text:
                total_bad_words += 1
        
        if total_bad_words > 0:
            # Блокируем пользователя
            self.moderation.ban_user(user_id, "Недопустимая лексика")
            
            user_name = event.from_user.full_name
            minutes = self.moderation.ban_time // 60
            warnings = self.moderation.get_warnings_count(user_id)
            
            # Создаём кнопки
            builder = InlineKeyboardBuilder()
            builder.button(text="🟢 Разблокировать", callback_data=f"unban_user:{user_id}")
            builder.button(text="🔴 Выгнать из группы", callback_data=f"kick_user:{user_id}")
            builder.button(text="✅ Оставить наказание", callback_data=f"keep_ban:{user_id}")
            builder.button(text="📩 Посмотреть сообщение", callback_data=f"view_message:{user_id}")
            builder.adjust(1)
            
            try:
                await event.delete()
            except:
                pass
            
            recently_deleted[user_id] = event.text  # Сохраняем удалённое сообщение для просмотра
            message = await event.bot.send_message(
                chat_id=event.chat.id,
                text=(
                    f"🚫 <a href='tg://user?id={user_id}'>{user_name}</a> "
                    f"заблокирован на {minutes} мин!\n"
                    f"📋 Причина: Недопустимая лексика\n"
                    f"🔤 Найдено слов: {int(total_bad_words)}\n"
                    f"⚠️ Предупреждений: {warnings}"
                ),
                reply_markup=builder.as_markup()
            )
            # Сохраняем ID сообщения с кнопками
            self.moderation.set_ban_message(user_id, event.chat.id, message.message_id)
            return  # ← Не вызываем handler
        
        # Всё ок - пропускаем
        return await handler(event, data)