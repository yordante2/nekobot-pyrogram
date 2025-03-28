import asyncio
import os
import subprocess
import re
import datetime
   
def human_readable_size(size, decimal_places=2):
    """
    Convierte bytes en un formato legible (KB, MB, GB, etc.).
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0
        

async def procesar_video(client, message, original_video_path, task_id, tareas_en_ejecucion):
    chat_id = message.chat.id
    compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"
    ffmpeg_command = [
        'ffmpeg', '-y', '-i', original_video_path,
        '-s', "640x400",  # Ajusta según tus settings dinámicos si es necesario
        '-crf', "28",
        '-b:a', "80k",
        '-r', "18",
        '-preset', "veryfast",
        '-c:v', "libx265",
        compressed_video_path
    ]

    progress_message = await client.send_message(chat_id=chat_id, text="🚀 **Iniciando proceso de compresión...**")

    try:
        # Obtener duración total del video usando ffprobe
        total_duration = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", original_video_path]
        )
        total_duration = float(total_duration.strip())

        start_time = datetime.datetime.now()
        process = subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)
        last_update_time = datetime.datetime.now()

        while True:
            # Cancelar tarea si se marca como cancelada
            if tareas_en_ejecucion[task_id]["cancel"]:
                process.terminate()
                await progress_message.edit_text(f"❌ Proceso cancelado para `{task_id}`.")
                if os.path.exists(compressed_video_path):
                    os.remove(compressed_video_path)
                    os.remove(original_video_path)
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

                    if (datetime.datetime.now() - last_update_time).seconds >= 10:
                        try:
                            await progress_message.edit_text(
                                text=(
                                    f"🚀 **Progreso:**\n"
                                    f"📊 Tamaño procesado: `{readable_size}`\n"
                                    f"⏱️ Tiempo actual: `{current_time_str}` / `{str(datetime.timedelta(seconds=total_duration))}`\n"
                                    f"📈 Porcentaje completado: `{percentage:.2f}%`\n"
                                    f"⏳ Tiempo total transcurrido: `{str(elapsed_time).split('.')[0]}`\n"
                                    f"⌛ **Tiempo estimado restante:** `{remaining_time}`\n\n"
                                    f"🔄 El mensaje de progreso se actualiza cada 10 segundos...\n"
                                    f"❌ `/cancel {task_id}`"
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
        return nombre, description, chat_id, compressed_video_path
    except Exception as e:
        await client.send_message(chat_id=chat_id, text=f"❌ **Ocurrió un error al procesar el video:**\n{e}")
        os.remove(original_video_path)
        os.remove(compressed_video_path)
    
