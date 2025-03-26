import os
import time
import shutil
import py7zr
import smtplib
from email.message import EmailMessage

# Diccionario para almacenar correos de los usuarios
user_emails = {}
verification_storage = {}

# Registrar el correo de un usuario
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
            

# Función para comprimir y dividir archivos en partes
def compressfile(file_path, part_size):
    parts = []
    part_size *= 1024 * 1024  # Convertir el tamaño a bytes
    archive_path = f"{file_path}.7z"
    with py7zr.SevenZipFile(archive_path, 'w') as archive:
        archive.write(file_path, os.path.basename(file_path))
    with open(archive_path, 'rb') as archive:
        part_num = 1
        while True:
            part_data = archive.read(part_size)
            if not part_data:
                break
            part_file = f"{archive_path}.{part_num:03d}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts

# Enviar correo al usuario registrado
async def send_mail(client, message):
    user_id = message.from_user.id
    if user_id not in user_emails:
        await message.reply("No has registrado ningún correo, usa /setmail para hacerlo.")
        return
    email = user_emails[user_id]

    # Identificar a qué tipo de mensaje se está respondiendo
    if not message.reply_to_message:
        await message.reply("Por favor, responde a un mensaje.")
        return
    
    if message.reply_to_message.text:
        try:
            # Si el mensaje al que responde es textual, enviar directamente
            msg = EmailMessage()
            msg['Subject'] = 'Mensaje de Telegram'
            msg['From'] = os.getenv('DISMAIL')
            msg['To'] = email
            msg.set_content(message.reply_to_message.text)
            with smtplib.SMTP('disroot.org', 587) as server:
                server.starttls()
                server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
                server.send_message(msg)
            await message.reply("Mensaje enviado correctamente.")
        except Exception as e:
            await message.reply(f"Error al enviar el mensaje: {e}")
        return

    # Obtener las variables de entorno
    mail_mb = os.getenv('MAIL_MB')
    mail_delay = os.getenv('MAIL_DELAY')

    if message.reply_to_message.document or message.reply_to_message.photo:
        media = await client.download_media(message.reply_to_message, file_name='mailtemp/')

        # Cuando las variables MAIL_MB son opcionales
        if not mail_mb:
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
            return

        # Convertir MAIL_MB a entero si existe
        mail_mb = int(mail_mb)
        if os.path.getsize(media) <= mail_mb * 1024 * 1024:
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
                await message.reply("Archivo enviado correctamente sin compresión.")
            except Exception as e:
                await message.reply(f"Error al enviar el archivo: {e}")
        else:
            # Lógica para comprimir si el tamaño excede MAIL_MB
            parts = compressfile(media, mail_mb)
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
                    time.sleep(float(mail_delay) if mail_delay else 0)  # Esperar antes de enviar la siguiente parte
                except Exception as e:
                    await message.reply(f"Error al enviar la parte {os.path.basename(part)}: {e}")
