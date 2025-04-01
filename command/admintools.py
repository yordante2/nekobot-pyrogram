import os
from pyrogram import Client
from pyrogram.types import Message
import asyncio

async def handle_start(client, message):
    await message.reply("Funcionando")
    
async def add_user(client, message, user_id):
    new_user_id = int(message.text.split()[1])
    temp_users.append(new_user_id)
    allowed_users.append(new_user_id)
    await message.reply(f"Usuario {new_user_id} añadido temporalmente.")

async def remove_user(client, message, user_id, chat_id):
    rem_user_id = int(message.text.split()[1])
    if rem_user_id in temp_users:
        temp_users.remove(rem_user_id)
        allowed_users.remove(rem_user_id)
        await message.reply(f"Usuario {rem_user_id} eliminado temporalmente.")
    else:
        await message.reply("Usuario no encontrado en la lista temporal.")

async def add_chat(client, message, user_id, chat_id):
    chat_id = message.chat.id
    temp_chats.append(chat_id)
    allowed_users.append(chat_id)
    await message.reply(f"Chat {chat_id} añadido temporalmente.")

async def remove_chat(client, message, user_id, chat_id):
    chat_id = message.chat.id
    if chat_id in temp_chats:
        temp_chats.remove(chat_id)
        allowed_users.remove(chat_id)
        await message.reply(f"Chat {chat_id} eliminado temporalmente.")
    else:
        await message.reply("Chat no encontrado en la lista temporal.")

async def ban_user(client, message, user_id, chat_id):
    ban_user_id = int(message.text.split()[1])
    if ban_user_id not in admin_users:
        ban_users.append(ban_user_id)
        await message.reply(f"Usuario {ban_user_id} baneado.")

async def deban_user(client, message, user_id,chat_id):
    deban_user_id = int(message.text.split()[1])
    if deban_user_id in ban_users:
        ban_users.remove(deban_user_id)
        await message.reply(f"Usuario {deban_user_id} desbaneado.")
    else:
        await message.reply("Usuario no encontrado en la lista de baneados.")
        
