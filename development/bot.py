import html
import re
import telebot
from telebot import types, apihelper

import coc

import os
from dotenv import load_dotenv
from functools import wraps

import json
import tempfile
from datetime import datetime, timezone
import time
import threading
import asyncio

from dev import init_dev_mode

# -----------------------------------------------
# Загрузка переменных окружения
# -----------------------------------------------

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

# Включаем middleware ДО создания бота
apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(TOKEN)

# Режим разработчика - бот реагирует только на указанного пользователя
init_dev_mode(bot, dev_id=1611458070)

# Флаг для паузы бота
bot_paused = False

# Список разрешённых ID пользователей
ALLOWED_USER_IDS = [1611458070, 417007190, 8376879508]  # Добавьте ваши ID сюда
# Абсолютные пути к файлам рядом с main.py, чтобы не зависеть от текущей директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SMERTNIKI_FILE = os.path.join(BASE_DIR, "smertniki.json")
SMERTNIKI_LOG = os.path.join(BASE_DIR, "smertniki.log")
BOT_STATE_FILE = os.path.join(BASE_DIR, "bot_state.json")
CHATIK_ID = int(os.getenv("NOTIFICATION_CHAT_ID", "1611458070"))
COC_EMAIL = os.getenv("COC_EMAIL")
COC_PASSWORD = os.getenv("COC_PASSWORD")
COC_API_TOKEN = os.getenv("COC_API_TOKEN")
CLAN_TAG = os.getenv("CLAN_TAG")
if not COC_EMAIL or not COC_PASSWORD or not COC_API_TOKEN or not CLAN_TAG:
    raise ValueError("Почта, пароль, API токен или тег клана для COC не найдены в переменных окружения")

SMERTNIKI = []
BAN_LONG = [
    'третий рейх',
    'купить голоса',
    'купить лайки',
    'купить фолловеров',
    'куплю аккаунт',
    'продам аккаунт',
    'ты тварь',
    'ты урод',
    'иди на хуй',
    'пошел на хуй',
]
BAN_WORDS = [
    # Расистские оскорбления
    'чурка',
    'чуркобес',
    'чурки',
    'хачик',
    'хачи',
    'басурман',
    'нежидь',
    
    # Экстремистские термины
    'фашист',
    'нацист',
    'геббельс',
    'третий рейх',
    
    # Сексуальные оскорбления и харассмент
    'педик',
    'педофил',
    'педофила',
    'педофило',
    'мудила',
    'мудак',
    'сучка',
    'проститутка',
    'проститутке',
    'еби',
    'соси',
    'член',
    
    # Религиозные оскорбления
    'иудей',
    'жидовин',
    'жид',
    'жидяра',
    
    # Оскорбления по инвалидности (только самое жесткое)
    'даун',
    'аутист',
    
    # Реклама и спам
    'casino',
    'казино',
    'poker',
    'покер',
    'ставки',
    'букмекер',
    'рефбонус',
    'рефссылка',
    'рефка',
    'купить голоса',
    'купить лайки',
    'купить фолловеров',
    'куплю аккаунт',
    'продам аккаунт',
    'порно',
    'xxx',
    'sex',
]

# Инициализация клиента Clash of Clans
coc_client = None
coc_client_lock = threading.Lock()

async def login_coc():
    """Создаёт новый клиент и логинится"""
    global coc_client
    try:
        # Закрываем старый клиент если есть
        if coc_client is not None:
            try:
                await coc_client.close()
            except:
                pass
        
        # Создаём новый клиент
        coc_client = coc.Client()
        await coc_client.login(COC_EMAIL, COC_PASSWORD)
        print(f"✅ Успешный вход в COC API через токен - {datetime.now(timezone.utc).isoformat()}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при входе в COC API: {e}")
        return False

'''async def login_coc():
    """Создаёт новый клиент и логинится"""
    global coc_client
    try:
        # Закрываем старый клиент если есть
        if coc_client is not None:
            try:
                await coc_client.close()
            except:
                pass
        
        # Создаём новый клиент
        coc_client = coc.Client()
        await coc_client.login_with_tokens(COC_API_TOKEN)
        print(f"✅ Успешный вход в COC API через токен - {datetime.now(timezone.utc).isoformat()}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при входе в COC API: {e}")
        return False'''

#-----------------------------------------------
# Загрузка состояния бота (пауза/работа)
#-----------------------------------------------

