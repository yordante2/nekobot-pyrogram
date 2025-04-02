import os
import shutil
import random
import string
import py7zr
import time
from pyrogram import Client, filters

user_comp = {} 
compression_size = 10  

def compressfile(file_path, part_size):
    parts = []
    part_size *= 1024 * 1024  
    archive_path = f"{file_path}.7z"
    with py7zr.SevenZipFile(archive_path, 'w') as archive:
        archive.write(file_path, os.path.basename(file_path))
    with open(archive_path, 'rb') as archive:
        part_num = 1
        while True:
            part_data = archive.read(part_size)
            if not part_data:
                break
            part_file = f"{archive_path}.{part_num:03d}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts

async def handle_compress(client, message, username):
    reply_message = message.reply_to_message

    # Crear la carpeta 'server' si no existe
    if not os.path.exists('server'):
        os.mkdir('server')

    if reply_message and reply_message.caption and reply_message.caption.startswith("Look Here") and reply_message.from_user.is_self:
        await message.reply("No puedes comprimir este contenido debido a restricciones.", protect_content=True)
        return

    try:
        os.system("rm -rf ./server/*")
        progress_msg = await message.reply("Descargando el archivo para comprimirlo...")

        def get_file_name(message):
            if message.reply_to_message.document:
                return os.path.basename(message.reply_to_message.document.file_name)[:50]
            elif message.reply_to_message.photo:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".jpg"
            elif message.reply_to_message.audio:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".mp3"
            elif message.reply_to_message.video:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".mp4"
            elif message.reply_to_message.sticker:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20)) + ".webp"
            else:
                return ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        
        file_name = get_file_name(message)
        file_path = await client.download_media(
            message.reply_to_message,
            file_name=file_name
        )
        await client.edit_message_text(chat_id=message.chat.id, message_id=progress_msg.id, text="Comprimiendo el archivo...")
        
        sizd = user_comp.get(username, 10)
        parts = compressfile(file_path, sizd)
        
        # Añadir la cantidad de partes al mensaje
        num_parts = len(parts)
        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=progress_msg.id,
            text=f"Se ha comprimido el archivo en {num_parts} partes, ahora se enviarán las partes"
        )

        for part in parts:
            try:
                await client.send_document(message.chat.id, part)
            except Exception as e:
                print(f"Error al enviar la parte {part}: {e}")
                await message.reply(f"Error al enviar la parte {part}: {e}")
        
        # Eliminar el mensaje de progreso
        await client.delete_messages(chat_id=message.chat.id, message_ids=[progress_msg.id])

        # Enviar el mensaje final de "Esas son todas las partes"
        await message.reply("Esas son todas las partes")

        # Eliminar la carpeta 'server' y recrearla
        shutil.rmtree('server')
        os.mkdir('server')
    
    except Exception as e:
        await message.reply(f'Error: {str(e)}')
    

async def rename(client, message):
    reply_message = message.reply_to_message

    if reply_message and reply_message.media:
        try:
            # Obtenemos el nuevo nombre desde el comando del usuario
            new_name = message.text.split(' ', 1)[1]
            await message.reply("Reenviando la media con el nuevo nombre...")

            if reply_message.sticker:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=reply_message.sticker.file_id,
                    file_name=new_name  # Asignar el nombre del archivo
                )
            elif reply_message.document:
                # Para documentos
                await client.send_document(
                    chat_id=message.chat.id,
                    document=reply_message.document.file_id,
                    file_name=new_name  # Asignar nuevo nombre al documento
                )
            elif reply_message.video:
                # Para videos
                await client.send_video(
                    chat_id=message.chat.id,
                    video=reply_message.video.file_id,
                    caption=new_name  # Asignar el nuevo nombre como caption
                )
            elif reply_message.photo:
                # Para fotos
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=reply_message.photo.file_id,
                    caption=new_name  # Usar el nuevo nombre como caption
                )
            elif reply_message.audio:
                # Para audios
                await client.send_audio(
                    chat_id=message.chat.id,
                    audio=reply_message.audio.file_id,
                    title=new_name  # Asignar nuevo nombre como título
                )
            elif reply_message.voice:
                # Para notas de voz
                await client.send_voice(
                    chat_id=message.chat.id,
                    voice=reply_message.voice.file_id,
                    caption=new_name  # Usar el nuevo nombre como caption
                )
            else:
                # Si el tipo de media no está soportado
                await message.reply("Este tipo de media aún no está soportado para renombrar.")
        except Exception as e:
            await message.reply(f'Error: {str(e)}')
    else:
        await message.reply('Por favor responde a un mensaje que contenga media para renombrar.')


async def set_size(client, message):
    try:
        valor = int(message.text.split(" ")[1])  # Intentar convertir el valor a entero
        if valor < 1:  # Validar que el tamaño sea mayor a 0 MB
            await client.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgIAAxkBAAIF02fm3-XonvGhnnaVYCwO-y71UhThAAJuOgAC4KOCB77pR2Nyg3apHgQ"
            )
            time.sleep(5)
            await message.reply("¿Qué haces pendejo? El tamaño debe ser mayor que 0 MB.")
            return
        username = message.from_user.username
        user_comp[username] = valor  # Registrar el tamaño para el usuario
        await message.reply(f"Tamaño de archivos {valor}MB registrado para el usuario @{username}.")
    except IndexError:
        await message.reply("Por favor, proporciona el tamaño del archivo después del comando.")
    except ValueError:
        await message.reply("El tamaño proporcionado no es un número válido. Intenta nuevamente.")
    except Exception as e:  # Capturar cualquier otro error inesperado
        await message.reply(f"Ha ocurrido un error inesperado: {str(e)}")
        logging.error(f"Error inesperado en set_size: {str(e)}")
