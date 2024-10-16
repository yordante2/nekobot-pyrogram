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
from nekocmd import handle_start, compress_video, update_video_settings, add_user, remove_user, add_chat, remove_chat, ban_user, deban_user, set_size, set_mail


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


video_settings = {
    'resolution': '640x480',
    'crf': '28',
    'audio_bitrate': '64k',
    'fps': '30',
    'preset': 'fast',
    'codec': 'libx264'
}

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

    if text.startswith(('start', '.start', '/start')):
        await handle_start(client, message)
    elif text.startswith('/convert'):
        await compress_video(client, message)
    elif text.startswith('/calidad'):
        await update_video_settings(client, message)
    elif text.startswith('/adduser'):
        await add_user(client, message)
    elif text.startswith('/remuser'):
        await remove_user(client, message)
    elif text.startswith('/addchat'):
        await add_chat(client, message)
    elif text.startswith('/remchat'):
        await remove_chat(client, message)
    elif text.startswith('/banuser'):
        await ban_user(client, message)
    elif text.startswith('/debanuser'):
        await deban_user(client, message)
    elif text.startswith('/up'):
        await handle_up(client, message)
    elif text.startswith('/compress'):
        await handle_compress(client, message, username)
    elif text.startswith("/setsize"):
        await set_size(client, message)
    elif text.startswith('/setmail'):
        await set_mail(client, message)
        
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
    elif text.startswith('/rename'):
        if bot_in_use:
            await message.reply("El bot está en uso, espere un poco")
            return

        bot_in_use = True

        if not message.reply_to_message or not message.reply_to_message.media:
            await message.reply("Debe usar el comando respondiendo a un archivo")
            bot_in_use = False
            return

        command = text.split()
        if len(command) < 2:
            await message.reply("Introduzca un nuevo nombre")
            bot_in_use = False
            return

        new_name = command[1]
        media = message.reply_to_message

        # Determinar el tipo de medio y obtener el file_id correspondiente
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

        # Obtener la extensión del archivo original
        file_extension = os.path.splitext(file_path)[1]

        # Crear el nuevo nombre con la extensión original
        new_file_path = f"temprename/{new_name}{file_extension}"

        # Renombrar el archivo
        os.rename(file_path, new_file_path)

        # Enviar el archivo renombrado
        await client.send_document(message.chat.id, new_file_path)

        # Limpiar la variable de estado
        bot_in_use = False

        # Eliminar el archivo temporal
        os.remove(new_file_path)
        shutil.rmtree('temprename')
        os.mkdir('temprename')


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
