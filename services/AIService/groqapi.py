from groq import AsyncGroq
from config import GROQ_API_KEY
from data.SystemPrompts.moderationPrompt import prompt as modPrompt
import json
import asyncio
import time
import io
from data.texts import BAN_LONG, BAN_WORDS
import re
from aiogram import Bot

client = AsyncGroq(api_key=GROQ_API_KEY)

async def promptguard(message, detect):
    try:
        completion = await client.chat.completions.create(
            model="meta-llama/llama-prompt-guard-2-86m",
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ]
        )
        if float(completion.choices[0].message.content) > detect:
            return True
        else:
            return False
    except Exception as e:
        print(f"🔴 Promptguard unexpected error:: {e}")
        return None

async def router(message, prompt, model):
    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            temperature=0,
            top_p=1.0,
            max_tokens=100
        )
        try:
            response = json.loads(completion.choices[0].message.content)
            return response
        except json.JSONDecodeError:
            print("🔴 AIRouter error: The model output was not json. Probably prompt injection from user.")
    except Exception as e:
        print(f"🔴 AIRouter unexpected error: {e}")
        return False

async def asuna(message, prompt):
    try:
        completion = await client.chat.completions.create(
            # model="llama-3.3-70b-versatile",
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            temperature=0.72,
            top_p=0.88,
            max_tokens=500
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"🔴 AsunaAI unexpected error: {e}")
        return False

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
    BAN = False
    ai = await ai_moderation(text)
    reason = None

    if ai != None:
        if ai["class"] == "ban":
            BAN = True
            reason = ai["reason"]
    else:
        text_lower = text.lower()
        if any(word in text_lower for word in BAN_WORDS):
            BAN = True
        cleaned_text = re.sub(r'[^а-яёa-z]', '', text_lower)
        for word in BAN_LONG:
            if word in cleaned_text:
                BAN = True
        reason = "Недопустимая лексика"
    return text, elapsed, BAN, reason

async def ai_moderation(message):
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": modPrompt,
                },
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model="openai/gpt-oss-safeguard-20b",
        )
        response = chat_completion.choices[0].message.content
        data = json.loads(response)

        return data
    except Exception as e:
        print(f"🔴 В ходе проверки сообщения нейросетью произошла ошибка: {e}")
        return None