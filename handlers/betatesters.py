from aiogram import Router, types, F
from config.config_holder import config
from config.state_holder import state
from aiogram.utils.keyboard import InlineKeyboardBuilder
import html

router = Router()

def get_allow_keyboard(id: int, name: str):
    builder  = InlineKeyboardBuilder()

    builder.button(text="✅ Да",  callback_data=f"call_beta:{id}:{name}")
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
    user_name = callback.data.split(":")[2]
    
    try:
        await callback.bot.send_message(config.dev_id, f"❗ Пользователь  <a href='tg://user?id={user_id}'>{html.escape(user_name)}</a> хочет получить права на использование бота. Разрешить?", reply_markup=dev_allow_keyboard(user_id))
        await callback.message.edit_text("✅ Разработчику отправлено уведомление.\nОжидайте подтверждения.\n\n❗ Обработка ваших сообщений была заблокирована до решения разработчика.\nПожалуйста, ничего не отправляйте.")
        state.beta_banned_ids.append(user_id)
    except Exception as e:
        await callback.answer("❌ Произошла ошибка.\nПопробуйте снова позже.")

@router.callback_query(F.data.startswith("hide_beta:"))
async def hide_beta(callback: types.CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer("✅ Сообщение было скрыто")

@router.callback_query(F.data.startswith("allow_beta:"))
async def allow_beta(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])

    try:
        state.beta_testers_ids.append(user_id)
        state.beta_banned_ids.remove(user_id)
        await callback.message.delete()
        await callback.bot.send_message(user_id, "✅ Разработчик дал вам разрешение на бета-тест.\nТеперь вы можете отправлять сообщения.")
        await callback.answer("✅ Успешно")
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("disallow_beta:"))
async def disallow_beta(callback: types.CallbackQuery) -> None:
    user_id = int(callback.data.split(":")[1])

    try:
        if user_id in config.BETA_TESTERS_IDS:
            state.beta_banned_ids.append(user_id)
            state.beta_testers_ids.remove(user_id)
        await callback.message.delete()
        await callback.answer("✅ Успешно")
        await callback.bot.send_message(user_id, "❌ Разработчик запретил вам использовать бота.\nПожалуйста, не отправляйте сообщения.")
    except Exception as e:
        await callback.answer("❌ Произошла ошибка")