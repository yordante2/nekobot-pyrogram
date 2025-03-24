from pyrogram import Client, filters
import zipfile
import shutil
import random
import os
import requests
from pyrogram.types import Message
from bs4 import BeautifulSoup
import asyncio
import re

def borrar_carpeta_h3dl():
    folder_name = 'h3dl'
    for root, dirs, files in os.walk(folder_name, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(folder_name)

async def nh_combined_operation(client, message, codes, link_type, operation_type="download"):
    if link_type == "nh":
        base_url = "nhentai.net/g"
    elif link_type == "3h":
        base_url = "3hentai.net/d"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for code in codes:
        url = f"https://{base_url}/{code}/"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"El código {code} es erróneo: {str(e)}")
            continue
        
        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        name = clean_string(title_tag.text.strip()) if title_tag else clean_string(code)

        # Descargar y enviar la portada
        img_url = f"https://{base_url}/{code}/1/"
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
                await client.send_photo(message.chat.id, img_filename, caption=f"https://{base_url}/{code} {name}")
            except Exception as e:
                await client.send_document(message.chat.id, img_filename, caption=f"https://{base_url}/{code} {name}")
        
        # Proseguir con la descarga si el tipo de operación es "download"
        if operation_type == "download":
            folder_name = os.path.join("h3dl", name)
            try:
                os.makedirs(folder_name, exist_ok=True)
            except OSError as e:
                if "File name too long" in str(e):
                    folder_name = folder_name[:50]
                    os.makedirs(folder_name, exist_ok=True)
                else:
                    print(f"Error al crear el directorio: {e}")
                    continue
            
            page_number = 1
            while True:
                page_url = f"https://{base_url}/{code}/{page_number}/"
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
            borrar_carpeta_h3dl()
                    

def sanitize_input(input_string):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', input_string)
def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)
