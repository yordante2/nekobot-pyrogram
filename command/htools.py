import os
import requests
import zipfile
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from command.get_files.hfiles import descargar_hentai

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
operation_status = {}

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

        random_folder_name = f"downloads/{uuid4()}"  # Crear carpeta aleatoria en downloads
        os.makedirs(random_folder_name, exist_ok=True)

        try:
            # Descargar contenido y generar CBZ y PDF dentro de la carpeta aleatoria
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, random_folder_name)
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
            else:
                caption = result.get("caption", "Contenido descargado")
                img_file = result.get("img_file")
                cbz_file_path = os.path.join(random_folder_name, os.path.basename(result['cbz_file']))
                pdf_file_path = os.path.join(random_folder_name, os.path.basename(result['pdf_file']))

                # Enviar CBZ al admin para obtener el File ID y eliminarlo del chat del admin
                cbz_message = await client.send_document(MAIN_ADMIN, cbz_file_path)
                cbz_file_id = cbz_message.document.file_id
                await cbz_message.delete()

                # Enviar PDF al admin para obtener el File ID y eliminarlo del chat del admin
                pdf_message = await client.send_document(MAIN_ADMIN, pdf_file_path)
                pdf_file_id = pdf_message.document.file_id
                await pdf_message.delete()

                # Crear botones con los File IDs
                cbz_button_id = str(uuid4())
                pdf_button_id = str(uuid4())
                fotos_button_id = str(uuid4())

                callback_data_map[cbz_button_id] = cbz_file_id  # Asociar botón con File ID del CBZ
                callback_data_map[pdf_button_id] = pdf_file_id  # Asociar botón con File ID del PDF
                callback_data_map[fotos_button_id] = cbz_file_id  # Guardar File ID del CBZ para descomprimir fotos

                operation_status[cbz_button_id] = False
                operation_status[pdf_button_id] = False
                operation_status[fotos_button_id] = False

                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"),
                        InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}")
                    ],
                    [InlineKeyboardButton("Ver Fotos", callback_data=f"fotos|{fotos_button_id}")]
                ])

                # Enviar imagen con botones
                await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

async def manejar_opcion(client, callback_query):
    data = callback_query.data.split('|')
    opcion = data[0]
    identificador = data[1]

    if operation_status.get(identificador, True):
        await callback_query.answer("Ya realizaste esta operación. Solo puedes hacerla una vez.", show_alert=True)
        return

    datos_reales = callback_data_map.get(identificador)
    if not datos_reales:
        await callback_query.answer("La opción ya no es válida.", show_alert=True)
        return

    if opcion == "cbz":
        cbz_file_id = datos_reales
        await client.send_document(callback_query.message.chat.id, cbz_file_id, caption="Aquí está tu CBZ 📚")
    elif opcion == "pdf":
        pdf_file_id = datos_reales
        await client.send_document(callback_query.message.chat.id, pdf_file_id, caption="Aquí está tu PDF 🖨️")
    elif opcion == "fotos":
        # Descargar CBZ desde el File ID
        cbz_file_path = f"downloads/{uuid4()}.cbz"
        await client.download_media(datos_reales, cbz_file_path)

        # Crear carpeta aleatoria para fotos
        folder_path = f"downloads/{uuid4()}"
        os.makedirs(folder_path, exist_ok=True)

        # Extraer fotos desde el CBZ
        with zipfile.ZipFile(cbz_file_path, 'r') as zipf:
            zipf.extractall(folder_path)

        # Eliminar el archivo CBZ tras extraer las fotos
        os.remove(cbz_file_path)

        # Enviar fotos al chat
        archivos = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        lote = 10
        for i in range(0, len(archivos), lote):
            grupo_fotos = [InputMediaPhoto(open(archivo, 'rb')) for archivo in archivos[i:i + lote]]
            await client.send_media_group(callback_query.message.chat.id, grupo_fotos)

        # Limpiar archivos temporales y la carpeta aleatoria
        for archivo in archivos:
            os.remove(archivo)
        os.rmdir(folder_path)  # Eliminar la carpeta aleatoria

    operation_status[identificador] = True
    await callback_query.answer("¡Opción procesada!")
