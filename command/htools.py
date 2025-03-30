import os
import requests
import zipfile
from uuid import uuid4
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from command.get_files.hfiles import descargar_hentai
import os, shutil
    
MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
operation_status = {}

async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
    if link_type not in ["nh", "3h"]:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    # Restaurando base_url
    base_url = "nhentai.net/g" if link_type == "nh" else "3hentai.net/d"

    for code in codes:
        try:
            # Utilizando base_url para construir la URL
            url = f"https://{base_url}/{code}/"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error con el código {code}: {str(e)}")
            continue

        try:
            # Crear el CBZ y PDF en el root de ejecución
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, "downloads")
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
            else:
                caption = result.get("caption", "Contenido descargado")
                img_file = result.get("img_file")
                cbz_file_path = result['cbz_file']  # CBZ en el root
                pdf_file_path = result['pdf_file']  # PDF en el root

                # Enviar CBZ y PDF al admin
                cbz_message = await client.send_document(MAIN_ADMIN, cbz_file_path)
                cbz_file_id = cbz_message.document.file_id
                await cbz_message.delete()
                
                pdf_message = await client.send_document(MAIN_ADMIN, pdf_file_path)
                pdf_file_id = pdf_message.document.file_id
                await pdf_message.delete()

                # Guardar los IDs para los botones
                cbz_button_id = str(uuid4())
                pdf_button_id = str(uuid4())

                callback_data_map[cbz_button_id] = cbz_file_id
                callback_data_map[pdf_button_id] = pdf_file_id

                operation_status[cbz_button_id] = False
                operation_status[pdf_button_id] = False

                # Crear botones para las opciones
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"),
                        InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}")
                ]
                ])

                # Enviar la imagen con los botones
                await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)

                # Eliminar los archivos del root tras enviarlos al admin
                if os.path.exists(cbz_file_path):
                    os.remove(cbz_file_path)
                if os.path.exists(pdf_file_path):
                    os.remove(pdf_file_path)

                if os.path.exists("downloads"): shutil.rmtree("downloads")

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
        # Descargar CBZ desde File ID
        cbz_file_path = f"downloads/{uuid4()}.cbz"
        await client.download_media(datos_reales, cbz_file_path)

        # Verificar si el archivo fue descargado
        if not os.path.exists(cbz_file_path):
            await callback_query.answer("No se pudo descargar el CBZ. Inténtalo de nuevo.", show_alert=True)
            return

        # Crear carpeta temporal para fotos
        folder_path = f"downloads/{uuid4()}"
        os.makedirs(folder_path, exist_ok=True)

        # Extraer fotos y limpiar
        with zipfile.ZipFile(cbz_file_path, 'r') as zipf:
            zipf.extractall(folder_path)

        os.remove(cbz_file_path)  # Borrar CBZ descargado

        archivos = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        lote = 10
        for i in range(0, len(archivos), lote):
            grupo_fotos = [InputMediaPhoto(open(archivo, 'rb')) for archivo in archivos[i:i + lote]]
            await client.send_media_group(callback_query.message.chat.id, grupo_fotos)

        # Limpiar archivos de fotos y carpeta
        for archivo in archivos:
            os.remove(archivo)
        os.rmdir(folder_path)

    operation_status[identificador] = True
    await callback_query.answer("¡Opción procesada!")
