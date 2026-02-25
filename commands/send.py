import html

async def send_message(message, CHAT_ID):
    if message.content_type != "text" and message.content_type != "photo":
            await message.answer("❌ Поддерживаются только текстовые сообщения и фотографии.\nПример: /send Ваше сообщение или /send (текст с фото)")
            return
    if message.content_type == "text":
        text = message.text.split(maxsplit=1)
        if len(text) < 2:
            await message.answer("❌ Пожалуйста, укажите текст для отправки.\nПример: /send Ваше сообщение")
            return
        text = (
            f"📢 Сообщение от <a href='tg://user?id={message.from_user.id}'><b>{html.escape(message.from_user.full_name)}</b></a>:\n\n"
            f"{html.escape(text[1])}"
        )
        await message.bot.send_message(CHAT_ID, text)
    elif message.content_type == "photo":
        caption = message.caption.split(maxsplit=1)
        caption = (
            f"📢 Сообщение от <a href='tg://user?id={message.from_user.id}'><b>{html.escape(message.from_user.full_name)}</b></a>:\n\n"
            f"{html.escape(caption[1]) if len(caption) > 1 else 'Без описания'}"
        )
        await message.bot.send_photo(CHAT_ID, message.photo[-1].file_id, caption=caption)