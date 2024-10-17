import os
import glob
from pyrogram import Client, filters
import zipfile
import shutil
import random
import string
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
import re
from moodleclient import upload_token
import datetime
import subprocess
from pyrogram.types import Message

compression_size = 10  # Tamaño de compresión por defecto en MB
file_counter = 0
bot_in_use = False

user_emails = {}
image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']


video_settings = {
    'resolution': '640x480',
    'crf': '28',
    'audio_bitrate': '64k',
    'fps': '30',
    'preset': 'fast',
    'codec': 'libx264'
}

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


async def handle_up(client, message):
    if message.reply_to_message:
        await message.reply("Descargando...")
        file_path = await client.download_media(message.reply_to_message.document.file_id)
        await message.reply("Subiendo a la nube...")
        link = upload_token(file_path, os.getenv("NUBETOKEN"), os.getenv("NUBELINK"))
        await message.reply("Enlace:\n" + str(link).replace("/webservice", ""))
        # Borrar el archivo después de subirlo
        os.remove(file_path)

async def cover3h_operation(client, message, codes):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for code in codes:
        url = f"https://es.3hentai.net/d/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"El código {code} es erróneo: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        page_name = re.sub(r'[^a-zA-Z0-9\[\] ]', '', title_tag.text.strip()) if title_tag else clean_string(code) + code

        img_url = f"https://es.3hentai.net/d/{code}/1/"
        try:
            response = requests.get(img_url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error al acceder a la página de la imagen: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content

            img_filename = f"1{img_extension}"
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)

            await client.send_photo(message.chat.id, img_filename, caption=f"https://es.3hentai.net/d/{code} {page_name}")
        else:
            await message.reply(f"No se encontró ninguna imagen para el código {code}")

async def h3_operation(client, message, codes):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for code in codes:
        url = f"https://es.3hentai.net/d/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"El código {code} es erróneo: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        folder_name = os.path.join("h3dl", clean_string(title_tag.text.strip()) if title_tag else clean_string(code))

        os.makedirs(folder_name, exist_ok=True)

        page_number = 1
        while True:
            page_url = f"https://es.3hentai.net/d/{code}/{page_number}/"
            try:
                response = requests.get(page_url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                if page_number == 1:
                    await message.reply(f"Error al acceder a la página: {str(e)}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if not img_tag:
                break

            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content

            img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)

            page_number += 1

        zip_filename = os.path.join(f"{folder_name}.cbz")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        await client.send_document(message.chat.id, zip_filename)

async def nh_operation(client, message, codes):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for code in codes:
        url = f"https://nhentai.net/g/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"El código {code} es erróneo: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        folder_name = os.path.join("h3dl", clean_string(title_tag.text.strip()) if title_tag else clean_string(code))

        os.makedirs(folder_name, exist_ok=True)

        page_number = 1
        while True:
            page_url = f"https://nhentai.net/g/{code}/{page_number}/"
            try:
                response = requests.get(page_url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                if page_number == 1:
                    await message.reply(f"Error al acceder a la página: {str(e)}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if not img_tag:
                break

            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content

            img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)

            page_number += 1

        zip_filename = os.path.join(f"{folder_name}.cbz")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        await client.send_document(message.chat.id, zip_filename)

async def covernh_operation(client, message, codes):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for code in codes:
        url = f"https://nhentai.net/g/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"El código {code} es erróneo: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        page_name = re.sub(r'[^a-zA-Z0-9\[\] ]', '', title_tag.text.strip()) if title_tag else clean_string(code) + code

        img_url = f"https://nhentai.net/g/{code}/1/"
        try:
            response = requests.get(img_url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error al acceder a la página de la imagen: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content

            img_filename = f"1{img_extension}"
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)


            try:
                await client.send_photo(message.chat.id, img_filename, caption=f"https://nhentai.net/g/{code} {page_name}")

            except Exception as e:
                await client.send_document(message.chat.id, img_filename, caption=f"https://nhentai.net/g/{code} {page_name}")
            #else:
                #await message.reply(f"No se encontró ninguna imagen para el código {code}")
            



    
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
