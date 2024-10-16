async def handle_start(client, message):
    await message.reply("Funcionando")


async def update_video_settings(client, message):
    settings = message.text[len('/calidad '):]
    global video_settings
    video_settings = settings
    await message.reply(f"Configuración de video actualizada: {video_settings}")

async def add_user(client, message):
    user_id = message.from_user.id
    if user_id in admin_users:
        new_user_id = int(message.text.split()[1])
        temp_users.append(new_user_id)
        allowed_users.append(new_user_id)
        await message.reply(f"Usuario {new_user_id} añadido temporalmente.")

async def remove_user(client, message):
    user_id = message.from_user.id
    if user_id in admin_users:
        rem_user_id = int(message.text.split()[1])
        if rem_user_id in temp_users:
            temp_users.remove(rem_user_id)
            allowed_users.remove(rem_user_id)
            await message.reply(f"Usuario {rem_user_id} eliminado temporalmente.")
        else:
            await message.reply("Usuario no encontrado en la lista temporal.")

async def add_chat(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id in admin_users:
        temp_chats.append(chat_id)
        allowed_users.append(chat_id)
        await message.reply(f"Chat {chat_id} añadido temporalmente.")

async def remove_chat(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id in admin_users:
        if chat_id in temp_chats:
            temp_chats.remove(chat_id)
            allowed_users.remove(chat_id)
            await message.reply(f"Chat {chat_id} eliminado temporalmente.")
        else:
            await message.reply("Chat no encontrado en la lista temporal.")

async def ban_user(client, message):
    user_id = message.from_user.id
    if user_id in admin_users:
        ban_user_id = int(message.text.split()[1])
        if ban_user_id not in admin_users:
            ban_users.append(ban_user_id)
            await message.reply(f"Usuario {ban_user_id} baneado.")

async def deban_user(client, message):
    user_id = message.from_user.id
    if user_id in admin_users:
        deban_user_id = int(message.text.split()[1])
        if deban_user_id in ban_users:
            ban_users.remove(deban_user_id)
            await message.reply(f"Usuario {deban_user_id} desbaneado.")
        else:
            await message.reply("Usuario no encontrado en la lista de baneados.")

async def set_size(client, message):
    username = message.from_user.username
    valor = message.text.split(" ")[1]
    user_comp[username] = int(valor)
    await message.reply(f"Tamaño de archivos {valor}MB registrado para el usuario @{username}")

async def set_mail(client, message):
    user_id = message.from_user.id
    email = message.text.split(' ', 1)[1]
    user_emails[user_id] = email
    await message.reply("Correo electrónico registrado correctamente.")
