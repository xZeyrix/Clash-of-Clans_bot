from services.ai_system.groqapi_functions import router, asuna, promptguard, ai_moderation, voice_to_text
from data.system_ai_prompts.main_router import RouterPrompt as router_prompt
from data.system_ai_prompts.asuna_router import AsunaRouterPrompt as asuna_router_prompt
from data.system_ai_prompts.asuna_general import longPrompt as general_prompt
from data.system_ai_prompts.asuna_coc import prompt as coc_prompt
from data.system_ai_prompts.asuna_member import prompt as member_prompt
from data.system_ai_prompts.asuna_rules import prompt as rules_prompt
from data.system_ai_prompts.asuna_smertniki import prompt as smertniki_prompt
from services.ai_system.asuna_jailbreak_phrases import randomReplica
from data.toxic_words_list import BAN_WORDS, BAN_LONG, BAN_LIGHT, BAN_TRIGGERS
from utils.moderation.antimat import regex_fallback_moderation, apply_moderation_result
from config.state_holder import state
from config.config_holder import config
from config.state_holder import state
import json
import html
from data.members_info import people
from commands.smertniki import smertnikiAdd, smertnikiRemove, smertnikiClear
from data.rules_texts import RULES_SHORT, RULES_MAIN, RULES_CW, RULES_CWL, RULES_EVENTS, RULES_RAIDS, RULES_ROLES, RULES_PENALTIES, RULES_INFO
from utils.cocapi_get_info import get_clan_info, get_clan_members, get_war_status, get_cwl_prep_members, get_cwl_status, get_raids
from utils.youtube_api import search_videos

