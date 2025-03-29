import os
import requests
import zipfile
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from command.get_files.hfiles import descargar_hentai, borrar_carpeta

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
message_ids_to_delete = []

async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
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
            await message.reply(f"Error con el código {code} es erróneo: {str(e)}")
            continue

        random_folder_name = f"downloads/{uuid4()}"
        os.makedirs(random_folder_name, exist_ok=True)

        try:
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, random_folder_name)
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
            else:
                caption = result.get("caption", "Contenido descargado")
                img_file = result.get("img_file")

                cbz_button_id = str(uuid4())
                pdf_button_id = str(uuid4())
                fotos_button_id = str(uuid4())

                callback_data_map[cbz_button_id] = result['cbz_file']
                callback_data_map[pdf_button_id] = result['pdf_file']
                callback_data_map[fotos_button_id] = result['cbz_file']

                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"),
                        InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}")
                    ],
                    [InlineKeyboardButton("Ver Fotos", callback_data=f"fotos|{fotos_button_id}")]
                ])

                # Enviar la imagen con el caption y los botones
                await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

                # Enviar CBZ y PDF a MAIN_ADMIN
                cbz_message = await client.send_document(
                    MAIN_ADMIN,
                    result['cbz_file']
                )
                message_ids_to_delete.append(cbz_message.id)

                pdf_message = await client.send_document(
                    MAIN_ADMIN,
                    result['pdf_file']
                )
                message_ids_to_delete.append(pdf_message.id)

                # Eliminar el PDF tras enviarlo
                if os.path.exists(result['pdf_file']):
                    os.remove(result['pdf_file'])
        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

        try:
            borrar_carpeta(random_folder_name, result.get("cbz_file"))
        except Exception as e:
            await message.reply(f"Error al limpiar carpeta: {str(e)}")

    await client.delete_messages(MAIN_ADMIN, message_ids_to_delete)
