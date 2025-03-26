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

# Registrar el correo de un usuario con verificación (/setmail)
async def set_mail(client, message):
    # Extraer el correo del mensaje
    email = message.text.split(' ', 1)[1]
    user_id = str(message.from_user.id)

    # Si el usuario ya tiene un correo registrado, se elimina primero
    if user_id in user_emails:
        del user_emails[user_id]

    # Obtener MAIL_CONFIRMED desde las variables de entorno
    mail_confirmed = os.getenv('MAIL_CONFIRMED', '')
    # Convertir MAIL_CONFIRMED en un diccionario: {user_id: correo}
    mail_confirmed_dict = {entry.split('=')[0]: entry.split('=')[1]
                           for entry in mail_confirmed.split(',') if '=' in entry}

    # Si el User ID y el correo ya están confirmados, regístralo directamente en user_emails.
    if user_id in mail_confirmed_dict and email == mail_confirmed_dict[user_id]:
        user_emails[user_id] = [email]
        await message.reply(f"El correo {email} registrado correctamente en user_emails.")
        return

    # Si no están confirmados, se inicia el proceso de verificación.
    await message.reply(f"El correo {email} no está confirmado. Iniciando proceso de verificación...")
    code = generate_verification_code()
    verification_codes[user_id] = {'email': email, 'code': code}

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

# Verificar el correo mediante el código (/verify)
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

        # Registrar el correo en user_emails
        user_emails[user_id] = [email]
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

# Enviar correo al usuario registrado (/sendmail)
async def send_mail(client, message):
    user_id = str(message.from_user.id)
    mail_confirmed = os.getenv('MAIL_CONFIRMED', '')

    # Verificar que el usuario ya tenga un correo confirmado
    if user_id not in mail_confirmed:
        await message.reply("No has registrado ni verificado ningún correo. Usa /setmail para hacerlo.")
        return

    # Extraer el correo confirmado para el usuario
    try:
        email = mail_confirmed.split(f"{user_id}=")[1].split(',')[0]
    except IndexError:
        await message.reply("Error al obtener el correo confirmado.")
        return

    # Determinar si hay archivos adjuntos
    tiene_archivos = message.reply_to_message and hasattr(message.reply_to_message, 'media')

    # Si no hay archivos, enviar un correo de solo texto
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
        return  # Finaliza la función si no hay archivos.

    # Si hay archivos, descargar y procesar según el tamaño.
    media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
    media_size = os.path.getsize(media) if os.path.exists(media) else 0

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
                time.sleep(float(os.getenv('MAIL_DELAY', '0')))  # Espera antes de enviar la siguiente parte.
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
