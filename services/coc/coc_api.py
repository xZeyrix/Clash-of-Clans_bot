# --------------------------------
# 🟢 Clash of Clans API
# --------------------------------

import coc
from config.config_holder import config
from datetime import datetime, timezone, timedelta

coc_client = None

# Функция для авторизации в COC API
async def login_coc():
    global coc_client
    try:
        # Если уже есть активный клиент, закрываем его перед созданием нового
        if coc_client is not None:
            try:
                await coc_client.close()
            except:
                pass
        # Создаем новый клиент и авторизуемся
        coc_client = coc.Client()
        if config.dev_mode:
            await coc_client.login(config.coc_email, config.coc_password)
            print(f"✅ Успешный вход в Clash of Clans API через email - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        else:
            await coc_client.login_with_tokens(config.coc_api_key)
            print(f"✅ Успешный вход в Clash of Clans API через токен - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        return True
    except Exception as e:
        # Логируем ошибку с указанием времени и способа авторизации
        if config.dev_mode:
            print(f"⚠️ Ошибка при входе в Clash of Clans API через email: {e} - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        else:
            print(f"⚠️ Ошибка при входе в Clash of Clans API через токен: {e} - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        return False

async def close_coc():
    """Закрытие COC API клиента"""
    global coc_client
    if coc_client is not None:
        try:
            await coc_client.close()
            print("✅ COC API клиент закрыт")
        except Exception as e:
            print(f"⚠️ Ошибка при закрытии COC клиента: {e}")
        finally:
            coc_client = None