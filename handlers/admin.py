from aiogram import Router, types, F
from aiogram.filters import Command
from services.coc import monitor
from utils.filters import AdminCheckMiddleware
from utils.files import save_bot_state
from services.coc.monitor import start_war_monitor, stop_war_monitor
import config
from config import DEV_MODE
import html
from config import CHAT_ID
from data.texts import ADMIN_TEXT
from commands.send import send_message
import logging
from commands.smertniki import smertniki

router = Router()
if not DEV_MODE:
    router.message.middleware(AdminCheckMiddleware())
    router.callback_query.middleware(AdminCheckMiddleware())

# -----------------------------------------------
#              Обработчики команд
# -----------------------------------------------

@router.message(Command("admin"))
async def admin_command_handler(message: types.Message) -> None:
    await message.answer(ADMIN_TEXT)

@router.message(Command("send"))
async def send_message_handler(message: types.Message) -> None:
    await send_message(message, CHAT_ID)

@router.message(Command("getchatid"))
async def get_chat_id_handler(message: types.Message) -> None:
    await message.answer(f"ID этого чата: <b>{message.chat.id}</b>")

@router.message(Command("pause"))
async def pause_command_handler(message: types.Message) -> None:
    config.bot_paused = True
    save_bot_state()
    await message.bot.send_message(CHAT_ID, "⏹️ Бот приостановлен администраторами. Он не будет отвечать на команды, пока не будет возобновлён.")

@router.message(Command("resume"))
async def resume_command_handler(message: types.Message) -> None:
    config.bot_paused = False
    save_bot_state()
    await message.bot.send_message(CHAT_ID, "▶️ Бот возобновлён администраторами. Он снова будет отвечать на команды.")

@router.message(Command("sm"))
async def smertniki_command_handler(message: types.Message) -> None:
    await smertniki(message)

@router.message(Command("mstart"))
async def start_war_monitor_handler(message: types.Message) -> None:
    result = await start_war_monitor(message.bot)
    await message.answer(result)

@router.message(Command("mstop"))
async def stop_war_monitor_handler(message: types.Message) -> None:
    stop_war_monitor()
    await message.answer("⏹️ Мониторинг войны остановлен")

@router.message(Command("mstatus"))
async def war_monitor_status_handler(message: types.Message) -> None:
    status = "✅ Активен" if monitor.war_monitor_active else "❌ Остановлен"
    task_status = ""
    if monitor.war_monitor_task:
        if monitor.war_monitor_task.done():
            task_status = "\n🔴 Задача завершена"
        else:
            task_status = "\n🟢 Задача работает"
    else:
        task_status = "\n⚪️ Задача не создана"
    
    await message.answer(f"📊 <b>Статус мониторинга войны:</b>\n{status}{task_status}")

@router.message(Command("mod"))
async def moderation_toggle_handler(message: types.Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or parts[1].lower() not in ["on", "off"]:
        await message.answer("❗ Использование: /mod [on | off]")
        return
    
    if parts[1].lower() == "on":
        config.MODERATION_ENABLED = True
        await message.answer("✅ Модерация включена")
    elif parts[1].lower() == "off":
        config.MODERATION_ENABLED = False
        await message.answer("❎ Модерация отключена")

# -----------------------------------------------
#              Обработчики кнопок
# -----------------------------------------------

@router.callback_query(F.data.startswith("unban_user:"))
async def unban_user_handler(callback: types.CallbackQuery) -> None:
    from utils.moderation import moderation  # ← Импортируем общую систему
    
    user_id = int(callback.data.split(":")[1])
    
    # Разблокируем пользователя
    success = moderation.unban_user(user_id)
    
    if success:
        await callback.answer("✅ Пользователь разблокирован")
        await callback.bot.send_message(chat_id=callback.message.chat.id, text=f"❗ Пользователь <a href='tg://user?id={user_id}'>{user_id}</a> был разблокирован админом <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.full_name}</a>")
        # ← УДАЛЯЕМ СООБЩЕНИЕ С КНОПКАМИ
        await moderation.delete_ban_message(user_id, callback.bot)
    else:
        await callback.answer("❌ Пользователь не был заблокирован", show_alert=True)

@router.callback_query(F.data.startswith("kick_user:"))
async def kick_user_handler(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])
    
    try:
        await callback.bot.ban_chat_member(
            chat_id=callback.message.chat.id,
            user_id=user_id
        )
        await callback.answer("✅ Пользователь выгнан")
        await callback.bot.send_message(chat_id=callback.message.chat.id, text=f"❗ Пользователь <a href='tg://user?id={user_id}'>{user_id}</a> был выгнан админом <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.full_name}</a>")
        await callback.message.edit_text(
            callback.message.text + "\n\n🔴 Выгнан администратором"
        )
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

@router.callback_query(F.data.startswith("keep_ban:"))
async def keep_ban_handler(callback: types.CallbackQuery) -> None:
    await callback.answer("✅ Наказание сохранено")
    await callback.message.delete()

@router.callback_query(F.data.startswith("view_message:"))
async def view_message_handler(callback: types.CallbackQuery) -> None:
    from utils.antimat import recently_deleted  # ← Импортируем словарь с удалёнными сообщениями

    user_id = int(callback.data.split(":")[1])

    if user_id in recently_deleted:
        original_message = recently_deleted[user_id]
        await callback.answer("📩 Исходное сообщение:", show_alert=True)
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"📩 Сообщение от <a href='tg://user?id={user_id}'>{user_id}</a>:\n\n{html.escape(original_message)}"
        )
    else:
        await callback.answer("❌ Исходное сообщение недоступно", show_alert=True)