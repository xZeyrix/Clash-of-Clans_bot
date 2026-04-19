from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Any, Dict, Awaitable
from config.config_holder import config
from config.state_holder import state
from handlers.betatesters import  get_allow_keyboard

class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id in config.admin_ids:
            return await handler(event, data)

class DevIdCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id == config.dev_id or event.from_user.id in state.beta_testers_ids:
            return await handler(event, data)
        elif event.from_user.id not in state.beta_banned_ids:
            await event.answer("‼️ У вас нет доступа к данному боту.\nОтправить разрабочику запрос на одобрение?", reply_markup=get_allow_keyboard(event.from_user.id, event.from_user.full_name))

class AllowedUsersMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id in config.admin_ids or event.chat.id == config.chat_id or event.chat.id == config.talk_chat_id:
            return await handler(event, data)

class PauseCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        if not state.bot_paused:
            return await handler(event, data)