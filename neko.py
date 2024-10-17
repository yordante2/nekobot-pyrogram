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
from nekocmd import compressfile, handle_compress, handle_up, cover3h_operation, h3_operation, covernh_operation, nh_operation, rename, handle_start, update_video_settings, add_user, remove_user, add_chat, remove_chat, ban_user, deban_user, set_size, set_mail


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

async def compress_video(client, message: Message):  # Cambiar a async
    if message.reply_to_message and message.reply_to_message.video:
        original_video_path = await app.download_media(message.reply_to_message.video)
        original_size = os.path.getsize(original_video_path)
        await app.send_message(chat_id=message.chat.id, text=f"Iniciando la compresión del video...\n"
                                                              f"Tamaño original: {original_size // (1024 * 1024)} MB")
        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', original_video_path,
            '-s', video_settings['resolution'], '-crf', video_settings['crf'],
            '-b:a', video_settings['audio_bitrate'], '-r', video_settings['fps'],
            '-preset', video_settings['preset'], '-c:v', video_settings['codec'],
            compressed_video_path
        ]
        try:
            start_time = datetime.datetime.now()
            process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
            await app.send_message(chat_id=message.chat.id, text="Compresión en progreso...")
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            # Recuperar tamaño y duración
            compressed_size = os.path.getsize(compressed_video_path)
            duration = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                                 compressed_video_path])
            duration = float(duration.strip())
            duration_str = str(datetime.timedelta(seconds=duration))
            processing_time = datetime.datetime.now() - start_time
            processing_time_str = str(processing_time).split('.')[0]  # Formato sin microsegundos
            # Descripción para el video comprimido
            description = (
                f"✅ Archivo procesado correctamente ☑️\n"
                f" Tamaño original: {original_size // (1024 * 1024)} MB\n"
                f" Tamaño procesado: {compressed_size // (1024 * 1024)} MB\n"
                f"⌛ Tiempo de procesamiento: {processing_time_str}\n"
                f" Duración: {duration_str}\n"
                f" ¡Muchas gracias por usar el bot!"
            )
            # Enviar el video comprimido con la descripción
            await app.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)
        except Exception as e:
            await app.send_message(chat_id=message.chat.id, text=f"Ocurrió un error al comprimir el video: {e}")
        finally:
            if os.path.exists(original_video_path):
                os.remove(original_video_path)
            if os.path.exists(compressed_video_path):
                os.remove(compressed_video_path)
    else:
        await app.send_message(chat_id=message.chat.id, text="Por favor, responde a un video para comprimirlo.")


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


def sanitize_input(input_string):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', input_string)

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)

common_lines = None

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



user_comp = {}

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

    if text.startswith(('/start', '.start')):
        await handle_start(client, message)
    elif text.startswith(('/convert', '.convert')):
        await compress_video(client, message)
    elif text.startswith(('/calidad', '.calidad')):
        await update_video_settings(client, message)
    elif text.startswith(('/adduser', '.adduser')):
        await add_user(client, message)
    elif text.startswith(('/remuser', '.remuser')):
        await remove_user(client, message)
    elif text.startswith(('/addchat', '.addchat')):
        await add_chat(client, message)
    elif text.startswith(('/remchat', '.remchat')):
        await remove_chat(client, message)
    elif text.startswith(('/banuser', '.banuser')):
        await ban_user(client, message)
    elif text.startswith(('/debanuser', '.debanuser')):
        await deban_user(client, message)
    elif text.startswith(('/up', '.up')):
        await handle_up(client, message)
    elif text.startswith(('/compress', '.compress')):
        await handle_compress(client, message, username)
    elif text.startswith(('/setsize', '.setsize')):
        await set_size(client, message)
    elif text.startswith(('/setmail', '.setmail')):
        await set_mail(client, message)
    elif text.startswith(('/rename', '.rename')):
        await rename(client, message)
        

    elif text.startswith('/sendmail'):
        if user_id not in user_emails:
            await message.reply("No has registrado ningún correo, usa /setmail para hacerlo.")
            return

        email = user_emails[user_id]
        if message.reply_to_message:
            msg = EmailMessage()
            msg['Subject'] = 'Mensaje de Telegram'
            msg['From'] = os.getenv('DISMAIL')
            msg['To'] = email

            if message.reply_to_message.text:
                msg.set_content(message.reply_to_message.text)
            elif message.reply_to_message.media:
                media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
                if os.path.getsize(media) < 59 * 1024 * 1024:  # 59 MB
                    with open(media, 'rb') as f:
                        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(media))
                else:
                    await message.reply("El archivo supera el límite de lo permitido (59 MB).")
                    return

            try:
                with smtplib.SMTP('disroot.org', 587) as server:
                    server.starttls()
                    server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                    server.send_message(msg)
                await message.reply("Correo electrónico enviado correctamente.")
            except Exception as e:
                await message.reply(f"Error al enviar el correo: {e}")
            finally:
                shutil.rmtree('mailtemp')
                os.mkdir('mailtemp')
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

    elif message.text.startswith(('/scan', '.scan', 'scan')):
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

            # Process results to check and modify links
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

    elif message.text.startswith(('/resumecodes', '.resumecodes', 'resumecodes')):
        # Obtener el mensaje completo
        full_message = message.text

        # Si el mensaje es una respuesta a un archivo, leer el contenido del archivo línea por línea
        if message.reply_to_message and message.reply_to_message.document:
            file_path = await message.reply_to_message.download()
            with open(file_path, 'r') as f:
                for line in f:
                    full_message += line
            os.remove(file_path)

        # Buscar todas las combinaciones de 6 números consecutivos
        codes = re.findall(r'\d{6}', full_message)
        
        if codes:
            # Dividir las combinaciones en grupos de 550
            chunk_size = 550
            chunks = [codes[i:i + chunk_size] for i in range(0, len(codes), chunk_size)]
            
            # Enviar cada grupo en un mensaje separado
            for chunk in chunks:
                result = ','.join(chunk)
                await message.reply(result)
        else:
            # Enviar mensaje si no hay códigos
            await message.reply("No hay códigos para resumir")


    elif message.text.startswith('/compare'):
        await handle_compare(message)

    elif message.text.startswith('/listo'):
        await handle_listo(message)


    elif message.text.startswith(('/resumetxtcodes', '.resumetxtcodes', 'resumetxtcodes')):
        # Obtener el mensaje completo
        full_message = message.text

        # Si el mensaje es una respuesta a un archivo, leer el contenido del archivo línea por línea
        if message.reply_to_message and message.reply_to_message.document:
            file_path = await message.reply_to_message.download()
            with open(file_path, 'r') as f:
                for line in f:
                    full_message += line
            os.remove(file_path)

        # Buscar todas las combinaciones de 6 números consecutivos
        codes = re.findall(r'\d{6}', full_message)
        
        if codes:
            # Crear un archivo de texto y escribir los códigos, cada uno en una línea distinta
            file_name = "codes.txt"
            with open(file_name, 'w') as f:
                for code in codes:
                    f.write(f"{code}\n")
            
            # Enviar el archivo al chat
            await message.reply_document(file_name)
            os.remove(file_name)
        else:
            # Enviar mensaje si no hay códigos
            await message.reply("No hay códigos para resumir")


    


    elif message.text.startswith(('/multiscan', '.multiscan', 'multiscan')):
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


            










app.run()
