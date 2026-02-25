from config import CLAN_TAG
from services.coc import coc_api
import html

async def get_clan_info(message) -> None:
    try:
        # Парсим сообщение, чтобы получить тег клана
        parts = message.text.split()
        clan_tag = parts[1] if len(parts) > 1 else CLAN_TAG

        # Если тег не начинается с '#', добавляем его
        if not clan_tag.startswith('#'):
            clan_tag = '#' + clan_tag
        
        # Получаем информацию о клане
        try:
            # Убираем login_coc() отсюда - он должен быть вызван один раз при старте
            clan = await coc_api.coc_client.get_clan(clan_tag)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка при получении информации о клане.")
            print(f"⚠️ Ошибка при получении информации о клане: {e}")
            return None
        
        # Формируем ответ с информацией о клане
        if clan:
            response = (
                f"🏰 <b>{html.escape(clan.name)}</b> ({html.escape(clan.tag)}), {clan.level} уровень\n\n"
                f"👥 Участников: {clan.member_count}/50\n"
                f"🔰 Лига ЛВК: {html.escape(clan.war_league.name)}\n"
                f"⚔️ Войны: {clan.war_wins} побед, {clan.war_losses} поражений\n"
                f"🔥 Серия побед в войнах: {clan.war_win_streak}\n\n"
                f"💬 Описание: {html.escape(clan.description) if clan.description else 'Нет описания'}\n"
                f"🔗 Ссылка на клан: {clan.share_link}"
            )     
            await message.answer(response)
        else:
            await message.answer("⚠️ Клан не найден или недоступен.")
    except Exception as e:
        await message.answer("⚠️ Произошла ошибка при получении информации о клане.")
        print(f"⚠️ Ошибка при обработке команды get_clan_info: {e}")