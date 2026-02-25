# --------------------------------
# 🟢 Clash of Clans API
# --------------------------------

import coc
from config import COC_API_TOKEN, COC_EMAIL, COC_PASSWORD, DEV_MODE
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
        if DEV_MODE:
            await coc_client.login(COC_EMAIL, COC_PASSWORD)
            print(f"✅ Успешный вход в Clash of Clans API через email - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        else:
            await coc_client.login_with_tokens(COC_API_TOKEN)
            print(f"✅ Успешный вход в Clash of Clans API через токен - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        return True
    except Exception as e:
        # Логируем ошибку с указанием времени и способа авторизации
        if DEV_MODE:
            print(f"⚠️ Ошибка при входе в Clash of Clans API через email: {e} - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        else:
            print(f"⚠️ Ошибка при входе в Clash of Clans API через токен: {e} - {datetime.now(timezone(timedelta(hours=5))).isoformat()} РК")
        return False