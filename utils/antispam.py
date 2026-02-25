from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Callable, Dict, Any, Awaitable, Union
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class AntiSpamMiddleware(BaseMiddleware):
    """Middleware для защиты от спама"""
    
    def __init__(self, moderation_system, rate_limit: int = 10, time_window: int = 60):
        self.moderation = moderation_system
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.user_messages = defaultdict(list)
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = datetime.now()
        
         # Пропускаем админские callback (разблокировка/кик)
        if isinstance(event, CallbackQuery):
            if event.data and (
                event.data.startswith("unban_user:") or 
                event.data.startswith("kick_user:") or
                event.data.startswith("keep_ban:") or
                event.data.startswith("view_message:")
            ):
                return await handler(event, data)  # Пропускаем без проверок

        # ========== ПРОВЕРКА БАНА ДОЛЖНА БЫТЬ ПЕРВОЙ ==========
        is_banned, time_left = self.moderation.is_banned(user_id)

        # ← УДАЛЯЕМ СООБЩЕНИЕ ПРИ АВТОМАТИЧЕСКОМ РАЗБАНЕ
        if not is_banned and user_id in self.moderation.ban_messages:
            await self.moderation.delete_ban_message(user_id, event.bot)

        if is_banned:
            reason = self.moderation.get_ban_reason(user_id)
            minutes = time_left // 60
            seconds = time_left % 60
            
            if isinstance(event, Message):
                try:
                    await event.delete()  # Удаляем сообщение забаненного
                except:
                    pass
                message = await event.answer(
                    f"🚫 Вы заблокированы!\n"
                    f"📋 Причина: {reason}\n"
                    f"⏱️ Осталось: {minutes}м {seconds}с"
                )
                await asyncio.sleep(3)  # Удаляем уведомление через 5 секунд
                try:
                    await message.delete()
                except:
                    pass
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    f"🚫 Заблокированы ({reason}). Осталось: {minutes}м {seconds}с",
                    show_alert=True
                )
            return  # ← ВАЖНО! Не вызываем handler
        
        # Только для сообщений проверяем спам
        if not isinstance(event, Message):
            return await handler(event, data)
        
        # Очищаем старые записи
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if now - msg_time < timedelta(seconds=self.time_window)
        ]
        
        # Проверяем лимит
        if len(self.user_messages[user_id]) >= self.rate_limit:
            # Блокируем пользователя
            self.moderation.ban_user(user_id, "Спам")
            
            user_name = event.from_user.full_name
            minutes = self.moderation.ban_time // 60
            warnings = self.moderation.get_warnings_count(user_id)
            
            # Создаём кнопки управления
            builder = InlineKeyboardBuilder()
            builder.button(text="🟢 Разблокировать", callback_data=f"unban_user:{user_id}")
            builder.button(text="🔴 Выгнать из группы", callback_data=f"kick_user:{user_id}")
            builder.button(text="✅ Оставить наказание", callback_data=f"keep_ban:{user_id}")
            builder.adjust(1)
            
            try:
                await event.delete()
            except:
                pass
            
            message = await event.bot.send_message(
                chat_id=event.chat.id,
                text=(
                    f"🚫 <a href='tg://user?id={user_id}'>{user_name}</a> "
                    f"заблокирован на {minutes} мин!\n"
                    f"📋 Причина: Спам\n"
                    f"⚠️ Предупреждений: {warnings}"
                ),
                reply_markup=builder.as_markup()
            )
            # Сохраняем ID сообщения с кнопками
            self.moderation.set_ban_message(user_id, event.chat.id, message.message_id)
            return  # ← Не вызываем handler
        
        # Добавляем текущее сообщение
        self.user_messages[user_id].append(now)
        
        return await handler(event, data)