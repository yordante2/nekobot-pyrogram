import os
import glob
from pyrogram import Client, filters
import zipfile
import shutil
import random
import string
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
import re
from moodleclient import upload_token
import datetime
import subprocess
from pyrogram.types import Message

async def handle_start(client, message):
    await message.reply("Funcionando")


async def rename(client, message):
    reply_message = message.reply_to_message
    if reply_message and reply_message.media:
        try:
            await message.reply("Descargando el archivo para renombrarlo...")
            new_name = message.text.split(' ', 1)[1]
            file_path = await client.download_media(reply_message)
            new_file_path = os.path.join(os.path.dirname(file_path), new_name)
            os.rename(file_path, new_file_path)
            await message.reply("Subiendo el archivo con nuevo nombre...")
            await client.send_document(message.chat.id, new_file_path)
            os.remove(new_file_path)
        except Exception as e:
            await message.reply(f'Error: {str(e)}')
    else:
        await message.reply('Ejecute el comando respondiendo a un archivo')
