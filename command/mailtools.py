import os
import time
import shutil
import py7zr
import smtplib
from email.message import EmailMessage

# Diccionario para almacenar correos de los usuarios
user_emails = {}

# Registrar el correo de un usuario
async def set_mail(client, message):
    email = message.text.split(' ', 1)[1]
    user_id = message.from_user.id
    user_emails[user_id] = email
    await message.reply("Correo electrónico registrado correctamente.")

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
