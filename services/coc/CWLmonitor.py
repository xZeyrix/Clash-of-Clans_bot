import coc
from services.coc import coc_api
from datetime import datetime, timezone, timedelta
from config import CLAN_TAG, CHAT_ID, ADMIN_IDS
import config
from aiogram import Bot
from utils.files import save_smertniki
CLAN_TAG = "#2QU8R8CRU"

# Состояния для отслеживания CWL
cwl_previous_state = None
cwl_league_season = None
cwl_war_notifications = {}  # Словарь {war_tag: {уведомления}}
cwl_preparation_notified = False
cwl_ended_notified = False

def reset_war_notifications_for_round(war_tag):
    """Сброс уведомлений для конкретного раунда CWL"""
    global cwl_war_notifications
    cwl_war_notifications[war_tag] = {
        'war_started': False,
        'hours_12': False,
        'hours_6': False,
        'hours_3': False,
        'hours_1': False,
        'war_ended': False
    }

async def get_war_day_number(league_group):
    """Определяет номер дня войны (1-7)"""
    try:
        day = 0
        async for war in league_group:
            if war.state == 'inWar' or war.state == 'warEnded':
                day += 1
        return day
    except:
        return None

async def check_war_status(bot: Bot):
    """Проверка статуса CWL (Лиги войн кланов)"""
    global cwl_previous_state, cwl_league_season, cwl_preparation_notified, cwl_ended_notified

    try:
        # Получаем информацию о лиге войн
        league_group = await coc_api.coc_client.get_league_group(CLAN_TAG)
        
        # Проверяем состояние лиги
        current_state = league_group.state
        
        # Состояние "preparation" - подготовка к CWL
        if current_state == 'preparation':
            # Проверяем, началась ли новая CWL (по season)
            current_season = league_group.season
            if cwl_league_season != current_season:
                cwl_league_season = current_season
                cwl_preparation_notified = False
                cwl_ended_notified = False
                cwl_war_notifications.clear()
            
            if not cwl_preparation_notified:
                # Отправляем уведомление о начале CWL
                message = (
                    f"🏆 <b>НАЧАЛАСЬ ЛИГА ВОЙН КЛАНОВ!</b>\n\n"
                    f"👥 Кланов в группе: {len(league_group.clans)}\n"
                    f"📅 Сезон: {league_group.season}\n"
                    f"⚔️ Впереди 7 дней сражений!\n\n"
                )
                await bot.send_message(CHAT_ID, message)
                cwl_preparation_notified = True
                print(f"✅ Отправлено уведомление о начале CWL - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
            
            cwl_previous_state = 'preparation'
            return
        
        # Состояние "inWar" - идут войны
        elif current_state == 'inWar':
            # Получаем текущую войну
            current_war = await coc_api.coc_client.get_current_war(CLAN_TAG, cwl_league=True)
            
            # Проверяем, что это действительно война CWL
            if not current_war or current_war.is_cwl is False:
                return
            
            war_tag = current_war.tag if hasattr(current_war, 'tag') else str(current_war.preparation_start_time.time.timestamp())
            
            # Определяем день войны (1-7)
            war_day = await get_war_day_number(league_group.get_wars_for_clan(CLAN_TAG))

            if war_day is None:
                war_day = "?"
            
            # Инициализируем уведомления для этой войны, если их еще нет
            if war_tag not in cwl_war_notifications:
                reset_war_notifications_for_round(war_tag)
            
            notifications = cwl_war_notifications[war_tag]
            
            # Вычисляем оставшееся время
            time_remaining = current_war.end_time.seconds_until
            hours_remaining = time_remaining // 3600
            minutes_remaining = (time_remaining % 3600) // 60
            
            # Уведомление о начале дня сражения
            if not notifications['war_started']:
                members_no_attacks = [m.name for m in current_war.clan.members if len(m.attacks) == 0]
                message = (
                    f"⚔️ <b>ДЕНЬ {war_day} - БИТВА НАЧАЛАСЬ!</b>\n\n"
                    f"🏰 <b>{current_war.clan.name}</b> VS <b>{current_war.opponent.name}</b>\n\n"
                    f"🔴 Атак использовано: {current_war.clan.attacks_used}/{current_war.team_size} VS {current_war.opponent.attacks_used}/{current_war.team_size}\n"
                    f"🟡 Звезды: {current_war.clan.stars}⭐️ : {current_war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {current_war.clan.destruction:.1f}% : {current_war.opponent.destruction:.1f}%\n\n"
                    f"🕐 До окончания: {int(hours_remaining)}ч {int(minutes_remaining)}мин"
                )
                await bot.send_message(CHAT_ID, message)
                notifications['war_started'] = True
                print(f"✅ Отправлено уведомление о начале дня {war_day} CWL")
            
            # Уведомления о времени (только во время боя)
            # Осталось 12 часов
            if hours_remaining <= 12 and not notifications['hours_12']:
                members_no_attacks = [m.name for m in current_war.clan.members if len(m.attacks) == 0]
                message = (
                    f"⏰ <b>ДЕНЬ {war_day} - ОСТАЛОСЬ 12 ЧАСОВ!</b>\n\n"
                    f"🟡 Звезды: {current_war.clan.stars}⭐️ : {current_war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {current_war.clan.destruction:.1f}% : {current_war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {current_war.clan.attacks_used}/{current_war.team_size} VS {current_war.opponent.attacks_used}/{current_war.team_size}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                notifications['hours_12'] = True
                print(f"✅ Отправлено уведомление: День {war_day}, осталось 12 часов")
            
            # Осталось 6 часов
            if hours_remaining <= 6 and not notifications['hours_6']:
                members_no_attacks = [m.name for m in current_war.clan.members if len(m.attacks) == 0]
                message = (
                    f"⏰ <b>ДЕНЬ {war_day} - ОСТАЛОСЬ 6 ЧАСОВ!</b>\n\n"
                    f"🟡 Звезды: {current_war.clan.stars}⭐️ : {current_war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {current_war.clan.destruction:.1f}% : {current_war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {current_war.clan.attacks_used}/{current_war.team_size} VS {current_war.opponent.attacks_used}/{current_war.team_size}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                notifications['hours_6'] = True
                print(f"✅ Отправлено уведомление: День {war_day}, осталось 6 часов")
            
            # Осталось 3 часа
            if hours_remaining <= 3 and not notifications['hours_3']:
                members_no_attacks = [m.name for m in current_war.clan.members if len(m.attacks) == 0]
                message = (
                    f"⏰ <b>ДЕНЬ {war_day} - ОСТАЛОСЬ 3 ЧАСА!</b>\n\n"
                    f"🟡 Звезды: {current_war.clan.stars}⭐️ : {current_war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {current_war.clan.destruction:.1f}% : {current_war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {current_war.clan.attacks_used}/{current_war.team_size} VS {current_war.opponent.attacks_used}/{current_war.team_size}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                notifications['hours_3'] = True
                print(f"✅ Отправлено уведомление: День {war_day}, осталось 3 часа")
            
            # Осталось 1 час
            if hours_remaining <= 1 and not notifications['hours_1']:
                members_no_attacks = [m.name for m in current_war.clan.members if len(m.attacks) == 0]
                message = (
                    f"🚨 <b>ДЕНЬ {war_day} - ПОСЛЕДНИЙ ЧАС!</b>\n\n"
                    f"🟡 Звезды: {current_war.clan.stars}⭐️ : {current_war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {current_war.clan.destruction:.1f}% : {current_war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {current_war.clan.attacks_used}/{current_war.team_size} VS {current_war.opponent.attacks_used}/{current_war.team_size}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                notifications['hours_1'] = True
                print(f"✅ Отправлено уведомление: День {war_day}, последний час")
            
            # Осталось <= 60 секунд - финальное сообщение об окончании дня
            if time_remaining <= 60 and not notifications['war_ended']:
                # Определяем результат дня
                if current_war.clan.stars > current_war.opponent.stars:
                    result = "🎉 <b>ПОБЕДА!</b> 🏆"
                    result_emoji = "🥇"
                elif current_war.clan.stars < current_war.opponent.stars:
                    result = "😔 <b>ПОРАЖЕНИЕ</b>"
                    result_emoji = "🥈"
                else:
                    # Если звезды равны, смотрим на разрушение
                    if current_war.clan.destruction > current_war.opponent.destruction:
                        result = "🎉 <b>ПОБЕДА!</b> 🏆"
                        result_emoji = "🥇"
                    elif current_war.clan.destruction < current_war.opponent.destruction:
                        result = "😔 <b>ПОРАЖЕНИЕ</b>"
                        result_emoji = "🥈"
                    else:
                        result = "🤝 <b>НИЧЬЯ!</b>"
                        result_emoji = "🤝"
                
                members_no_attacks = [m.name for m in current_war.clan.members if len(m.attacks) == 0]
                message = (
                    f"🏁 <b>ДЕНЬ {war_day} ЗАВЕРШЁН!</b>\n\n"
                    f"{result}\n\n"
                    f"🏰 <b>{current_war.clan.name}</b> VS <b>{current_war.opponent.name}</b>\n\n"
                    f"{result_emoji} Итоговый счёт:\n"
                    f"⭐️ Звёзды: {current_war.clan.stars} : {current_war.opponent.stars}\n"
                    f"💥 Разрушения: {current_war.clan.destruction:.1f}% : {current_war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {current_war.clan.attacks_used}/{current_war.team_size} VS {current_war.opponent.attacks_used}/{current_war.team_size}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали и автоматически добавлены в список смертников ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                await bot.send_message(CHAT_ID, message)
                
                # Добавляем не атаковавших в список смертников
                for name in members_no_attacks:
                    if name not in config.SMERTNIKI:
                        config.SMERTNIKI.append(name)
                    else:
                        for admin_id in ADMIN_IDS:
                            await bot.send_message(admin_id, f"⚠️ {name} уже 2 раза подряд пропустил атаки в CWL!")
                save_smertniki()
                
                notifications['war_ended'] = True
                print(f"✅ Отправлено уведомление: День {war_day} CWL завершён")
            
            cwl_previous_state = 'inWar'
        
        # Состояние "ended" - CWL завершена
        elif current_state == 'ended':
            if not cwl_ended_notified:
                # Получаем информацию о результатах
                try:
                    # Находим наш клан в группе
                    our_clan = None
                    for clan in league_group.clans:
                        if clan.tag == CLAN_TAG:
                            our_clan = clan
                            break
                    
                    if our_clan:
                        message = (
                            f"🏆 <b>ЛИГА ВОЙН КЛАНОВ ЗАВЕРШЕНА!</b>\n\n"
                            f"📊 <b>Итоги сезона:</b>\n"
                            f"🏰 Клан: {our_clan.name}\n"
                            f"🎖 Место: #{league_group.clans.index(our_clan) + 1} из {len(league_group.clans)}\n"
                            f"⭐️ Всего звёзд: {sum(getattr(clan, 'stars', 0) for clan in league_group.clans if clan.tag == CLAN_TAG)}\n\n"
                            f"Спасибо всем за участие! 💪"
                        )
                    else:
                        message = f"🏆 <b>ЛИГА ВОЙН КЛАНОВ ЗАВЕРШЕНА!</b>\n\nСпасибо всем за участие! 💪"
                    
                    await bot.send_message(CHAT_ID, message)
                    cwl_ended_notified = True
                    print("✅ Отправлено уведомление об окончании CWL")
                except Exception as e:
                    # Если не удалось получить детальную информацию, отправляем простое сообщение
                    message = f"🏆 <b>ЛИГА ВОЙН КЛАНОВ ЗАВЕРШЕНА!</b>\n\nСпасибо всем за участие! 💪"
                    await bot.send_message(CHAT_ID, message)
                    cwl_ended_notified = True
                    print(f"✅ Отправлено уведомление об окончании CWL (упрощённое): {e}")
            
            cwl_previous_state = 'ended'
    
    except coc.errors.GatewayError as e:
        # Если клан не участвует в CWL, это может вызвать ошибку
        if cwl_previous_state and cwl_previous_state != 'notInCWL':
            print(f"⚠️ Клан не участвует в CWL или недоступна информация: {e}")
            cwl_previous_state = 'notInCWL'
    except coc.PrivateWarLog:
        print("⚠️ Журнал войн клана скрыт")
    except coc.errors.Maintenance:
        print("⚠️ COC API на техническом обслуживании")
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса CWL: {e}")
        import traceback
        traceback.print_exc()