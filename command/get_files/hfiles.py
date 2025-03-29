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
        # Crear nombre dinámico para el PDF
        pdf_filename = os.path.join(folder_name, f"{page_title}.pdf")

        # Crear una instancia del objeto PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Obtener las imágenes en orden numérico
        images = sorted(
            [file for file in os.listdir(folder_name) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp'))],
            key=lambda x: int(re.findall(r'\d+', x)[0])
        )

        # Agregar cada imagen al PDF
        for image in images:
            img_path = os.path.join(folder_name, image)
            pdf.add_page()
            pdf.image(img_path, x=10, y=10, w=190)  # Ajustar tamaño y posición de la imagen

        # Guardar el archivo PDF
        pdf.output(pdf_filename)

        return pdf_filename
    except Exception as e:
        print(f"Error al crear PDF: {e}")
        return None

def descargar_hentai(url, code, base_url, operation_type, protect_content, folder_name):
    results = {}
    try:
        # Asegurar que el directorio base aleatorio existe
        os.makedirs(folder_name, exist_ok=True)

        # Descargar la página inicial y obtener el título para el nombre y caption
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('title')
        page_title = clean_string(title_tag.text.strip()) if title_tag else f"Contenido_{code}"

        # Descargar la portada (1.jpg/1.png/etc.)
        page_url = f"https://{base_url}/{code}/1/"
        response = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})

        img_filename = None
        if img_tag:
            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_filename = os.path.join(folder_name, f"1{img_extension}")

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
            zip_filename = os.path.join(folder_name, f"{page_title}.cbz")
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for root, _, files in os.walk(folder_name):
                    for file in files:
                        zipf.write(os.path.join(root, file), arcname=file)

            # Crear PDF
            pdf_filename = os.path.join(folder_name, f"{page_title}.pdf")
            pdf_result = crear_pdf(folder_name, pdf_filename)

            results = {
                "caption": page_title,
                "img_file": img_filename,  # La portada será la primera imagen
                "cbz_file": zip_filename,
                "pdf_file": pdf_result
            }
        else:
            results = {"caption": page_title, "img_file": img_filename}
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
