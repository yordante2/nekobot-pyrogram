import os
import glob
from pyrogram import Client, filters
import zipfile
import shutil
import random
import string
import smtplib
import requests
import re
import datetime
import subprocess
import asyncio
import os
import hashlib
import py7zr
import shutil
import string
import random
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from moodleclient import upload_token
from email.message import EmailMessage
from pyrogram.types import Message
from PIL import Image
from htools import nh_combined_operation
from admintools import add_user, remove_user, add_chat, remove_chat, ban_user, deban_user
from imgtools import create_imgchest_post
from webtools import handle_scan, handle_multiscan
from mailtools import send_mail, set_mail
from videotools import update_video_settings, compress_video

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
compression_size = 10  
file_counter = 0
bot_in_use = False
user_emails = {}
image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']

def compressfile(file_path, part_size):
    parts = []
    part_size *= 1024 * 1024  
    archive_path = f"{file_path}.7z"
    with py7zr.SevenZipFile(archive_path, 'w') as archive:
        archive.write(file_path, os.path.basename(file_path))
    with open(archive_path, 'rb') as archive:
        part_num = 1
        while True:
            part_data = archive.read(part_size)
            if not part_data:
                break
            part_file = f"{archive_path}.{part_num:03d}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts

async def handle_compress(client, message, username):
    try:
        os.system("rm -rf ./server/*")
        await message.reply("Descargando el archivo para comprimirlo...")
        def get_file_name(message):
            if message.reply_to_message.document:
                return os.path.basename(message.reply_to_message.document.file_name)[:50]
            elif message.reply_to_message.photo:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".jpg"
            elif message.reply_to_message.audio:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".mp3"
            elif message.reply_to_message.video:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".mp4"
            elif message.reply_to_message.sticker:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".webp"
            else:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        file_name = get_file_name(message)
        file_path = await client.download_media(
            message.reply_to_message,
            file_name=file_name
        )
        await message.reply("Comprimiendo el archivo...")
        sizd = user_comp.get(username, 10)
        parts = compressfile(file_path, sizd)
        original_hashes = [hash_file(part) for part in parts]
        await message.reply("Se ha comprimido el archivo, ahora se enviarán las partes")
        for part, original_hash in zip(parts, original_hashes):
            try:
                await client.send_document(message.chat.id, part)
                received_hash = hash_file(part)  
                if received_hash != original_hash:
                    await message.reply(f"El archivo {part} recibido está corrupto.")
            except Exception as e:
                print(f"Error al enviar la parte {part}: {e}")
                await message.reply(f"Error al enviar la parte {part}: {e}")
        await message.reply("Esas son todas las partes")
        shutil.rmtree('server')
        os.mkdir('server')
    except Exception as e:
        await message.reply(f'Error: {str(e)}')
async def rename(client, message):
    reply_message = message.reply_to_message
    if reply_message and reply_message.media:
        try:
            await message.reply("Descargando el archivo para renombrarlo...")
            new_name = message.text.split(' ', 1)[1]
            file_path = await client.download_media(reply_message)
            new_file_path = os.path.join(os.path.dirname(file_path), new_name)
            os.rename(file_path, new_file_path)
            await message.reply("Subiendo el archivo con nuevo nombre...")
            await client.send_document(message.chat.id, new_file_path)
            os.remove(new_file_path)
        except Exception as e:
            await message.reply(f'Error: {str(e)}')
    else:
        await message.reply('Ejecute el comando respondiendo a un archivo')

async def handle_up(client, message):
    if message.reply_to_message:
        await message.reply("Descargando...")
        file_path = await client.download_media(message.reply_to_message.document.file_id)
        await message.reply("Subiendo a la nube...")
        link = upload_token(file_path, os.getenv("NUBETOKEN"), os.getenv("NUBELINK"))
        await message.reply("Enlace:\n" + str(link).replace("/webservice", ""))
        os.remove(file_path)

async def handle_start(client, message):
    await message.reply("Funcionando")
        
async def rename(client, message):
    reply_message = message.reply_to_message
    if reply_message and reply_message.media:
        try:
            await message.reply("Descargando el archivo para renombrarlo...")
            new_name = message.text.split(' ', 1)[1]
            file_path = await client.download_media(reply_message)
            new_file_path = os.path.join(os.path.dirname(file_path), new_name)
            os.rename(file_path, new_file_path)
            await message.reply("Subiendo el archivo con nuevo nombre...")
            await client.send_document(message.chat.id, new_file_path)
            os.remove(new_file_path)
        except Exception as e:
            await message.reply(f'Error: {str(e)}')
    else:
        await message.reply('Ejecute el comando respondiendo a un archivo')
        
