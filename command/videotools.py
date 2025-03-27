import asyncio
import os
import subprocess
import re
import datetime
import uuid
from command.video_processor import procesar_video


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


def human_readable_size(size, decimal_places=2):
    """
    Convierte bytes en un formato legible (por ejemplo, KB, MB, GB).
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0


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


async def cancelar_tarea(client, task_id, chat_id):
    global cola_de_tareas
    if task_id in tareas_en_ejecucion:
        tareas_en_ejecucion[task_id]["cancel"] = True
        await client.send_message(chat_id=chat_id, text=f"❌ Tarea `{task_id}` cancelada.")
    elif task_id in [t["id"] for t in cola_de_tareas]:
        cola_de_tareas = [t for t in cola_de_tareas if t["id"] != task_id]
        await client.send_message(chat_id=chat_id, text=f"❌ Tarea `{task_id}` eliminada de la cola.")
    else:
        await client.send_message(chat_id=chat_id, text=f"⚠️ No se encontró la tarea con ID `{task_id}`.")


async def compress_video(client, message):
    global cola_de_tareas
    task_id = str(uuid.uuid4())
    chat_id = message.chat.id

    # Si se excede el límite de tareas en ejecución, encolar la tarea
    if len(tareas_en_ejecucion) >= max_tareas:
        cola_de_tareas.append({"id": task_id, "client": client, "message": message})
        await client.send_message(chat_id=chat_id, text=f"🕒 Tarea encolada con ID `{task_id}`.")
        return

    # Registrar tarea en ejecución
    tareas_en_ejecucion[task_id] = {"cancel": False}
    await client.send_message(chat_id=chat_id, text=f"🎥 Preparando la compresión del video...\n`{task_id}`")

    try:
        # Identificar el archivo original a descargar
        if message.video:  # Si el mensaje contiene un video directamente
            video_path = await client.download_media(message.video)
        elif message.reply_to_message and message.reply_to_message.video:  # Si es una respuesta con video
            video_path = await client.download_media(message.reply_to_message.video)
        else:
            await client.send_message(chat_id=chat_id, text=f"⚠️ No se encontró un video en el mensaje o respuesta asociada.")
            return

        # Procesar el video (utilizando la lógica existente)
        await procesar_video(client, message, video_path, task_id, tareas_en_ejecucion)
    finally:
        # Eliminar la tarea de la lista en ejecución
        try:
            del tareas_en_ejecucion[task_id]
        except KeyError:
            pass

        # Procesar la siguiente tarea en la cola, si existe
        if cola_de_tareas:
            siguiente_tarea = cola_de_tareas.pop(0)
            await compress_video(siguiente_tarea["client"], siguiente_tarea["message"])
