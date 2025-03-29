import os
import requests
import zipfile
from uuid import uuid4  # Generar identificadores únicos
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from command.get_files.hfiles import descargar_hentai, borrar_carpeta

# Variable MAIN_ADMIN definida en las variables de entorno
MAIN_ADMIN = os.getenv("MAIN_ADMIN")

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

        random_folder_name = f"downloads/{uuid4()}"
        os.makedirs(random_folder_name, exist_ok=True)

        try:
            # Descargar el contenido
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, random_folder_name)
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
            else:
                caption = result.get("caption", "Contenido descargado")

                # Subir CBZ al chat de MAIN_ADMIN y registrar el ID del mensaje
                cbz_message = await client.send_document(
                    MAIN_ADMIN,
                    result['cbz_file']
                )
                cbz_file_id = cbz_message.document.file_id
                await client.delete_messages(MAIN_ADMIN, cbz_message.id)  # Eliminar mensaje del chat del admin

                # Subir PDF al chat de MAIN_ADMIN y registrar el ID del mensaje
                pdf_message = await client.send_document(
                    MAIN_ADMIN,
                    result['pdf_file']
                )
                pdf_file_id = pdf_message.document.file_id
                await client.delete_messages(MAIN_ADMIN, pdf_message.id)  # Eliminar mensaje del chat del admin

                cbz_button_id = str(uuid4())
                pdf_button_id = str(uuid4())
                fotos_button_id = str(uuid4())

                # Crear botones Inline directamente con File IDs
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_file_id}"),
                        InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_file_id}")
                    ],
                    [InlineKeyboardButton("Ver Fotos", callback_data=f"fotos|{cbz_file_id}")]
                ])

                await message.reply("Opciones disponibles:", reply_markup=keyboard)
        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

        try:
            borrar_carpeta(random_folder_name, result.get("cbz_file"))
        except Exception as e:
            await message.reply(f"Error al limpiar carpeta: {str(e)}")

async def manejar_opcion(client, callback_query):
    """
    Procesa las opciones seleccionadas usando File IDs directamente.
    """
    data = callback_query.data.split('|')
    opcion = data[0]
    file_id = data[1]

    if opcion == "cbz":
        await client.send_document(
            callback_query.message.chat.id,
            file_id,
            caption="Aquí está tu CBZ 📚"
        )
    elif opcion == "pdf":
        await client.send_document(
            callback_query.message.chat.id,
            file_id,
            caption="Aquí está tu PDF 🖨️"
        )
    elif opcion == "fotos":
        temp_folder = f"temp/{uuid4()}"
        os.makedirs(temp_folder, exist_ok=True)

        cbz_file_path = await client.download_media(file_id)
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