def load_bot_state():
    """Загружает состояние бота из файла"""
    global bot_paused
    try:
        if os.path.exists(BOT_STATE_FILE):
            with open(BOT_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                bot_paused = state.get('paused', False)
                print(f"✅ Состояние бота загружено: {'На паузе' if bot_paused else 'Работает'}")
                if bot_paused:
                    bot_paused = False
                    bot.send_message(CHATIK_ID, '🟢 Техническое обслуживание бота было завершено.\nАдминистраторы, пожалуйста, запустите бота через <b>/resume</b>.', parse_mode='HTML')
                else:
                    bot_paused = True
                    save_bot_state()
                    bot.send_message(CHATIK_ID, '❗ В прошлый раз работа бота была завершена некорректно.\nАдминистраторы, пожалуйста, запустите бота через <b>/resume</b>.', parse_mode='HTML')
        else:
            bot_paused = False
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке состояния бота: {e}")
        bot_paused = False

def save_bot_state():
    """Сохраняет текущее состояние бота в файл"""
    try:
        with open(BOT_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({'paused': bot_paused}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка при сохранении состояния бота: {e}")

#-----------------------------------------------
# Загрузка списка смертников из файла при старте
#-----------------------------------------------

def load_smertniki():
    global SMERTNIKI
    try:
        if os.path.exists(SMERTNIKI_FILE):
            # Если файл пустой — инициализируем пустым списком
            if os.path.getsize(SMERTNIKI_FILE) == 0:
                SMERTNIKI = []
                save_smertniki()
                return
            with open(SMERTNIKI_FILE, "r", encoding="utf-8") as f:
                try:
                    SMERTNIKI = json.load(f)
                except json.JSONDecodeError:
                    # Файл повреждён или содержит неправильный JSON — перезапишем пустым списком
                    SMERTNIKI = []
                    save_smertniki()
                    return
                # на случай, если файл имеет корректный JSON, но не список
                if not isinstance(SMERTNIKI, list):
                    SMERTNIKI = []
        # Лог загрузки
        try:
            with open(SMERTNIKI_LOG, "a", encoding="utf-8") as lf:
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - load_smertniki - loaded {len(SMERTNIKI)} items\n")
        except Exception:
            pass
    except Exception:
        SMERTNIKI = []

def save_smertniki():
    # запись атомарно: сначала во временный файл в той же директории, потом replace/move
    try:
        tmp_dir = os.path.dirname(SMERTNIKI_FILE) or "."
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=tmp_dir) as tf:
            json.dump(SMERTNIKI, tf, ensure_ascii=False, indent=2)
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
                lf.write(f"{datetime.now(timezone.utc).isoformat()} - save_smertniki - saved {len(SMERTNIKI)} items\n")
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

# Вызвать загрузку сразу после определения SMERTNIKI
load_smertniki()

# Загрузка состояния бота (пауза/работа)
load_bot_state()

#-----------------------------------------------
# Декораторы
#-----------------------------------------------

# Декоратор для проверки доступа
def access_control(allowed_ids):
    """Декоратор для проверки, что пользователь есть в списке разрешённых"""
    def decorator(func):
        @wraps(func)
        def wrapper(message):
            if message.from_user.id not in allowed_ids:
                bot.send_message(message.chat.id, f"❌ <b>{html.escape(message.from_user.first_name)}</b> у вас нет доступа к этой команде. Только администраторы могут её использовать.", parse_mode='HTML')
                return
            return func(message)
        return wrapper
    return decorator
# Декоратор для проверки паузы бота
def check_pause(func):
    """Декоратор для проверки, не находится ли бот на паузе"""
    @wraps(func)
    def wrapper(message):
        if bot_paused:
            return  # Не отвечаем, если бот на паузе
        return func(message)
    return wrapper

# -----------------------------------------------
# Проверка на запрещенку
# -----------------------------------------------

async def ban_msg(message):
    global BAN_WORDS
    try:
        msg = bot.send_message(message, "❗ <b>Ваше сообщение было удалено, в связи с использованием запрещённых слов/фраз.</b>", parse_mode='HTML')
        await asyncio.sleep(10)
        bot.delete_message(message, msg.message_id)
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления о бане: {e}")



# -----------------------------------------------
# Текстовые константы
# -----------------------------------------------

HELP_TEXT = (
    "Команды:\n"
    "/start — приветствие\n"
    "/help — показать эту справку\n"
    "/getmyid — получить ваш ID пользователя\n"
    "/rules — правила клана\n"
    "/smertniki — показать список смертников\n"
    "/clan <tag (опционально)> — информация о клане по тегу (если не указан, то о нашем клане)\n"
    "/war — информация о текущей войне клана\n"
    "/admin — админ-команды (только для администраторов)\n\n"
    "Вы также можете написать мне что-нибудь через /bot и я постараюсь помочь!"
)
ADMIN_TEXT = (
    "Админ-команды:\n"
    "/send <текст> — отправить сообщение в клановый чат\n"
    "/getchatid — получить ID текущего чата\n"
    "/pause — приостановить работу бота\n"
    "/resume — возобновить работу бота\n"
    "/smrt <add|del|list|clear> <id> — управление списком смертников\n"
    "/mstart — запустить мониторинг войны\n"
    "/mstop — остановить мониторинг войны"
)
RULES_SHORT = (
    "СОКРАЩЕННЫЕ ПРАВИЛА\n"
    "1. безосновательные оскорбления - бан\n"
    "2. пропуск атак без причины - бан\n"
    "3. реклама - бан\n"
    "4. игра в других кланах - бан\n"
    "\n"
    "ЛВК\n"
    "1. атаки строго по меткам главы, если не по метке - бан\n"
    "2. атаки на отьебись - бан\n"
    "3. атака без фулл армии и героев - бан(используйте зелья)\n"
    "ИК минималка 1500 очков\n"
)
RULES_MAIN = (
    "ОСНОВНЫЕ ПРАВИЛА\n"
    "1. Безосновательные оскорбления участников или Соруководителей/Главы — мгновенный кик.\n"
    "2. Не нойте при донате, если сами не указали, что вам нужно.\n"
    "«А на х*я ты мне бомберов закинул?» — (c) Киану Ривз, 5 млн лет до н. э.\n"
    "3. Не \"жмотьте\" и не давайте войска чересчур низкого уровня при донате соклановцам.\n"
    "4. При необоснованном пропуске атак на КВ/ЛВК будут применены меры.\n"
    "5. Запрещены любые формы спама и рекламы.\n\n"
)
RULES_CWL = (
    "ЛИГА ВОЙН КЛАНОВ (ЛВК)\n"
    "1. Минимум для участия — ТХ15+ и опыт микса от 2 недель.\n"
    "2. Атака идёт строго по меткам! Метки ставят Соруководители или Глава.\n"
    "3. Пропустили атаку? — Это будет исключительно ваша вина. Вы не будете допущены к следующим дням данного лвк, НО всё равно обязаны написать причину пропуска.\n"
    "4. При форс-мажорах сообщайте сразу. Если осталось ≤10 минут и никого нет в сети, то у вас есть ровно 24 часа на атаку.\n"
    "5. Ошибся и взял 1 звезду? — Ничего страшного, ошибки бывают у всех. Вас возьмут на следующие дни, но при условии, что такого больше не повторится.\n"
    "6. Перед началом лвк будет определен \"костяк\" из самых сильных игроков клана, которые будут участвовать во всех 7 днях. Что касается остальных, вам будет уделено как минимум 3 дня (исключения к десантникам, им — 4+) для того, чтобы набрать 8 звёзд (смысла набирать больше нет, т.к. максимальное кол-во медалей идёт за 8+ звёзд).\n"
    "P.S. «электроводы» не допускаются к лвк.\n"
    "Доп. информация: https://t.me/ostrovv_65/25897\n\n"
)
RULES_CW = (
    "КЛАНОВЫЕ ВОЙНЫ (КВ)\n"
    "1. Участвовать может каждый вне зависимости от уровня ратуши, но для повышения шанса попадания на КВ — ТХ15+.\n"
    "2. Обязательно нужно делать 2 атаки. Почему? — Кто-то атаковал на 1-2 звёзды, и необходимо за ними добить.\n"
    "3. Даже если «всё уже закрыто на трёшки», можно атаковать 1-2 номера для фарма руды.\n"
    "4. Если не взяли на КВ — не значит, что забыли. Как минимум за 12 часов до старта КВ в клановый чат отправляется заявка на участие. Если вы не увидели ее, то не попадете на КВ. В том случае, если вы увидели заявку, но вас не взяли — вспомните, пропускали ли вы атаки в прошлом, и написали ли причину?\n"
    "5. Пропустили атаку и не написали причину? — следующую КВ можете наблюдать со «скамейки запасных».\n"
    "6. Если вы решили пофармить вместо добива, и мы из-за этого проиграли, будут применены меры.\n\n"
)
RULES_EVENTS = (
    "ИГРЫ КЛАНОВ/СОБЫТИЯ\n"
    "1. Минимальное количество очков, которые вы должны набрать в ИК: 1500.\n"
    "2. В сезонных событиях минимальный порог будет установлен Соруководителями/Главой.\n"
    "3. При не достижении минимального порога будут применены серьезные меры!\n"
    "4. Если вы не собираетесь набирать 1500+ очков в ИК, то не играйте в них вообще. Тогда вы не получите награды по завершении ИК.\n\n"
)
RULES_RAIDS = (
    "СТОЛИЧНЫЕ РЕЙДЫ\n"
    "1. Все улучшения уже произведены. Просьба сливать столичное золото в нашу академку \"Побережье 65\".\n"
    "2. Каждый должен делать все 6 атак в рейдах (Лайфхак: скидываете 2 заморозки на ключевую защиту, отправляете 10 супершахтеров, и перезаходите в игру. Благодаря такому подходу на все 6 атак уйдет 3-5 минут).\n"
    "3. Начали бить регион — ДОБИВАЕТЕ до конца! В случае, если вы не добили регион, а перешли к следующему, начали разбирать рейд на \"лего-набор\" будут применены серьезные меры.\n\n"
)
RULES_ROLES = (
    "РОЛИ В КЛАНЕ\n"
    "1. «Старейшина» выдаётся спустя время после вступления, если вы проявляете активность, тренируетесь делать \"трёшки\", не пропускаете атаки.\n"
    "2. «Соруководитель» даётся исключительно по доверию. Нет фиксированного срока после вступления в клан или каких-либо критериев. При получении этой роли на вас возлагаются определенные обязанности по управлению кланом.\n"
    "«Я думал, соруковод — это только плюсик к нику…»\n\n"
)
RULES_PENALTIES = (
    "ЗА ЧТО МОГУТ ВЫГНАТЬ\n"
    "1. Постоянные пропуски атак без объяснения причин.\n"
    "2. Отсутствие активности и пофигизм.\n"
    "3. Систематические нарушения правил.\n"
    "4. Попытки «покататься на двух стульях» (ЛВК в другом клане и т.п.).\n"
    "5. Если вы являетесь «бегуном» или «раком».\n"
    "6. Неуважение к соклановцам, Соруководителям/Главе.\n\n"
    "ЕСЛИ ВАС ВЫГНАЛИ\n"
    "Не беда! Если Соруководители/Глава уверены, что вы изменились, то вам дадут второй шанс."
)

# -----------------------------------------------
# Система мониторинга войны
# -----------------------------------------------

war_monitor_active = False
war_previous_state = None
war_last_data = None
war_notifications_sent = {
    'preparation_started': False,
    'war_started': False,
    'hours_12': False,
    'hours_6': False,
    'hours_3': False,
    'hours_1': False,
    'war_ended': False,
    'war_almost_ended': False,  # Флаг для уведомления когда остаётся <= 60 секунд
    'current_war_tag': None  # Тег текущей войны для сброса уведомлений
}

def reset_war_notifications():
    global war_notifications_sent
    war_notifications_sent = {
    'preparation_started': False,
    'war_started': False,
    'hours_12': False,
    'hours_6': False,
    'hours_3': False,
    'hours_1': False,
    'war_ended': False,
    'war_almost_ended': False,
    'current_war_tag': war_notifications_sent.get('current_war_tag')
}

async def check_war_status():
    global war_previous_state, war_last_data

    try:
        # Переподключаемся к API перед каждым запросом
        login_success = await login_coc()
        if not login_success:
            print("⚠️ Не удалось залогиниться в COC API, пропускаем проверку")
            return
        
        war = await coc_client.get_current_war(CLAN_TAG)

        if war.state == 'notInWar':
            # Проверяем переход из inWar в notInWar (война только что закончилась)
            if war_previous_state == 'inWar':
                # Сохраняем данные из war_last_data если они есть
                war_data = war_last_data
                war_last_data = None  # Очищаем данные
            
            # Сбрасываем уведомления если войны нет
            if war_notifications_sent['current_war_tag'] is not None:
                reset_war_notifications()
                war_notifications_sent['current_war_tag'] = None
            
            war_previous_state = 'notInWar'
            return
        
        # Проверяем, началась ли новая война
        war_id = f"{war.preparation_start_time.time.timestamp()}"
        if war_notifications_sent['current_war_tag'] != war_id:
            reset_war_notifications()
            war_notifications_sent['current_war_tag'] = war_id
        
        # Получаем оставшееся время в часах
        time_remaining = war.end_time.seconds_until
        hours_remaining = time_remaining / 3600
        minutes_remaining = (time_remaining % 3600) // 60
        
        # День подготовки начался
        if war.state == 'preparation' and not war_notifications_sent['preparation_started']:
            message = (
                f"⏳ <b>ОБЪЯВЛЕНА ВОЙНА!</b>\n\n"
                f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n"
                f"👥 Война: {war.team_size} на {war.team_size}\n"
                f"🕐 До начала дня сражения: {int(hours_remaining-24)}ч {int(minutes_remaining)}мин"
            )
            bot.send_message(CHATIK_ID, message, parse_mode='HTML')
            war_notifications_sent['preparation_started'] = True
            print("✅ Отправлено уведомление о начале подготовки")
        
        # День сражений начался
        elif war.state == 'inWar':
            if not war_notifications_sent['war_started']:
                message = (
                    f"⚔️ <b>ДЕНЬ СРАЖЕНИЙ НАЧАЛСЯ!</b>\n\n"
                    f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                    f"🕐 До окончания: {int(hours_remaining)}ч {int(minutes_remaining)}мин"
                )
                bot.send_message(CHATIK_ID, message, parse_mode='HTML')
                war_notifications_sent['war_started'] = True
                print("✅ Отправлено уведомление о начале войны")
            
            # Проверяем уведомления о времени (только во время боя)
            # Осталось 12 часов
            if hours_remaining <= 12 and not war_notifications_sent['hours_12']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"⏰ <b>ОСТАЛОСЬ 12 ЧАСОВ!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                bot.send_message(CHATIK_ID, message, parse_mode='HTML')
                war_notifications_sent['hours_12'] = True
                print("✅ Отправлено уведомление: осталось 12 часов")
            
            # Осталось 6 часов
            if hours_remaining <= 6 and not war_notifications_sent['hours_6']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"⏰ <b>ОСТАЛОСЬ 6 ЧАСОВ!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                bot.send_message(CHATIK_ID, message, parse_mode='HTML')
                war_notifications_sent['hours_6'] = True
                print("✅ Отправлено уведомление: осталось 6 часов")
            
            # Осталось 3 часа
            if hours_remaining <= 3 and not war_notifications_sent['hours_3']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"⏰ <b>ОСТАЛОСЬ 3 ЧАСА!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                bot.send_message(CHATIK_ID, message, parse_mode='HTML')
                war_notifications_sent['hours_3'] = True
                print("✅ Отправлено уведомление: осталось 3 часа")
            
            # Осталось 1 час
            if hours_remaining <= 1 and not war_notifications_sent['hours_1']:
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"🚨 <b>ПОСЛЕДНИЙ ЧАС!</b>\n\n"
                    f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                bot.send_message(CHATIK_ID, message, parse_mode='HTML')
                war_notifications_sent['hours_1'] = True
                print("✅ Отправлено уведомление: последний час")
            
            # Осталось <= 60 секунд - отправляем финальное сообщение об окончании войны
            if time_remaining <= 60 and not war_notifications_sent['war_almost_ended']:
                # Определяем результат
                if war.clan.stars > war.opponent.stars:
                    result = "🎉 <b>ПОБЕДА!</b> 🏆"
                    result_emoji = "🥇"
                elif war.clan.stars < war.opponent.stars:
                    result = "😔 <b>ПОРАЖЕНИЕ</b>"
                    result_emoji = "🥈"
                else:
                    # Если звезды равны, смотрим на разрушение
                    if war.clan.destruction > war.opponent.destruction:
                        result = "🎉 <b>ПОБЕДА!</b> 🏆"
                        result_emoji = "🥇"
                    elif war.clan.destruction < war.opponent.destruction:
                        result = "😔 <b>ПОРАЖЕНИЕ</b>"
                        result_emoji = "🥈"
                    else:
                        result = "🤝 <b>НИЧЬЯ!</b>"
                        result_emoji = "🤝"
                
                members_no_attacks = [m.name for m in war.clan.members if m.attacks == []]
                message = (
                    f"🏁 <b>ВОЙНА ЗАВЕРШЕНА!</b>\n\n"
                    f"{result}\n\n"
                    f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n\n"
                    f"{result_emoji} Итоговый счёт:\n"
                    f"⭐️ Звёзды: {war.clan.stars} : {war.opponent.stars}\n"
                    f"💥 Разрушения: {war.clan.destruction:.1f}% : {war.opponent.destruction:.1f}%\n"
                    f"⚔️ Атак использовано: {war.clan.attacks_used}/{war.team_size * 2}\n"
                )
                if members_no_attacks:
                    message += f"\n⚠️ <b>Не атаковали ({len(members_no_attacks)}):</b>\n"
                    message += "\n".join([f"• {name}" for name in members_no_attacks[:15]])
                    if len(members_no_attacks) > 15:
                        message += f"\n... и ещё {len(members_no_attacks) - 15}"
                bot.send_message(CHATIK_ID, message, parse_mode='HTML')
                for name in members_no_attacks:
                    if name not in SMERTNIKI:
                        SMERTNIKI.append(name)
                    else:
                        for i in range(len(ALLOWED_USER_IDS)):
                            bot.send_message(ALLOWED_USER_IDS[i], f"⚠️ {name} уже 2 раза подряд пропустил атаки в войне!")
                save_smertniki()
                war_notifications_sent['war_almost_ended'] = True
                print("✅ Отправлено уведомление: война почти завершена (осталось <= 60 секунд)")
            
            # Сохраняем данные о войне для уведомления об окончании
            war_last_data = war
        
        # Обновляем предыдущее состояние
        war_previous_state = war.state

    except coc.PrivateWarLog:
        print("Журнал войн клана скрыт")
    except coc.errors.Maintenance:
        print("⚠️ COC API на техническом обслуживании")
    except coc.errors.GatewayError as e:
        print(f"⚠️ Ошибка соединения с COC API (Gateway): {e}")
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса войны: {e}")
        import traceback
        traceback.print_exc()

def war_monitor_loop():
    global war_monitor_active
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while war_monitor_active:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(check_war_status())
                consecutive_errors = 0  # Сбрасываем счётчик при успешном выполнении
            finally:
                # Гарантируем закрытие loop
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except:
                    pass
                loop.close()
        except Exception as e:
            consecutive_errors += 1
            print(f"❌ Ошибка в мониторинге войны ({consecutive_errors}/{max_consecutive_errors}): {e}")
            
            # Если слишком много ошибок подряд, пытаемся переподключиться
            if consecutive_errors >= max_consecutive_errors:
                print("⚠️ Слишком много ошибок подряд, делаем длинную паузу...")
                time.sleep(300)  # 5 минут паузы
                consecutive_errors = 0

        time.sleep(30)

def start_war_monitor():
    global war_monitor_active
    if not war_monitor_active:
        war_monitor_active = True
        monitor_thread = threading.Thread(target=war_monitor_loop, daemon=True)
        monitor_thread.start()
        print("▶️ Мониторинг войны запущен")
    else:
        print("❌ Мониторинг войны уже запущен")

def stop_war_monitor():
    global war_monitor_active
    war_monitor_active = False
    print("⏹️ Мониторинг войны остановлен")

# -----------------------------------------------
# Команды администратора
# -----------------------------------------------

# Запуск бота
@bot.message_handler(commands=['start'])
@check_pause
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который соориентирует тебя по нашему клану «Остров 65» в игре Clash of Clans." + "\n\n" + HELP_TEXT)

# Админ-команды
@bot.message_handler(commands=['admin'])
@access_control(ALLOWED_USER_IDS)
def admin_message(message):
    try:
        # Сначала пытаемся отправить в ЛС
        bot.send_message(message.from_user.id, ADMIN_TEXT)
        # Если успешно - уведомляем в чат
        if message.chat.id != message.from_user.id:
            bot.send_message(message.chat.id, f"<b>{html.escape(message.from_user.first_name)}</b>, отправил список админ-команд в <a href=\"https://t.me/{bot.get_me().username}\">ЛС</a>. Ознакомьтесь пожалуйста.", parse_mode="HTML")
    except telebot.apihelper.ApiTelegramException as e:
        # Любая ошибка Telegram API (403, 400, и т.д.)
        print(f"Telegram API Error {e.error_code}: {e.description}")
        bot.send_message(message.chat.id, f"❌ <b>{html.escape(message.from_user.first_name)}</b>, не удалось отправить сообщение. Перейдите в <a href=\"https://t.me/{bot.get_me().username}\">ЛС</a> и нажмите 'START'.", parse_mode="HTML")
    except Exception as e:
        print(f"Unexpected error: {e}")
        bot.send_message(message.chat.id, f"❌ Упс! Произошла ошибка при отправке сообщения. Попробуйте ещё раз позже.")

# Получение id чата
@bot.message_handler(commands=['getchatid'])
@access_control(ALLOWED_USER_IDS)
def get_chat_id(message):
    bot.send_message(message.chat.id, f"ID этого чата: {message.chat.id}")

# Пауза / Продолжение работы бота
@bot.message_handler(commands=['pause'])
@access_control(ALLOWED_USER_IDS)
def pause_command(message):
    """Команда для остановки бота (только для администраторов)"""
    global bot_paused
    bot_paused = True
    save_bot_state()  # Сохраняем состояние в файл
    bot.send_message(CHATIK_ID, "⏸️ Бот приостановлен. Он не будет отвечать на сообщения.")

@bot.message_handler(commands=['resume'])
@access_control(ALLOWED_USER_IDS)
def resume_command(message):
    """Команда для возобновления работы бота (только для администраторов)"""
    global bot_paused
    bot_paused = False
    save_bot_state()  # Сохраняем состояние в файл
    bot.send_message(CHATIK_ID, "▶️ Бот возобновил работу и готов к ответам.")

# Отправка сообщений в клановый чат
@bot.message_handler(commands=['send'])
@access_control(ALLOWED_USER_IDS)
def admin_command(message):
    """Команда для отправки сообщения в клановый чат (только для администраторов)"""
    try:
        parts = message.text.split(maxsplit=1)
        bot.send_message(CHATIK_ID, parts[1] if len(parts) > 1 else "❌ Использование: /send <сообщение>")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Упс! Произошла ошибка при отправке сообщения. Попробуйте ещё раз позже.")

# Управление списком смертников
@bot.message_handler(commands=['smrt'])
@access_control(ALLOWED_USER_IDS)
def smertniki_command(message):
    try:
        # Парсим команду: /smrt <action> <id>
        parts = message.text.split()
        
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Использование: /smrt <action> <id>\nДоступные действия: add | del | clear | list")
            return
        
        action = parts[1].lower()
        
        if action == "add":
            if len(parts) < 3:
                bot.send_message(message.chat.id, "❌ Укажите ID: /smrt add <id>")
                return
            user_id = parts[2]
            if user_id not in SMERTNIKI:
                SMERTNIKI.append(user_id)
                save_smertniki()
                bot.send_message(message.chat.id, f"✅ Пользователь {user_id} добавлен в список смертников.")
                if message.chat.id != CHATIK_ID:
                    bot.send_message(CHATIK_ID, f"✅ Пользователь {user_id} добавлен в список смертников.")
            else:
                bot.send_message(message.chat.id, f"⚠️ Пользователь {user_id} уже в списке.")
        
        elif action == "del":
            if len(parts) < 3:
                bot.send_message(message.chat.id, "❌ Укажите ID: /smertniki del <id>")
                return
            user_id = parts[2]
            if user_id in SMERTNIKI:
                SMERTNIKI.remove(user_id)
                save_smertniki()
                bot.send_message(message.chat.id, f"✅ Пользователь {user_id} удалён из списка смертников.")
                if message.chat.id != CHATIK_ID:
                    bot.send_message(CHATIK_ID, f"✅ Пользователь {user_id} удалён из списка смертников.")
            else:
                bot.send_message(message.chat.id, f"⚠️ Пользователь {user_id} не найден в списке.")
        elif action == "list":
            if SMERTNIKI:
                bot.send_message(message.chat.id, "📋 Список смертников:\n" + "\n".join(SMERTNIKI))
            else:
                bot.send_message(message.chat.id, "📋 Список смертников пуст.")
        
        elif action == "clear":
            SMERTNIKI.clear()
            save_smertniki()
            bot.send_message(message.chat.id, "✅ Список смертников очищен.")
            if message.chat.id != CHATIK_ID:
                bot.send_message(CHATIK_ID, "✅ Список смертников очищен.")

        else:
            bot.send_message(message.chat.id, "❌ Неверная команда. Используйте: add, del, clear или list")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Упс! Произошла ошибка при отправке сообщения. Попробуйте ещё раз позже.")

# Управление мониторингом войны
@bot.message_handler(commands=['mstart'])
@access_control(ALLOWED_USER_IDS)
def start_monitor_command(message):
    start_war_monitor()
    bot.send_message(message.chat.id, "▶️ Мониторинг войны запущен.")

@bot.message_handler(commands=['mstop'])
@access_control(ALLOWED_USER_IDS)
def stop_monitor_command(message):
    stop_war_monitor()
    bot.send_message(message.chat.id, "⏹️ Мониторинг войны остановлен.")

# -----------------------------------------------
# Стандартные команды бота
# -----------------------------------------------

# Помощь
@bot.message_handler(commands=['help'])
@check_pause
def help_message(message):
    bot.send_message(message.chat.id, HELP_TEXT)

# Получение id пользователя
@bot.message_handler(commands=['getmyid'])
@check_pause
def get_user_id(message):
    bot.send_message(message.chat.id, f"Ваш ID: {message.from_user.id}")

# Вывод списка смертников
@bot.message_handler(commands=['smertniki'])
@check_pause
def smertniki_message(message):
    if SMERTNIKI:
        bot.send_message(message.chat.id, "📋 Список смертников:\n" + "\n".join(SMERTNIKI))
    else:
        bot.send_message(message.chat.id, "📋 Список смертников пуст.")

# Функция для создания клавиатуры правил
def get_rules_keyboard():
    rules = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Основное", callback_data="main_rules")
    btn1 = types.InlineKeyboardButton("ЛВК", callback_data="cwl_rules")
    btn2 = types.InlineKeyboardButton("КВ", callback_data="cw_rules")
    btn3 = types.InlineKeyboardButton("ИК/ивенты", callback_data="cg_rules")
    btn4 = types.InlineKeyboardButton("Рейды", callback_data="raids_rules")
    btn5 = types.InlineKeyboardButton("Роли в клане", callback_data="roles_rules")
    btn6 = types.InlineKeyboardButton("За что могут выгнать", callback_data="penalties_rules")
    rules.add(btn, btn1, btn2, btn3, btn4, btn5, btn6)
    return rules

# Правила
@bot.message_handler(commands=['rules'])
@check_pause
def rules_message(message):
    bot.send_message(message.chat.id, "Здесь представлены полные правила нашего клана. Нажмите соответсвующую кнопку, чтобы их увидеть.", reply_markup=get_rules_keyboard())

# -----------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data == "main_rules")
def main_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_MAIN, reply_markup=get_rules_keyboard())
@bot.callback_query_handler(func=lambda call: call.data == "cwl_rules")
def cwl_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_CWL, reply_markup=get_rules_keyboard())
@bot.callback_query_handler(func=lambda call: call.data == "cw_rules")
def cw_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_CW, reply_markup=get_rules_keyboard())
@bot.callback_query_handler(func=lambda call: call.data == "cg_rules")
def cg_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_EVENTS, reply_markup=get_rules_keyboard())
@bot.callback_query_handler(func=lambda call: call.data == "raids_rules")
def raids_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_RAIDS, reply_markup=get_rules_keyboard())
@bot.callback_query_handler(func=lambda call: call.data == "roles_rules")
def roles_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_ROLES, reply_markup=get_rules_keyboard())
@bot.callback_query_handler(func=lambda call: call.data == "penalties_rules")
def penalties_rules(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, RULES_PENALTIES, reply_markup=get_rules_keyboard())

