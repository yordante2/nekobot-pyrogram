import os
import requests
import re
from uuid import uuid4  # Generar identificadores únicos
from command.get_files.hfiles import descargar_hentai, borrar_carpeta

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
            await message.reply(f"El código {code} es erróneo: {str(e)}")
            continue

        # Generar nombre único para la carpeta
        random_folder_name = f"h3dl/{uuid4()}"

        try:
            # Descargar el contenido
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, random_folder_name)
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
            else:
                # Enviar archivos procesados
                await client.send_photo(
                    message.chat.id,
                    result['img_file'],
                    caption=result['caption'],
                    protect_content=protect_content
                )
                await client.send_document(
                    message.chat.id,
                    result['cbz_file'],
                    caption=result['caption'],
                    protect_content=protect_content
                )
                await client.send_document(
                    message.chat.id,
                    result['pdf_file'],
                    caption=result['caption'],
                    protect_content=protect_content
                )
        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

        try:
            # Limpiar únicamente la carpeta temporal
            borrar_carpeta(random_folder_name, result.get("cbz_file"))
        except Exception as e:
            await message.reply(f"Error al limpiar carpeta para el código {code}: {str(e)}")
