import os
import requests
from uuid import uuid4
from fpdf import FPDF
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
import shutil
from command.get_files.hfiles import descargar_hentai

MAIN_ADMIN = os.getenv("MAIN_ADMIN")
callback_data_map = {}
operation_status = {}
default_selection_map = {}  # Diccionario para asociar default_selection con user_id


def convertir_a_png_sobre_si_misma(img_file):
    """Convierte una imagen a PNG optimizado y la sobreescribe."""
    try:
        # Verificar si el archivo existe
        if not os.path.isfile(img_file):
            print(f"Archivo no encontrado: {img_file}")
            return None
        
        with Image.open(img_file) as img:
            # Convertir a modo RGB si es necesario (por ejemplo, para imágenes en modo 'P' o 'LA')
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            
            nuevo_path = os.path.splitext(img_file)[0] + ".png"  # Ruta con extensión .png
            img.save(nuevo_path, "PNG", optimize=True)  # Comprimir al máximo
            
            # Si el nuevo archivo tiene una extensión diferente, reemplazar el original
            if nuevo_path != img_file:
                os.remove(img_file)  # Eliminar el archivo original
                img_file = nuevo_path  # Actualizar img_file con el nuevo archivo optimizado

            return img_file  # Retorna la ruta actualizada del archivo optimizado
    except Exception as e:
        print(f"Error al convertir la imagen {img_file} a PNG: {e}")
        return None
        
def convertir_a_png_con_compresion(image_path, output_dir):
    """Convierte imágenes de cualquier formato a PNG optimizado."""
    try:
        os.makedirs(output_dir, exist_ok=True)  # Crear la carpeta si no existe
        with Image.open(image_path) as img:
            nuevo_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_path))[0]}.png")
            img.save(nuevo_path, "PNG", optimize=True)  # Comprimir al máximo
            return nuevo_path
    except Exception as e:
        print(f"Error al convertir la imagen {image_path} a PNG: {e}")
        return None

