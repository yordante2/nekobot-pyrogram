import os
import re
import requests
import zipfile
from bs4 import BeautifulSoup
from uuid import uuid4  # Para generar nombres únicos
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
                pdf.image(file_path, x=0, y=0, w=210)

        pdf.output(pdf_filename)
        print(f"PDF creado: {pdf_filename}")
        return pdf_filename
    except Exception as e:
        print(f"Error al crear PDF: {e}")
        return None

def descargar_hentai(url, code, base_url, operation_type, protect_content, folder_name):
    results = {}
    try:
        # Asegurar que el directorio base aleatorio existe
        os.makedirs(folder_name, exist_ok=True)

        # Descargar la portada
        img_url = f"https://{base_url}/{code}/1/"
        response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})

        img_filename = None
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_filename = os.path.join(folder_name, f"cover{img_extension}")

            with open(img_filename, 'wb') as img_file:
                img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content
                img_file.write(img_data)

        if operation_type == "download":
            # Descargar páginas y guardar en la carpeta temporal
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
                img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")

                with open(img_filename, 'wb') as img_file:
                    img_file.write(requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content)

                page_number += 1

            # Crear CBZ
            zip_filename = f"{folder_name}.cbz"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for root, _, files in os.walk(folder_name):
                    for file in files:
                        zipf.write(os.path.join(root, file), arcname=file)

            # Crear PDF
            pdf_filename = f"{folder_name}.pdf"
            pdf_result = crear_pdf(folder_name, pdf_filename)

            results = {
                "caption": code,
                "img_file": img_filename,
                "cbz_file": zip_filename,
                "pdf_file": pdf_result
            }
        else:
            results = {"caption": code, "img_file": img_filename}
    except Exception as e:
        results = {"error": str(e)}

    return results

def borrar_carpeta(folder_name, cbz_file):
    try:
        # Borrar archivos en la carpeta temporal
        if os.path.exists(folder_name):
            for file in os.listdir(folder_name):
                os.remove(os.path.join(folder_name, file))
            os.rmdir(folder_name)

        # Borrar archivo CBZ
        if cbz_file and os.path.exists(cbz_file):
            os.remove(cbz_file)
    except Exception as e:
        print(f"Error al borrar: {e}")
