import os
import glob
from pyrogram import Client, filters
import zipfile
import shutil
import random
import string
import smtplib
from email.message import EmailMessage
from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import re

async def handle_adduser(message):
    user_id = message.from_user.id
    if user_id in admin_users:
        new_user_id = int(message.text.split()[1])
        temp_users.append(new_user_id)
        allowed_users.append(new_user_id)
        await message.reply(f"Usuario {new_user_id} añadido temporalmente.")

async def handle_remuser(message):
    user_id = message.from_user.id
    if user_id in admin_users:
        rem_user_id = int(message.text.split()[1])
        if rem_user_id in temp_users:
            temp_users.remove(rem_user_id)
            allowed_users.remove(rem_user_id)
            await message.reply(f"Usuario {rem_user_id} eliminado temporalmente.")
        else:
            await message.reply("Usuario no encontrado en la lista temporal.")

async def handle_addchat(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id in admin_users:
        temp_chats.append(chat_id)
        allowed_users.append(chat_id)
        await message.reply(f"Chat {chat_id} añadido temporalmente.")

async def handle_remchat(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if user_id in admin_users:
        if chat_id in temp_chats:
            temp_chats.remove(chat_id)
            allowed_users.remove(chat_id)
            await message.reply(f"Chat {chat_id} eliminado temporalmente.")
        else:
            await message.reply("Chat no encontrado en la lista temporal.")

async def handle_banuser(message):
    user_id = message.from_user.id
    if user_id in admin_users:
        ban_user_id = int(message.text.split()[1])
        if ban_user_id not in admin_users:
            ban_users.append(ban_user_id)
            await message.reply(f"Usuario {ban_user_id} baneado.")

async def handle_debanuser(message):
    user_id = message.from_user.id
    if user_id in admin_users:
        deban_user_id = int(message.text.split()[1])
        if deban_user_id in ban_users:
            ban_users.remove(deban_user_id)
            await message.reply(f"Usuario {deban_user_id} desbaneado.")
        else:
            await message.reply("Usuario no encontrado en la lista de baneados.")