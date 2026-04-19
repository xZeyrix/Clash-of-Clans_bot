import os
from dotenv import load_dotenv
from dataclasses import dataclass
from pathlib import Path

load_dotenv()

@dataclass(frozen=True)
class Config:
    # Dev mode (turn off at deploy)
    dev_mode: bool

    # Telegram
    chat_id: int
    talk_chat_id: int
    bot_token: str

    admin_ids: list[int]
    dev_id: int

    # COC
    coc_email: str | None
    coc_password: str | None
    clan_tag: str | None
    coc_api_key: str

    # API
    groq_api_key: str
    youtube_api_key: str

    # Paths
    base_dir: str
    json_dir: str
    smertniki_file: str
    state_file: str
    smertniki_log: str

def load_config() -> Config:
    dev_mode = os.getenv("DEV_MODE", "true").lower() == "true"

    base_dir = Path.cwd()
    json_dir = os.path.join(base_dir, "data/json_files")

    return Config(
        dev_mode=dev_mode,

        chat_id=int(os.getenv("DEV_NOTIFICATIONS_CHAT_ID" if dev_mode else "NOTIFICATIONS_CHAT_ID")),
        talk_chat_id=int(os.getenv("DEV_TALK_CHAT_ID" if dev_mode else "TALK_CHAT_ID")),
        bot_token=os.getenv("DEV_TELEGRAM_BOT_TOKEN" if dev_mode else "TELEGRAM_BOT_TOKEN"),

        admin_ids=[int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x],
        dev_id=int(os.getenv("DEVELOPER_USER_ID")),

        coc_email=os.getenv("COC_EMAIL"),
        coc_password=os.getenv("COC_PASSWORD"),
        clan_tag=os.getenv("CLAN_TAG"),
        coc_api_key=os.getenv("DEV_COC_API_KEY" if dev_mode else "COC_API_KEY"),

        groq_api_key=os.getenv("DEV_GROQ_API_KEY" if dev_mode else "GROQ_API_KEY"),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY"),

        base_dir=base_dir,
        json_dir=json_dir,
        smertniki_file=os.path.join(json_dir, "smertniki.json"),
        state_file=os.path.join(json_dir, "bot_state.json"),
        smertniki_log=os.path.join(json_dir, "smertniki.log")
    )