async def set_size(client, message):
    valor = int(message.text.split(" ")[1])
    username = message.from_user.username
    user_comp[username] = valor
    await message.reply(f"Tamaño de archivos {valor}MB registrado para el usuario @{username}")
        
CODEWORD = os.getenv("CODEWORD")
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
        
BOT_IS_PUBLIC = os.getenv("BOT_IS_PUBLIC")
def is_bot_public():
    return BOT_IS_PUBLIC and BOT_IS_PUBLIC.lower() == "true"
    
    
@app.on_message(filters.text)
async def handle_message(client, message):
    text = message.text.strip().lower()
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    if user_id in ban_users:
        return
    if not is_bot_public():
        if user_id not in allowed_users and chat_id not in allowed_users:
            return
    active_cmd = os.getenv("ACTIVE_CMD", "").lower()
    admin_cmd = os.getenv("ADMIN_CMD", "").lower()
    def is_command_allowed(command_env):
        return active_cmd == "all" or command_env in active_cmd
    def is_admin_command_allowed(command_env):
        return admin_cmd == "all" or command_env in admin_cmd
    if text.startswith(("/nh", "/3h", "/cover", "/covernh")):
        if is_command_allowed("htools") or (is_admin_command_allowed("htools") and user_id in admin_users):
            parts = text.split(maxsplit=1)
            command = parts[0]
            codes = parts[1].split(',') if len(parts) > 1 and ',' in parts[1] else [parts[1]] if len(parts) > 1 else []

            # Determina el tipo de operación
            operation_type = "download" if command in ("/nh", "/3h") else "cover"
            global link_type
            link_type = "nh" if command in ("/nh", "/covernh") else "3h"
            

            # Llama a la función combinada
            await asyncio.create_task(nh_combined_operation(client, message, codes, link_type, operation_type))
        else:
            return
    
    elif text.startswith(("/setmail", "/sendmail")):
        if is_command_allowed("mailtools") or (is_admin_command_allowed("mailtools") and user_id in admin_users):
            if text.startswith("/setmail"):
                await set_mail(client, message)
            elif text.startswith("/sendmail"):
                await send_mail(client, message)
        else:
            return
    elif text.startswith(("/compress", "/setsize", "/rename")):
        if is_command_allowed("filetools") or (is_admin_command_allowed("filetools") and user_id in admin_users):
            if text.startswith("/compress"):
                await handle_compress(client, message, username)
            elif text.startswith("/setsize"):
                valor = text.split(" ")[1]
                user_comp[username] = int(valor)
                await message.reply(f"Tamaño de archivos {valor}MB registrado para el usuario @{username}")
            elif text.startswith("/rename"):
                await rename(client, message)
        else:
            return
    elif text.startswith(("/convert", "/calidad")):
        if is_command_allowed("videotools") or (is_admin_command_allowed("videotools") and user_id in admin_users):
            if text.startswith("/convert") and message.reply_to_message and message.reply_to_message.video:
                original_video_path = await client.download_media(message.reply_to_message.video)
                await compress_video(client, message, original_video_path)
            elif text.startswith("/calidad"):
                await update_video_settings(client , message)
                
        else:
            return
    elif text.startswith("/imgchest"):
        if is_command_allowed("imgchest") or (is_admin_command_allowed("imgchest") and user_id in admin_users):
            if message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.document):
                await create_imgchest_post(client, message)
            else:
                await message.reply("Por favor, usa el comando respondiendo a una foto.")
        else:
            return
    elif text.startswith(("/scan", "/multiscan")):
        if is_command_allowed("webtools") or (is_admin_command_allowed("webtools") and user_id in admin_users):
            if text.startswith("/scan"):
                await handle_scan(client, message)
            elif text.startswith("/multiscan"):
                await handle_multiscan(client, message)
        else:
            return
    elif text.startswith(("/adduser", "/remuser", "/addchat", "/remchat")) and user_id in admin_users:
        if text.startswith("/adduser"):
            await add_user(client, message, user_id, chat_id)
        elif text.startswith("/remuser"):
            await remove_user(client, message, user_id, chat_id)
        elif text.startswith("/addchat"):
            await add_chat(client, message, user_id, chat_id)
        elif text.startswith("/remchat"):
            await remove_chat(client, message, user_id, chat_id)

app.run()
