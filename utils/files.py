from config import SMERTNIKI_FILE, STATE_FILE, CHAT_ID, SMERTNIKI_LOG, bot_paused
from datetime import datetime, timezone
import tempfile
import os
import json
from aiogram import Bot
import config

async def load_bot_state(bot: Bot):
    """Загружает состояние бота из файла"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                config.bot_paused = state.get('paused', False)
                print(f"✅ Состояние бота загружено: {'На паузе' if config.bot_paused else 'Работает'}")
                if config.bot_paused:
                    await bot.send_message(CHAT_ID, '🟢 Техническое обслуживание бота было завершено.\nАдминистраторы, пожалуйста, запустите бота через <b>/resume</b>.')
                else:
                    config.bot_paused = True
                    save_bot_state()
                    await bot.send_message(CHAT_ID, '❗ В прошлый раз работа бота была завершена некорректно.\nАдминистраторы, пожалуйста, запустите бота через <b>/resume</b>.')
        else:
            config.bot_paused = False
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке состояния бота: {e}")
        config.bot_paused = False

def save_bot_state():
    """Сохраняет текущее состояние бота в файл"""
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'paused': config.bot_paused}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка при сохранении состояния бота: {e}")
        
def load_smertniki():
    try:
        if os.path.exists(SMERTNIKI_FILE):
            # Если файл пустой — инициализируем пустым списком
            if os.path.getsize(SMERTNIKI_FILE) == 0:
                config.SMERTNIKI = []
                save_smertniki()
                return
            with open(SMERTNIKI_FILE, "r", encoding="utf-8") as f:
                try:
                    config.SMERTNIKI = json.load(f)
                except json.JSONDecodeError:
                    # Файл повреждён или содержит неправильный JSON — перезапишем пустым списком
                    config.SMERTNIKI = []
                    save_smertniki()
                    return
                # на случай, если файл имеет корректный JSON, но не список
                if not isinstance(config.SMERTNIKI, list):
                    config.SMERTNIKI = []
        # Лог загрузки
        try:
            with open(SMERTNIKI_LOG, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - load_smertniki - loaded {len(config.SMERTNIKI)} items\n")
        except Exception:
            pass
    except Exception:
        config.SMERTNIKI = []

def save_smertniki():
    # запись атомарно: сначала во временный файл в той же директории, потом replace/move
    try:
        tmp_dir = os.path.dirname(SMERTNIKI_FILE) or "."
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=tmp_dir) as tf:
            json.dump(config.SMERTNIKI, tf, ensure_ascii=False, indent=2)
            tmpname = tf.name
        try:
            os.replace(tmpname, SMERTNIKI_FILE)
        except OSError:
            # Возможна ошибка EXDEV (Invalid cross-device link) — используем копирование как фолбэк
            import shutil
            shutil.copyfile(tmpname, SMERTNIKI_FILE)
            os.remove(tmpname)
        # логируем успешную запись
        try:
            with open(SMERTNIKI_LOG, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - save_smertniki - saved {len(config.SMERTNIKI)} items\n")
        except Exception:
            pass
    except Exception:
        # логируем ошибку записи
        try:
            import traceback
            with open(SMERTNIKI_LOG, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - save_smertniki - ERROR:\n")
                lf.write(traceback.format_exc())
                lf.write("\n")
        except Exception:
            pass