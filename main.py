import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, DEV_MODE
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from development.betatesters import  router as dev_router

from utils.filters import DevIdCheckMiddleware, AllowedUsersMiddleware
from utils.files import load_bot_state, load_smertniki
from utils.moderation import ModerationSystem
from utils.antispam import AntiSpamMiddleware
from utils.antimat import AntiMatMiddleware
from utils import moderation as moderation_module

from services.coc.coc_api import login_coc

from data.texts import BAN_WORDS, BAN_LONG, BAN_LIGHT, BAN_TRIGGERS

dp = Dispatcher()

# Мидлвари
if DEV_MODE:
    dp.message.middleware(DevIdCheckMiddleware())
else:
    dp.message.middleware(AllowedUsersMiddleware())

# Система модерации
moderation = ModerationSystem(ban_time=3600)
moderation_module.moderation = moderation

# Подключаем мидлвари
antispam = AntiSpamMiddleware(moderation, rate_limit=10, time_window=60)
antimat = AntiMatMiddleware(moderation, bad_words=BAN_WORDS, long_bad_words=BAN_LONG, words_light=BAN_LIGHT, words_triggers=BAN_TRIGGERS)

# Проверяем на маты, потом на спам
dp.message.middleware(antimat)
dp.message.middleware(antispam)
dp.callback_query.middleware(antispam)

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Регитсрация роутеров
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(dev_router)

    # Загрузка состояния бота и смертников
    await load_bot_state(bot)
    load_smertniki()

    # Авторизация COC API
    await login_coc()

    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Бот остановлен")