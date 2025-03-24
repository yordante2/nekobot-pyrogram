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
from filetools import handle_compress, rename, set_size

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

async def handle_start(client, message):
    await message.reply("Funcionando")
    
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

            operation_type = "download" if command in ("/nh", "/3h") else "cover"
            global link_type
            link_type = "nh" if command in ("/nh", "/covernh") else "3h"
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
                await set_size(client, message)
            elif text.startswith("/rename"):
                await rename(client, message)
        else:
            return
    elif text.startswith(("/convert", "/calidad")):
        if is_command_allowed("videotools") or (is_admin_command_allowed("videotools") and user_id in admin_users):
            if text.startswith("/convert"):
                await compress_video(client, message)
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
app.start()
