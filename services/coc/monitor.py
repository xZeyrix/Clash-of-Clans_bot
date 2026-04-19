from services.coc.cw_monitor import check_war_status
from services.coc.cwl_monitor import check_war_status as check_cwl_status
import asyncio
from aiogram import Bot
from services.coc import coc_api
from config.config_holder import config

war_monitor_active = False
war_monitor_task = None 

async def war_monitor_loop(bot: Bot):
    """
    Бесконечный цикл мониторинга войны.
    Запускается как фоновая задача через asyncio.create_task()
    """
    global war_monitor_active
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    print("▶️ Мониторинг войны запущен")
    
    while war_monitor_active:
        try:
            try:
                cwl = await coc_api.coc_client.get_league_group(config.clan_tag)
                cw = None
            except Exception as e:
                cwl = None
                cw = await coc_api.coc_client.get_current_war(config.clan_tag)
            if cwl is not None:
                await check_cwl_status(bot)
            elif cw is not None:
                await check_war_status(bot)
            consecutive_errors = 0  # Сбрасываем счётчик при успешном выполнении
            
        except Exception as e:
            consecutive_errors += 1
            print(f"❌ Ошибка в мониторинге войны ({consecutive_errors}/{max_consecutive_errors}): {e}")
            
            # Если слишком много ошибок подряд, делаем длинную паузу
            if consecutive_errors >= max_consecutive_errors:
                print("⚠️ Слишком много ошибок подряд, делаем длинную паузу...")
                await asyncio.sleep(300)  # 5 минут паузы
                consecutive_errors = 0
        
        await asyncio.sleep(30)  # Проверка каждые 30 секунд
    
    print("⏹️ Мониторинг войны остановлен")
    
# Остановка мониторинга войны
def stop_war_monitor():
    """Выключает флаг мониторинга"""
    global war_monitor_active
    war_monitor_active = False
    print("🛑 Флаг мониторинга войны снят")

# Функция для запуска мониторинга войны (создаёт задачу, если нужно)
async def start_war_monitor(bot: Bot):
    """Запускает мониторинг войны (создает задачу если нужно)"""
    global war_monitor_task, war_monitor_active
    
    # Если задача уже запущена и активна
    if war_monitor_task and not war_monitor_task.done():
        if war_monitor_active:
            return "⚠️ Мониторинг войны уже активен"
        else:
            # Задача есть, но флаг выключен - включаем
            war_monitor_active = True
            return "▶️ Мониторинг войны возобновлен"
    
    # Создаем новую задачу
    war_monitor_active = True
    war_monitor_task = asyncio.create_task(war_monitor_loop(bot))
    return "▶️ Мониторинг войны запущен"