async def AICheckMessage(message):
    try:
        if message.chat.id != config.talk_chat_id and message.chat.id != config.admin_ids[0]:
            return False

        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption
        elif message.voice:
            text, decryptedMessage = await voice_to_text(message)
            if not text:
                return
        else:
            return False
        
        history = list()
        promptInjection = await promptguard(text, 0.7)
        if promptInjection:
            await message.answer("💫 <b>Асуна</b>:\n\n" + randomReplica())
            return

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
                history = state.asuna_history[message.from_user.id]
            except:
                history = list()
        else:
            startRouter = await router(text, router_prompt, "llama-3.1-8b-instant", history)
            if not startRouter:
                return False
            action = startRouter.get("action")

        if action == "to_safeguard":
            ai_result = await ai_moderation(text)
            if ai_result is None:
                raise RuntimeError("Safeguard moderation returned None")

            if state.moderation is not None:
                await apply_moderation_result(message, state.moderation, ai_result)

            if ai_result["class"] == "safe":
                return True
            else:
                try:
                    if message.voice:
                        await decryptedMessage.delete()
                except:
                    pass
                return False

        if action == "to_asuna":
            response = await message.answer("💫 <b>Асуна</b>:\n\nПечатаю...")
            gptoss120b = "openai/gpt-oss-120b"
            llama70b = "llama-3.3-70b-versatile"
            
            asunaClassifyPrompt = asuna_router_prompt + str(people.keys())
            asunaClassify = await router(text, asunaClassifyPrompt, "openai/gpt-oss-20b", history)
            route = asunaClassify.get("route")

            if route == "general":
                output = await asuna(text, general_prompt, gptoss120b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            elif route == "coc":
                param = asunaClassify.get("coc_mode")
                if param == "strategies" or param == "layouts":
                    option = {
                        "strategies": lambda: search_videos('strategy'),
                        'layouts': lambda: search_videos('layout')
                    }
                    result = await option[param]()
                    titles = [x["title"] for x in result]
                    youtubeLinks = "\n".join(
                        f"{i}) <a href='{x['url']}'>Ссылка на ролик</a>"
                        for i, x in enumerate(result, 1)
                    )
                    prompt = coc_prompt + f"Ссылок нет. НО ты должна ответить пользователю, что ты нашла для него видео и стратегии, скажи что вот ссылки, НО НИКАКИЕ ССЫЛКИ ЕМУ НЕ ОТПРАВЛЯЙ. Просто на русском языке перескажи ВКРАТЦЕ содержимое {titles}, например, если там 3 огромных описания, несколькими русскими словами возьми все это в совокупности и не нарушая нормы/грамматику ответь пользователю вкратце по порядку, каждое ПРОНУМЕРУЙ (1-3). НЕ ПРЕДЛАГАЙ пользователю следующий шаг, т.е. никогда не говори по типу 'могу рассказать побольше о них если хочешь'. Конец твоего сообщения ДОЛЖЕН заканчиваться на знак ':', например 'вот ссылки:'. Подсказки по переводу с английского на русский: th -> тх, thrower -> метатель, dragon duke -> драгон дюк, root riders -> корни, grand warden -> дед, archer queen -> королева, barb king -> король, fireball -> огенный шар, revive -> возрождение, troop launcher -> войскомет, log launcher -> бревномет, siege barracks -> казармы, battle blimp -> дирик, flame flinger -> огнеметатель."

                    output = await asuna(text, prompt, llama70b, history)
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + output + f"\n{youtubeLinks}\n\n P.S. если захочешь что-то из этого использовать - у каждого ролика в описании есть ссылка на микс/базу")
                else:
                    cocCommands = {
                        "clan_members": get_clan_members,
                        "current_war": get_war_status,
                        "raids": get_raids,
                        "clan_info": get_clan_info,
                        "strategies": lambda: search_videos('strategy'),
                        "layouts": lambda: search_videos('layout')
                    }
                    result = await cocCommands[param]()
                    prompt = coc_prompt + str(result)

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
                prompt = rules_prompt + rule

                output = await asuna(text, prompt, llama70b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            elif route == "smertniki":
                param = asunaClassify.get("smertniki_action")
                prompt = smertniki_prompt + (str(state.smertniki) if state.smertniki else "Список смертников пуст")

                output = await asuna(text, prompt, llama70b, history)
                output = json.loads(output)
                users = output["users"]
                secondParam = output["action"]
                if message.from_user.id in config.admin_ids or param == "list" or param == "info":
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + output["text"])
                    if param == "add" and secondParam == "add":
                        smertnikiAdd(users)
                        await message.bot.send_message(config.chat_id, f"✅ <b>Асуна</b> добавляет в список смертников игрока/игроков: {html.escape(users)} по воле админа <b>{html.escape(message.from_user.full_name)}</b>")
                    elif param == "remove" and secondParam == "add":
                        smertnikiRemove(users)
                        await message.bot.send_message(config.chat_id, f"✅ <b>Асуна</b> удаляет из списка смертников игрока/игроков: {html.escape(users)} по воле админа <b>{html.escape(message.from_user.full_name)}</b>")
                    elif param == "clear" and secondParam == "clear":
                        smertnikiClear()
                        await message.bot.send_message(config.chat_id, f"✅ <b>Асуна</b> очищает список смертников по воле админа <b>{html.escape(message.from_user.full_name)}</b>")
                else:
                    await response.edit_text("💫 <b>Асуна</b>:\n\n" + "Нетушки. Я что-то не вижу в тебе админа, так что отказано")
            elif route == "member":
                param = asunaClassify.get("member_name")
                try:
                    prompt = member_prompt + people[param]
                except:
                    prompt = member_prompt + "Данные отсутствуют."

                output = await asuna(text, prompt, llama70b, history)
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + output)
            else:
                await response.edit_text("💫 <b>Асуна</b>:\n\n" + "An error occurred. Try again.")
                print(route)

            if route != "smertniki":
                state.asuna_history[message.from_user.id] = [{"role": "user", "content": text}, {"role": "assistant", "content": output}]
            else:
                state.asuna_history[message.from_user.id] = [{"role": "user", "content": text}, {"role": "assistant", "content": output["text"]}]
        return True

    except Exception as e:
        print(f"🔴 Unexpected error occured during the AISystem: {e}")
        try:
            text = (message.text or "").lower()
            fallback_result = regex_fallback_moderation(
                text=text,
                bad_words=BAN_WORDS,
                long_bad_words=BAN_LONG,
                words_light=BAN_LIGHT,
                words_triggers=BAN_TRIGGERS,
            )
            if state.moderation is not None:
                await apply_moderation_result(message, state.moderation, fallback_result)
        except Exception as fallback_error:
            print(f"🔴 Regex fallback failed: {fallback_error}")
        return False