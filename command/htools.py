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

async def manejar_opcion(client, callback_query, protect_content, user_id):
    try:
        # Responder rápidamente al callback query para evitar expiración
        await callback_query.answer("Procesando tu solicitud...", show_alert=False)

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

        # Procesar cada código uno por uno
        for code in codes:
            code_directory = None
            cbz_file = None
            pdf_file = None

            try:
                # Crear un directorio específico para este código
                code_directory = os.path.join("downloads", code)
                os.makedirs(code_directory, exist_ok=True)

                # Descargar imágenes y generar archivos
                url = f"https://{base_url}/{code}/"
                result = descargar_hentai(url, code, base_url, operation_type, protect_content, code_directory)

                if result.get("error"):
                    await client.send_message(callback_query.message.chat.id, f"Error con el código {code}: {result['error']}")
                    continue

                # Recuperar archivos generados
                cbz_file = result.get("cbz_file")
                pdf_file = result.get("pdf_file")

                # Asegúrate de que ambos archivos se han generado antes de continuar
                if not cbz_file or not pdf_file:
                    await client.send_message(callback_query.message.chat.id, f"Error generando archivos para el código {code}.")
                    continue

                # Enviar CBZ y/o PDF según la selección
                if accion in ["multi_cbz", "multi_both"]:
                    await client.send_document(callback_query.message.chat.id, cbz_file, caption=f"CBZ para el código {code} 📚")
                if accion in ["multi_pdf", "multi_both"]:
                    await client.send_document(callback_query.message.chat.id, pdf_file, caption=f"PDF para el código {code} 🖨️")

            except Exception as e:
                await client.send_message(callback_query.message.chat.id, f"Error procesando el código {code}: {str(e)}")
                continue

            finally:
                # Limpieza (puedes desactivarla para depuración, si es necesario)
                if cbz_file and os.path.exists(cbz_file):
                    os.remove(cbz_file)
                if pdf_file and os.path.exists(pdf_file):
                    os.remove(pdf_file)
                if code_directory and os.path.exists(code_directory):
                    shutil.rmtree(code_directory)

        # Confirmar finalización
        await client.send_message(callback_query.message.chat.id, "¡Operación completada correctamente!")
    except Exception as e:
        await callback_query.answer(f"Error procesando la solicitud: {str(e)}", show_alert=True)
                                                                                                                         
