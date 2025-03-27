import asyncio
import os
import subprocess
import re
import datetime

# Configuración inicial de video_settings
video_settings = {
    'resolution': '640x400',
    'crf': '28',
    'audio_bitrate': '80k',
    'fps': '18',
    'preset': 'veryfast',
    'codec': 'libx265'
}

# Función para actualizar configuraciones de video
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
        configuracion_texto = "/calidad " + re.sub(r"[{},']", "", str(video_settings)).replace(":", "=").replace(",", " ")
        await message.reply_text(f"⚙️ Configuraciones de video actualizadas:\n`{configuracion_texto}`")
    except Exception as e:
        await message.reply_text(f"❌ Error al procesar el comando:\n{e}")

# Función para manejar tamaños con unidades dinámicas
def human_readable_size(size_in_kb):
    size_in_bytes = size_in_kb * 1024
    if size_in_bytes < 1024**2:
        return f"{size_in_kb} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_kb // 1024} MB"
    else:
        return f"{size_in_kb // (1024**2)} GB"

# Función para comprimir el video con manejo de progreso
async def compress_video(client, message, original_video_path):
    original_size = os.path.getsize(original_video_path)
    progress_message = await client.send_message(
        chat_id=message.chat.id,
        text=f"🎥 Convirtiendo el video...\n📂 Tamaño original: {human_readable_size(original_size // 1024)}"
    )

    compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
    ffmpeg_command = [
        'ffmpeg', '-y', '-i', original_video_path,
        '-s', video_settings['resolution'], '-crf', video_settings['crf'],
        '-b:a', video_settings['audio_bitrate'], '-r', video_settings['fps'],
        '-preset', video_settings['preset'], '-c:v', video_settings['codec'],
        compressed_video_path
    ]

    try:
        # Obtener la duración total del video usando ffprobe
        total_duration = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", original_video_path]
        )
        total_duration = float(total_duration.strip())  # Convertir duración a segundos

        start_time = datetime.datetime.now()
        process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
        last_update_time = datetime.datetime.now()

        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break

            # Filtrar y mostrar solo `size=` y `time=`
            if "size=" in output and "time=" in output:
                match = re.search(r"size=\s*([\d]+).*time=([\d:.]+)", output)
                if match:
                    size_kb, current_time_str = match.groups()
                    size_kb = int(size_kb)
                    readable_size = human_readable_size(size_kb)

                    # Convertir el tiempo actual del video a segundos
                    current_time_parts = list(map(float, current_time_str.split(':')))
                    current_time = (
                        current_time_parts[0] * 3600 +  # Horas a segundos
                        current_time_parts[1] * 60 +    # Minutos a segundos
                        current_time_parts[2]           # Segundos
                    )

                    # Calcular el porcentaje procesado
                    percentage = (current_time / total_duration) * 100

                    # Tiempo transcurrido desde el inicio del procesamiento
                    elapsed_time = str(datetime.datetime.now() - start_time).split('.')[0]

                    # Actualiza el mensaje cada 10 segundos
                    if (datetime.datetime.now() - last_update_time).seconds >= 10:
                        try:
                            await progress_message.edit_text(
                                text=(
                                    f"🚀 **Progreso:**\n"
                                    f"📊 Tamaño procesado: `{readable_size}`\n"
                                    f"⏱️ Tiempo actual: `{current_time_str}` / `{str(datetime.timedelta(seconds=total_duration))}`\n"
                                    f"📈 Porcentaje completado: `{percentage:.2f}%`\n"
                                    f"⏳ Tiempo total transcurrido: `{elapsed_time}`\n\n"
                                    f"🔄 El mensaje de progreso se edita cada 10 segundos..."
                                )
                            )
                            last_update_time = datetime.datetime.now()
                        except Exception as e:
                            if "MESSAGE_NOT_MODIFIED" in str(e):
                                pass  # Ignorar error si el mensaje no se modifica
                            else:
                                raise

        # Mostrar el mensaje "Proceso completado" durante 5 segundos antes de borrarlo
        complete_message = await progress_message.edit_text("✅ **Proceso completado. Preparando resultados...**")
        await asyncio.sleep(5)
        await complete_message.delete()

        compressed_size = os.path.getsize(compressed_video_path)
        duration_str = str(datetime.timedelta(seconds=total_duration))
        processing_time = datetime.datetime.now() - start_time
        processing_time_str = str(processing_time).split('.')[0]

        # Variables para el tamaño
        original_size_display = human_readable_size(original_size // 1024)
        compressed_size_display = human_readable_size(compressed_size // 1024)

        # Descripción con unidades dinámicas
        description = (
            f"✅ **Archivo procesado correctamente ☑️**\n"
            f"📂 **Tamaño original:** {original_size_display}\n"
            f"📁 **Tamaño procesado:** {compressed_size_display}\n"
            f"⌛ **Tiempo de procesamiento:** {processing_time_str}\n"
            f"🎥 **Duración del video:** {duration_str}\n"
            f"🎉 **¡Gracias por usar el bot!**"
        )
        nombre = os.path.splitext(os.path.basename(compressed_video_path))[0]
        
        await client.send_video(chat_id=message.chat.id, video=compressed_video_path, caption=nombre)
        await client.send_message(chat_id=message.chat.id, text=description)
    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"❌ **Ocurrió un error al comprimir el video:**\n{e}")
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)
