import asyncio
import html
from config import config

async def admin_moderation_handler(message):
    if not message.reply_to_message:
        response = await message.answer("❗ Чтобы использовать эту команду, вы должны ответить на сообщение пользователя, против которого собираетесь принять меры.\n\nДоступные команды: !unban | !kick\nПример использования: !unmute [причина]")
        await asyncio.sleep(7)
        await response.delete()
        return
    elif not message.reply_to_message:
        response = await message.answer("❗ Чтобы использовать эту команду, вы должны ответить на сообщение пользователя, против которого собираетесь принять меры.\n\nДоступные команды: !unban | !kick\nПример использования: !unmute [причина]")
        await asyncio.sleep(7)
        await response.delete()
        return
    parts = message.text.split(maxsplit=1)
    reason = html.escape(parts[1]) if len(parts) == 2 else "Причина не указана"
    user_id = message.reply_to_message.from_user.id
    if parts[0] == "!unban":
        try:
            from utils.moderation.moderation import moderation
            moderation.unban_user(user_id)
            response = await message.answer("✅ Успешно!\nПользователь вновь получил право слова")
            await message.bot.send_message(config.chat_id, f"❗Админ <a href='tg://user?id={message.from_user.id}'>{html.escape(message.from_user.full_name)}</a> предоставил пользователю <a href='tg://user?id={user_id}'>{html.escape(message.reply_to_message.from_user.full_name)}</a> право слова.\nПричина: {reason}")
            await asyncio.sleep(3)
            await response.delete()
            return
        except Exception as e:
            response = await message.answer("❌ Не удалось разбанить пользователя.\nВозможно, он уже не в бане или произошла ошибка.")
            await asyncio.sleep(3)
            await response.delete()
            return

    elif parts[0] == "!kick":
        try:
            await message.bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=user_id
            )
            response = await message.answer("✅ Успешно!\nПользователь был выгнан из чата")
            await message.bot.send_message(config.chat_id, f"❗Админ <a href='tg://user?id={message.from_user.id}'>{html.escape(message.from_user.full_name)}</a> выгоняет из группы пользователя <a href='tg://user?id={user_id}'>{html.escape(message.reply_to_message.from_user.full_name)}</a>.\nПричина: {reason}")
            await asyncio.sleep(3)
            await response.delete()
            return
        except Exception as e:
            response = await message.answer("❌ Не удалось выгнать пользователя.\nВозможно, он уже не в группе или произошла ошибка.")
            await asyncio.sleep(3)
            await response.delete()
            return
    else:
        response = await message.answer("❗ Неизвестная команда.\nДоступные команды: !unmute | !kick")
        await asyncio.sleep(4)
        await response.delete()
        return