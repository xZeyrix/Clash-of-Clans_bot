from utils.json_save_and_load import save_smertniki
import config.config as config
import html
from config.state_holder import state
from config.config_holder import config

def smertnikiAdd(names):
    nicknames = [name.strip() for name in names.split(',')]
    output = []
    for nickname in nicknames:
        if nickname not in state.smertniki:
            state.smertniki.append(nickname)
            output.append(nickname)
    save_smertniki()
    if not output:
        return False
    else:
        return output
def smertnikiRemove(names):
    indexes = [int(i.strip()) - 1 for i in names.split(',')]
    indexes.sort(reverse=True)
    deleted_users = []
    for index in indexes:
        if 0 <= index < len(state.smertniki):
            user = state.smertniki[index]
            del state.smertniki[index]
            deleted_users.append(user)
    save_smertniki()
    if not deleted_users:
        return False
    else:
        return deleted_users
def smertnikiClear():
    state.smertniki.clear()
    save_smertniki()
async def smertniki(message, id=None):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("❌ Неверный формат команды.\nИспользуйте: /sm &lt;add|rm|clear|list&gt;")
        return
    command = parts[1]
    if command == 'add':
        if len(parts) < 3:
            await message.answer("❌ Укажите никнейм для добавления.\nПример: /sm add gamer123 или /sm add user1,user2,user3")
            return
        output = smertnikiAdd(parts[2])
        if not output:
            await message.answer("❗ Указанные никнеймы уже есть в списке смертников.")
            return
        await message.answer(f"✅ Пользователь/пользователи {html.escape(', '.join(output))} добавлен(ы) в список смертников.")
        await message.bot.send_message(config.chat_id, f"✅ Админ <a href='tg://user?id={message.from_user.id}'>{html.escape(message.from_user.full_name)}</a> добавил пользователя/пользователей <b>{html.escape(', '.join(output))}</b> в список смертников.")
    elif command == 'rm':
        if len(parts) < 3:
            await message.answer("❌ Укажите ID для удаления.\nПример: /sm rm 1 или /sm rm 1,2,3")
            return
        try:
            deleted_users = smertnikiRemove(parts[2])
            if not deleted_users:
                await message.answer("❗ Указанные ID не найдены в списке смертников.")
                return
            await message.answer(f"✅ Пользователь/пользователи {html.escape(', '.join(deleted_users))} удален(ы) из списка смертников.")
            await message.bot.send_message(config.chat_id, f"✅ Админ <a href='tg://user?id={message.from_user.id}'>{html.escape(message.from_user.full_name)}</a> удалил пользователя/пользователей <b>{html.escape(', '.join(deleted_users))}</b> из списка смертников.")
        except ValueError:
            await message.answer("❌ ID должен быть числом.")
    elif command == 'clear':
        if not state.smertniki:
            await message.answer("❗ Список смертников уже пуст.")
            return
        smertnikiClear()
        await message.answer("✅ Список смертников очищен.")
        await message.bot.send_message(config.chat_id, f"✅ Админ <a href='tg://user?id={message.from_user.id}'>{html.escape(message.from_user.full_name)}</a> очистил список смертников.")
    elif command == 'list':
        if not state.smertniki:
            await message.answer("❗ Список смертников пуст.")
        else:
            response = "📋 Список смертников:\n"
            for i, nickname in enumerate(state.smertniki, 1):
                response += f"<b>{i}.</b> {html.escape(nickname)}\n"
            await message.answer(response)
    else:
        await message.answer("❌ Неизвестная команда.\nИспользуйте: /sm &lt;add|rm|clear|list&gt;")