import os
import asyncio
import nest_asyncio
from pyrogram import Client
from pyrogram.types import Message
from command.moodleclient import upload_token
from command.htools import nh_combined_operation
from command.admintools import add_user, remove_user, add_chat, remove_chat, ban_user, deban_user, handle_start
from command.imgtools import create_imgchest_post
from command.webtools import handle_scan, handle_multiscan
from command.mailtools import send_mail, set_mail, verify_mail, set_mail_limit
from command.videotools import update_video_settings, compress_video, cancelar_tarea, listar_tareas
from command.filetools import handle_compress, rename, set_size
from command.telegramtools import get_file_id, send_file_by_id

nest_asyncio.apply()

# Definir usuarios administradores y VIPs
admin_users = list(map(int, os.getenv('ADMINS', '').split(','))) if os.getenv('ADMINS') else []
vip_users = list(map(int, os.getenv('VIP_USERS', '').split(','))) if os.getenv('VIP_USERS') else []

# Definir lista de IDs permitidos (allowed_ids)
allowed_ids = set(admin_users).union(set(vip_users))

# Revisar PROTECT_CONTENT
protect_content_env = os.getenv('PROTECT_CONTENT', '').strip().lower()
is_protect_content_enabled = protect_content_env == 'true'  # Evaluamos si es "True" en cualquier formato
auto_users = {}

async def process_command(client: Client, message: Message, active_cmd: str, admin_cmd: str, user_id: int, username: str, chat_id: int):
    global allowed_ids
    text = message.text.strip().lower() if message.text else ""
    if not is_protect_content_enabled and user_id not in allowed_ids:
        allowed_ids = allowed_ids.union({user_id})
    user_id = message.from_user.id
    auto = auto_users.get(user_id, False)
    
    def cmd(command_env, is_admin=False, is_vip=False):
        return (
            active_cmd == "all" or 
            command_env in active_cmd or 
            ((is_admin or is_vip) and (admin_cmd == "all" or command_env in admin_cmd))
        )

    if text.startswith("/start"):
        await asyncio.create_task(handle_start(client, message))
    
    elif text.startswith(("/nh", "/3h", "/cover", "/covernh")):
        if cmd("htools", user_id in admin_users, user_id in vip_users):
            parts = text.split(maxsplit=1)
            command = parts[0]
            codes = parts[1].split(',') if len(parts) > 1 and ',' in parts[1] else [parts[1]] if len(parts) > 1 else []
            operation_type = "download" if command in ("/nh", "/3h") else "cover"
            global link_type
            link_type = "nh" if command in ("/nh", "/covernh") else "3h"
            protect_content = user_id not in allowed_ids
            await asyncio.create_task(nh_combined_operation(client, message, codes, link_type, protect_content, operation_type))
        return
    
    elif text.startswith(("/setmail", "/sendmail", "/verify", "/setmb")):
        if cmd("mailtools", user_id in admin_users, user_id in vip_users):
            if text.startswith("/setmail"):
                await asyncio.create_task(set_mail(client, message))
            elif text.startswith("/sendmail"):
                await asyncio.create_task(send_mail(client, message))

            elif text.startswith("/setmb"):
                await asyncio.create_task(set_mail_limit(client, message))
                
            elif text.startswith("/verify"):
                await asyncio.create_task(verify_mail(client, message))
        return

    elif text.startswith(("/id", "/sendid")):
        if text.startswith("/id"):
            await asyncio.create_task(get_file_id(client, message))
            return
        elif text.startswith("/sendid"):
            await asyncio.create_task(send_file_by_id(client, message))
            return
    
    elif text.startswith(("/compress", "/setsize", "/rename")):
        if cmd("filetools", user_id in admin_users, user_id in vip_users):
            if text.startswith("/compress"):
                await asyncio.create_task(handle_compress(client, message, username))
            elif text.startswith("/setsize"):
                await asyncio.create_task(set_size(client, message))
            elif text.startswith("/rename"):
                await asyncio.create_task(rename(client, message))
        return

    if text.startswith(("/convert", "/calidad", "/autoconvert", "/cancel", "/list")) or (message.video is not None):
        if cmd("videotools", user_id in admin_users, user_id in vip_users):
            if text.startswith("/convert"):
                if message.reply_to_message and message.reply_to_message.media:
                    await asyncio.create_task(compress_video(admin_users, client, message, allowed_ids))

            elif text.startswith("/autoconvert"):
                # Activar/desactivar "auto" para este usuario
                if user_id in auto_users and auto_users[user_id]:
                    auto_users[user_id] = False
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="🛑 Modo automático desactivado.",
                        protect_content=True
                    )
                else:
                    auto_users[user_id] = True
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="✅ Modo automático activado.",
                        protect_content=True
                    )

            elif text.startswith("/calidad"):
                await asyncio.create_task(update_video_settings(client, message, allowed_ids))

            elif text.startswith("/cancel"):
                try:
                    task_id = text.split(" ", 1)[1].strip()
                    await cancelar_tarea(admin_users, client, task_id, message.chat.id, message, allowed_ids)
                except IndexError:
                    await client.send_message(
                        chat_id=message.chat.id,
                        text="⚠️ Debes proporcionar un ID válido para cancelar la tarea. Ejemplo: `/cancel <ID>`",
                        protect_content=True
                    )

            elif text.startswith("/list"):
                await listar_tareas(client, message.chat.id, allowed_ids, message)

            elif auto and (message.video or message.document):
                await asyncio.create_task(compress_video(admin_users, client, message, allowed_ids))
                                              
            elif text.startswith("/list"):
                await listar_tareas(client, message.chat.id, allowed_ids, message)

            elif auto and (message.video or message.document):
                await asyncio.create_task(compress_video(admin_users, client, message, allowed_ids))
                
        
    elif text.startswith("/imgchest"):
        if cmd("imgtools", user_id in admin_users, user_id in vip_users):
            if message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.document):
                await asyncio.create_task(create_imgchest_post(client, message))
            else:
                await message.reply("Por favor, usa el comando respondiendo a una foto.")
        return
    
    elif text.startswith(("/scan", "/multiscan")):
        if cmd("webtools", user_id in admin_users, user_id in vip_users):
            if text.startswith("/scan"):
                await asyncio.create_task(handle_scan(client, message))
            elif text.startswith("/multiscan"):
                await asyncio.create_task(handle_multiscan(client, message))
        return
    
    elif text.startswith(("/adduser", "/remuser", "/addchat", "/remchat")) and user_id in admin_users:
        if text.startswith("/adduser"):
            await asyncio.create_task(add_user(client, message, user_id, chat_id))
        elif text.startswith("/remuser"):
            await asyncio.create_task(remove_user(client, message, user_id, chat_id))
        elif text.startswith("/addchat"):
            await asyncio.create_task(add_chat(client, message, user_id, chat_id))
        elif text.startswith("/remchat"):
            await asyncio.create_task(remove_chat(client, message, user_id, chat_id))
        return
