import asyncio
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
import html
from utils.filters import PauseCheckMiddleware
from data.texts import help_text, RULES_SHORT
import config
from commands.rules import RULES_LIST, get_navigation_keyboard
from services.coc.clan import get_clan_info
from services.coc.war import get_war_info
from services.AIService.groqapi import voice_to_text
from commands.adminModeration import admin_moderation_handler
from services.AIService.AICheck import AICheckMessage

router = Router()
router.message.middleware(PauseCheckMiddleware())

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
    if config.SMERTNIKI:
        response = "📋 Список смертников:\n"
        for i, nickname in enumerate(config.SMERTNIKI, 1):
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

@router.message(F.voice)
async def voice_message_handler(message: types.Message) -> None:
    if not message.voice:
        return
    
    duration = message.voice.duration # секунды
    duration_minutes = duration // 60 # минуты
    estimated_time = 0.5 + duration * 0.03
    if duration > 600:
        await message.answer("❌ Голосовое сообщение слишком длинное (макс 10 минут).")
        return

    response = await message.answer(
        f"⏳ Распознаю голосовое ({duration_minutes} мин {duration} сек)...\n"
        f"⏱️ Это займет около: {estimated_time:.2f} секунд"
        )

    text, elapsed, BAN, reason = await voice_to_text(message.bot, message.voice.file_id)

    if not text:
        await response.edit_text("❌ Не удалось распознать речь.")
        return
    
    if BAN:
        await message.delete()
        await response.edit_text(f"🚫 Ваше голосовое сообщение содержит недопустимую лексику и было удалено.\nПричина: {reason}")
        await asyncio.sleep(7)
        await response.delete()
        return

    await response.edit_text(
        f"🔄️ Преобразовано в текст:\n\n{text}\n\n⏱️ Время распознавания: {elapsed:.2f} секунд"
    )

# ================== ЭТОТ ХЕНДЛЕР ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ ==================
@router.message()
async def text_message_handler(message: types.Message) -> None:
    text = message.text or message.caption or ""

    if text.startswith("!"):
        await admin_moderation_handler(message)
    await AICheckMessage(message)

@router.edited_message()
async def edited_message_handler(message: types.Message) -> None:
    await AICheckMessage(message)