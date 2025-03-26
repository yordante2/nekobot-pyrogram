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

# Generar código de 6 dígitos
def generate_verification_code():
    return f"{random.randint(100000, 999999)}"

# Registrar el correo de un usuario con verificación
async def set_mail(client, message):
    email = message.text.split(' ', 1)[1]
    user_id = str(message.from_user.id)

    # Verificar si el User ID tiene correos verificados en MAIL_CONFIRMED
    mail_confirmed = os.getenv('MAIL_CONFIRMED', '')
    user_entries = [entry for entry in mail_confirmed.split(',') if entry.startswith(f"{user_id}=")]
    
    if user_entries:
        # Extraer correos existentes y agregar el nuevo al diccionario user_emails
        existing_emails = user_entries[0].split('=')[1:]  # Obtener correos asociados al User ID
        user_emails[user_id] = existing_emails
        if email not in user_emails[user_id]:
            user_emails[user_id].append(email)
        
        await message.reply(f"Correo registrado directamente en user_emails: {email}.")
        return

    # Si no tiene correos verificados, iniciar proceso de verificación
    code = generate_verification_code()
    verification_codes[user_id] = {'email': email, 'code': code}

    # Enviar el código al correo
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Código de Verificación'
        msg['From'] = os.getenv('DISMAIL')
        msg['To'] = email
        msg.set_content(f"Tu código de verificación es: {code}")
        with smtplib.SMTP('disroot.org', 587) as server:
            server.starttls()
            server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
            server.send_message(msg)
        await message.reply(f"Código de verificación enviado a {email}. Usa /verify Código para verificar.")
    except Exception as e:
        await message.reply(f"Error al enviar el código de verificación: {e}")
        

# Verificar el correo del usuario
async def verify_mail(client, message):
    user_id = str(message.from_user.id)
    if user_id not in verification_codes:
        await message.reply("No hay un proceso de verificación en curso para tu usuario. Usa /setmail primero.")
        return
    
    code = message.text.split(' ', 1)[1]
    if verification_codes[user_id]['code'] == code:
        email = verification_codes[user_id]['email']
        del verification_codes[user_id]

        # Agregar el correo a MAIL_CONFIRMED
        mail_confirmed = os.getenv('MAIL_CONFIRMED', '')
        if mail_confirmed:
            mail_confirmed += f",{user_id}={email}"
        else:
            mail_confirmed = f"{user_id}={email}"
        
        os.environ['MAIL_CONFIRMED'] = mail_confirmed
        await message.reply("Correo electrónico verificado y registrado correctamente.")
    else:
        await message.reply("Código de verificación incorrecto. Intenta nuevamente.")

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
    user_id = str(message.from_user.id)
    mail_confirmed = os.getenv('MAIL_CONFIRMED', '')

    if user_id not in mail_confirmed:
        await message.reply("No has registrado ni verificado ningún correo. Usa /setmail para hacerlo.")
        return

    email = mail_confirmed.split(f"{user_id}=")[1].split(',')[0]

    # Definir las variables
    tiene_archivos = message.reply_to_message and hasattr(message.reply_to_message, 'media')
    sobre_limite = tiene_archivos and os.getenv('MAIL_MB') and os.path.getsize(await client.download_media(message.reply_to_message, file_name='mailtemp/')) > int(os.getenv('MAIL_MB')) * 1024 * 1024
    debajo_limite = tiene_archivos and os.getenv('MAIL_MB') and os.path.getsize(await client.download_media(message.reply_to_message, file_name='mailtemp/')) <= int(os.getenv('MAIL_MB')) * 1024 * 1024
    no_limite = tiene_archivos and not os.getenv('MAIL_MB')

    # Acción según las variables
    if not tiene_archivos:
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

    if sobre_limite:
        media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
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
                time.sleep(float(os.getenv('MAIL_DELAY', '0')))  # Esperar el tiempo indicado antes de enviar la siguiente parte
            except Exception as e:
                await message.reply(f"Error al enviar la parte {os.path.basename(part)}: {e}")

    if debajo_limite or no_limite:
        media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
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
            
