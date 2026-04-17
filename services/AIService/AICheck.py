from services.AIService.groqapi import router, asuna, promptguard, ai_moderation
from data.SystemPrompts.RouterPrompt import RouterPrompt
from data.SystemPrompts.AsunaRouterPrompt import AsunaRouterPrompt
from data.SystemPrompts.aiPrompt import longPrompt as generalPrompt
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
import html
from data.people import people
from commands.smertniki import smertnikiAdd, smertnikiRemove, smertnikiClear
from data.texts import RULES_SHORT, RULES_MAIN, RULES_CW, RULES_CWL, RULES_EVENTS, RULES_RAIDS, RULES_ROLES, RULES_PENALTIES, RULES_INFO
from utils.cocCommands import get_clan_info, get_clan_members, get_war_status, get_cwl_prep_members, get_cwl_status, get_raids

async def AICheckMessage(message):
    try:
        if message.chat.id != config.TALK_CHAT_ID and message.chat.id != config.ADMIN_IDS[0]:
            return False

        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption
        else:
            return False
        
        history = list()
        promptInjection = await promptguard(text, 0.7)
        if promptInjection:
            await message.answer("💫 <b>Асуна</b>:\n\n" + randomReplica())
            return None

        reply = message.reply_to_message
        reply_text = (reply.text or reply.caption or "") if reply else ""

        is_reply_to_bot = bool(
            reply
            and reply.from_user
            and message.bot
            and reply.from_user.id == message.bot.id
        )

        # Чтобы не реагировать на reply к любому сообщению бота,
        # ограничиваемся только сообщениями с префиксом Асуны.
        is_reply_to_asuna = is_reply_to_bot and reply_text.startswith("💫 Асуна:")

        if is_reply_to_asuna:
            action = "to_asuna"
            try:
                history = config.ASUNA_HISTORY[message.from_user.id]
            except:
                history = list()
        else:
            startRouter = await router(text, RouterPrompt, "llama-3.1-8b-instant", history)
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

            if ai_result["class"] == "safe":
                return True
            else:
                return False

        if action == "to_asuna":
            response = await message.answer("💫 <b>Асуна</b>:\n\nПечатаю...")
            gptoss120b = "openai/gpt-oss-120b"
            llama70b = "llama-3.3-70b-versatile"
            
            asunaClassifyPrompt = AsunaRouterPrompt + str(people.keys())
            asunaClassify = await router(text, asunaClassifyPrompt, "openai/gpt-oss-20b", history)
            route = asunaClassify.get("route")

            if route == "general":
                output = await asuna(text, generalPrompt, gptoss120b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            elif route == "coc":
                param = asunaClassify.get("coc_mode")
                if param.startswith("strategies_") or param.startswith("layouts_"):
                    prompt = cocPrompt + "Не нашлось подходящих стратегий/расстановок. Ответь, что ты в этом не разбираешься."
                else:
                    cocCommands = {
                        "clan_members": get_clan_members,
                        "current_war": get_war_status,
                        "raids": get_raids,
                        "clan_info": get_clan_info,
                    }
                    result = await cocCommands[param]()
                    prompt = cocPrompt + str(result)
                output = await asuna(text, prompt, llama70b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
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
                    "roles": RULES_ROLES,
                    "info": RULES_INFO
                }
                rule = rules[param]
                prompt = rulesPrompt + rule

                output = await asuna(text, prompt, llama70b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            elif route == "smertniki":
                param = asunaClassify.get("smertniki_action")
                prompt = smertnikiPrompt + (str(config.SMERTNIKI) if config.SMERTNIKI else "Список смертников пуст")

                output = await asuna(text, prompt, llama70b, history)
                output = json.loads(output)
                users = output["users"]
                secondParam = output["action"]
                if message.from_user.id in config.ADMIN_IDS or param == "list" or param == "info":
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + output["text"])
                    if param == "add" and secondParam == "add":
                        smertnikiAdd(users)
                        await message.bot.send_message(config.CHAT_ID, f"✅ <b>Асуна</b> добавляет в список смертников игрока/игроков: {html.escape(users)} по воле админа <b>{html.escape(message.from_user.full_name)}</b>")
                    elif param == "remove" and secondParam == "add":
                        smertnikiRemove(users)
                        await message.bot.send_message(config.CHAT_ID, f"✅ <b>Асуна</b> удаляет из списка смертников игрока/игроков: {html.escape(users)} по воле админа <b>{html.escape(message.from_user.full_name)}</b>")
                    elif param == "clear" and secondParam == "clear":
                        smertnikiClear()
                        await message.bot.send_message(config.CHAT_ID, f"✅ <b>Асуна</b> очищает список смертников по воле админа <b>{html.escape(message.from_user.full_name)}</b>")
                else:
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + "Нетушки. Я что-то не вижу в тебе админа, так что отказано")
            elif route == "member":
                param = asunaClassify.get("member_name")
                try:
                    prompt = memberPrompt + people[param]
                except:
                    prompt = memberPrompt + "Данные отсутствуют."

                output = await asuna(text, prompt, llama70b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            else:
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + "An error occurred. Try again.")
                print(route)

            if route != "smertniki":
                config.ASUNA_HISTORY[message.from_user.id] = [{"role": "user", "content": text}, {"role": "assistant", "content": output}]
            else:
                config.ASUNA_HISTORY[message.from_user.id] = [{"role": "user", "content": text}, {"role": "assistant", "content": output["text"]}]
        return True

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