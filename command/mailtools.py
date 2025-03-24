import os
import shutil
import random
import string
import py7zr
import requests
import re
import smtplib
from email.message import EmailMessage
from pyrogram import Client, filters
from PIL import Image

user_emails = {}


async def set_mail(client, message):
    email = message.text.split(' ', 1)[1]
    user_id = message.from_user.id
    user_emails[user_id] = email
    await message.reply("Correo electrónico registrado correctamente.")
    
async def send_mail(client, message):
    user_id = message.from_user.id
    if user_id not in user_emails:
        await message.reply("No has registrado ningún correo, usa /setmail para hacerlo.")
        return
    email = user_emails[user_id]
    if message.reply_to_message:
        msg = EmailMessage()
        msg['Subject'] = 'Mensaje de Telegram'
        msg['From'] = os.getenv('DISMAIL')
        msg['To'] = email
        if message.reply_to_message.text:
            msg.set_content(message.reply_to_message.text)
        elif message.reply_to_message.media:
            media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
            if os.path.getsize(media) < 59 * 1024 * 1024:  
                with open(media, 'rb') as f:
                    msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(media))
            else:
                await message.reply("El archivo supera el límite de lo permitido (59 MB).")
                return
        try:
            with smtplib.SMTP('disroot.org', 587) as server:
                server.starttls()
                server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                server.send_message(msg)
            await message.reply("Correo electrónico enviado correctamente.")
        except Exception as e:
            await message.reply(f"Error al enviar el correo: {e}")
        finally:
            shutil.rmtree('mailtemp')
            os.mkdir('mailtemp')
