import os
import requests
import shutil
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from command.get_files.hfiles import descargar_hentai

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}

# Función principal para manejar operaciones
async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
    if link_type not in ["nh", "3h"]:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    base_url = "nhentai.net/g" if link_type == "nh" else "3hentai.net/d"

    if len(codes) == 1:  # Un solo código
        await process_and_send_code(client, message, codes[0], base_url, operation_type, protect_content)
    else:  # Múltiples códigos
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("CBZ", callback_data="multi_cbz"),
                InlineKeyboardButton("PDF", callback_data="multi_pdf"),
                InlineKeyboardButton("CBZ + PDF", callback_data="multi_both")
            ]
        ])
        code_list = ', '.join(codes)  # Lista de códigos en un string
        await message.reply(f"Se detectaron múltiples códigos: {code_list}. ¿Qué desea hacer?", reply_markup=keyboard)

        # Guardar los códigos y contexto para el callback
        callback_data_map["multi_cbz"] = {"codes": codes, "format": "cbz", "base_url": base_url, "operation_type": operation_type, "protect_content": protect_content}
        callback_data_map["multi_pdf"] = {"codes": codes, "format": "pdf", "base_url": base_url, "operation_type": operation_type, "protect_content": protect_content}
        callback_data_map["multi_both"] = {"codes": codes, "format": "both", "base_url": base_url, "operation_type": operation_type, "protect_content": protect_content}

# Función para procesar y enviar un solo código
async def process_and_send_code(client, message, code, base_url, operation_type, protect_content):
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
            cbz_file_path = result.get("cbz_file")
            pdf_file_path = result.get("pdf_file")

            # Enviar archivos al administrador y obtener los file_id
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

            # Crear botones para enviar archivos al usuario
            cbz_button_id = str(uuid4())
            pdf_button_id = str(uuid4())
            callback_data_map[f"cbz|{cbz_button_id}"] = cbz_file_id
            callback_data_map[f"pdf|{pdf_button_id}"] = pdf_file_id

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"),
                    InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}")
                ]
            ])

            # Enviar la portada con los botones
            await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

            # Limpieza de archivos después de procesarlos
            if os.path.exists(cbz_file_path):
                os.remove(cbz_file_path)
            if os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
    except Exception as e:
        await message.reply(f"Error al manejar el código {code}: {str(e)}")

# Función para manejar el callback
async def manejar_opcion(client, callback_query, protect_content, user_id):
    # Separar la data del callback
    data = callback_query.data.split('|')

    # Validar que el formato del callback sea correcto
    if len(data) != 2:  # Revisar si `data` contiene exactamente dos elementos
        await callback_query.answer("Opción inválida o expirada.", show_alert=True)
        return

    opcion = data[0]  # Puede ser "cbz" o "pdf"
    identificador = data[1]

    # Obtener el file_id del mapa
    file_id = callback_data_map.get(callback_query.data)
    if not file_id:
        await callback_query.answer("La opción ya no es válida o el archivo no está disponible.", show_alert=True)
        return

    # Enviar el archivo según la opción seleccionada
    try:
        if opcion == "cbz":
            await client.send_document(callback_query.message.chat.id, file_id, caption="Aquí está tu CBZ 📚", protect_content=protect_content)
        elif opcion == "pdf":
            await client.send_document(callback_query.message.chat.id, file_id, caption="Aquí está tu PDF 🖨️", protect_content=protect_content)

        await callback_query.answer("Archivo enviado correctamente.")
    except Exception as e:
        await callback_query.answer(f"Ocurrió un error al enviar el archivo: {str(e)}", show_alert=True)
