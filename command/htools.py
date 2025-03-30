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

async def nh_combined_operation(client, message, codes, protect_content, formato_seleccionado):
    """Realiza la descarga y manejo de archivos según el formato seleccionado."""
    try:
        base_url = "nhentai.net/g"
        for code in codes:
            url = f"https://{base_url}/{code}/"
            result = descargar_hentai(url, code, base_url, "download", protect_content, "downloads")
            if not result or result.get("error"):
                await message.reply(f"Error al manejar el código {code}: {result.get('error', 'Desconocido')}")
                continue

            caption = result.get("caption", "Contenido descargado")
            img_file = result.get("img_file")
            cbz_file_path = result.get("cbz_file")

            # Proceso según el formato seleccionado
            if formato_seleccionado in ["pdf", "cbzpdf"]:
                new_png_dir = "new_png"
                os.makedirs(new_png_dir, exist_ok=True)
                for image_name in os.listdir("downloads"):
                    image_path = os.path.join("downloads", image_name)
                    convertir_a_png_con_compresion(image_path, new_png_dir)

                pdf_file_path = f"{caption}.pdf"
                pdf_creado = crear_pdf_desde_png(caption, new_png_dir, pdf_file_path)
                if pdf_creado:
                    pdf_message = await client.send_document(MAIN_ADMIN, pdf_file_path)
                    pdf_file_id = pdf_message.document.file_id
                    callback_data_map[f"pdf_{code}"] = pdf_file_id
                    await pdf_message.delete()
                shutil.rmtree(new_png_dir)

            if formato_seleccionado in ["cbz", "cbzpdf"] and cbz_file_path:
                cbz_message = await client.send_document(MAIN_ADMIN, cbz_file_path)
                cbz_file_id = cbz_message.document.file_id
                callback_data_map[f"cbz_{code}"] = cbz_file_id
                await cbz_message.delete()

            # Enviar la primera imagen con su caption si es individual
            if len(codes) == 1 and img_file:
                buttons = [
                    InlineKeyboardButton("CBZ", callback_data=f"select_file|cbz|cbz_{code}"),
                    InlineKeyboardButton("PDF", callback_data=f"select_file|pdf|pdf_{code}")
                ]
                keyboard = InlineKeyboardMarkup([buttons])
                await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

            # Limpieza de directorios
            shutil.rmtree("downloads")

    except Exception as e:
        await message.reply(f"Error al procesar los códigos: {str(e)}")

async def manejar_opcion(client, callback_query, protect_content, user_id):
    """Maneja las solicitudes específicas del usuario según su elección de formato."""
    data = callback_query.data.split('|')
    opcion = data[1]  # Puede ser "cbz" o "pdf"
    identificador = data[2]  # Identificador único asociado al archivo

    if protect_content:
        text1 = "Contenido protegido. "
    else:
        text1 = ""

    # Verificar que el archivo aún está disponible
    file_id = callback_data_map.get(identificador)
    if not file_id:
        await callback_query.answer("El archivo ya no está disponible o fue eliminado.", show_alert=True)
        return

    # Enviar el archivo al usuario según el formato elegido
    if opcion == "cbz":
        await client.send_document(
            callback_query.message.chat.id,
            file_id,
            caption=f"{text1}Aquí está tu CBZ 📚",
            protect_content=protect_content
        )
    elif opcion == "pdf":
        await client.send_document(
            callback_query.message.chat.id,
            file_id,
            caption=f"{text1}Aquí está tu PDF 🖨️",
            protect_content=protect_content
        )

    # Confirmar la operación al usuario
    await callback_query.answer("¡Operación completada!")

    # Eliminar el identificador una vez utilizado
    callback_data_map.pop(identificador, None)
    

async def handle_callback(client, callback_query):
    """Maneja los callbacks según la selección del usuario."""
    data = callback_query.data.split('|')
    user_id = callback_query.from_user.id

    if data[0] == "select_file":
        formato = data[1]
        identificador = data[2]
        file_id = callback_data_map.get(identificador)

        if not file_id:
            await callback_query.answer("Archivo no disponible o ya eliminado.", show_alert=True)
            return

        if formato == "cbz":
            await client.send_document(callback_query.message.chat.id, file_id, caption="Aquí está tu CBZ 📚")
        elif formato == "pdf":
            await client.send_document(callback_query.message.chat.id, file_id, caption="Aquí está tu PDF 🖨️")

        # Elimina la referencia después de enviar el archivo
        callback_data_map.pop(identificador, None)

    elif data[0] == "detect_codes":
        codes = data[1].split(',')
        callback_data_map[user_id] = codes

        # Preguntar formato si hay múltiples códigos
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("CBZ", callback_data="select_format|cbz"),
                InlineKeyboardButton("PDF", callback_data="select_format|pdf"),
                InlineKeyboardButton("CBZ+PDF", callback_data="select_format|cbzpdf"),
            ]
        ])
        await callback_query.message.reply("Se han detectado varios códigos. ¿Qué formato deseas?", reply_markup=keyboard)

    elif data[0] == "select_format":
        formato_seleccionado = data[1]
        codes = callback_data_map.pop(user_id, None)
        if not codes:
            await callback_query.answer("No se encontraron códigos pendientes.", show_alert=True)
            return

        await nh_combined_operation(client, callback_query.message, codes, protect_content=True, formato_seleccionado=formato_seleccionado)
