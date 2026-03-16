import io
import time
import json
from aiogram import Bot
from groq import AsyncGroq
from config import GROQ_API_KEY
from data.texts import BAN_WORDS, BAN_LONG
import re
from data.moderationPrompt import prompt as modPrompt
from data.aiPrompt import prompt as aiPrompt

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

async def ai_promptguard(message, detect):
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
        if float(completion.choices[0].message.content) <= detect:
            return True
        else:
            return False
    except Exception as e:
        print(f"🔴 В ходе проверки сообщения промптгуардом произошла ошибка: {e}")
        return None

async def ai_chat(message):
    try:
        if not message.text:
            await ("❗ Простите, но я не умею обрабатывать что-то помимо текста.")
            return
        if message.text.startswith("/ai"):
            parts = message.text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                await message.answer("❗ Напишите запрос после команды.\nНапример: /ai расскажи про клановые войны\nТакже, вы можете обратиться ко мне по имени без команды - просто «Асуна»")
                return
            text = parts[1]
        else:
            text = message.text
        response = await message.answer("💫 <b>Асуна</b>:\n\nПечатаю...")
        promptguard = await ai_promptguard(text, 0.5)
        if promptguard is True:
            chat_completion = await client.chat.completions.create(
                #
                # Required parameters
                #
                messages=[
                    # Set an optional system message. This sets the behavior of the
                    # assistant and can be used to provide specific instructions for
                    # how it should behave throughout the conversation.
                    {
                        "role": "system",
                        "content": aiPrompt
                    },
                    # Set a user message for the assistant to respond to.
                    {
                        "role": "user",
                        "content": text,
                    }
                ],

                # The language model which will generate the completion.
                #model="llama-3.1-8b-instant",
                model="llama-3.3-70b-versatile",

                #
                # Optional parameters
                #

                # Controls randomness: lowering results in less random completions.
                # As the temperature approaches zero, the model will become
                # deterministic and repetitive.
                temperature=0.7,

                # The maximum number of tokens to generate. Requests can use up to
                # 2048 tokens shared between prompt and completion.
                max_completion_tokens=500,

                # Controls diversity via nucleus sampling: 0.5 means half of all
                # likelihood-weighted options are considered.
                top_p=0.9,

                # A stop sequence is a predefined or user-specified text string that
                # signals an AI to stop generating content, ensuring its responses
                # remain focused and concise. Examples include punctuation marks and
                # markers like "[end]".
                stop=None,

                # If set, partial message deltas will be sent.
                stream=False,
            )
            await response.edit_text("💫 <b>Асуна</b>:\n\n" + chat_completion.choices[0].message.content)
        elif promptguard is False:
            chat_completion = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": aiPrompt
                    },
                    {
                        "role": "user",
                        "content": "Тебя только что пытались взломать"
                    }
                ]
            )
            await response.edit_text("💫 <b>Асуна</b>:\n\n" + chat_completion.choices[0].message.content)
        elif promptguard is None:
            await message.answer("🔴 Упс! Произошла ошибка: Модерация не смогла проверить данный запрос на безопасность\nПопробуйте еще раз через несколько минут")

    except Exception as e:
        print(f"🔴 В ходе AI-чата произошла ошибка: {e}")
        await message.answer("🔴 Упс! Произошла непредвиденная ошибка\nПопробуйте еще раз через несколько минут")