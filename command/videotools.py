import os
import shutil
import random
import string
import subprocess
import requests
import re
from pyrogram import Client, filters
from PIL import Image
import datetime


# Crear instancia del cliente
app = Client("mi_bot")

# Configuración inicial de video_settings
video_settings = {
    'resolution': '640x480',
    'crf': '28',
    'audio_bitrate': '64k',
    'fps': '25',
    'preset': 'fast',
    'codec': 'libx264'
}

async def update_video_settings(client, message):
    global video_settings
    try:
        # Extraer parámetros del mensaje
        command_params = message.text.split()[1:]
        params = dict(item.split('=') for item in command_params)

        # Actualizar video_settings con los nuevos valores
        for key, value in params.items():
            if key in video_settings:
                video_settings[key] = value

        # Responder con los nuevos valores actualizados
        await message.reply_text(f"Configuraciones de video actualizadas: {video_settings}")
    except Exception as e:
        await message.reply_text(f"Error al procesar el comando: {e}")

async def compress_video(client, message):  
    if message.reply_to_message.media:
        original_video_path = await client.download_media(message.reply_to_message.video or message.reply_to_message.document)
        original_size = os.path.getsize(original_video_path)
        await client.send_message(chat_id=message.chat.id, text=f"Iniciando la compresión del video...\n"
                                                                f"Tamaño original: {original_size // (1024 * 1024)} MB")
        compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', original_video_path,
            '-s', video_settings['resolution'], '-crf', video_settings['crf'],
            '-b:a', video_settings['audio_bitrate'], '-r', video_settings['fps'],
            '-preset', video_settings['preset'], '-c:v', video_settings['codec'],
            compressed_video_path
        ]
        try:
            start_time = datetime.datetime.now()
            process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
            await client.send_message(chat_id=message.chat.id, text="Compresión en progreso...")
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            compressed_size = os.path.getsize(compressed_video_path)
            duration = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                                 "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                                 compressed_video_path])
            duration = float(duration.strip())
            duration_str = str(datetime.timedelta(seconds=duration))
            processing_time = datetime.datetime.now() - start_time
            processing_time_str = str(processing_time).split('.')[0]  
            # Variables para el tamaño
            if original_size < (1024 * 1024):  # Menor a 1MB
                original_unit = "KB"
                original_size_display = original_size // 1024
            else:  # Igual o mayor a 1MB
                original_unit = "MB"
                original_size_display = original_size // (1024 * 1024)

            if compressed_size < (1024 * 1024):  # Menor a 1MB
                compressed_unit = "KB"
                compressed_size_display = compressed_size // 1024
            else:  # Igual o mayor a 1MB
                compressed_unit = "MB"
                compressed_size_display = compressed_size // (1024 * 1024)

            # Descripción con unidades dinámicas
            description = (
                f"✅ Archivo procesado correctamente ☑️\n"
                f" Tamaño original: {original_size_display} {original_unit}\n"
                f" Tamaño procesado: {compressed_size_display} {compressed_unit}\n"
                f"⌛ Tiempo de procesamiento: {processing_time_str}\n"
                f" Duración: {duration_str}\n"
                f" ¡Muchas gracias por usar el bot!"
            )
            nombre = os.path.splitext(os.path.basename(compressed_video_path))[0]
            
            await client.send_video(chat_id=message.chat.id, video=compressed_video_path, caption=nombre)
            await client.send_message(chat_id=message.chat.id, text=description)
        except Exception as e:
            await client.send_message(chat_id=message.chat.id, text=f"Ocurrió un error al comprimir el video: {e}")
        finally:
            if os.path.exists(original_video_path):
                os.remove(original_video_path)
            if os.path.exists(compressed_video_path):
                os.remove(compressed_video_path)
    else:
        await client.send_message(chat_id=message.chat.id, text="Por favor, responde a un video para comprimirlo.")