# Информация о клане
@bot.message_handler(commands=['clan'])
@check_pause
def clan_info(message):
    try:
        import asyncio
        
        # Получаем тег клана из сообщения или используем дефолтный
        parts = message.text.split()
        clan_tag = parts[1] if len(parts) > 1 else CLAN_TAG
        
        # Убираем # если пользователь не указал
        if not clan_tag.startswith('#'):
            clan_tag = '#' + clan_tag
        
        # Получаем данные о клане асинхронно
        async def get_clan_data():
            try:
                login_success = await login_coc()
                if not login_success:
                    return None
                clan = await coc_client.get_clan(clan_tag)
                return clan
            except coc.NotFound:
                return None
            except Exception as e:
                print(f"Ошибка при получении данных клана: {e}")
                return None
        
        # Запускаем асинхронную функцию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            clan = loop.run_until_complete(get_clan_data())
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except:
                pass
            loop.close()
        
        if clan:
            response = (
                f"🏰 <b>{clan.name}</b> ({clan.tag})\n\n"
                f"👥 Участников: {clan.member_count}/50\n"
                f"🏆 Требуемые трофеи: {clan.required_trophies:,}\n"
                f"🔰 Лига: {clan.war_league.name}\n"
                f"🎚️ Уровень: {clan.level}\n"
                f"🔥 Серия побед в войнах: {clan.war_win_streak}\n"
                f"✅ Побед: {clan.war_wins} | ❌ Поражений: {clan.war_losses}\n\n"
                f"💬 Описание: {clan.description if clan.description else 'Нет описания'}"
            )
            bot.send_message(message.chat.id, response, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, f"❌ Клан с тегом {clan_tag} не найден. Проверьте правильность тега!")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла ошибка при получении информации о клане. Попробуйте ещё раз позже.")
        print(f"Unexpected error: {e}")

