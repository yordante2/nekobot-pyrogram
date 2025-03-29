import os
import re
import requests
import zipfile
from bs4 import BeautifulSoup
from uuid import uuid4
from fpdf import FPDF

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9\[\] ]', '', s)

def crear_pdf(folder_name, page_title):
    try:
        # Crear nombre dinámico para el PDF en la carpeta PDF
        pdf_folder = os.path.join(folder_name, "PDF")
        os.makedirs(pdf_folder, exist_ok=True)
        pdf_filename = os.path.join(pdf_folder, f"{page_title}.pdf")

        # Crear una instancia del objeto PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Obtener las imágenes en orden numérico desde la carpeta PDF
        images = sorted(
            [file for file in os.listdir(pdf_folder) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))],
            key=lambda x: int(re.findall(r'\d+', x)[0])
        )

        # Agregar cada imagen al PDF
        for image in images:
            img_path = os.path.join(pdf_folder, image)
            pdf.add_page()
            pdf.image(img_path, x=10, y=10, w=190)

        # Guardar el archivo PDF
        pdf.output(pdf_filename)

        # Borrar la carpeta PDF
        for file in os.listdir(pdf_folder):
            os.remove(os.path.join(pdf_folder, file))
        os.rmdir(pdf_folder)

        return pdf_filename
    except Exception as e:
        print(f"Error al crear PDF: {e}")
        return None

def descargar_hentai(url, code, base_url, operation_type, protect_content, folder_name):
    results = {}
    try:
        # Crear directorios aleatorios y subcarpetas
        os.makedirs(folder_name, exist_ok=True)
        cbz_folder = os.path.join(folder_name, "CBZ")
        pdf_folder = os.path.join(folder_name, "PDF")
        os.makedirs(cbz_folder, exist_ok=True)
        os.makedirs(pdf_folder, exist_ok=True)

        # Descargar la página inicial y obtener el título para el nombre y caption
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('title')
        page_title = clean_string(title_tag.text.strip()) if title_tag else f"Contenido_{code}"

        # Descargar la portada (1.jpg/1.png/etc.) y guardarla con el nombre de la página web
        page_url = f"https://{base_url}/{code}/1/"
        response = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})

        img_filename = None
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_filename_root = os.path.join(folder_name, f"{base_url}{img_extension}")  # Nombre de página web
            img_filename = os.path.join(cbz_folder, f"1{img_extension}")  # Nombre normal
            img_filename_pdf = os.path.join(pdf_folder, f"1{img_extension}")

            img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content
            with open(img_filename_root, 'wb') as img_file:
                img_file.write(img_data)
            with open(img_filename, 'wb') as img_cbz_file:
                img_cbz_file.write(img_data)
            with open(img_filename_pdf, 'wb') as img_pdf_file:
                img_pdf_file.write(img_data)

        if operation_type == "download":
            # Descargar páginas y guardar en las carpetas CBZ y PDF
            page_number = 2
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
                img_filename_cbz = os.path.join(cbz_folder, f"{page_number}{img_extension}")
                img_filename_pdf = os.path.join(pdf_folder, f"{page_number}{img_extension}")

                img_data = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}).content
                with open(img_filename_cbz, 'wb') as img_cbz_file:
                    img_cbz_file.write(img_data)
                with open(img_filename_pdf, 'wb') as img_pdf_file:
                    img_pdf_file.write(img_data)

                page_number += 1

            # Crear CBZ
            zip_filename = os.path.join(folder_name, f"{page_title}.cbz")
            added_files = set()
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for file in os.listdir(cbz_folder):
                    if file not in added_files:
                        zipf.write(os.path.join(cbz_folder, file), arcname=file)
                        added_files.add(file)

            # Borrar la carpeta CBZ
            for file in os.listdir(cbz_folder):
                os.remove(os.path.join(cbz_folder, file))
            os.rmdir(cbz_folder)

            # Crear PDF
            pdf_filename = crear_pdf(folder_name, page_title)

            results = {
                "caption": page_title,
                "img_file": img_filename_root,
                "cbz_file": zip_filename,
                "pdf_file": pdf_filename
            }
        else:
            results = {"caption": page_title, "img_file": img_filename_root}
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
