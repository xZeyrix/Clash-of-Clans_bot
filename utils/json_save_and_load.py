from datetime import datetime, timezone
import tempfile
import os
import json
from aiogram import Bot
from config.config_holder import config
from config.state_holder import state

async def load_bot_state(bot: Bot):
    """Загружает состояние бота из файла"""
    try:
        if os.path.exists(config.state_file):
            with open(config.state_file, 'r', encoding='utf-8') as f:
                bot_state = json.load(f)
                state.bot_paused = bot_state.get('paused', False)
                print(f"✅ Состояние бота загружено: {'На паузе' if state.bot_paused else 'Работает'}")
                if state.bot_paused:
                    await bot.send_message(config.chat_id, '🟢 Техническое обслуживание бота было завершено.\nВ прошлый раз бот был поставлен на паузу.\nЧтобы бот снова заработал, необходимо возобновить работу с помощью <b>/resume</b>.')
                else:
                    await bot.send_message(config.chat_id, '🟢 Техническое обслуживание бота было завершено.\nБот полностью готов к работе.')
        else:
            state.bot_paused = False
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке состояния бота: {e}")
        state.bot_paused = False

def save_bot_state():
    """Сохраняет текущее состояние бота в файл"""
    try:
        with open(config.state_file, 'w', encoding='utf-8') as f:
            json.dump({'paused': state.bot_paused}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка при сохранении состояния бота: {e}")
        
def load_smertniki():
    try:
        if os.path.exists(config.smertniki_file):
            # Если файл пустой — инициализируем пустым списком
            if os.path.getsize(config.smertniki_file) == 0:
                state.smertniki = []
                save_smertniki()
                return
            with open(config.smertniki_file, "r", encoding="utf-8") as f:
                try:
                    state.smertniki = json.load(f)
                except json.JSONDecodeError:
                    # Файл повреждён или содержит неправильный JSON — перезапишем пустым списком
                    state.smertniki = []
                    save_smertniki()
                    return
                # на случай, если файл имеет корректный JSON, но не список
                if not isinstance(state.smertniki, list):
                    state.smertniki = []
        # Лог загрузки
        try:
            with open(config.smertniki_log, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - load_smertniki - loaded {len(state.smertniki)} items\n")
        except Exception:
            pass
    except Exception:
        state.smertniki = []

def save_smertniki():
    # запись атомарно: сначала во временный файл в той же директории, потом replace/move
    try:
        tmp_dir = os.path.dirname(config.smertniki_file) or "."
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=tmp_dir) as tf:
            json.dump(state.smertniki, tf, ensure_ascii=False, indent=2)
            tmpname = tf.name
        try:
            os.replace(tmpname, config.smertniki_file)
        except OSError:
            # Возможна ошибка EXDEV (Invalid cross-device link) — используем копирование как фолбэк
            import shutil
            shutil.copyfile(tmpname, config.smertniki_file)
            os.remove(tmpname)
        # логируем успешную запись
        try:
            with open(config.smertniki_log, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - save_smertniki - saved {len(state.smertniki)} items\n")
        except Exception:
            pass
    except Exception:
        # логируем ошибку записи
        try:
            import traceback
            with open(config.smertniki_log, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - save_smertniki - ERROR:\n")
                lf.write(traceback.format_exc())
                lf.write("\n")
        except Exception:
            pass