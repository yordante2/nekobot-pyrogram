import os
import re
import requests
import zipfile
from bs4 import BeautifulSoup
import shutil
from fpdf import FPDF

def sanitize_input(input_string):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', input_string)

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)

def crear_pdf(folder_name, pdf_filename):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=0)

        for file in sorted(os.listdir(folder_name)):
            file_path = os.path.join(folder_name, file)
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                pdf.add_page()
                pdf.image(file_path, x=0, y=0, w=210)  # Ajustar tamaño según sea necesario

        pdf.output(pdf_filename)
        print(f"PDF creado: {pdf_filename}")
        return pdf_filename
    except Exception as e:
        print(f"Error al crear PDF: {e}")
        return None

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

            # Crear PDF
            pdf_filename = f"{folder_name}.pdf"
            pdf_result = crear_pdf(folder_name, pdf_filename)

            results = {
                "caption": name,
                "img_file": img_filename,
                "cbz_file": zip_filename,
                "pdf_file": pdf_result
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
