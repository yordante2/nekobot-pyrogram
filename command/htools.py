import os
import requests
import shutil
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from command.get_files.hfiles import descargar_hentai

# Mapa global para almacenar datos de callbacks
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
        # Generar identificador único para esta operación
        callback_id = str(uuid4())
        callback_data_map[callback_id] = {
            "codes": codes,
            "base_url": base_url,
            "operation_type": operation_type,
            "protect_content": protect_content
        }

        # Crear botones de opciones para múltiples descargas
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("CBZ", callback_data=f"multi_cbz|{callback_id}"),
                InlineKeyboardButton("PDF", callback_data=f"multi_pdf|{callback_id}"),
                InlineKeyboardButton("CBZ + PDF", callback_data=f"multi_both|{callback_id}")
            ]
        ])
        code_list = ', '.join(codes)
        await message.reply(f"Se detectaron múltiples códigos: {code_list}. ¿Qué desea hacer?", reply_markup=keyboard)

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

            # Enviar al administrador y guardar los file_id
            if cbz_file_path:
                cbz_message = await client.send_document(os.getenv("MAIN_ADMIN"), cbz_file_path)
                cbz_file_id = cbz_message.document.file_id
                await cbz_message.delete()
            else:
                cbz_file_id = None

            if pdf_file_path:
                pdf_message = await client.send_document(os.getenv("MAIN_ADMIN"), pdf_file_path)
                pdf_file_id = pdf_message.document.file_id
                await pdf_message.delete()
            else:
                pdf_file_id = None

            # Crear botones para enviar los archivos al usuario
            cbz_button_id = str(uuid4())
            pdf_button_id = str(uuid4())
            callback_data_map[f"cbz|{cbz_button_id}"] = {"file_id": cbz_file_id}
            callback_data_map[f"pdf|{pdf_button_id}"] = {"file_id": pdf_file_id}

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"),
                    InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}")
                ]
            ])

            await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

            # Limpieza de archivos
            if os.path.exists(cbz_file_path):
                os.remove(cbz_file_path)
            if os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")
    except Exception as e:
        await message.reply(f"Error al manejar el código {code}: {str(e)}")


async def manejar_opcion(client, callback_query, protect_content, user_id):
    try:
        # Separar la data del callback
        data = callback_query.data.split('|')
        if len(data) != 2:
            raise ValueError("Callback data no válida o mal formateada.")

        accion, callback_id = data[0], data[1]

        # Recuperar datos del mapa
        context = callback_data_map.get(callback_id)
        if not context:
            await callback_query.answer("La opción ya no es válida o ha expirado.", show_alert=True)
            return

        codes = context["codes"]
        base_url = context["base_url"]
        operation_type = context["operation_type"]

        # Borrar el mensaje que muestra las opciones
        await callback_query.message.delete()

        await callback_query.answer("Procesando tu solicitud...", show_alert=False)

        # Lista para recopilar archivos generados
        generated_cbz_files = []
        generated_pdf_files = []

        # Procesar los códigos según la acción seleccionada
        for code in codes:
            try:
                url = f"https://{base_url}/{code}/"
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()

                result = descargar_hentai(url, code, base_url, operation_type, protect_content, "downloads")
                if result.get("error"):
                    await client.send_message(callback_query.message.chat.id, f"Error con el código {code}: {result['error']}")
                    continue

                # Registrar archivos generados para su posterior eliminación
                if accion in ["multi_cbz", "multi_both"] and result.get("cbz_file"):
                    generated_cbz_files.append(result["cbz_file"])
                    await client.send_document(callback_query.message.chat.id, result["cbz_file"], caption=f"CBZ para el código {code} 📚")
                if accion in ["multi_pdf", "multi_both"] and result.get("pdf_file"):
                    generated_pdf_files.append(result["pdf_file"])
                    await client.send_document(callback_query.message.chat.id, result["pdf_file"], caption=f"PDF para el código {code} 🖨️")

            except Exception as e:
                await client.send_message(callback_query.message.chat.id, f"Error con el código {code}: {str(e)}")
                continue

        # Limpiar los archivos generados al finalizar el procesamiento de todos los códigos
        for file_path in generated_cbz_files + generated_pdf_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        # Eliminar el directorio de descargas si existe
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")

        await callback_query.answer("¡Operación completada correctamente!")
    except Exception as e:
        await callback_query.answer(f"Error procesando la solicitud: {str(e)}", show_alert=True)
