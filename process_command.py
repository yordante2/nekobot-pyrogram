import os
import asyncio
from pyrogram import Client
from pyrogram.types import Message

# Importa las funciones específicas que se utilizan en la lógica de comandos
from moodleclient import upload_token
from htools import nh_combined_operation
from admintools import add_user, remove_user, add_chat, remove_chat, ban_user, deban_user
from imgtools import create_imgchest_post
from webtools import handle_scan, handle_multiscan
from mailtools import send_mail, set_mail
from videotools import update_video_settings, compress_video
from filetools import handle_compress, rename, set_size

async def process_command(client: Client, message: Message, active_cmd: str, admin_cmd: str, user_id: int, username: str, chat_id: int):
    text = message.text.strip().lower()
    
    def cmd(command_env, is_admin=False):
        return (
            active_cmd == "all" or 
            command_env in active_cmd or 
            (is_admin and (admin_cmd == "all" or command_env in admin_cmd))
        )
    
    if text.startswith(("/nh", "/3h", "/cover", "/covernh")):
        if cmd("htools", user_id in admin_users):
            parts = text.split(maxsplit=1)
            command = parts[0]
            codes = parts[1].split(',') if len(parts) > 1 and ',' in parts[1] else [parts[1]] if len(parts) > 1 else []
            operation_type = "download" if command in ("/nh", "/3h") else "cover"
            global link_type
            link_type = "nh" if command in ("/nh", "/covernh") else "3h"
            await asyncio.create_task(nh_combined_operation(client, message, codes, link_type, operation_type))
        return
    
    elif text.startswith(("/setmail", "/sendmail")):
        if cmd("mailtools", user_id in admin_users):
            if text.startswith("/setmail"):
                await set_mail(client, message)
            elif text.startswith("/sendmail"):
                await send_mail(client, message)
        return
    
    elif text.startswith(("/compress", "/setsize", "/rename")):
        if cmd("filetools", user_id in admin_users):
            if text.startswith("/compress"):
                await handle_compress(client, message, username)
            elif text.startswith("/setsize"):
                await set_size(client, message)
            elif text.startswith("/rename"):
                await rename(client, message)
        return
    
    elif text.startswith(("/convert", "/calidad")):
        if cmd("videotools", user_id in admin_users):
            if text.startswith("/convert"):
                await compress_video(client, message)
            elif text.startswith("/calidad"):
                await update_video_settings(client, message)
        return
    
    elif text.startswith("/imgchest"):
        if cmd("imgchest", user_id in admin_users):
            if message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.document):
                await create_imgchest_post(client, message)
            else:
                await message.reply("Por favor, usa el comando respondiendo a una foto.")
        return
    
    elif text.startswith(("/scan", "/multiscan")):
        if cmd("webtools", user_id in admin_users):
            if text.startswith("/scan"):
                await handle_scan(client, message)
            elif text.startswith("/multiscan"):
                await handle_multiscan(client, message)
        return
    
    elif text.startswith(("/adduser", "/remuser", "/addchat", "/remchat")) and user_id in admin_users:
        if text.startswith("/adduser"):
            await add_user(client, message, user_id, chat_id)
        elif text.startswith("/remuser"):
            await remove_user(client, message, user_id, chat_id)
        elif text.startswith("/addchat"):
            await add_chat(client, message, user_id, chat_id)
        elif text.startswith("/remchat"):
            await remove_chat(client, message, user_id, chat_id)
        return
          
