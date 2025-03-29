import os
import requests
import zipfile
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
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

                await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

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

                if os.path.exists(result['pdf_file']):
                    os.remove(result['pdf_file'])
        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

        try:
            borrar_carpeta(random_folder_name, result.get("cbz_file"))
        except Exception as e:
            await message.reply(f"Error al limpiar carpeta: {str(e)}")

    await client.delete_messages(MAIN_ADMIN, message_ids_to_delete)

async def manejar_opcion(client, callback_query):
    data = callback_query.data.split('|')
    opcion = data[0]
    identificador = data[1]

    datos_reales = callback_data_map.get(identificador)
    if not datos_reales:
        await callback_query.answer("La opción ya no es válida.", show_alert=True)
        return

    if opcion == "cbz":
        cbz_file_id = datos_reales
        await client.send_document(
            callback_query.message.chat.id,
            cbz_file_id,
            caption="Aquí está tu CBZ 📚"
        )
    elif opcion == "pdf":
        pdf_file_id = datos_reales
        await client.send_document(
            callback_query.message.chat.id,
            pdf_file_id,
            caption="Aquí está tu PDF 🖨️"
        )
    elif opcion == "fotos":
        cbz_file_id = datos_reales
        temp_folder = f"temp/{uuid4()}"
        os.makedirs(temp_folder, exist_ok=True)

        cbz_file_path = await client.download_media(cbz_file_id)
        os.rename(cbz_file_path, f"{temp_folder}/downloaded.cbz")

        for file in os.listdir(temp_folder):
            if file.lower().endswith(".cbz"):
                with zipfile.ZipFile(os.path.join(temp_folder, file), 'r') as zipf:
                    zipf.extractall(temp_folder)

        archivos = sorted([os.path.join(temp_folder, f) for f in os.listdir(temp_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        lote = 10
        for i in range(0, len(archivos), lote):
            grupo_fotos = [InputMediaPhoto(open(archivo, 'rb')) for archivo in archivos[i:i + lote]]
            await client.send_media_group(callback_query.message.chat.id, grupo_fotos)

        for archivo in archivos:
            os.remove(archivo)
        os.rmdir(temp_folder)

    await callback_query.answer("¡Opción procesada!")
