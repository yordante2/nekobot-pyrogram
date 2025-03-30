import os
import requests
import zipfile
from uuid import uuid4
from fpdf import FPDF
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
import shutil
from command.get_files.hfiles import descargar_hentai

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
operation_status = {}

def convertir_a_webp(image_path, output_dir):
    """Convierte imágenes a WebP y las guarda en new_webp."""
    try:
        os.makedirs(output_dir, exist_ok=True)  # Crear carpeta si no existe
        with Image.open(image_path) as img:
            nuevo_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.webp")
            img.convert("RGB").save(nuevo_path, "WebP", quality=85)  # Ajusta la calidad si es necesario
            return nuevo_path
    except Exception as e:
        print(f"Error al convertir la imagen {image_path} a WebP: {e}")
        return None

def crear_pdf_con_webp(page_title, new_webp_dir, output_path):
    """Crea un PDF usando las imágenes WebP en la carpeta new_webp."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        for image_name in sorted(os.listdir(new_webp_dir)):
            image_path = os.path.join(new_webp_dir, image_name)
            if image_name.lower().endswith('.webp'):
                pdf.add_page()
                pdf.image(image_path, x=10, y=10, w=190)
        pdf.output(output_path)
        return True
    except Exception as e:
        print(f"Error al crear el PDF: {e}")
        return False

async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
    if link_type not in ["nh", "3h"]:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    # Restaurando base_url
    base_url = "nhentai.net/g" if link_type == "nh" else "3hentai.net/d"

    for code in codes:
        try:
            # Utilizando base_url para construir la URL
            url = f"https://{base_url}/{code}/"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error con el código {code}: {str(e)}")
            continue

        try:
            # Llama a la función para descargar y procesar el contenido
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, "downloads")
            if not result:
                await message.reply(f"Error con el código {code}: La función descargar_hentai retornó 'None'.")
                continue
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
                continue

            # Extraer resultados del diccionario
            caption = result.get("caption", "Contenido descargado")
            img_file = result.get("img_file")
            if not img_file:
                await message.reply(f"Error con el código {code}: Imagen no encontrada.")
                continue

            cbz_file_path = result.get("cbz_file")
            pdf_file_path = result.get("pdf_file")

            # Crear carpeta new_webp y convertir imágenes
            new_webp_dir = "new_webp"
            os.makedirs(new_webp_dir, exist_ok=True)
            for image_name in os.listdir("downloads"):
                image_path = os.path.join("downloads", image_name)
                convertir_a_webp(image_path, new_webp_dir)

            # Si no se genera el PDF, crearlo aquí con las imágenes en new_webp
            if not pdf_file_path:
                pdf_file_path = f"{result.get('caption', 'output')}.pdf"
                pdf_creado = crear_pdf_con_webp(result.get("caption", "output"), new_webp_dir, pdf_file_path)
                if not pdf_creado:
                    await message.reply(f"Error al generar el PDF para el código {code}.")
                    continue

            # Verifica si los archivos CBZ y PDF están presentes
            if cbz_file_path:
                cbz_message = await client.send_document(MAIN_ADMIN, cbz_file_path)
                cbz_file_id = cbz_message.document.file_id
                await cbz_message.delete()
            else:
                cbz_file_id = None

            if pdf_file_path:
                pdf_message = await client.send_document(MAIN_ADMIN, pdf_file_path)
                pdf_file_id = pdf_message.document.file_id
                await pdf_message.delete()
            else:
                pdf_file_id = None

            # Crear botones para los archivos
            cbz_button_id = str(uuid4()) if cbz_file_id else None
            pdf_button_id = str(uuid4()) if pdf_file_id else None

            if cbz_button_id:
                callback_data_map[cbz_button_id] = cbz_file_id
                operation_status[cbz_button_id] = False
            if pdf_button_id:
                callback_data_map[pdf_button_id] = pdf_file_id
                operation_status[pdf_button_id] = False

            # Crear botones según los archivos disponibles
            buttons = []
            if cbz_button_id:
                buttons.append(InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"))
            if pdf_button_id:
                buttons.append(InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}"))

            keyboard = InlineKeyboardMarkup([buttons])

            # Enviar la imagen con los botones
            await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

            # Eliminar los archivos y carpetas temporales
            if cbz_file_path and os.path.exists(cbz_file_path):
                os.remove(cbz_file_path)
            if pdf_file_path and os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
            if os.path.exists(new_webp_dir):
                shutil.rmtree(new_webp_dir)

        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")


async def manejar_opcion(client, callback_query, protect_content, user_id):
    data = callback_query.data.split('|')
    opcion = data[0]
    identificador = data[1]

    if protect_content is True:
        text1 = "Look Here"
    elif protect_content is False:
        text1 = ""

    if operation_status.get(identificador, True):
        await callback_query.answer("Ya realizaste esta operación. Solo puedes hacerla una vez.", show_alert=True)
        return

    datos_reales = callback_data_map.get(identificador)
    if not datos_reales:
        await callback_query.answer("La opción ya no es válida.", show_alert=True)
        return

    if opcion == "cbz":
        cbz_file_id = datos_reales
        await client.send_document(callback_query.message.chat.id, cbz_file_id, caption=f"{text1}Aquí está tu CBZ 📚", protect_content=protect_content)
    elif opcion == "pdf":
        pdf_file_id = datos_reales
        await client.send_document(callback_query.message.chat.id, pdf_file_id, caption=f"{text1}Aquí está tu PDF 🖨️", protect_content=protect_content)

    operation_status[identificador] = True
    await callback_query.answer("¡Opción procesada!")
