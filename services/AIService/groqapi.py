from groq import AsyncGroq
from config import GROQ_API_KEY
from data.SystemPrompts.RouterPrompt import RouterPrompt
from data.SystemPrompts.AsunaRouterPrompt import AsunaRouterPrompt
import json
import asyncio

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

async def router(message, prompt):
    try:
        completion = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
            model="llama-3.3-70b-versatile",
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
            temperature=0.75,
            top_p=0.92,
            max_tokens=500
        )
        response = completion.choices[0].message.content
        return response
    except Exception as e:
        print(f"🔴 AsunaAI unexpected error: {e}")
        return False