def crear_pdf_desde_png(page_title, png_dir, output_path):
    """Crea un PDF usando las imágenes PNG en una carpeta."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        for image_name in sorted(os.listdir(png_dir)):
            image_path = os.path.join(png_dir, image_name)
            if image_name.lower().endswith('.png'):
                pdf.add_page()
                pdf.image(image_path, x=10, y=10, w=190)
        pdf.output(output_path)
        shutil.rmtree(png_dir)
        return True
    except Exception as e:
        print(f"Error al crear el PDF: {e}")
        return False

def cambiar_default_selection(user_id, nueva_seleccion):
    """Cambia la selección predeterminada del usuario."""
    opciones_validas = [None, "pdf", "cbz", "both"]  # Todas las opciones en minúsculas
    if nueva_seleccion is not None:  # Transformar a minúsculas si no es None
        nueva_seleccion = nueva_seleccion.lower()

    if nueva_seleccion not in opciones_validas:
        raise ValueError("Selección inválida. Debe ser None, 'PDF', 'CBZ', o 'Both'.")
    default_selection_map[user_id] = nueva_seleccion  # Almacenamos en formato uniforme

async def enviar_archivo_admin_y_obtener_file_id(client, admin_id, file_path):
    """Envía un archivo al administrador principal del bot, obtiene el file_id y lo elimina del chat."""
    try:
        message = await client.send_document(admin_id, file_path)
        file_id = message.document.file_id
        await message.delete()  # Borra el archivo del chat del administrador
        return file_id
    except Exception as e:
        print(f"Error al enviar archivo al administrador: {e}")
        return None

async def nh_combined_operation(client, message, codes, link_type, protect_content, user_id, operation_type="download"):
    if link_type not in ["nh", "3h"]:
        await message.reply("Tipo de enlace no válido. Use 'nh' o '3h'.")
        return

    
    # Configuración inicial del usuario
    user_default_selection = default_selection_map.get(user_id, None)

    if MAIN_ADMIN is None and user_default_selection is None and operation_type=="download":
        await message.reply("Debe usar `/setfile` antes de descargar.")
        return


    # Verificación de múltiples códigos y default_selection
    if len(codes) > 1 and user_default_selection is None and operation_type=="download":
        await message.reply("Para la descarga múltiple debe seleccionar un tipo de archivo con `/setfile`.")
        return

    # Restaurando base_url
    base_url = "nhentai.net/g" if link_type == "nh" else "3hentai.net/d"

    for code in codes:
        try:
            url = f"https://{base_url}/{code}/"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await message.reply(f"Error con el código {code}: {str(e)}")
            continue

        try:
            result = descargar_hentai(url, code, base_url, operation_type, protect_content, user_default_selection, "downloads")
            if not result:
                await message.reply(f"Error con el código {code}: La función descargar_hentai retornó 'None'.")
                continue
            if result.get("error"):
                await message.reply(f"Error con el código {code}: {result['error']}")
                continue

            caption = result.get("caption", "Contenido descargado")
            img_file = result.get("img_file")
            if not img_file:
                await message.reply(f"Error con el código {code}: Imagen no encontrada.")
                continue

            cbz_file_path = result.get("cbz_file")
            pdf_file_path = result.get("pdf_file")

            if operation_type=="cover":
                img_file = convertir_a_png_sobre_si_misma(img_file)
                await message.reply_photo(photo=img_file, caption=caption)
                os.remove(img_file)
                continue

            if not pdf_file_path and operation_type=="download":
                pdf_file_path = f"{result.get('file_name', 'output')}.pdf"
                new_png_dir = "new_png"
                os.makedirs(new_png_dir, exist_ok=True)
                for image_name in os.listdir("downloads"):
                    image_path = os.path.join("downloads", image_name)
                    convertir_a_png_con_compresion(image_path, new_png_dir)
                pdf_creado = crear_pdf_desde_png(result.get("caption", "output"), new_png_dir, pdf_file_path)
                if not pdf_creado:
                    await message.reply(f"Error al generar el PDF para el código {code}.")
                    continue

            # Envío según la selección del usuario
            if user_default_selection:
                img_file = convertir_a_png_sobre_si_misma(img_file)
                await message.reply_photo(photo=img_file, caption=caption)
                os.remove(img_file)
                # Enviar archivo según selección
                if user_default_selection == "cbz" and cbz_file_path:
                    await client.send_document(message.chat.id, cbz_file_path, caption="", protect_content=protect_content)
                elif user_default_selection == "pdf" and pdf_file_path:
                    await client.send_document(message.chat.id, pdf_file_path, caption="", protect_content=protect_content)
                elif user_default_selection == "both":
                    if cbz_file_path:
                        await client.send_document(message.chat.id, cbz_file_path, caption="", protect_content=protect_content)
                    if pdf_file_path:
                        await client.send_document(message.chat.id, pdf_file_path, caption="", protect_content=protect_content)
            else:
                # Enviar archivos al administrador y obtener file_id
                img_file = convertir_a_png_sobre_si_misma(img_file)
                cbz_file_id = await enviar_archivo_admin_y_obtener_file_id(client, MAIN_ADMIN, cbz_file_path) if cbz_file_path else None
                pdf_file_id = await enviar_archivo_admin_y_obtener_file_id(client, MAIN_ADMIN, pdf_file_path) if pdf_file_path else None

                # Crear botones para descargar desde file_id
                buttons = []
                if cbz_file_id:
                    cbz_button_id = str(uuid4())
                    callback_data_map[cbz_button_id] = cbz_file_id
                    operation_status[cbz_button_id] = False
                    buttons.append(InlineKeyboardButton("Descargar CBZ", callback_data=f"cbz|{cbz_button_id}"))
                if pdf_file_id:
                    pdf_button_id = str(uuid4())
                    callback_data_map[pdf_button_id] = pdf_file_id
                    operation_status[pdf_button_id] = False
                    buttons.append(InlineKeyboardButton("Descargar PDF", callback_data=f"pdf|{pdf_button_id}"))

                keyboard = InlineKeyboardMarkup([buttons])

                # Enviar imagen y botones al usuario
                await message.reply_photo(photo=img_file, caption=caption, reply_markup=keyboard)
                os.remove(img_file)

            # Limpieza de archivos
            if cbz_file_path and os.path.exists(cbz_file_path):
                os.remove(cbz_file_path)
            if pdf_file_path and os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)
            if os.path.exists("downloads"):
                shutil.rmtree("downloads")

        except Exception as e:
            await message.reply(f"Error al manejar archivos para el código {code}: {str(e)}")

async def manejar_opcion(client, callback_query, protect_content, user_id):
    data = callback_query.data.split('|')
    opcion = data[0]
    identificador = data[1]

    if protect_content is True:
        text1 = "Look Here"
    elif protect_content is False:
        text1 = ""

    if operation_status.get(identificador, True):
        await callback_query.answer("Ya realizaste esta operación. Solo puedes hacerla una vez.", show_alert=True)
        return

    datos_reales = callback_data_map.get(identificador)
    if not datos_reales:
        await callback_query.answer("La opción ya no es válida.", show_alert=True)
        return

    if opcion == "cbz":
        cbz_file_id = datos_reales
        await client.send_document(callback_query.message.chat.id, cbz_file_id, caption=f"{text1}", protect_content=protect_content)
    elif opcion == "pdf":
        pdf_file_id = datos_reales
        await client.send_document(callback_query.message.chat.id, pdf_file_id, caption=f"{text1}", protect_content=protect_content)
    elif opcion == "pdf":
        await client.send_document(callback_query.message.chat.id, pdf_file_id, caption=f"{text1}", protect_content=protect_content)

    operation_status[identificador] = True
    await callback_query.answer("¡Opción procesada!")
    
        