# Информация о вайне
@bot.message_handler(commands=['war'])
@check_pause
def war_info(message):
    """Получить статус текущей войны клана"""
    try:
        import asyncio
        from datetime import timedelta
        
        # Получаем тег клана из сообщения или используем дефолтный
        parts = message.text.split()
        clan_tag = parts[1] if len(parts) > 1 else CLAN_TAG
        
        # Убираем # если пользователь не указал
        if not clan_tag.startswith('#'):
            clan_tag = '#' + clan_tag
        
        # Получаем данные о войне асинхронно
        async def get_war_data():
            try:
                login_success = await login_coc()
                if not login_success:
                    return None
                war = await coc_client.get_current_war(clan_tag)
                return war
            except coc.PrivateWarLog:
                return "private"
            except coc.NotFound:
                return None
            except Exception as e:
                print(f"Ошибка при получении данных о войне: {e}")
                return None
        
        # Запускаем асинхронную функцию
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            war = loop.run_until_complete(get_war_data())
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except:
                pass
            loop.close()
        
        if war == "private":
            bot.send_message(message.chat.id, "❌ Журнал войн клана закрыт. Попросите лидера открыть его в настройках клана.")
            return
        
        if war is None:
            bot.send_message(message.chat.id, f"❌ Не удалось получить данные о войне для клана {clan_tag}")
            return
        
        # Определяем статус войны
        if war.state == 'notInWar':
            bot.send_message(message.chat.id, "🟠 Клан сейчас не в воюет.")
            return
        
        # Вычисляем оставшееся время
        time_remaining = war.end_time.seconds_until
        hours = time_remaining // 3600
        minutes = (time_remaining % 3600) // 60
        
        # Формируем сообщение в зависимости от статуса
        if war.state == 'preparation':
            status_emoji = "⏳"
            status_text = "ДЕНЬ ПОДГОТОВКИ"
            time_text = f"До начала сражения: {hours-24}ч {minutes}мин"
        elif war.state == 'inWar':
            status_emoji = "⚔️"
            status_text = "ДЕНЬ СРАЖЕНИЙ"
            time_text = f"До окончания войны: {hours}ч {minutes}мин"
        else:
            status_emoji = "🏁"
            status_text = "ВОЙНА ЗАВЕРШЕНА"
            time_text = "Война окончена"
        
        # Формируем полное сообщение
        response = (
            f"{status_emoji} <b>{status_text}</b>\n\n"
            f"🏰 <b>{war.clan.name}</b> VS <b>{war.opponent.name}</b>\n\n"
            f"🟡 Звезды: {war.clan.stars}⭐️ : {war.opponent.stars}⭐️\n"
            f"💥 Разрушения: {war.clan.destruction:.2f}% : {war.opponent.destruction:.2f}%\n"
            f"⚔️ Атак использовано: {war.clan.attacks_used}/{war.team_size * 2}\n\n"
            f"👥 Размер: {war.team_size} на {war.team_size}\n"
            f"🕐 {time_text}"
        )
        
        bot.send_message(message.chat.id, response, parse_mode='HTML')
    
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла ошибка при получении информации о войне. Попробуйте ещё раз позже.")
        print(f"Unexpected error: {e}")

