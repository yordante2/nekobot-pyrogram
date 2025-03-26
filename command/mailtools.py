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
    
    if user_id in os.getenv('MAIL_CONFIRMED', ''):
        await message.reply("El correo ya ha sido registrado y verificado previamente.")
        return

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

    # Obtener las variables de entorno
    mail_mb = os.getenv('MAIL_MB')
    mail_delay = os.getenv('MAIL_DELAY')

    if mail_mb and mail_delay:
        mail_mb = int(mail_mb)  # Convertir a entero
        mail_delay = float(mail_delay)  # Convertir a flotante

        if message.reply_to_message:
            media = await client.download_media(message.reply_to_message, file_name='mailtemp/')
            if os.path.getsize(media) > mail_mb * 1024 * 1024:
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
                        time.sleep(mail_delay)  # Esperar el tiempo indicado antes de enviar la siguiente parte
                    except Exception as e:
                        await message.reply(f"Error al enviar la parte {os.path.basename(part)}: {e}")
            else:
                await message.reply("El archivo no supera el tamaño indicado en MAIL_MB. No se realizará compresión.")
        else:
            await message.reply("Por favor, responde a un mensaje con un archivo para procesarlo.")
    else:
        # Si las variables no están definidas, enviar el archivo completo sin compresión ni delay
        if message.reply_to_message:
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
        else:
            await message.reply("Por favor, responde a un mensaje con un archivo para procesarlo.")
