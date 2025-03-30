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

async def manejar_opcion_formato(client, message, codes, formato_seleccionado, protect_content):
    """Procesa la operación según el formato seleccionado por el usuario."""
    try:
        base_url = "nhentai.net/g"
        for code in codes:
            url = f"https://{base_url}/{code}/"
            result = descargar_hentai(url, code, base_url, "download", protect_content, "downloads")
            if not result or result.get("error"):
                await message.reply(f"Error al manejar el código {code}.")
                continue
            
            caption = result.get("caption", "Contenido descargado")
            img_file = result.get("img_file")
            cbz_file_path = result.get("cbz_file")

            # Proceso según formato seleccionado
            if formato_seleccionado in ["pdf", "cbzpdf"]:
                new_png_dir = "new_png"
                os.makedirs(new_png_dir, exist_ok=True)
                for image_name in os.listdir("downloads"):
                    image_path = os.path.join("downloads", image_name)
                    convertir_a_png_con_compresion(image_path, new_png_dir)

                pdf_file_path = f"{caption}.pdf"
                pdf_creado = crear_pdf_desde_png(caption, new_png_dir, pdf_file_path)
                if pdf_creado:
                    await client.send_document(message.chat.id, pdf_file_path, caption="Aquí está tu PDF 🖨️")
                shutil.rmtree(new_png_dir)

            if formato_seleccionado in ["cbz", "cbzpdf"] and cbz_file_path:
                await client.send_document(message.chat.id, cbz_file_path, caption="Aquí está tu CBZ 📚")

            # Enviar la primera imagen con el caption
            if img_file:
                await message.reply_photo(photo=img_file, caption=caption)
            
            shutil.rmtree("downloads")

    except Exception as e:
        await message.reply(f"Error al procesar la operación: {str(e)}")

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

        await manejar_opcion_formato(client, callback_query.message, codes, formato_seleccionado, protect_content=True)
        callback_data_map.pop(user_id, None)
    elif data[0] == "detect_codes":
        codes = data[1].split(",")
        callback_data_map[user_id] = codes

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("CBZ", callback_data="select_format|cbz"),
                InlineKeyboardButton("PDF", callback_data="select_format|pdf"),
                InlineKeyboardButton("CBZ+PDF", callback_data="select_format|cbzpdf"),
            ]
        ])
        await callback_query.message.reply("Se han detectado varios códigos. ¿Qué formato deseas?", reply_markup=keyboard)
