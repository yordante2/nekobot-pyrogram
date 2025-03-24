# Neko Bot

## Variables de Entorno

### Necesarias
```
API_ID = Ingrese su API ID para acceder a Telegram.
API_HASH = Ingrese la API HASH de su API ID
TOKEN =  Ingrese el Token de su bot
ADMINS = Ingrese el User ID de los administradores del bot, separelos por coma
USERS = Ingrese el User ID de los usuarios del bot, si no quiere colocar a nadie coloque 0 (No dejar vacio)
```

### Extras
```
BOT_IS_PUBLIC = Coloque el valor "True" para que cualquiera pueda usar el bot (Aún asi, coloque 0 en USERS)
CODEWORD = Coloque una contraseña para que otros usen el comanndo /access
DISMAIL = Coloque un correo de @disroot.org para usar /sendmail
DISPASS = Coloque la contraseña del correo anterior
IMGAPI = Coloque su API de Imgchest para publicar fotos con el comando /imgchest
```

### Activar comandos

Las variables de entorno **ACTIVE_CMD** o **ADMIN_CMD** no son necesarias para el arranque del bot, pero sin ellas el bot es inutil.
Introdusca en esta variable, separado por comas, los nombres de los archivos de la carpeta [command](https://github.com/nakigeplayer/nekobot-pyrogram/tree/main/command)  para que el bot use estos comandos.
Los **ACTIVE_CMD** son comandos para todos mientras **ADMIN_CMD** son comandos para admin

```
all - permite el uso de todos los comandos

```


## Comandos del bot

Envie esto a BotFather para configurar los comandos:
```
start - Comprobar actividad  
setsize - Defina el tamaño en Mb para /compress (Default: 10MB)  
compress - Comprimir un archivo en partes  
rename - Cambia el nombre de un archivo  
convert - Convierte un video  
calidad - Ajusta la calidad de /convert  
setmail - Configure su correo para usar /send  
sendmail - Envía un archivo a su correo
nh - Descarga un manga hentai de Nhentai
3h - Descarga un manga hentai de 3Hentai
covernh - Obtener info de un manga hentai de Nhentai
cover3h - Obtener info de un manga hentai de 3Hentai
scan - Escanea los links dentro de un link indicando
imgchest - Publica una imagen en Imgchest
access - Obten acceso al bot mediante una contraseña
```

## Comandos admin
```
adduser - Permite a un usuario usar el bot
remuser - Quita el acceso
addchat - Permite al chat actual el uso del bot
remchat - Quita el acceso
```
