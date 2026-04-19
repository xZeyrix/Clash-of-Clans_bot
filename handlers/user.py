import asyncio
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
import html
from utils.middlewares import PauseCheckMiddleware
from data.rules_texts import help_text, RULES_SHORT
from config.config_holder import config
from config.state_holder import state
from commands.rules import RULES_LIST, get_navigation_keyboard
from services.coc.clan import get_clan_info
from services.coc.war import get_war_info
from services.ai_system.groqapi_functions import voice_to_text
from commands.admin_moderation import admin_moderation_handler
from services.ai_system.asuna_ai import AICheckMessage

router = Router()
router.message.middleware(PauseCheckMiddleware())
router.edited_message.middleware(PauseCheckMiddleware())
router.callback_query.middleware(PauseCheckMiddleware())

@router.message(Command("start"))
async def start_command_handler(message: types.Message) -> None:
    await message.answer("Привет! Я бот, который соориентирует тебя по нашему клану «Остров 65» в игре Clash of Clans." + "\n\n" + help_text(message.from_user.id, message.from_user.full_name))

@router.message(Command("help"))
async def help_command_handler(message: types.Message) -> None:
    await message.answer(help_text(message.from_user.id, message.from_user.full_name))

@router.message(Command("short"))
async def short_rules_command_handler(message: types.Message) -> None:
    await message.answer(RULES_SHORT)

@router.message(Command("rules"))
async def rules_command_handler(message: types.Message) -> None:
    text = RULES_LIST[0]
    await message.answer(text, reply_markup=get_navigation_keyboard(0))
# Обработчик навигации по правилам
@router.callback_query(F.data.startswith("rules_page:"))
async def navigate_rules(callback: types.CallbackQuery) -> None:
    await callback.answer()
    page = int(callback.data.split(":")[1])
    text = RULES_LIST[page]
    await callback.message.edit_text(text, reply_markup=get_navigation_keyboard(page))

@router.message(Command("smertniki"))
async def smertniki_command_handler(message: types.Message) -> None:
    if state.smertniki:
        response = "📋 Список смертников:\n"
        for i, nickname in enumerate(state.smertniki, 1):
            response += f"<b>{i}.</b> {html.escape(nickname)}\n"
        await message.answer(response)
    else:
        await message.answer("📋 Список смертников пуст.")

@router.message(Command("getmyid"))
async def get_me_id_command_handler(message: types.Message) -> None:
    await message.answer(f"Ваш ID: <b>{message.from_user.id}</b>")

@router.message(Command("clan"))
async def clan_command_handler(message: types.Message) -> None:
    await get_clan_info(message)

@router.message(Command("war"))
async def war_command_handler(message: types.Message) -> None:
    await get_war_info(message)



# ================== ЭТОТ ХЕНДЛЕР ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ ==================
@router.message()
async def text_message_handler(message: types.Message) -> None:
    text = message.text or message.caption or ""

    ai = await AICheckMessage(message)
    if text.startswith("!") and ai:
        await admin_moderation_handler(message)

@router.edited_message()
async def edited_message_handler(message: types.Message) -> None:
    await AICheckMessage(message)