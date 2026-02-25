from data.texts import RULES_MAIN, RULES_CWL, RULES_CW, RULES_EVENTS, RULES_RAIDS, RULES_ROLES, RULES_PENALTIES
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Список правил
RULES_LIST = [
    ("Тут вы можете ознакомиться с основными правилами нашего клана «Остров 65» в игре Clash of Clans.\nПожалуйста, внимательно прочитайте их, чтобы избежать недоразумений и обеспечить комфортное пребывание в нашем сообществе.\n\n"),
    (RULES_MAIN),
    (RULES_CWL),
    (RULES_CW),
    (RULES_EVENTS),
    (RULES_RAIDS),
    (RULES_ROLES),
    (RULES_PENALTIES),
    ("Для получения дополнительной информации или если у вас возникнут вопросы, не стесняйтесь обращаться к Соруководителям или Главе клана. Мы всегда готовы помочь и поддержать вас в нашем сообществе!\n\nСпасибо за внимание и добро пожаловать в «Остров 65»!")
]

# Функция для создания клавиатуры навигации
def get_navigation_keyboard(current_page: int):
    builder = InlineKeyboardBuilder()       
    
    # Кнопка "Назад"
    if current_page > 0:
        builder.button(text="◀️ Назад", callback_data=f"rules_page:{current_page-1}")
    
    # Кнопка "Далее"
    if current_page < len(RULES_LIST) - 1:
        builder.button(text="Далее ▶️", callback_data=f"rules_page:{current_page+1}")
    
    builder.adjust(2)  # Две кнопки в ряд
    return builder.as_markup()