import os
import asyncio
import nest_asyncio
from pyrogram import Client
from pyrogram.types import Message

# Importa las funciones específicas que se utilizan en la lógica de comandos
from command.moodleclient import upload_token
from command.htools import nh_combined_operation
from command.admintools import add_user, remove_user, add_chat, remove_chat, ban_user, deban_user, handle_start
from command.imgtools import create_imgchest_post
from command.webtools import handle_scan, handle_multiscan
from command.mailtools import send_mail, set_mail, verify_mail
from command.videotools import update_video_settings, compress_video
from command.filetools import handle_compress, rename, set_size

nest_asyncio.apply()

admin_users = list(map(int, os.getenv('ADMINS').split(',')))

auto = False
async def setauto(client,user_id):
    global auto
    if auto is False:
        auto = True
        client.send_message(chat_id=user_id, text="Se ha activado la auto conversión de videos")
        return

    if auto is True:
        auto = False
        client.send_message(chat_id=user_id, text="Se ha desactivado la auto conversión de videos")
        return



async def process_command(client: Client, message: Message, active_cmd: str, admin_cmd: str, user_id: int, username: str, chat_id: int):
    text = message.text.strip().lower()
    
    def cmd(command_env, is_admin=False):
        return (
            active_cmd == "all" or 
            command_env in active_cmd or 
            (is_admin and (admin_cmd == "all" or command_env in admin_cmd))
        )

    if text.startswith("/start"):
        await asyncio.create_task(handle_start(client, message))
    
    elif text.startswith(("/nh", "/3h", "/cover", "/covernh")):
        if cmd("htools", user_id in admin_users):
            parts = text.split(maxsplit=1)
            command = parts[0]
            codes = parts[1].split(',') if len(parts) > 1 and ',' in parts[1] else [parts[1]] if len(parts) > 1 else []
            operation_type = "download" if command in ("/nh", "/3h") else "cover"
            global link_type
            link_type = "nh" if command in ("/nh", "/covernh") else "3h"
            await asyncio.create_task(nh_combined_operation(client, message, codes, link_type, operation_type))
        return
    
    elif text.startswith(("/setmail", "/sendmail", "/verify")):
        if cmd("mailtools", user_id in admin_users):
            if text.startswith("/setmail"):
                await asyncio.create_task(set_mail(client, message))
            elif text.startswith("/sendmail"):
                await asyncio.create_task(send_mail(client, message))
            elif text.startswith("/verify"):
                await asyncio.create_task(verify_mail(client, message))
                    
        return
    
    elif text.startswith(("/compress", "/setsize", "/rename")):
        if cmd("filetools", user_id in admin_users):
            if text.startswith("/compress"):
                await asyncio.create_task(handle_compress(client, message, username))
            elif text.startswith("/setsize"):
                await asyncio.create_task(set_size(client, message))
            elif text.startswith("/rename"):
                await asyncio.create_task(rename(client, message))
        return
    
    elif text.startswith(("/convert", "/calidad", "/autoconvert")):
        if cmd("videotools", user_id in admin_users):
            if text.startswith("/convert"):
                await asyncio.create_task(compress_video(client, message))
            elif text.startswith("/autoconvert"):
                await asyncio.create_task(setauto(client, user_id))
            elif text.startswith("/calidad"):
                await asyncio.create_task(update_video_settings(client, message))
        return
    
    elif text.startswith("/imgchest"):
        if cmd("imgtools", user_id in admin_users):
            if message.reply_to_message and (message.reply_to_message.photo or message.reply_to_message.document):
                await asyncio.create_task(create_imgchest_post(client, message))
            else:
                await message.reply("Por favor, usa el comando respondiendo a una foto.")
        return
    
    elif text.startswith(("/scan", "/multiscan")):
        if cmd("webtools", user_id in admin_users):
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

            
