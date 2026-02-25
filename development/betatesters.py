from aiogram import Router, types, F
from  config import DEV_ID, BETA_TESTERS_IDS, BETA_BANNED_IDS
import config
from aiogram.utils.keyboard import InlineKeyboardBuilder

router =  Router()

def get_allow_keyboard(id: int):
    builder  = InlineKeyboardBuilder()

    builder.button(text="✅ Да",  callback_data=f"call_beta:{id}")
    builder.button(text="❌ Нет",  callback_data=f"hide_beta:{id}")

    builder.adjust(2)
    return builder.as_markup()
def dev_allow_keyboard(id: int):
    builder  = InlineKeyboardBuilder()

    builder.button(text="✅ Да",  callback_data=f"allow_beta:{id}")
    builder.button(text="❌ Нет",  callback_data=f"disallow_beta:{id}")

    builder.adjust(2)
    return builder.as_markup()

@router.callback_query(F.data.startswith("call_beta:"))
async def call_beta(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])
    
    try:
        await callback.bot.send_message(DEV_ID, f"❗ Пользователь  {user_id} хочет получить права на использование бота. Разрешить?", reply_markup=dev_allow_keyboard(user_id))
        await callback.message.edit_text("✅ Разработчику отправлено уведомление.\nОжидайте подтверждения.")
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("hide_beta:"))
async def hide_beta(callback: types.CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer("✅ Сообщение было скрыто")

@router.callback_query(F.data.startswith("allow_beta:"))
async def allow_beta(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])

    try:
        BETA_TESTERS_IDS.append(user_id)
        await callback.answer("✅ Успешно")
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("disallow_beta:"))
async def disallow_beta(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])

    try:
        BETA_BANNED_IDS.append(user_id)
        await callback.answer("✅ Успешно")
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")

# ================== ЭТОТ ХЕНДЛЕР ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ ==================
@router.message()
async def text_message_handler(message: types.Message) -> None:
    pass
