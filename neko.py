import os
from pyrogram import Client, filters
import zipfile

# Configuracion del bot
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TOKEN')

# Administradores y Usuarios del bot
admin_users = list(map(int, os.getenv('ADMINS').split(',')))
users = list(map(int, os.getenv('USERS').split(',')))
temp_users = []
temp_chats = []
ban_users = []
allowed_users = admin_users + users + temp_users + temp_chats

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

compression_size = 10  # Tamaño de compresión por defecto en MB

bot_in_use = False


def compressfile(filename, sizd):
    maxsize = 1024 * 1024 * sizd
    mult_file = zipfile.MultiFile(filename + '.7z', maxsize)
    zip = zipfile.ZipFile(mult_file, mode='w', compression=zipfile.ZIP_DEFLATED)
    zip.write(filename)
    zip.close()
    mult_file.close()
    files = []
    for part in zipfile.files:
        files.append(part)
    return files



@app.on_message(filters.text)
def handle_message(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in allowed_users or user_id in ban_users:
        return

    if message.text.startswith(('start', '.start', '/start')):
        message.reply("Funcionando")
    elif message.text.startswith('/adduser'):
        if user_id in admin_users:
            new_user_id = int(message.text.split()[1])
            temp_users.append(new_user_id)
            allowed_users.append(new_user_id)
            message.reply(f"Usuario {new_user_id} añadido temporalmente.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith('/remuser'):
        if user_id in admin_users:
            rem_user_id = int(message.text.split()[1])
            if rem_user_id in temp_users:
                temp_users.remove(rem_user_id)
                allowed_users.remove(rem_user_id)
                message.reply(f"Usuario {rem_user_id} eliminado temporalmente.")
            else:
                message.reply("Usuario no encontrado en la lista temporal.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith('/addchat'):
        if user_id in admin_users:
            temp_chats.append(chat_id)
            allowed_users.append(chat_id)
            message.reply(f"Chat {chat_id} añadido temporalmente.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith('/remchat'):
        if user_id in admin_users:
            if chat_id in temp_chats:
                temp_chats.remove(chat_id)
                allowed_users.remove(chat_id)
                message.reply(f"Chat {chat_id} eliminado temporalmente.")
            else:
                message.reply("Chat no encontrado en la lista temporal.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith('/banuser'):
        if user_id in admin_users:
            ban_user_id = int(message.text.split()[1])
            ban_users.append(ban_user_id)
            message.reply(f"Usuario {ban_user_id} baneado.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith('/debanuser'):
        if user_id in admin_users:
            deban_user_id = int(message.text.split()[1])
            if deban_user_id in ban_users:
                ban_users.remove(deban_user_id)
                message.reply(f"Usuario {deban_user_id} desbaneado.")
            else:
                message.reply("Usuario no encontrado en la lista de baneados.")
        else:
            message.reply("No eres admin")
    elif message.text.startswith(("compress", ".compress", "/compress")):
        if not message.reply_to_message or not message.reply_to_message.document:
            message.reply_text("Debe usar el comando respondiendo a un archivo")
            return

        global bot_in_use
        if bot_in_use:
            message.reply_text("El bot está en uso")
            return

        bot_in_use = True

        try:
            # Descargar el archivo
            file_id = message.reply_to_message.document.file_id
            file_path = client.download_media(file_id, file_name="compress/")
            
            # Crear carpeta si no existe
            if not os.path.exists("compress"):
                os.makedirs("compress")

            # Comprimir el archivo
            compressed_files = compressfile(file_path, compression_size)

            # Enviar las partes comprimidas al chat
            for part in compressed_files:
                client.send_document(chat_id, part)

            # Limpiar la carpeta compress
            for file in os.listdir("compress"):
                file_path = os.path.join("compress", file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except Exception as e:
            message.reply_text("Error")
        finally:
            bot_in_use = False

    elif message.text.startswith(("setsize", ".setsize", "/setsize")):
        try:
            new_size = int(message.text.split()[1])
            compression_size = new_size
            message.reply_text(f"Tamaño de compresión establecido a {new_size} MB")
        except (IndexError, ValueError):
            message.reply_text("Uso: setsize <tamaño en MB>")




app.run()
