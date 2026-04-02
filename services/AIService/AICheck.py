from services.AIService.groqapi import router, asuna, promptguard, ai_moderation
from data.SystemPrompts.RouterPrompt import RouterPrompt
from data.SystemPrompts.AsunaRouterPrompt import AsunaRouterPrompt
from data.SystemPrompts.aiPrompt import prompt as generalPrompt
from data.SystemPrompts.aiCocPrompt import prompt as cocPrompt
from data.SystemPrompts.aiMemberPrompt import prompt as memberPrompt
from data.SystemPrompts.aiRulesPrompt import prompt as rulesPrompt
from data.SystemPrompts.aiSmertnikiPrompt import prompt as smertnikiPrompt
from services.AIService.AsunaJailbreakPhrases import randomReplica
from data.texts import BAN_WORDS, BAN_LONG, BAN_LIGHT, BAN_TRIGGERS
from utils.antimat import regex_fallback_moderation, apply_moderation_result
from utils import moderation as moderation_module
import config
import json
from commands.smertniki import smertnikiAdd, smertnikiRemove, smertnikiClear
from data.texts import RULES_SHORT, RULES_MAIN, RULES_CW, RULES_CWL, RULES_EVENTS, RULES_RAIDS, RULES_ROLES, RULES_PENALTIES

async def AICheckMessage(message):
    try:
        if not message.text:
            return False

        text = message.text
        startRouter = await router(text, RouterPrompt, "llama-3.1-8b-instant")

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
            gptoss120b = "openai/gpt-oss-120b"
            llama70b = "llama-3.3-70b-versatile"

            promptInjection = await promptguard(text, 0.5)
            if promptInjection:
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + randomReplica())
                return None
            
            asunaClassify = await router(text, AsunaRouterPrompt, "openai/gpt-oss-20b")
            route = asunaClassify.get("route")

            if route == "general":
                output = await asuna(text, generalPrompt, gptoss120b)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            elif route == "coc":
                param = asunaClassify.get("coc_mode")
                if param == "clan_members":
                    pass
                elif param == "current_war":
                    pass
                elif param == "raids":
                    pass
                elif param == "clan_info":
                    pass
                elif param.startswith("strategies_"):
                    pass
                elif param.startswith("layouts_"):
                    pass
            elif route == "rules":
                param = asunaClassify.get("rules_part")
                rules = {
                    "short": RULES_SHORT,
                    "main": RULES_MAIN,
                    "cw": RULES_CW,
                    "cwl": RULES_CWL,
                    "events": RULES_EVENTS,
                    "raids": RULES_RAIDS,
                    "kicks": RULES_PENALTIES,
                    "roles": RULES_ROLES
                }
                rule = rules[param]
                prompt = rulesPrompt + rule

                output = await asuna(text, prompt, llama70b)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            elif route == "smertniki":
                param = asunaClassify.get("smertniki_action")
                prompt = smertnikiPrompt + (str(config.SMERTNIKI) if config.SMERTNIKI else "Список смертников пуст")

                output = await asuna(text, prompt, llama70b)
                output = json.loads(output)
                users = output["users"]
                if message.from_user.id in config.ADMIN_IDS or param == "list" or param == "info":
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + output["text"])
                    if param == "add":
                        smertnikiAdd(users)
                    elif param == "remove":
                        smertnikiRemove(users)
                    elif param == "clear":
                        smertnikiClear()
                else:
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + "Нетушки. Я что-то не вижу в тебе админа, так что отказано")
            elif route == "member":
                param = asunaClassify.get("member_name")
            else:
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + "Такое я пока не могу сказать, но скоро смогу!")
                print(route)

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