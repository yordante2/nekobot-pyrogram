import os
import shutil
import random
import zipfile
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from bs4 import BeautifulSoup
import asyncio
import re

# Obtener valores de entorno de ADMINS y VIP_USERS
ADMINS = os.getenv("ADMINS", "")
VIP_USERS = os.getenv("VIP_USERS", "")

# Crear lista de User IDs
admin_ids = set(map(int, ADMINS.split(","))) if ADMINS else set()
vip_ids = set(map(int, VIP_USERS.split(","))) if VIP_USERS else set()
allowed_ids = admin_ids.union(vip_ids)

# Función para verificar si un usuario está permitido
def is_user_allowed(allowed_ids, user_id):
    return user_id in allowed_ids

# Función para borrar carpeta temporal
def borrar_carpeta_h3dl():
    try:
        folder_name = 'h3dl'
        for root, dirs, files in os.walk(folder_name, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(folder_name)
    except Exception as e:
        print(f"Error al borrar la carpeta: {e}")

# Funciones de sanitización
def sanitize_input(input_string):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', input_string)

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)

# Función principal de operación combinada
async def nh_combined_operation(client, message, codes, link_type, allowed_ids, operation_type="download"):
    if link_type == "nh":
        base_url = "nhentai.net/g"
    elif link_type == "3h":
        base_url = "3hentai.net/d"
    else:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for code in codes:
        url = f"https://{base_url}/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error al procesar el código {code}: {str(e)}")
            continue

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            name = clean_string(title_tag.text.strip()) if title_tag else clean_string(code)

            # Descargar y enviar la portada
            img_url = f"https://{base_url}/{code}/1/"
            response = requests.get(img_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})

            if img_tag:
                img_url = img_tag['src']
                img_extension = os.path.splitext(img_url)[1]
                img_data = requests.get(img_url, headers=headers).content
                img_filename = f"1{img_extension}"

                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)

                # Determinar si el contenido está protegido
                protect_content = not is_user_allowed(allowed_ids, message.from_user.id)
                caption = "Look Here" if protect_content else name

                await client.send_photo(
                    message.chat.id,
                    img_filename,
                    caption=f"{caption} https://{base_url}/{code} {name}",
                    protect_content=protect_content
                )
        except Exception as e:
            await message.reply(f"Error al procesar la portada del código {code}: {str(e)}")
            continue

        # Descargar si el tipo de operación es "download"
        if operation_type == "download":
            folder_name = os.path.join("h3dl", name)
            try:
                os.makedirs(folder_name, exist_ok=True)
            except OSError as e:
                await message.reply(f"Error al crear el directorio: {e}")
                continue

            page_number = 1
            while True:
                page_url = f"https://{base_url}/{code}/{page_number}/"
                try:
                    response = requests.get(page_url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    if page_number == 1:
                        await message.reply(f"Error al acceder a las páginas del código {code}: {str(e)}")
                    break

                try:
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
                except Exception as e:
                    await message.reply(f"Error al procesar la imagen de la página {page_number}: {str(e)}")
                    break

            try:
                zip_filename = os.path.join(f"{folder_name}.cbz")
                with zipfile.ZipFile(zip_filename, 'w') as zipf:
                    for root, _, files in os.walk(folder_name):
                        for file in files:
                            zipf.write(os.path.join(root, file), arcname=file)

                # Determinar si el archivo CBZ está protegido
                protect_content = not is_user_allowed(allowed_ids, message.from_user.id)
                caption = f"Look Here {name}" if protect_content else name

                await client.send_document(
                    message.chat.id,
                    zip_filename,
                    caption=caption,
                    protect_content=protect_content
                )
            except Exception as e:
                await message.reply(f"Error al comprimir o enviar el archivo {name}: {str(e)}")

            borrar_carpeta_h3dl()
