import os
import re
import requests
import zipfile
from bs4 import BeautifulSoup
import shutil

def sanitize_input(input_string):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', input_string)

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)

def descargar_hentai(url, code, base_url, operation_type, protect_content, folder_name):
    results = {}

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('title')
        name = clean_string(title_tag.text.strip()) if title_tag else clean_string(str(code))

        # Obtener portada
        img_url = f"https://{base_url}/{code}/1/"
        response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})

        img_filename = None
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content
            img_filename = f"{folder_name}_cover{img_extension}"

            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)

        # Descargar imágenes y crear CBZ si es necesario
        if operation_type == "download":
            os.makedirs(folder_name, exist_ok=True)

            page_number = 1
            while True:
                page_url = f"https://{base_url}/{code}/{page_number}/"
                try:
                    response = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"})
                    response.raise_for_status()
                except requests.exceptions.RequestException:
                    break

                soup = BeautifulSoup(response.content, 'html.parser')
                img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
                if not img_tag:
                    break

                img_url = img_tag['src']
                img_extension = os.path.splitext(img_url)[1]
                img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content
                img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")

                with open(img_filename, 'wb') as img_file:
                    img_file.write(img_data)

                page_number += 1

            zip_filename = f"{folder_name}.cbz"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for root, _, files in os.walk(folder_name):
                    for file in files:
                        zipf.write(os.path.join(root, file), arcname=file)

            results = {
                "caption": name,
                "img_file": img_filename,
                "cbz_file": zip_filename
            }
        else:
            results = {"caption": name, "img_file": img_filename}

    except Exception as e:
        results = {"error": str(e)}

    return results

def borrar_carpeta(folder_name, cbz_file):
    try:
        # Borrar todos los archivos en la carpeta
        for file in os.listdir(folder_name):
            file_path = os.path.join(folder_name, file)
            os.remove(file_path)
        # Borrar carpeta y CBZ
        os.rmdir(folder_name)
        os.remove(cbz_file)
    except Exception as e:
        print(f"Error al borrar: {e}")
        
