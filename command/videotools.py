import asyncio
import os
import subprocess
import re
import datetime
import uuid  # Para generar IDs únicos

# Configuración inicial
video_settings = {
    'resolution': '640x400',
    'crf': '28',
    'audio_bitrate': '80k',
    'fps': '18',
    'preset': 'veryfast',
    'codec': 'libx265'
}
max_tareas = 1  # Número máximo de tareas simultáneas

# Variables globales
tareas_en_ejecucion = {}
cola_de_tareas = []

async def update_video_settings(client, message):
    global video_settings
    try:
        command_params = message.text.split()[1:]
        params = dict(item.split('=') for item in command_params)
        for key, value in params.items():
            if key in video_settings:
                video_settings[key] = value
        configuracion_texto = "/calidad " + re.sub(r"[{},']", "", str(video_settings)).replace(":", "=").replace(",", " ")
        await message.reply_text(f"⚙️ Configuraciones de video actualizadas:\n`{configuracion_texto}`")
    except Exception as e:
        await message.reply_text(f"❌ Error al procesar el comando:\n{e}")

def human_readable_size(size_in_kb):
    size_in_bytes = size_in_kb * 1024
    if size_in_bytes < 1024**2:
        return f"{size_in_kb} KB"
    elif size_in_bytes < 1024**3:
        return f"{size_in_kb // 1024} MB"
    else:
        return f"{size_in_kb // (1024**2)} GB"
        

async def cancelar_tarea(client, task_id, chat_id):
    global cola_de_tareas  # Declaramos la variable global para interactuar con la cola
    if task_id in tareas_en_ejecucion:
        # Marcar la tarea en ejecución como cancelada
        tareas_en_ejecucion[task_id]["cancel"] = True
        await client.send_message(chat_id=chat_id, text=f"❌ Tarea `{task_id}` cancelada.")
    elif task_id in [t["id"] for t in cola_de_tareas]:
        # Eliminar la tarea de la cola
        cola_de_tareas = [t for t in cola_de_tareas if t["id"] != task_id]
        await client.send_message(chat_id=chat_id, text=f"❌ Tarea `{task_id}` eliminada de la cola.")
    else:
        # Notificar si el ID de la tarea no se encuentra
        await client.send_message(chat_id=chat_id, text=f"⚠️ No se encontró la tarea con ID `{task_id}`.")

async def compress_video(client, message, original_video_path):
    global cola_de_tareas  # Declarar la cola como variable global
    task_id = str(uuid.uuid4())  # Generar un ID único para la tarea
    chat_id = message.chat.id

    # Añadir tarea a la cola si excede el límite de tareas simultáneas
    if len(tareas_en_ejecucion) >= max_tareas:
        cola_de_tareas.append({"id": task_id, "client": client, "message": message, "path": original_video_path})
        await client.send_message(chat_id=chat_id, text=f"🕒 Tarea encolada con ID `{task_id}`.")
        return

    # Registrar la tarea como en ejecución
    tareas_en_ejecucion[task_id] = {"cancel": False}
    progress_message = await client.send_message(
        chat_id=chat_id,
        text=f"🎥 Convirtiendo el video...\n📂 Tamaño original: {human_readable_size(os.path.getsize(original_video_path) // 1024)}\n`{task_id}`"
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
        total_duration = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", original_video_path]
        )
        total_duration = float(total_duration.strip())

        start_time = datetime.datetime.now()
        process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
        last_update_time = datetime.datetime.now()

        while True:
            # Cancelación de la tarea
            if tareas_en_ejecucion[task_id]["cancel"]:
                process.terminate()
                await progress_message.edit_text(f"❌ Proceso cancelado para `{task_id}`.")
                try:
                    del tareas_en_ejecucion[task_id]
                except KeyError:
                    pass  # Si el ID ya fue eliminado, continuar normalmente
                if os.path.exists(compressed_video_path):
                    os.remove(compressed_video_path)
                return

            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break

            if "size=" in output and "time=" in output:
                match = re.search(r"size=\s*([\d]+).*time=([\d:.]+)", output)
                if match:
                    size_kb, current_time_str = match.groups()
                    size_kb = int(size_kb)
                    readable_size = human_readable_size(size_kb)

                    current_time_parts = list(map(float, current_time_str.split(':')))
                    current_time = (
                        current_time_parts[0] * 3600 +
                        current_time_parts[1] * 60 +
                        current_time_parts[2]
                    )

                    percentage = (current_time / total_duration) * 100
                    elapsed_time = datetime.datetime.now() - start_time
                    elapsed_seconds = elapsed_time.total_seconds()
                    estimated_total_time = elapsed_seconds / (percentage / 100) if percentage > 0 else 0
                    remaining_seconds = estimated_total_time - elapsed_seconds
                    remaining_time = str(datetime.timedelta(seconds=int(remaining_seconds)))

                    if (datetime.datetime.now() - last_update_time).seconds >= 1:
                        try:
                            await progress_message.edit_text(
                                text=(
                                    f"🚀 **Progreso:**\n"
                                    f"📊 Tamaño procesado: `{readable_size}`\n"
                                    f"⏱️ Tiempo actual: `{current_time_str}` / `{str(datetime.timedelta(seconds=total_duration))}`\n"
                                    f"📈 Porcentaje completado: `{percentage:.2f}%`\n"
                                    f"⏳ Tiempo total transcurrido: `{str(elapsed_time).split('.')[0]}`\n"
                                    f"⌛ **Tiempo estimado restante:** `{remaining_time}`\n\n"
                                    f"🔄 El mensaje de progreso se edita cada segundo...\n`{task_id}`"
                                )
                            )
                            last_update_time = datetime.datetime.now()
                        except Exception as e:
                            if "MESSAGE_NOT_MODIFIED" in str(e):
                                pass
                            else:
                                raise

        await progress_message.edit_text("✅ **Proceso completado. Preparando resultados...**")
        await asyncio.sleep(5)
        await progress_message.delete()

        compressed_size = os.path.getsize(compressed_video_path)
        duration_str = str(datetime.timedelta(seconds=total_duration))
        processing_time = datetime.datetime.now() - start_time
        processing_time_str = str(processing_time).split('.')[0]

        original_size_display = human_readable_size(os.path.getsize(original_video_path) // 1024)
        compressed_size_display = human_readable_size(os.path.getsize(compressed_video_path) // 1024)

        description = (
            f"✅ **Archivo procesado correctamente ☑️**\n"
            f"📂 **Tamaño original:** {original_size_display}\n"
            f"📁 **Tamaño procesado:** {compressed_size_display}\n"
            f"⌛ **Tiempo de procesamiento:** {processing_time_str}\n"
            f"🎥 **Duración del video:** {duration_str}\n"
            f"🎉 **¡Gracias por usar el bot!**"
        )
        nombre = os.path.splitext(os.path.basename(compressed_video_path))[0]

        await client.send_video(chat_id=chat_id, video=compressed_video_path, caption=nombre)
        await client.send_message(chat_id=chat_id, text=description)
    except Exception as e:
        await client.send_message(chat_id=chat_id, text=f"❌ **Ocurrió un error al comprimir el video:**\n{e}")
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)
        
        # Intentar eliminar la tarea en ejecución
        try:
            del tareas_en_ejecucion[task_id]
        except KeyError:
            pass  # Si ya fue eliminado, continuar normalmente

        # Procesar la siguiente tarea en la cola
        if cola_de_tareas:
            siguiente_tarea = cola_de_tareas.pop(0)
            await compress_video(
                siguiente_tarea["client"],
                siguiente_tarea["message"],
                siguiente_tarea["path"]
            )
            