# -----------------------------------------------
# Обработка текстовых сообщений
# -----------------------------------------------

@bot.message_handler(content_types=['text'])
@check_pause
def answerr(message):
    # Расизм, нацизм, оскорбления, реклама, спам и т.д.
    text = message.text.lower()
    
    # Функция для нормализации текста (удаление спецсимволов и цифр)
    def normalize_text(s):
        return re.sub(r'[^а-яёa-z]', '', s)
    
    # Функция для замены кириллицы, похожей на латиницу
    def normalize_cyrillic_lookalikes(s):
        # Заменяем похожие символы: о->о, с->с, е->е и т.д.
        replacements = {
            'o': 'о',  # латинское O на кириллицу О
            'c': 'с',  # латинское C на кириллицу С
            'e': 'е',  # латинское E на кириллицу Е
            'p': 'р',  # латинское P на кириллицу Р
            'a': 'а',  # латинское A на кириллицу А
            'b': 'в',  # латинское B на кириллицу В
            'h': 'н',  # латинское H на кириллицу Н
            'k': 'к',  # латинское K на кириллицу К
            'm': 'м',  # латинское M на кириллицу М
            't': 'т',  # латинское T на кириллицу Т
            'x': 'х',  # латинское X на кириллицу Х
            'y': 'у',  # латинское Y на кириллицу У
        }
        result = s
        for lat, cyr in replacements.items():
            result = result.replace(lat, cyr)
        return result
    
    # Проверяем каждое слово
    words = text.split()
    ban_detected = False
    
    for word in words:
        # Очищаем слово от спецсимволов
        cleaned = normalize_text(word)
        
        # Проверка 1: прямое совпадение (уже кириллица)
        if cleaned in BAN_WORDS:
            ban_detected = True
            print(f"🚫 Обнаружено запрещённое слово (прямое): {cleaned}")
            break
        
        # Проверка 2: замена похожих символов
        normalized = normalize_cyrillic_lookalikes(cleaned)
        if normalized in BAN_WORDS:
            ban_detected = True
            print(f"🚫 Обнаружено запрещённое слово (транслит): {word} -> {normalized}")
            break

        # Проверка 3: длинные фразы
        for word in BAN_LONG:
            if word in text:
                ban_detected = True
                print(f"🚫 Обнаружено запрещённое выражение: {word}")
                break
    
    if ban_detected:
        bot.delete_message(message.chat.id, message.message_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(ban_msg(message.chat.id))
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            except:
                pass
            loop.close()
        return
    # Вопросы о клане
    if "/bot" in message.text.lower():
        words = message.text.lower().split()
        text_lower = message.text.lower()
        # Информация о клане
        if "клан" in words or "название" in words or "основа" in words:
            bot.send_message(message.chat.id, "Наш клан называется «Остров 65». Мы активно развиваемся и всегда рады новым участникам!\n\nТег клана: #9G29PC8U\nСсылка для вступления: <a href=\"https://link.clashofclans.com/ru/?action=OpenClanProfile&tag=9G29PC8U\">ТЫК</a>", parse_mode="HTML")
        
        # Информация об академке
        elif "академ" in words or "академка" in words or "побережье" in words:
            bot.send_message(message.chat.id, "Наша академка называется «Побережье 65». Мы активно развиваемся и всегда рады новым участникам!\n\nТег академки: #2JQJ9YUC9\nСсылка для вступления: <a href=\"https://link.clashofclans.com/ru/?action=OpenClanProfile&tag=2JQJ9YUC9\">ТЫК</a>", parse_mode="HTML")
        # Требования для вступления
        elif "требования" in words or "вступить" in words or "вступление" in words or "присоединиться" in words:
            bot.send_message(message.chat.id, "Для вступления в наш клан необходимо иметь ТХ не ниже 17 уровня и быть активным игроком.")
        
        # Войны кланов (КВ)
        elif "кв" in words or ("клановые" in words and "войны" in words) or ("война" in words and "клана" in words):
            bot.send_message(message.chat.id, "Мы участвуем в войнах кланов регулярно. Войны проходят на постоянной основе, и мы ожидаем от участников активного участия и выполнения своих атак. Обязательно делайте 2 атаки!")
        
        # Лига Войн Кланов (ЛВК)
        elif "лвк" in words or "лига" in words or "лига войн кланов" in text_lower:
            bot.send_message(message.chat.id, "Для участия в Лиге Войн Кланов (ЛВК) необходимо иметь ТХ15+ и опыт микса от 2 недель. Атаки должны выполняться строго по меткам, которые ставят Соруководители или Глава.")
        
        # Игры Кланов (ИК)
        elif "ик" in words or "игры" in words or "игры кланов" in text_lower:
            bot.send_message(message.chat.id, "Минимальное количество очков, которые вы должны набрать в Играх Кланов: 1500. Если не собираетесь набирать минимум, лучше не участвуйте вообще.")
        
        # Столичные рейды
        elif "рейды" in words or "рейд" in words or "столица" in words or "столичные" in words:
            bot.send_message(message.chat.id, "Каждый должен делать все 6 атак в рейдах. Лайфхак: скидываете 2 заморозки на ключевую защиту, отправляете 10 супершахтеров и перезаходите. На все 6 атак уйдет 3-5 минут. Столичное золото сливайте в академку «Побережье 65».")
        
        # Донат
        elif "донат" in words or "донаты" in words or "войска" in words or "подкрепление" in words:
            bot.send_message(message.chat.id, "Не жмотьте и не давайте войска низкого уровня! Указывайте, что вам нужно при запросе. Помните: «А на х*я ты мне бомберов закинул?» — Киану Ривз.")
        
        # Ратуша (ТХ)
        elif "ратуша" in words or "тх" in words or "townhall" in text_lower or "th" in words:
            bot.send_message(message.chat.id, "Минимальная ратуша для вступления — ТХ17. Для участия в ЛВК нужна ТХ15+. Для КВ принимаем всех, но приоритет у ТХ15+.")
        
        # Атаки
        elif "атака" in words or "атаки" in words or "напасть" in words or "наступление" in words:
            bot.send_message(message.chat.id, "На войнах обязательно делайте 2 атаки. Атакуйте по меткам, которые ставят Соруководители или Глава. Пропуск атак без причины — серьёзное нарушение!")
        
        # Пропуск атак
        elif "пропустил" in words or "пропуск" in words or "не атаковал" in words or "забыл" in words:
            bot.send_message(message.chat.id, "Пропуск атак без объяснения причин — это серьёзно! При форс-мажоре сообщайте сразу. Систематические пропуски могут привести к кику из клана.")
        
        # Роли в клане
        elif "роль" in words or "роли" in words or "старейшина" in words or "соруководитель" in words or "соруковод" in words:
            bot.send_message(message.chat.id, "«Старейшина» выдаётся за активность и участие. «Соруководитель» даётся по доверию с определёнными обязанностями по управлению. Это не просто плюсик к нику!")
        
        # Кик/исключение
        elif "кик" in words or "выгнать" in words or "исключение" in words or "выгонят" in words:
            bot.send_message(message.chat.id, "Выгнать могут за: постоянные пропуски атак, неактивность, нарушения правил, неуважение к соклановцам. Но если изменитесь — дадут второй шанс!")
        
        # Тактики и стратегии
        elif "тактика" in words or "стратегия" in words or "как" in words and "атаковать" in words:
            bot.send_message(message.chat.id, "Изучайте базы противников перед атакой! Используйте миксы войск, подходящие под защиту. Смотрите гайды, тренируйтесь. Главное — «трёшки» на войнах!")
        
        # Тренировка
        elif "тренировка" in words or "тренироваться" in words or "практика" in words or "учиться" in words:
            bot.send_message(message.chat.id, "Тренируйтесь делать «трёшки» (атаки на 3 звезды). Практикуйтесь в дружественных вызовах, смотрите реплеи лучших атак. Опыт приходит со временем!")
        
        # Трофеи и лига
        elif "трофеи" in words or "кубки" in words or "лига" in words and "трофеев" in text_lower:
            bot.send_message(message.chat.id, "Поддерживайте достойное количество трофеев. Это показывает вашу активность и навыки. В ЛВК особенно важен ваш уровень!")
        
        # Герои
        elif "герой" in words or "герои" in words or "король" in words or "королева" in words or "чемпион" in words or "хранитель" in words:
            bot.send_message(message.chat.id, "Не идите на войны с прокачивающимися героями — это сильно снижает шансы на победу, особенно в ЛВК. Старайтесь иметь героев на высоком уровне для максимальной эффективности, либо используйте зелья.")
        # Супервойска
        elif "супервойска" in words or "супервойско" in words or "супервойск" in words:
            bot.send_message(message.chat.id, "Супервойска — мощный инструмент! Выбирайте подходящие под вашу стратегию и базы противников. Меняйте их, если нужно, перед важными войнами.")
        
        # Заклинания
        elif "заклинание" in words or "заклинания" in words or "спелл" in words or "спеллы" in words:
            bot.send_message(message.chat.id, "Правильный выбор заклинаний критичен! Ярость, лечение, прыжок, заморозка — каждое имеет своё применение. Не забывайте про осадные машины!")
        
        # Ловушки
        elif "ловушка" in words or "ловушки" in words or "бомба" in words or "пружина" in words:
            bot.send_message(message.chat.id, "При планировании атаки учитывайте возможное расположение ловушек! Опытные игроки видят типичные места для бомб и пружин.")
        
        # Защита базы
        elif "защита" in words or "база" in words or "расстановка" in words or "планировка" in words:
            bot.send_message(message.chat.id, "Правильная планировка базы — залог успешной защиты! Используйте проверенные планировки, адаптируйте их под мету. Не оставляйте слабых мест!")
        
        # Ресурсы
        elif "ресурсы" in words or "золото" in words or "эликсир" in words or "тёмный" in words and "эликсир" in text_lower:
            bot.send_message(message.chat.id, "Фармите ресурсы активно! Используйте щит мудро, не теряйте много при защите. Столичное золото сливайте в академку.")
        
        # События
        elif "событие" in words or "события" in words or "ивент" in words or "ивенты" in words:
            bot.send_message(message.chat.id, "В сезонных событиях минимальный порог устанавливают Соруководители/Глава. При недостижении порога будут применены серьезные меры!")
        
        # Как вступить
        elif "как" in words and ("вступить" in words or "попасть" in words or "присоединиться" in words):
            bot.send_message(message.chat.id, "Чтобы вступить в клан:\n1) Убедитесь, что ваша ратуша ТХ17+.\n2) Найдите клан «Остров 65» в игре.\n3) Отправьте заявку. Ждём активных игроков!")
        
        # Активность
        elif "активность" in words or "активный" in words or "онлайн" in words or "играть" in words:
            bot.send_message(message.chat.id, "Активность — ключ к успеху в клане! Играйте регулярно, участвуйте в войнах, донатьте соклановцам, общайтесь в чате.")
        
        # Правила
        elif "правила" in words:
            bot.send_message(message.chat.id, f"{RULES_SHORT}\n❗Полные правила клана можно найти по команде /rules. Обязательно ознакомьтесь с ними!")
        
        # Смертники
        elif "список смертников" in text_lower or "смертники" in words or "смертник" in words:
            bot.send_message(message.chat.id, "Список смертников — это список игроков с провинностями (пропуски атак, нарушения правил). Администраторы управляют им через /smrt.")
        
        # Связь/контакты
        elif "связь" in words or "контакт" in words or "телеграм" in words or "чат" in words:
            bot.send_message(message.chat.id, "Основной чат клана в Telegram: https://t.me/ostrovv_65. Присоединяйтесь для общения и координации!")
        
        # Помощь
        elif "помощь" in words or "помоги" in words or "команды" in words:
            bot.send_message(message.chat.id, "Доступные команды можно посмотреть через /help. Я отвечу на вопросы о клане и Clash of Clans!")
        
        # Если ничего не подошло
        else:
            bot.send_message(message.chat.id, "Извините, я не понимаю ваш запрос. Попробуйте переформулировать вопрос или используйте /help для списка команд.")


# -----------------------------------------------
# Запуск бота
# -----------------------------------------------

import signal
import sys

def signal_handler(sig, frame):
    """Обработчик сигнала для graceful shutdown"""
    print("\n🛑 Получен сигнал завершения, останавливаем бот...")
    
    # Ставим бота
    global bot_paused
    bot_paused = True
    save_bot_state()  # Сохраняем состояние в файл
    bot.send_message(CHATIK_ID, "⏸️ Бот приостановлен. Он не будет отвечать на сообщения.")
    
    # Останавливаем мониторинг войны
    stop_war_monitor()
    
    # Закрываем COC клиент
    if coc_client is not None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coc_client.close())
            loop.close()
            print("✅ COC клиент закрыт")
        except Exception as e:
            print(f"⚠️ Ошибка при закрытии COC клиента: {e}")
    
    sys.exit(0)

# Регистрируем обработчик сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("🚀 Запуск бота...")
print(f"📅 Время запуска: {datetime.now(timezone.utc).isoformat()}")

while True:
    try:
        bot.polling(none_stop=True, interval=2, timeout=60)
    except Exception as e:
        print(f"💥 Bot crashed with exception: {e}")
        import traceback
        traceback.print_exc()
        print("⏳ Перезапуск через 15 секунд...")
        time.sleep(15)