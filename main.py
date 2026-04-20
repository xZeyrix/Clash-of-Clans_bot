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

from config import config, state
from handlers import admin_router, user_router, beta_router

from utils import DevIdCheckMiddleware, AllowedUsersMiddleware
from utils import load_bot_state, load_smertniki
from utils.moderation import ModerationSystem, AntiMatMiddleware, AntiSpamMiddleware

from services.coc import login_coc, close_coc, stop_war_monitor

from data import BAN_LONG, BAN_WORDS, BAN_LIGHT, BAN_TRIGGERS

dp = Dispatcher()
shutdown_event = asyncio.Event()

# Middleware based on current mode
dp.message.middleware(DevIdCheckMiddleware()) if config.dev_mode else dp.message.middleware(AllowedUsersMiddleware())
dp.edited_message.middleware(DevIdCheckMiddleware()) if config.dev_mode else dp.edited_message.middleware(AllowedUsersMiddleware())
dp.callback_query.middleware(DevIdCheckMiddleware()) if config.dev_mode else dp.callback_query.middleware(AllowedUsersMiddleware())

moderation = ModerationSystem(ban_time=86400)
state.moderation = moderation

antispam = AntiSpamMiddleware(moderation, rate_limit=10, time_window=60)
antimat = AntiMatMiddleware(moderation, bad_words=BAN_WORDS, long_bad_words=BAN_LONG, words_light=BAN_LIGHT, words_triggers=BAN_TRIGGERS)

dp.message.middleware(antispam)
dp.message.middleware(antimat)
dp.edited_message.middleware(antimat)

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp.include_router(admin_router)
    dp.include_router(beta_router)
    dp.include_router(user_router)

    await load_bot_state(bot)
    load_smertniki()

    # To ignore all the messages while the bot was off
    await bot.delete_webhook(drop_pending_updates=True)

    # COC API Auth
    await login_coc()

    # Signals (for fallback)
    loop = asyncio.get_running_loop()
    setup_signal_handlers(loop, dp)

    try:
        await dp.start_polling(bot)
    finally:
        await shutdown(dp, bot)

async def shutdown(dp, bot):
    logging.info("The signal received. Stopping the bot...")
    
    # Stop COC war monitor
    stop_war_monitor()
    
    # Отправляем уведомление
    try:
        await asyncio.wait_for(
            bot.send_message(config.chat_id, "❗ Бот уходит на техобслуживание."),
            timeout=5.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        logging.error(f"An error occured while sending a message that the bot was stopped: {e}")
    
    # COC client close
    await close_coc()
    
    # Closing the bot & storage
    await bot.session.close()
    if dp.storage:
        await dp.storage.close()
    
    logging.info("The bot was succefully stopped.")


def setup_signal_handlers(loop, dp):
    def signal_handler(sig, frame):
        logging.info(f"\nThe signal received: {sig}, trying to stop the bot...")
        loop.call_soon_threadsafe(lambda: asyncio.create_task(dp.stop_polling()))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    max_restarts = 3
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            asyncio.run(main())
            break
        except KeyboardInterrupt:
            logging.info("Exit is in progress because Ctrl+C.")
            break
        except Exception:
            restart_count += 1
            logging.exception(f"The bot crashed (retry {restart_count}/{max_restarts})")
            if restart_count < max_restarts:
                logging.info("Reboot in 15 seconds...")
                time.sleep(15)