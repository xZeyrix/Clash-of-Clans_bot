from utils.files import save_smertniki
import config
import html
from config import CHAT_ID

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
        nicknames = [name.strip() for name in parts[2].split(',')]
        output = []
        for nickname in nicknames:
            if nickname not in config.SMERTNIKI:
                config.SMERTNIKI.append(nickname)
                output.append(nickname)
        save_smertniki()
        if not output:
            await message.answer("❗ Указанные никнеймы уже есть в списке смертников.")
            return
        await message.answer(f"✅ Пользователь/пользователи {html.escape(', '.join(output))} добавлен(ы) в список смертников.")
        await message.bot.send_message(CHAT_ID, f"✅ Админ <b>{html.escape(message.from_user.full_name)}</b> добавил пользователя/пользователей <b>{html.escape(', '.join(output))}</b> в список смертников.")
    elif command == 'rm':
        if len(parts) < 3:
            await message.answer("❌ Укажите ID для удаления.\nПример: /sm rm 1 или /sm rm 1,2,3")
            return
        try:
            indexes = [int(i.strip()) - 1 for i in parts[2].split(',')]
            indexes.sort(reverse=True)
            deleted_users = []
            for index in indexes:
                if 0 <= index < len(config.SMERTNIKI):
                    user = config.SMERTNIKI[index]
                    del config.SMERTNIKI[index]
                    deleted_users.append(user)
            save_smertniki()
            if not deleted_users:
                await message.answer("❗ Указанные ID не найдены в списке смертников.")
                return
            await message.answer(f"✅ Пользователь/пользователи {html.escape(', '.join(deleted_users))} удален(ы) из списка смертников.")
            await message.bot.send_message(CHAT_ID, f"✅ Админ <b>{html.escape(message.from_user.full_name)}</b> удалил пользователя/пользователей <b>{html.escape(', '.join(deleted_users))}</b> из списка смертников.")
        except ValueError:
            await message.answer("❌ ID должен быть числом.")
    elif command == 'clear':
        if not config.SMERTNIKI:
            await message.answer("❗ Список смертников уже пуст.")
            return
        config.SMERTNIKI.clear()
        save_smertniki()
        await message.answer("✅ Список смертников очищен.")
        await message.bot.send_message(CHAT_ID, f"✅ Админ <b>{html.escape(message.from_user.full_name)}</b> очистил список смертников.")
    elif command == 'list':
        if not config.SMERTNIKI:
            await message.answer("❗ Список смертников пуст.")
        else:
            response = "📋 Список смертников:\n"
            for i, nickname in enumerate(config.SMERTNIKI, 1):
                response += f"{i}. {html.escape(nickname)}\n"
            await message.answer(response)
    else:
        await message.answer("❌ Неизвестная команда.\nИспользуйте: /sm &lt;add|rm|clear|list&gt;")