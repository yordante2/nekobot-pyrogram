import os
from pyrogram import Client, filters
from process_command import process_command  # El archivo que maneja los comandos.

# Configuración y variables globales
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TOKEN')
admin_users = list(map(int, os.getenv('ADMINS').split(',')))
users = list(map(int, os.getenv('USERS').split(',')))
temp_users = []
temp_chats = []
ban_users = []
allowed_users = admin_users + users + temp_users + temp_chats
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

CODEWORD = os.getenv("CODEWORD")
BOT_IS_PUBLIC = os.getenv("BOT_IS_PUBLIC")

# Funciones y manejadores
async def handle_start(client, message):
    await message.reply("Funcionando")

def is_bot_public():
    return BOT_IS_PUBLIC and BOT_IS_PUBLIC.lower() == "true"

@app.on_message(filters.command("access") & filters.private)
def access_command(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1 and message.command[1] == CODEWORD:
        if user_id not in temp_users:
            temp_users.append(user_id)
            allowed_users.append(user_id)
            message.reply("Acceso concedido.")
        else:
            message.reply("Ya estás en la lista de acceso temporal.")
    else:
        message.reply("Palabra secreta incorrecta.")

@app.on_message(filters.text)
async def handle_message(client, message):
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id

    if user_id in ban_users:
        return

    if not is_bot_public() and user_id not in allowed_users and chat_id not in allowed_users:
        return

    active_cmd = os.getenv("ACTIVE_CMD", "").lower()
    admin_cmd = os.getenv("ADMIN_CMD", "").lower()

    await process_command(client, message, active_cmd, admin_cmd, user_id, username, chat_id)

# Inicio del bot
app.run()
