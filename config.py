# --------------------------------
# 🟢 Конфигурационные параметры
# --------------------------------

import os
from dotenv import load_dotenv

load_dotenv()

# Режим разработки (отключать при деплое)
DEV_MODE = True

# Telegram
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if DEV_MODE:
    CHAT_ID, TALK_CHAT_ID = int(os.getenv("DEV_NOTIFICATION_CHAT_ID")), int(os.getenv("DEV_NOTIFICATION_CHAT_ID"))
else:
    CHAT_ID = int(os.getenv("NOTIFICATION_CHAT_ID"))
    TALK_CHAT_ID = int(os.getenv("COMMUNICATION_CHAT_ID"))

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS").split(",")]
DEV_ID = int(os.getenv("DEVELOPER_USER_ID"))
BETA_TESTERS_IDS = []
BETA_BANNED_IDS = []

bot_paused = False

# Clash of Clans
COC_EMAIL = os.getenv("COC_EMAIL")
COC_PASSWORD = os.getenv("COC_PASSWORD")
CLAN_TAG = os.getenv("CLAN_TAG")
COC_API_TOKEN = os.getenv("COC_API_TOKEN")

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SMERTNIKI_FILE = os.path.join(DATA_DIR, "smertniki.json")
STATE_FILE = os.path.join(DATA_DIR, "bot_state.json")
SMERTNIKI_LOG = os.path.join(DATA_DIR, "smertniki.log")
SMERTNIKI = []