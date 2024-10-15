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

async def handle_compare(message):
    global common_lines

    if message.reply_to_message and message.reply_to_message.document:
        file_path = await message.reply_to_message.download()
        with open(file_path, 'r') as f:
            lines = set(f.readlines())
        os.remove(file_path)

        if common_lines is None:
            common_lines = lines
        else:
            common_lines = common_lines.intersection(lines)

        await message.reply("Archivo analizado, responda /compare a otro para seguir o /listo para terminar")

async def handle_listo(message):
    global common_lines

    if common_lines is not None:
        with open('resultado.txt', 'w') as f:
            f.writelines(common_lines)
        await message.reply_document('resultado.txt')
        os.remove('resultado.txt')
        common_lines = None
    else:
        await message.reply("No hay líneas comunes para enviar")
        
async def handle_resumetxtcodes(message):
    full_message = message.text
    if message.reply_to_message and message.reply_to_message.document:
        file_path = await message.reply_to_message.download()
        with open(file_path, 'r') as f:
            for line in f:
                full_message += line
        os.remove(file_path)
    codes = re.findall(r'\d{6}', full_message)
    if codes:
        file_name = "codes.txt"
        with open(file_name, 'w') as f:
            for code in codes:
                f.write(f"{code}\n")
        await message.reply_document(file_name)
        os.remove(file_name)
    else:
        await message.reply("No hay códigos para resumir")
        
async def handle_multiscan(message):
    global bot_in_use
    if bot_in_use:
        await message.reply("El bot está en uso actualmente, espere un poco")
        return
    bot_in_use = True
    parts = message.text.split(' ')
    if len(parts) < 4:
        await message.reply("Por favor, proporcione todos los parámetros necesarios: URL base, inicio y fin.")
        bot_in_use = False
        return
    base_url = parts[1]
    try:
        start = int(parts[2])
        end = int(parts[3])
    except ValueError:
        await message.reply("Los parámetros de inicio y fin deben ser números enteros.")
        bot_in_use = False
        return
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    all_results = set()
    try:
        for i in range(start, end + 1):
            url = f"{base_url}{i}"
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if not href.endswith(('.pdf', '.jpg', '.png', '.doc', '.docx', '.xls', '.xlsx')):
                    page_name = link.get_text(strip=True)
                    if page_name:
                        if not href.startswith('http'):
                            href = f"{base_url}{href}"
                        all_results.add(f"{page_name}\n{href}\n")
        if all_results:
            with open('results.txt', 'w') as f:
                f.write("\n".join(all_results))
            await message.reply_document('results.txt')
            os.remove('results.txt')
        else:
            await message.reply("No se encontraron enlaces de páginas web.")
    except Exception as e:
        await message.reply(f"Error al escanear las páginas: {e}")
    bot_in_use = False

async def rename_file(message, client, bot_in_use):
    if bot_in_use:
        await message.reply("El bot está en uso, espere un poco")
        return
    bot_in_use = True
    if not message.reply_to_message or not message.reply_to_message.media:
        await message.reply("Debe usar el comando respondiendo a un archivo")
        bot_in_use = False
        return
    command = message.text.split()
    if len(command) < 2:
        await message.reply("Introduzca un nuevo nombre")
        bot_in_use = False
        return
    new_name = command[1]
    media = message.reply_to_message
    file_id = None

    if media.photo:
        file_id = media.photo.file_id
    elif media.video:
        file_id = media.video.file_id
    elif media.document:
        file_id = media.document.file_id
    elif media.audio:
        file_id = media.audio.file_id
    else:
        await message.reply("Tipo de archivo no soportado")
        bot_in_use = False
        return

    # Descargar el archivo
    file_path = await client.download_media(file_id, file_name=f"temprename/{file_id}")
    file_extension = os.path.splitext(file_path)[1]
    new_file_path = f"temprename/{new_name}{file_extension}"
    
    # Renombrar el archivo
    os.rename(file_path, new_file_path)
    await client.send_document(message.chat.id, new_file_path)
    
    # Limpiar la variable de estado
    bot_in_use = False
    os.remove(new_file_path)
    shutil.rmtree('temprename')
    os.mkdir('temprename')

async def handle_scan(message):
    if bot_in_use:
        await message.reply("El bot está en uso actualmente, espere un poco")
        return
    bot_in_use = True
    url = message.text.split(' ', 1)[1]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)
        results = []
        for link in links:
            href = link['href']
            if not href.endswith(('.pdf', '.jpg', '.png', '.doc', '.docx', '.xls', '.xlsx')):
                page_name = link.get_text(strip=True)
                if page_name:
                    results.append(f"{page_name}\n{href}\n")
        final_results = []
        for result in results:
            lines = result.split('\n')
            if len(lines) > 1:
                href = lines[1]
                if not href.startswith('http'):
                    base_url = '/'.join(url.split('/')[:3])
                    href = f"{base_url}{href}"
                final_results.append(f"{lines[0]}\n{href}\n")
        if final_results:
            with open('results.txt', 'w') as f:
                f.write("\n".join(final_results))
            await message.reply_document('results.txt')
            os.remove('results.txt')
        else:
            await message.reply("No se encontraron enlaces de páginas web.")
    except Exception as e:
        await message.reply(f"Error al escanear la página: {e}")
    bot_in_use = False
