from services.AIService.groqapi import router, asuna, promptguard
from services.groqapi import ai_moderation
from data.SystemPrompts.RouterPrompt import RouterPrompt
from data.SystemPrompts.AsunaRouterPrompt import AsunaRouterPrompt
from data.SystemPrompts.aiPrompt import prompt
from services.AIService.AsunaJailbreakPhrases import randomReplica
from data.texts import BAN_WORDS, BAN_LONG, BAN_LIGHT, BAN_TRIGGERS
from utils.antimat import regex_fallback_moderation, apply_moderation_result
from utils import moderation as moderation_module

async def AICheckMessage(message):
    try:
        if not message.text:
            return False

        text = message.text
        startRouter = await router(text, RouterPrompt)

        if not startRouter:
            return False

        action = startRouter.get("action")

        if action == "to_safeguard":
            ai_result = await ai_moderation(text)
            if ai_result is None:
                raise RuntimeError("Safeguard moderation returned None")

            moderation = moderation_module.moderation
            if moderation is not None:
                await apply_moderation_result(message, moderation, ai_result)
            return None

        if action == "to_asuna":
            response = await message.answer("💫 <b>Асуна</b>:\n\nПечатаю...")

            promptInjection = await promptguard(text, 0.5)
            if promptInjection:
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + randomReplica())
                return None
            
            asunaClassify = await router(text, AsunaRouterPrompt)
            route = (asunaClassify or {}).get("route")

            if route == "general":
                output = await asuna(text, prompt)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            else:
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + "Такое я пока не могу сказать, но скоро смогу!")
                print(route)

            return None

        return False

    except Exception as e:
        print(f"🔴 Unexpected error occured during the AICheck: {e}")
        try:
            text = (message.text or "").lower()
            fallback_result = regex_fallback_moderation(
                text=text,
                bad_words=BAN_WORDS,
                long_bad_words=BAN_LONG,
                words_light=BAN_LIGHT,
                words_triggers=BAN_TRIGGERS,
            )
            moderation = moderation_module.moderation
            if moderation is not None:
                await apply_moderation_result(message, moderation, fallback_result)
        except Exception as fallback_error:
            print(f"🔴 Regex fallback failed: {fallback_error}")
        return False