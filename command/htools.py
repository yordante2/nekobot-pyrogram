import os
import requests
from uuid import uuid4
from fpdf import FPDF
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
import shutil
from command.get_files.hfiles import descargar_hentai

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
operation_status = {}

def convertir_a_png_con_compresion(image_path, output_dir):
    """Convierte imágenes de cualquier formato a PNG optimizado."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        with Image.open(image_path) as img:
            nuevo_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.png")
            img.save(nuevo_path, "PNG", optimize=True)
            return nuevo_path
    except Exception as e:
        print(f"Error al convertir la imagen {image_path} a PNG: {e}")
        return None

def crear_pdf_desde_png(page_title, png_dir, output_path):
    """Crea un PDF usando las imágenes PNG en una carpeta."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        for image_name in sorted(os.listdir(png_dir)):
            image_path = os.path.join(png_dir, image_name)
            if image_name.lower().endswith('.png'):
                pdf.add_page()
                pdf.image(image_path, x=10, y=10, w=190)
        pdf.output(output_path)
        return True
    except Exception as e:
        print(f"Error al crear el PDF: {e}")
        return False

async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
    """Realiza operaciones combinadas: descarga, conversión y manejo de archivos."""
    if link_type not in ["nh", "3h"]:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    base_url = "nhentai.net/g" if link_type == "nh" else "3hentai.net/d"

    for code in codes:
        try:
            url = f"https://{base_url}/{code}/"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error con el código {code}: {str(e)}")
            continue

        try:
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, "downloads")
            if not result or result.get("error"):
                await message.reply(f"Error con el código {code}: {result.get('error', 'La función descargar_hentai retornó un error desconocido.')}")
                continue

            caption = result.get("caption", "Contenido descargado")
            img_file = result.get("img_file")
            cbz_file_path = result.get("cbz_file")

            new_png_dir = "new_png"
            os.makedirs(new_png_dir, exist_ok=True)

            for image_name in os.listdir("downloads"):
                image_path = os.path.join("downloads", image_name)
                convertir_a_png_con_compresion(image_path, new_png_dir)

            pdf_file_path = f"{caption}.pdf"
            pdf_creado = crear_pdf_desde_png(caption, new_png_dir, pdf_file_path)

            if pdf_creado and operation_type in ["pdf", "both"]:
                await client.send_document(message.chat.id, pdf_file_path, caption="Aquí está tu PDF 🖨️")

            if cbz_file_path and operation_type in ["cbz", "both"]:
                await client.send_document(message.chat.id, cbz_file_path, caption="Aquí está tu CBZ 📚")

            if img_file:
                await message.reply_photo(photo=img_file, caption=caption)

            shutil.rmtree("downloads")
            shutil.rmtree(new_png_dir)

        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

async def handle_callback(client, callback_query):
    """Maneja los callbacks que vienen del script principal."""
    data = callback_query.data.split('|')
    user_id = callback_query.from_user.id

    if data[0] == "select_format":
        formato_seleccionado = data[1]
        codes = callback_data_map.get(user_id)  # Recuperar los códigos previamente almacenados
        if not codes:
            await callback_query.answer("No se encontraron códigos pendientes.", show_alert=True)
            return

        await nh_combined_operation(client, callback_query.message, codes, "nh", protect_content=True, user_id=user_id, operation_type=formato_seleccionado)
        callback_data_map.pop(user_id, None)
    elif data[0] == "detect_codes":
        codes = data[1].split(",")
        callback_data_map[user_id] = codes

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("CBZ", callback_data="select_format|cbz"),
                InlineKeyboardButton("PDF", callback_data="select_format|pdf"),
                InlineKeyboardButton("CBZ+PDF", callback_data="select_format|both"),
            ]
        ])
        await callback_query.message.reply("Se han detectado varios códigos. ¿Qué formato deseas?", reply_markup=keyboard)
