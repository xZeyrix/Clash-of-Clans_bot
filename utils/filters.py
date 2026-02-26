from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Any, Dict, Awaitable
from config import ADMIN_IDS, DEV_ID, CHAT_ID, TALK_CHAT_ID,  BETA_TESTERS_IDS, BETA_BANNED_IDS
import config
from development.betatesters import  get_allow_keyboard

# Проверка на админов
class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id in ADMIN_IDS:
            return await handler(event, data)
        # Не пропускаем дальше, если id не разрешён
        # await event.answer("У вас нет доступа к этой функции.")
        # Не вызываем handler, обработка останавливается

# Проверка на разработчика (для DEV_MODE)
class DevIdCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id == 1 or event.from_user.id in config.BETA_TESTERS_IDS:
            return await handler(event, data)
        elif event.from_user.id not in config.BETA_BANNED_IDS:
            await event.answer("‼️ У вас нет доступа к данному боту.\nОтправить разрабочику запрос на одобрение?", reply_markup=get_allow_keyboard(event.from_user.id, event.from_user.full_name))
        # Не пропускаем дальше, если id не разрешён
        # await event.answer("У вас нет доступа к этому боту.")
        # Не вызываем handler, обработка останавливается

# Проверка на разрешенных юзеров
class AllowedUsersMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id in ADMIN_IDS or event.chat.id == CHAT_ID or event.chat.id == TALK_CHAT_ID:
            return await handler(event, data)
        # Не пропускаем дальше, если id не разрешён
        # await event.answer("У вас нет доступа к этому боту.")
        # Не вызываем handler, обработка останавливается

# Проверка на паузу бота
class PauseCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        import config
        
        # # Пропускаем админов даже когда бот на паузе
        # if event.from_user.id in config.ADMIN_IDS:
        #     return await handler(event, data)
        
        # Для остальных проверяем паузу
        if not config.bot_paused:
            return await handler(event, data)
        
        # await event.answer("⏸️ Бот временно на паузе")
        return