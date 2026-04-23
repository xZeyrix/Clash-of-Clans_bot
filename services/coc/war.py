from config.config_holder import config
from services.coc import coc_api
from services.coc.tag_utils import normalize_clan_tag
import html
from datetime import datetime

async def get_war_info(message) -> None:
    try:
        # Отправляем "печатаю..." для улучшения UX
        msg = await message.answer("⌛ Получаю информацию о войне...")

        # Парсим сообщение, чтобы получить тег клана
        parts = message.text.split()
        requested_tag = parts[1] if len(parts) > 1 else None
        clan_tag = normalize_clan_tag(requested_tag, config.clan_tag)

        if clan_tag is None:
            await msg.edit_text("⚠️ Не задан тег клана. Укажи тег в команде или настрой CLAN_TAG в .env")
            return None
        
        # Получаем информацию о войне
        try:
            try:
                war = await coc_api.coc_client.get_current_war(clan_tag)
                isCwlPreparation = False
            except:
                war = await coc_api.coc_client.get_league_group(clan_tag)
                isCwlPreparation = True
        except Exception as e:
            await msg.edit_text(f"⚠️ Такого клана не существует.")
            print(f"⚠️ Ошибка при получении информации о войне: {e}")
            return None
        
        # Проверка на наличие информации о войне
        if war == "private":
            await msg.edit_text("⚠️ Информация о войне недоступна (журнал войн закрыт).")
            return
        if war is None:
            await msg.edit_text("⚠️ Война не найдена или недоступна.")
            return
        if war.state == 'notInWar':
            await msg.edit_text("⚠️ Клан сейчас не воюет.")
            return

        if isCwlPreparation:
            months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
            response = (
                f"🏆 <b>ИДЕТ ПОДГОТОВКА К ЛВК!</b>\n\n"
                f"📅 Сезон: {months[datetime.now().month-1]}\n"
                f"⚔️ Впереди 7 дней сражений!\n\n"
            )
            await msg.edit_text(response)
        if not isCwlPreparation:
            # Вычисляем оставшееся время
            time_remaining = war.end_time.seconds_until
            hours = time_remaining // 3600
            minutes = (time_remaining % 3600) // 60
            
            # Формируем сообщение в зависимости от статуса
            if war.state == 'preparation':
                status_emoji = "⏳"
                status_text = "ДЕНЬ ПОДГОТОВКИ"
                time_text = f"До начала сражения: {hours-24}ч {minutes}м"
            elif war.state == 'inWar':
                status_emoji = "⚔️"
                status_text = "ДЕНЬ СРАЖЕНИЯ"
                time_text = f"До окончания войны: {hours}ч {minutes}м"
            elif war.state == 'warEnded':
                status_emoji = "🏁"
                status_text = "ВОЙНА ЗАВЕРШЕНА"
                time_text = f"Война закончилась {abs(hours)}ч {abs(minutes)}м назад"
            else:
                status_emoji = "❓"
                status_text = f"Неизвестный статус: {war.state}"
                time_text = ""
            
            # Формируем полное сообщение
            response = (
                f"{status_emoji} <b>{status_text}</b>\n\n"
                f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n\n"
                f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                f"💥 Разрушения: {war.clan.destruction:.2f}% : {war.opponent.destruction:.2f}%\n"
                f"⚔️ Атак использовано: {war.clan.attacks_used}/{war.team_size * 2} VS {war.opponent.attacks_used}/{war.team_size * 2}\n\n"
                f"👥 Размер: {war.team_size} на {war.team_size}\n"
                f"🕐 {time_text}"
            )
            await msg.edit_text(response)

    except Exception as e:
        await msg.edit_text("⚠️ Произошла ошибка при получении информации о войне.")
        print(f"⚠️ Ошибка при обработке команды get_war_info: {e}")