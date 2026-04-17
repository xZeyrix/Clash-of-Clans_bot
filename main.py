# NON-COMMERCIAL CLASH OF CLANS COMMUNITY LICENSE
# Short summary: non-commercial use only.
# Full license: LICENSES/NON-COMMERCIAL_FULL.md

import asyncio
import logging
import sys
import signal
import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from config import BOT_TOKEN, DEV_MODE, CHAT_ID
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from handlers.betatesters import  router as dev_router

from utils.filters import DevIdCheckMiddleware, AllowedUsersMiddleware
from utils.files import load_bot_state, load_smertniki, save_bot_state
from utils.moderation.moderation import ModerationSystem
from utils.moderation.antispam import AntiSpamMiddleware
from utils.moderation.antimat import AntiMatMiddleware
from utils.moderation import moderation as moderation_module

from services.coc.coc_api import login_coc
from services.coc.monitor import stop_war_monitor

from data.texts import BAN_WORDS, BAN_LONG, BAN_LIGHT, BAN_TRIGGERS

dp = Dispatcher()
shutdown_event = asyncio.Event()

# Мидлвари
if DEV_MODE:
    dp.message.middleware(DevIdCheckMiddleware())
else:
    dp.message.middleware(AllowedUsersMiddleware())

# Система модерации
moderation = ModerationSystem(ban_time=86400)
moderation_module.moderation = moderation

# Подключаем мидлвари
antispam = AntiSpamMiddleware(moderation, rate_limit=10, time_window=60)
antimat = AntiMatMiddleware(moderation, bad_words=BAN_WORDS, long_bad_words=BAN_LONG, words_light=BAN_LIGHT, words_triggers=BAN_TRIGGERS)

# Проверяем на маты, потом на спам
dp.message.middleware(antispam)
dp.message.middleware(antimat)
dp.edited_message.middleware(antimat)

async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Регистрация роутеров
    dp.include_router(admin_router)
    dp.include_router(dev_router)
    dp.include_router(user_router)

    # Загрузка состояния бота и смертников
    await load_bot_state(bot)
    load_smertniki()

    # Авторизация COC API
    await login_coc()

    # Настройка обработчиков сигналов
    loop = asyncio.get_running_loop()
    setup_signal_handlers(loop, dp)

    # Запуск поллинга (теперь ждём его завершения)
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown(dp, bot)

async def shutdown(dp, bot):
    print("🛑 Получен сигнал завершения, останавливаем бот...")
    
    config.bot_paused = True
    save_bot_state()
    
    # Останавливаем мониторинг войны
    stop_war_monitor()
    
    # Отправляем уведомление
    try:
        await asyncio.wait_for(
            bot.send_message(CHAT_ID, "⏸️ Бот приостановлен."),
            timeout=5.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        print(f"⚠️ Не удалось отправить уведомление: {e}")
    
    # Закрываем COC клиент
    from services.coc.coc_api import close_coc
    await close_coc()
    
    # Закрываем бота
    await bot.session.close()
    if dp.storage:
        await dp.storage.close()
    
    print("✅ Бот остановлен корректно")


def setup_signal_handlers(loop, dp):
    """Настройка обработчиков сигналов (кросс-платформенно)"""
    def signal_handler(sig, frame):
        print(f"\n🛑 Получен сигнал {sig}, инициируем остановку...")
        # Останавливаем polling изящно
        loop.call_soon_threadsafe(lambda: asyncio.create_task(dp.stop_polling()))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    max_restarts = 3
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            asyncio.run(main())
            break  # Нормальный выход
        except KeyboardInterrupt:
            print("Выход по Ctrl+C")
            break
        except Exception:
            restart_count += 1
            logging.exception(f"💥 Bot crashed (попытка {restart_count}/{max_restarts})")
            if restart_count < max_restarts:
                print("⏳ Перезапуск через 15 секунд...")
                time.sleep(15)