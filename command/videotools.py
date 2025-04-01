import asyncio
import os
import uuid
import re
import subprocess
import random
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
max_tareas = int(os.getenv('MAX_TASKS', '1'))

tareas_en_ejecucion = {}
cola_de_tareas = []

# Convertir tamaño en formato legible
def human_readable_size(size, decimal_places=2):
    for unit in ['MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0

# Actualizar configuraciones de video
async def update_video_settings(client, message, allowed_ids):
    user_id = message.from_user.id
    protect_content = user_id not in allowed_ids

    global video_settings
    try:
        command_params = message.text.split()[1:]
        params = dict(item.split('=') for item in command_params)
        for key, value in params.items():
            if key in video_settings:
                # Validación adicional
                if key == 'resolution' and not re.match(r'^\d+x\d+$', value):
                    raise ValueError("Resolución inválida. Usa formato WIDTHxHEIGHT.")
                video_settings[key] = value
        configuracion_texto = "/calidad " + re.sub(r"[{},']", "", str(video_settings)).replace(":", "=").replace(",", " ")
        await message.reply_text(f"⚙️ Configuraciones de video actualizadas:\n`{configuracion_texto}`", protect_content=protect_content)
    except ValueError as ve:
        await message.reply_text(f"❌ Error de validación:\n{ve}", protect_content=protect_content)
    except Exception as e:
        await message.reply_text(f"❌ Error al procesar el comando:\n{e}", protect_content=protect_content)

# Cancelar tareas
async def cancelar_tarea(admin_users, client, task_id, chat_id, message, allowed_ids):
    user_id_requesting = message.from_user.id
    protect_content = user_id_requesting not in allowed_ids

    global cola_de_tareas
    if task_id in tareas_en_ejecucion:
        tarea = tareas_en_ejecucion[task_id]
        if tarea["user_id"] == user_id_requesting or user_id_requesting in admin_users:
            tarea["cancel"] = True
            await client.send_message(chat_id=chat_id, text=f"❌ Tarea `{task_id}` cancelada.", protect_content=protect_content)
        else:
            await client.send_message(chat_id=chat_id, text="⚠️ No tienes permiso para cancelar esta tarea.", protect_content=protect_content)
    elif task_id in [t["id"] for t in cola_de_tareas]:
        tarea = next((t for t in cola_de_tareas if t["id"] == task_id), None)
        if tarea and (tarea["user_id"] == user_id_requesting or user_id_requesting in admin_users):
            cola_de_tareas = [t for t in cola_de_tareas if t["id"] != task_id]
            await client.send_message(chat_id=chat_id, text=f"❌ Tarea `{task_id}` eliminada de la cola.", protect_content=protect_content)
        else:
            await client.send_message(chat_id=chat_id, text="⚠️ No tienes permiso para eliminar esta tarea de la cola.", protect_content=protect_content)
    else:
        await client.send_message(chat_id=chat_id, text=f"⚠️ No se encontró la tarea con ID `{task_id}`.", protect_content=protect_content)

# Listar tareas
async def listar_tareas(client, chat_id, allowed_ids, message):
    user_id_requesting = message.from_user.id
    protect_content = user_id_requesting not in allowed_ids

    global cola_de_tareas, tareas_en_ejecucion

    # Inicia el mensaje con la tarea actual
    lista_tareas = "📝 Lista de tareas:\n\n"
    if tareas_en_ejecucion:
        for task_id, tarea in tareas_en_ejecucion.items():
            user_info = await client.get_users(tarea["user_id"])
            username = f"@{user_info.username}" if user_info.username else "Usuario Anónimo"
            lista_tareas += f"Tarea actual: ID {task_id} {username} (`{tarea['user_id']}`)\n\n"

    # Añade las tareas en cola
    if cola_de_tareas:
        for index, tarea in enumerate(cola_de_tareas, start=1):
            user_info = await client.get_users(tarea["user_id"])
            username = f"@{user_info.username}" if user_info.username else "Usuario Anónimo"
            lista_tareas += f"{index}. ID: `{tarea['id']}`\n   Usuario: {username} (`{tarea['user_id']}`)\n\n"
    else:
        if not tareas_en_ejecucion:
            lista_tareas += "📝 No hay tareas en ejecución ni en cola.\n"

    await client.send_message(chat_id=chat_id, text=lista_tareas, protect_content=protect_content)

import random
import subprocess
import os

# Función para obtener el número total de fotogramas
def get_video_metadata(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=nb_frames",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        metadata = result.stdout.strip()
        total_frames = int(metadata) if metadata.isdigit() else None

        if total_frames is None or total_frames == 0:
            raise ValueError("No se pudo obtener el número de fotogramas del video.")

        return total_frames
    except Exception as e:
        print(f"Error al obtener los metadatos del video: {e}")
        return 0


# Función para generar una miniatura desde un fotograma aleatorio
async def generate_thumbnail(video_path):
    try:
        # Obtener el número total de fotogramas
        total_frames = get_video_metadata(video_path)
        if total_frames <= 0:
            raise ValueError("No se pudo determinar el número de fotogramas.")

        # Limitar la selección a los primeros 10,000 fotogramas
        max_frames = min(total_frames, 10000)
        random_frame = random.randint(0, max_frames - 1)  # Fotograma aleatorio entre 0 y max_frames - 1

        output_thumb = f"{os.path.splitext(video_path)[0]}_miniatura.jpg"

        # Extraer el fotograma aleatorio
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vf", f"select='eq(n,{random_frame})'",
            "-vframes", "1",
            output_thumb
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Verificar que la miniatura se haya generado correctamente
        if not os.path.exists(output_thumb):
            raise IOError("No se pudo generar la miniatura.")

        return output_thumb
    except Exception as e:
        print(f"Error al generar la miniatura: {e}")
        return None


# Ajuste en compress_video
async def compress_video(admin_users, client, message, allowed_ids):
    user_id = message.from_user.id
    protect_content = user_id not in allowed_ids

    global cola_de_tareas
    task_id = str(uuid.uuid4())
    chat_id = message.chat.id

    user_info = await client.get_users(user_id)
    username = f"@{user_info.username}" if user_info.username else f"Usuario Anónimo ({user_id})"

    if len(tareas_en_ejecucion) >= max_tareas:
        cola_de_tareas.append({
            "id": task_id,
            "user_id": user_id,
            "username": username,
            "client": client,
            "message": message
        })
        await client.send_message(chat_id=chat_id, text=f"🕒 Tarea añadida a la cola con ID `{task_id}`.", protect_content=protect_content)
        return

    tareas_en_ejecucion[task_id] = {"cancel": False, "user_id": user_id}
    await client.send_message(chat_id=chat_id, text=f"🎥 Preparando la compresión del video...\n", protect_content=protect_content)

    try:
        if message.video:
            video_path = await client.download_media(message.video)
        elif message.reply_to_message and message.reply_to_message.video:
            video_path = await client.download_media(message.reply_to_message.video)
        else:
            await client.send_message(chat_id=chat_id, text=f"⚠️ No se encontró un video en el mensaje o respuesta asociada.", protect_content=protect_content)
            return

        # Generar la miniatura del video
        thumb_path = await generate_thumbnail(video_path)
        if not thumb_path:
            await client.send_message(chat_id=chat_id, text="⚠️ No se pudo generar una miniatura para el video.", protect_content=protect_content)

        # Obtener la duración del video
        duration = get_video_duration(video_path)
        if duration <= 0:
            await client.send_message(chat_id=chat_id, text="⚠️ No se pudo obtener la duración del video.", protect_content=protect_content)

        # Procesar el video
        file_name, description, chat_id, file_path, original_video_path = await procesar_video(client, message, video_path, task_id, tareas_en_ejecucion)

        # Enviar el video comprimido con la miniatura generada
        await client.send_video(
            chat_id=user_id,
            video=file_path,
            thumb=thumb_path,  # Miniatura generada aleatoriamente
            caption=file_name,
            duration=duration,
            protect_content=protect_content
        )

        # Notificar el resultado al usuario
        await client.send_message(chat_id=chat_id, text=description, protect_content=protect_content)

        # Eliminar los archivos temporales
        os.remove(original_video_path)
        os.remove(file_path)
        if thumb_path:
            os.remove(thumb_path)  # Eliminar la miniatura
    finally:
        try:
            del tareas_en_ejecucion[task_id]
        except KeyError:
            pass

        if cola_de_tareas:
            siguiente_tarea = cola_de_tareas.pop(0)
            await compress_video(admin_users, siguiente_tarea["client"], siguiente_tarea["message"], allowed_ids)
        print(f"Generando miniatura en el segundo {random_time}...")

        output_thumb = "miniatura.jpg"  # Nombre fijo para la miniatura
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-ss", str(random_time),
            "-vframes", "1",
            output_thumb
        ], stdout=devnull, stderr=devnull, check=True)
        return output_thumb
    except Exception as e:
        print(f"Error al generar la miniatura: {e}")
        return None


def get_video_duration(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = float(result.stdout.strip())
        return int(duration)  # Duración en segundos (redondeado)
    except Exception as e:
        print(f"Error al obtener la duración del video: {e}")
        return 0
