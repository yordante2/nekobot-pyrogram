import asyncio
import os
import uuid
import re
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
            lista_tareas += f"Tarea actual: ID {task_id} {username} /{tarea['user_id']}\n\n"

    # Añade las tareas en cola
    if cola_de_tareas:
        for index, tarea in enumerate(cola_de_tareas, start=1):
            user_info = await client.get_users(tarea["user_id"])
            username = f"@{user_info.username}" if user_info.username else "Usuario Anónimo"
            lista_tareas += f"{index}. ID: `{tarea['id']}`\n   Usuario: {username} (`{tarea['user_id')]`}\n\n"
    else:
        if not tareas_en_ejecucion:
            lista_tareas += "📝 No hay tareas en ejecución ni en cola.\n"

    await client.send_message(chat_id=chat_id, text=lista_tareas, protect_content=protect_content)

# Comprimir videos
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

        nombre, description, chat_id, compressed_video_path, original_video_path = await procesar_video(client, message, video_path, task_id, tareas_en_ejecucion)

        caption = f"Look Here {nombre}" if protect_content else nombre

        await client.send_video(chat_id=chat_id, video=compressed_video_path, caption=caption, protect_content=protect_content)
        await client.send_message(chat_id=chat_id, text=description, protect_content=protect_content)
        os.remove(original_video_path)
        os.remove(compressed_video_path)
    finally:
        try:
            del tareas_en_ejecucion[task_id]
        except KeyError:
            pass

        if cola_de_tareas:
            siguiente_tarea = cola_de_tareas.pop(0)
            await compress_video(admin_users, siguiente_tarea["client"], siguiente_tarea["message"], allowed_ids)
