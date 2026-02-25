import io
import time
from aiogram import Bot
from groq import AsyncGroq
from config import GROQ_API_KEY
from data.texts import BAN_WORDS, BAN_LONG
import re

client = AsyncGroq(api_key=GROQ_API_KEY)

async def voice_to_text(bot: Bot, file_id: str, language: str = "ru") -> tuple[str, float]:
    start = time.perf_counter()

    tg_file = await bot.get_file(file_id)

    buf = io.BytesIO()
    await bot.download_file(tg_file.file_path, buf)
    audio_bytes = buf.getvalue()

    resp = await client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=("voice.ogg", audio_bytes),
        language=language
    )

    elapsed = time.perf_counter() - start
    text = (getattr(resp, "text", None) or "").strip()

    # Проверка на запрещённые слова
    text_lower = text.lower()
    BAN = False
    if any(word in text_lower for word in BAN_WORDS):
        BAN = True
    cleaned_text = re.sub(r'[^а-яёa-z]', '', text_lower)
    for word in BAN_LONG:
        if word in cleaned_text:
            BAN = True

    return text, elapsed, BAN