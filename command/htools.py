import os
import requests
import shutil
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from command.get_files.hfiles import descargar_hentai

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
operation_status = {}

# Función principal para manejar la operación
async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
    if link_type not in ["nh", "3h"]:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    base_url = "nhentai.net/g" if link_type == "nh" else "3hentai.net/d"

    if len(codes) == 1:  # Un solo código
        await process_single_code(client, message, codes[0], base_url, operation_type, protect_content)
    else:  # Múltiples códigos
        cover_images = []
        captions = []
        for code in codes:
            try:
                url = f"https://{base_url}/{code}/"
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

                result = descargar_hentai(url, code, base_url, operation_type, protect_content, "downloads")
                if result.get("error"):
                    await message.reply(f"Error con el código {code}: {result['error']}")
                    continue

                img_file = result.get("img_file")
                if img_file and os.path.exists(img_file):
                    cover_images.append(img_file)
                captions.append(code)

            except Exception as e:
                await message.reply(f"Error al procesar el código {code}: {str(e)}")
        
        # Combinar y enviar la portada con los nombres
        if cover_images:
            first_cover = cover_images[0]  # Usar la primera imagen como portada
            combined_caption = "Códigos detectados: " + ", ".join(captions)
            await message.reply_photo(photo=first_cover, caption=combined_caption)

        # Mostrar botones de opciones
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("CBZ", callback_data="multi_cbz"),
                InlineKeyboardButton("PDF", callback_data="multi_pdf"),
                InlineKeyboardButton("CBZ + PDF", callback_data="multi_both")
            ]
        ])
        await message.reply("¿Cómo desea el contenido?", reply_markup=keyboard)

        # Guardar datos para el callback
        callback_data_map["multi_cbz"] = {"codes": codes, "format": "cbz"}
        callback_data_map["multi_pdf"] = {"codes": codes, "format": "pdf"}
        callback_data_map["multi_both"] = {"codes": codes, "format": "both"}

# Función para manejar un solo código
async def process_single_code(client, message, code, base_url, operation_type, protect_content):
    try:
        url = f"https://{base_url}/{code}/"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        result = descargar_hentai(url, code, base_url, operation_type, protect_content, "downloads")
        if result.get("error"):
            await message.reply(f"Error con el código {code}: {result['error']}")
        else:
            caption = result.get("caption", "Contenido descargado")
            img_file = result.get("img_file")

            # Enviar foto y archivos CBZ y PDF
            await message.reply_photo(photo=img_file, caption=caption)

            if result.get("cbz_file"):
                await client.send_document(message.chat.id, result["cbz_file"], caption="Aquí está tu CBZ 📚")
            if result.get("pdf_file"):
                await client.send_document(message.chat.id, result["pdf_file"], caption="Aquí está tu PDF 🖨️")

            # Limpieza de archivos después
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
    except Exception as e:
        await message.reply(f"Error al manejar el código {code}: {str(e)}")

# Función para manejar opciones en el callback
async def manejar_opcion(client, callback_query, protect_content, user_id):
    data = callback_query.data.split('|')
    opcion = data[0]  # "multi_cbz", "multi_pdf", o "multi_both"
    callback_data = callback_data_map.get(callback_query.data)

    if not callback_data:
        await callback_query.answer("Opción inválida o expirada.", show_alert=True)
        return

    codes = callback_data["codes"]
    format = callback_data["format"]

    # Responder al usuario que la operación ha comenzado
    await callback_query.answer("Procesando tu solicitud...", show_alert=False)

    try:
        base_url = "nhentai.net/g" if "nh" in callback_query.data else "3hentai.net/d"
        cover_images = []
        for code in codes:
            try:
                url = f"https://{base_url}/{code}/"
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

                # Descargar el contenido
                result = descargar_hentai(url, code, base_url, "download", protect_content, "downloads")
                if result.get("error"):
                    await client.send_message(callback_query.message.chat.id, f"Error con el código {code}: {result['error']}")
                    continue

                if result.get("img_file"):
                    cover_images.append(result["img_file"])

                # Enviar archivos según el formato seleccionado
                if format in ["cbz", "both"] and result.get("cbz_file"):
                    await client.send_document(callback_query.message.chat.id, result["cbz_file"], caption=f"CBZ para el código {code} 📚")
                if format in ["pdf", "both"] and result.get("pdf_file"):
                    await client.send_document(callback_query.message.chat.id, result["pdf_file"], caption=f"PDF para el código {code} 🖨️")

            except Exception as e:
                await client.send_message(callback_query.message.chat.id, f"Error con el código {code}: {str(e)}")
                continue

        # Enviar portada combinada con todos los códigos
        if cover_images:
            first_cover = cover_images[0]  # Usar la primera imagen como portada
            combined_caption = "Códigos procesados: " + ", ".join(codes)
            await client.send_photo(callback_query.message.chat.id, photo=first_cover, caption=combined_caption)

    finally:
        # Limpieza de archivos
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
