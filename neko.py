import os
import glob
from pyrogram import Client, filters
import zipfile
import shutil
import random
import string
import smtplib
from email.message import EmailMessage
from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import re
from moodleclient import upload_token
from nekohdl import cover3h_operation, h3_operation, nh_operation, covernh_operation
from nekomail import handle_setmail, handle_sendmail
from nekoadmintools import handle_adduser, handle_remuser, handle_addchat,handle_remchat,  handle_banuser, handle_debanuser
from nekocompress import handle_compress, compressfile, handle_setsize
from nekoup import handle_up
from nekoother import handle_compare, handle_listo, handle_resumetxtcodes, handle_scan, handle_multiscan, rename_file

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
file_counter = 0
bot_in_use = False

user_emails = {}
image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']

    
def sanitize_input(input_string):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', input_string)

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)

common_lines = None

user_comp = {}

async def handle_start(message):
    await message.reply("Funcionando")

@app.on_message(filters.text)
async def handle_message(client, message):
    text = message.text
    username = message.from_user.username
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id in allowed_users:
        pass
    else:
        if chat_id not in allowed_users:
            return
        if user_id in ban_users:
            return
    if text.startswith(('/resumetxtcodes', '.resumetxtcodes', 'resumetxtcodes')):
        await handle_resumetxtcodes(message)
    elif text.startswith(('/multiscan', '.multiscan', 'multiscan')):
        await handle_multiscan(message)
    elif text.startswith(('start', '.start', '/start')):
        await handle_start(message)
    elif text.startswith('/adduser'):
        await handle_adduser(message)
    elif text.startswith('/remuser'):
        await handle_remuser(message)
    elif text.startswith('/addchat'):
        await handle_addchat(message)
    elif text.startswith('/remchat'):
        await handle_remchat(message)
    elif text.startswith('/banuser'):
        await handle_banuser(message)
    elif text.startswith('/debanuser'):
        await handle_debanuser(message)
    elif text.startswith('/compress'):
        await handle_compress(client, message, username)
    elif text.startswith('/up'):
        await handle_up(client, message)
    elif text.startswith("/setsize"):
        await handle_setsize(message)
    elif text.startswith('/setmail'):
        await handle_setmail(message)
    elif text.startswith('/sendmail'):
        await handle_sendmail(client, message)
    elif text.startswith('/rename'):
        await rename_file(client, message)
    elif text.startswith(('/scan', '.scan', 'scan')):
        await handle_scan(message)
    elif text.startswith(('/3h', '.3h', '3h')):
        codes = text.split(maxsplit=1)[1].split(',') if ',' in text.split(maxsplit=1)[1] else [text.split(maxsplit=1)[1]]
        for code in codes:
            await cover3h_operation(client, message, [code])
            await h3_operation(client, message, [code])
    elif text.startswith(('/cover3h', '.cover3h')):
        codes = [code.strip() for code in text.split()[1].split(',')]
        for code in codes:
            await cover3h_operation(client, message, [code])
    elif text.startswith(('/covernh', '.covernh')):
        codes = [code.strip() for code in text.split()[1].split(',')]
        for code in codes:
            await covernh_operation(client, message, [code])
    elif text.startswith(('/nh', '.nh', 'nh')):
        codes = text.split(maxsplit=1)[1].split(',') if ',' in text.split(maxsplit=1)[1] else [text.split(maxsplit=1)[1]]
        for code in codes:
            await covernh_operation(client, message, [code])
            await nh_operation(client, message, [code])
    elif message.text.startswith('/compare'):
        await handle_compare(message)
    elif message.text.startswith('/listo'):
        await handle_listo(message)

app.run()
