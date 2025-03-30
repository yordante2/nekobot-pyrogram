import os
from pyrogram import Client, filters
from process_command import process_command
import asyncio
import nest_asyncio

nest_asyncio.apply()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TOKEN')
admin_users = list(map(int, os.getenv('ADMINS').split(','))) if os.getenv('ADMINS') else []
users = list(map(int, os.getenv('USERS').split(','))) if os.getenv('USERS') else []
temp_users = []
temp_chats = []
ban_users = []
allowed_users = admin_users + users + temp_users + temp_chats
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

CODEWORD = os.getenv('CODEWORD', '')
BOT_IS_PUBLIC = os.getenv('BOT_IS_PUBLIC', 'false')

vip_users = list(map(int, os.getenv('VIP_USERS', '').split(','))) if os.getenv('VIP_USERS') else []
allowed_ids = set(admin_users).union(set(vip_users))
protect_content_env = os.getenv('PROTECT_CONTENT', '').strip().lower()
is_protect_content_enabled = protect_content_env == 'true'

MAIN_ADMIN = os.getenv("MAIN_ADMIN")

def is_bot_public():
    return BOT_IS_PUBLIC and BOT_IS_PUBLIC.lower() == "true"

async def process_access_command(message):
    user_id = message.from_user.id
    if len(message.command) > 1 and message.command[1] == CODEWORD:
        if user_id not in temp_users:
            temp_users.append(user_id)
            allowed_users.append(user_id)
            await message.reply("Acceso concedido.")
        else:
            await message.reply("Ya estás en la lista de acceso temporal.")
    else:
        await message.reply("Palabra secreta incorrecta.")
        
async def notify_main_admin(app):
    if MAIN_ADMIN:
        try:
            if MAIN_ADMIN.isdigit():
                # MAIN_ADMIN is a user ID
                await app.send_message(chat_id=int(MAIN_ADMIN), text=f"Bot @{app.me.username} iniciado")
            else:
                # MAIN_ADMIN is a username
                await app.send_message(chat_id=MAIN_ADMIN, text=f"Bot @{app.me.username} iniciado")
        except Exception as e:
            print(f"Error al enviar el mensaje al MAIN_ADMIN: {e}")

from command.htools import manejar_opcion

@app.on_callback_query(filters.regex("^(cbz|pdf|fotos)"))
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    if is_protect_content_enabled and user_id not in allowed_ids:
        protect_content = True
    else:
        protect_content = False
    await manejar_opcion(client, callback_query, protect_content, user_id)

@app.on_callback_query()
async def callback_handler(client, callback_query):
    from command.help import handle_help_callback
    await asyncio.create_task(handle_help_callback(client, callback_query))

@app.on_message()
async def handle_message(client, message):
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    auto = True

    if message.text and message.text.startswith("/access") and message.chat.type == "private":
        await process_access_command(message)
        return

    if user_id in ban_users:
        return

    if not is_bot_public() and user_id not in allowed_users and chat_id not in allowed_users:
        return

    active_cmd = os.getenv('ACTIVE_CMD', '').lower()
    admin_cmd = os.getenv('ADMIN_CMD', '').lower()
    await asyncio.create_task(process_command(client, message, active_cmd, admin_cmd, user_id, username, chat_id))

try:
    app.start()
    if MAIN_ADMIN:
        await notify_main_admin(app)
except KeyboardInterrupt:
    print("Detención forzada realizada")
