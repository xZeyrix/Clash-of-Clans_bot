from groq import AsyncGroq
from config.config_holder import config
from data.system_ai_prompts.antitoxic_moderation import prompt as modPrompt
import json
import time
import io

client = AsyncGroq(api_key=config.groq_api_key)

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
        raise Exception(f"🔴 Promptguard unexpected error:: {e}")

async def router(message, prompt, model, history=[]):
    try:
        system = [
            {
                "role": "system",
                "content": prompt
            }
        ]
        user = [
            {
                "role": "user",
                "content": message
            }
        ]
        messages = system + history + user
        if model == "llama-3.1-8b-instant":
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                top_p=1.0,
                max_tokens=100,
                response_format={"type": "json_object"}
            )
        else:
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                top_p=1.0,
                max_tokens=200,
                reasoning_effort="low",
                response_format={"type": "json_object"}
            )
        try:
            response = json.loads(completion.choices[0].message.content)
            print(response)
            return response
        except json.JSONDecodeError:
            print(f"🔴 AIRouter error: The model output was not json. Probably inappropriate content or prompt injection:\n{completion.choices[0].message.content}")
            return {"route": "general"}
    except Exception as e:
        print(f"🔴 AIRouter unexpected error: {e}")
        return False

async def asuna(message, prompt, model, history=[], temperature=0.9):
    try:
        system = [
            {
                "role": "system",
                "content": prompt
            }
        ]
        user = [
            {
                "role": "user",
                "content": message
            }
        ]
        messages = system + history + user
        completion = await client.chat.completions.create(
            # model="llama-3.3-70b-versatile",
            # model="openai/gpt-oss-120b",
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=0.95,
            max_tokens=500
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"🔴 AsunaAI unexpected error: {e}")
        return False

async def voice_to_text(message, language: str = "ru") -> tuple[str, float]:
    try:
        start = time.perf_counter()
        
        duration = message.voice.duration # секунды
        duration_minutes = duration // 60 # минуты
        estimated_time = 1 + duration * 0.03
        if duration > 600:
            await message.answer("❌ Голосовое сообщение слишком длинное (макс 10 минут).")
            return False, False

        response = await message.answer(
            f"⏳ Распознаю голосовое ({duration_minutes} мин {duration} сек)...\n"
            f"⏱️ Это займет около: {estimated_time:.2f} секунд"
        )

        tg_file = await message.bot.get_file(message.voice.file_id)

        buf = io.BytesIO()
        await message.bot.download_file(tg_file.file_path, buf)
        audio_bytes = buf.getvalue()

        resp = await client.audio.transcriptions.create(
            model="whisper-large-v3",
            prompt = "Групповой чат в Telegram. Иногда упоминается имя ИИ-агента Асуна. Правильно пишется именно 'Асуна'. Остальной текст — обычный разговор между людьми.",
            file=("voice.ogg", audio_bytes),
            language=language
        )

        elapsed = time.perf_counter() - start
        text = (getattr(resp, "text", None) or "").strip()

        if not text or text == "Продолжение следует..." or text == "Продолжение следует." or text == "Продолжение следует":
            await response.edit_text("❌ Не удалось распознать речь.")
            return None, response

        await response.edit_text(
            f"🔄️ Преобразовано в текст:\n\n{text}\n\n⏱️ Время распознавания: {elapsed:.2f} секунд"
        )

        return text, response
    except Exception as e:
        print(f"🔴 An error occured in voice_to_text function: {e}")
        return False
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