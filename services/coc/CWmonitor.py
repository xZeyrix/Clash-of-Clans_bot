import coc
from services.coc import coc_api
from datetime import datetime, timezone, timedelta
from config import CLAN_TAG, CHAT_ID, ADMIN_IDS
import config
from aiogram import Bot
from utils.files import save_smertniki

war_previous_state = None
war_last_data = None
war_notifications_sent = {
    'preparation_started': False,
    'war_started': False,
    'hours_12': False,
    'hours_6': False,
    'hours_3': False,
    'hours_1': False,
    'war_ended': False,
    'war_almost_ended': False,
    'current_war_tag': None
}

def reset_war_notifications():
    global war_notifications_sent
    war_notifications_sent = {
        'preparation_started': False,
        'war_started': False,
        'hours_12': False,
        'hours_6': False,
        'hours_3': False,
        'hours_1': False,
        'war_ended': False,
        'war_almost_ended': False,
        'current_war_tag': war_notifications_sent.get('current_war_tag')
    }

async def check_war_status(bot: Bot):
    global war_previous_state, war_last_data

    try:
        war = await coc_api.coc_client.get_current_war(CLAN_TAG)

        if war.state == 'notInWar':
            if war_previous_state == 'InWar':
                war_data = war_last_data
                war_last_data = None

            if war_notifications_sent['current_war_tag'] is not None:
                reset_war_notifications()
                war_notifications_sent['current_war_tag'] = None
            
            war_previous_state = 'notInWar'
            return
        
        war_id = f"{war.preparation_start_time.time.timestamp()}"
        if war_notifications_sent['current_war_tag'] != war_id:
            reset_war_notifications()
            war_notifications_sent['current_war_tag'] = war_id
        
        time_remaining = war.end_time.seconds_until
        hours_remaining = time_remaining // 3600
        minutes_remaining = (time_remaining % 3600) // 60
        
        if war.state == 'preparation' and not war_notifications_sent['preparation_started']:
            message = (
                f"⏳ <b>ОБЪЯВЛЕНА ВОЙНА!</b>\n\n"
                f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n"
                f"👥 Война: {war.team_size} на {war.team_size}\n"
                f"🕐 До начала дня сражения: {int(hours_remaining-24)}ч {int(minutes_remaining)}мин"
            )
            await bot.send_message(CHAT_ID, message)
            war_notifications_sent['preparation_started'] = True
            print(f"✅ Отправлено уведомление о начале подготовки к войне - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")

        elif war.state == 'inWar':
            if not war_notifications_sent['war_started']:
                message = (
                    f"⚔️ <b>ДЕНЬ СРАЖЕНИЙ НАЧАЛСЯ!</b>\n\n"
                    f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                    f"🕐 До окончания: {int(hours_remaining)}ч {int(minutes_remaining)}мин"
                )
                await bot.send_message(CHAT_ID, message)
                war_notifications_sent['war_started'] = True
                print("✅ Отправлено уведомление о начале войны")
            
            # Проверяем уведомления о времени (только во время боя)
            # Осталось 12 часов
            if hours_remaining < 12 and not war_notifications_sent['hours_12']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"⏰ <b>ОСТАЛОСЬ 12 ЧАСОВ!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                war_notifications_sent['hours_12'] = True
                print("✅ Отправлено уведомление: осталось 12 часов")
            
            # Осталось 6 часов
            if hours_remaining < 6 and not war_notifications_sent['hours_6']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"⏰ <b>ОСТАЛОСЬ 6 ЧАСОВ!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                war_notifications_sent['hours_6'] = True
                print("✅ Отправлено уведомление: осталось 6 часов")
            
            # Осталось 3 часа
            if hours_remaining < 3 and not war_notifications_sent['hours_3']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"⏰ <b>ОСТАЛОСЬ 3 ЧАСА!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                war_notifications_sent['hours_3'] = True
                print("✅ Отправлено уведомление: осталось 3 часа")
            
            # Осталось 1 час
            if hours_remaining < 1 and not war_notifications_sent['hours_1']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"🚨 <b>ПОСЛЕДНИЙ ЧАС!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                war_notifications_sent['hours_1'] = True
                print("✅ Отправлено уведомление: последний час")
            
            # Осталось <= 60 секунд - отправляем финальное сообщение об окончании войны
            if time_remaining <= 60 and not war_notifications_sent['war_almost_ended']:
                # Определяем результат
                if war.clan.stars > war.opponent.stars:
                    result = "🎉 <b>ПОБЕДА!</b> 🏆"
                    result_emoji = "🥇"
                elif war.clan.stars < war.opponent.stars:
                    result = "😔 <b>ПОРАЖЕНИЕ</b>"
                    result_emoji = "🥈"
                else:
                    # Если звезды равны, смотрим на разрушение
                    if war.clan.destruction > war.opponent.destruction:
                        result = "🎉 <b>ПОБЕДА!</b> 🏆"
                        result_emoji = "🥇"
                    elif war.clan.destruction < war.opponent.destruction:
                        result = "😔 <b>ПОРАЖЕНИЕ</b>"
                        result_emoji = "🥈"
                    else:
                        result = "🤝 <b>НИЧЬЯ!</b>"
                        result_emoji = "🤝"
                
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"🏁 <b>ВОЙНА ЗАВЕРШЕНА!</b>\n\n"
                    f"{result}\n\n"
                    f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n\n"
                    f"{result_emoji} Итоговый счёт:\n"
                    f"⭐️ Звёзды: {war.clan.stars} : {war.opponent.stars}\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {war.clan.attacks_used}/{war.team_size * 2}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали и автоматически добавлены в список смертников({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                for name in members_no_attacks:
                    if name not in config.SMERTNIKI:
                        config.SMERTNIKI.append(name)
                    else:
                        for admin_id in ADMIN_IDS:
                            await bot.send_message(admin_id, f"⚠️ {name} уже 2 раза подряд пропустил атаки в войне!")
                save_smertniki()
                war_notifications_sent['war_almost_ended'] = True
                print("✅ Отправлено уведомление: война почти завершена (осталось <= 60 секунд)")
            
            # Сохраняем данные о войне для уведомления об окончании
            war_last_data = war
        war_previous_state = war.state
        
    except coc.PrivateWarLog:
        print("Журнал войн клана скрыт")
    except coc.errors.Maintenance:
        print("⚠️ COC API на техническом обслуживании")
    except coc.errors.GatewayError as e:
        print(f"⚠️ Ошибка соединения с COC API (Gateway): {e}")
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса войны: {e}")
        import traceback
        traceback.print_exc()