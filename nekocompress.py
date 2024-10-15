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

def compressfile(file_path, part_size):
    parts = []
    with open(file_path, 'rb') as f:
        part_num = 1
        while True:
            part_data = f.read(part_size * 1024 * 1024)
            if not part_data:
                break
            part_file = f"{file_path}.7z.{part_num:03d}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts
    
async def handle_compress(client, message, username):
    global bot_in_use
    if bot_in_use:
        await message.reply("El comando está en uso actualmente, espere un poco")
        return
    try:
        bot_in_use = True
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

        # Descargar archivo
        file_name = get_file_name(message)
        file_path = await client.download_media(
            message.reply_to_message,
            file_name=file_name
        )
        await message.reply("Comprimiendo el archivo...")
        sizd = user_comp.get(username, 10)
        # Comprimir archivo
        parts = compressfile(file_path, sizd)
        await message.reply("Se ha comprimido el archivo, ahora se enviarán las partes")
        # Enviar partes
        for part in parts:
            try:
                await client.send_document(message.chat.id, part)
            except:
                pass
        await message.reply("Esas son todas las partes")
        shutil.rmtree('server')
        os.mkdir('server')
        bot_in_use = False
    except Exception as e:
        await message.reply(f'Error: {str(e)}')
    finally:
        bot_in_use = False
        
async def handle_setsize(message):
    valor = message.text.split(" ")[1]
    user_comp[username] = int(valor)
    await message.reply(f"Tamaño de archivos {valor}MB registrado para el usuario @{username}")
    