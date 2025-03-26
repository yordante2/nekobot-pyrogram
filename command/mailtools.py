import os
import time
import shutil
import py7zr
import smtplib
import random
from email.message import EmailMessage

# Diccionario para almacenar correos y códigos temporales
user_emails = {}
verification_codes = {}

import random

# Función para generar un código de verificación de 6 números
def generate_verification_code():
    return f"{random.randint(100000, 999999)}"

# Modificación de la función set_mail para enviar el código de verificación por correo
async def set_mail(client, message):
    email = message.text.split(' ', 1)[1]
    user_id = message.from_user.id

    # Revisar MAIL_CONFIRMED
    mail_confirmed = os.getenv('MAIL_CONFIRMED')
    if mail_confirmed:
        confirmed_users = {item.split('=')[0]: item.split('=')[1:] for item in mail_confirmed.split(',')}
        if str(user_id) in confirmed_users and email in confirmed_users[str(user_id)]:
            user_emails[user_id] = email
            await message.reply("Correo electrónico registrado automáticamente porque está confirmado en el entorno.")
            return

    # Generar código de verificación y enviarlo por correo
    verification_code = generate_verification_code()

    # Enviar el correo con el código de verificación
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Código de Verificación'
        msg['From'] = os.getenv('DISMAIL')
        msg['To'] = email
        msg.set_content(f"Tu código de verificación es: {verification_code}")

        with smtplib.SMTP('disroot.org', 587) as server:
            server.starttls()
            server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
            server.send_message(msg)

        # Almacenar temporalmente el código y el correo
        verification_storage[user_id] = {'email': email, 'code': verification_code}

        await message.reply("Código de verificación enviado a tu correo. Por favor, verifica el código para registrar tu correo electrónico.")
    except Exception as e:
        await message.reply(f"Error al enviar el correo de verificación: {e}")

# Función para verificar el código y registrar el correo
async def verify_mail(client, message):
    user_id = message.from_user.id
    code = message.text.split(' ', 1)[1]

    if user_id in verification_storage:
        stored_email = verification_storage[user_id]['email']
        stored_code = verification_storage[user_id]['code']
        if code == stored_code:
            user_emails[user_id] = stored_email
            del verification_storage[user_id]  # Eliminar almacenamiento temporal
            await message.reply("Correo electrónico verificado y registrado correctamente.")
        else:
            await message.reply("El código de verificación es incorrecto. Intenta de nuevo.")
    else:
        await message.reply("No hay un código de verificación pendiente. Usa /setmail para iniciar el proceso.")

# Enviar correo al usuario registrado (/sendmail)
async def send_mail(client, message):
    user_id = str(message.from_user.id)
    mail_confirmed = os.getenv('MAIL_CONFIRMED', '')

    # Verificar que el usuario tenga un correo confirmado
    if user_id not in mail_confirmed:
        await message.reply("No has registrado ni verificado ningún correo. Usa /setmail para hacerlo.")
        return

    # Obtener el correo confirmado para el usuario
    try:
        email = mail_confirmed.split(f"{user_id}=")[1].split(',')[0]
    except IndexError:
        await message.reply("Error al obtener el correo confirmado.")
        return

    # Verificar si hay archivos adjuntos
    tiene_archivos = message.reply_to_message and hasattr(message.reply_to_message, 'media')

    # Si no hay archivos, enviar correo con texto
    if not tiene_archivos:
        if not message.text.strip():
            await message.reply("No hay texto para enviar en el correo.")
            return
        try:
            msg = EmailMessage()
            msg['Subject'] = 'Mensaje de texto'
            msg['From'] = os.getenv('DISMAIL')
            msg['To'] = email
            msg.set_content(message.text)
            with smtplib.SMTP('disroot.org', 587) as server:
                server.starttls()
                server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                server.send_message(msg)
            await message.reply("Correo de texto enviado correctamente.")
        except Exception as e:
            await message.reply(f"Error al enviar el correo: {e}")
        return  # Termina aquí si no hay archivos

    # Si hay archivos, descargar y procesar
    media = None
    if tiene_archivos:  # Descargar solo si hay archivos adjuntos
        media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
        media_size = os.path.getsize(media) if os.path.exists(media) else 0

        # Determinar límites de tamaño
        if os.getenv('MAIL_MB'):
            limite_bytes = int(os.getenv('MAIL_MB')) * 1024 * 1024
            sobre_limite = media_size > limite_bytes
            debajo_limite = media_size <= limite_bytes
        else:
            sobre_limite = False
            debajo_limite = True

        if sobre_limite:
            parts = compressfile(media, int(os.getenv('MAIL_MB')))
            for part in parts:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = 'Parte de archivo comprimido'
                    msg['From'] = os.getenv('DISMAIL')
                    msg['To'] = email
                    with open(part, 'rb') as f:
                        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(part))
                    with smtplib.SMTP('disroot.org', 587) as server:
                        server.starttls()
                        server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                        server.send_message(msg)
                    await message.reply(f"Parte {os.path.basename(part)} enviada correctamente.")
                    time.sleep(float(os.getenv('MAIL_DELAY', '0')))  # Esperar antes de enviar otra parte
                except Exception as e:
                    await message.reply(f"Error al enviar la parte {os.path.basename(part)}: {e}")

        if debajo_limite:
            try:
                msg = EmailMessage()
                msg['Subject'] = 'Archivo de Telegram'
                msg['From'] = os.getenv('DISMAIL')
                msg['To'] = email
                with open(media, 'rb') as f:
                    msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(media))
                with smtplib.SMTP('disroot.org', 587) as server:
                    server.starttls()
                    server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                    server.send_message(msg)
                await message.reply("Archivo enviado correctamente.")
            except Exception as e:
                await message.reply(f"Error al enviar el archivo: {e}")
