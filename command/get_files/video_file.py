import os
import subprocess
import random
import datetime
import re

# Función para generar una miniatura
def generate_thumbnail(video_path, thumbnail_name="miniatura.jpg"):
    try:
        random_time = random.randint(0, 10)  # Generar tiempo aleatorio entre 1:00 y 3:00
        print(f"Generando miniatura en el segundo {random_time}...")

        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-ss", str(random_time),
            "-vframes", "1",
            thumbnail_name
        ], check=True)
        return thumbnail_name  # Devolver la ruta de la miniatura
    except Exception as e:
        print(f"Error al generar la miniatura: {e}")
        return None

# Función para obtener la duración de un video
def obtener_duracion_video(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = float(result.stdout.strip())
        return int(duration)  # Duración en segundos (redondeado)
    except Exception as e:
        print(f"Error al obtener la duración del video: {e}")
        return 0

# Función para comprimir el video
def comprimir_video(original_video_path, compressed_video_path):
    ffmpeg_command = [
        'ffmpeg', '-y', '-i', original_video_path,
        '-s', "640x400",
        '-crf', "28",
        '-b:a', "80k",
        '-r', "18",
        '-preset', "veryfast",
        '-c:v', "libx265",
        compressed_video_path
    ]
    return subprocess.Popen(ffmpeg_command, stderr=subprocess.PIPE, text=True)

# Función para convertir tamaño de archivo a formato legible
def human_readable_size(size, decimal_places=2):
    for unit in ['KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0

# Función para calcular el progreso de compresión
def calcular_progreso(output, total_duration):
    if "size=" in output and "time=" in output:
        match = re.search(r"size=\s*([\d]+).*time=([\d:.]+)", output)
        if match:
            size_kb, current_time_str = match.groups()
            size_kb = int(size_kb)
            readable_size = human_readable_size(size_kb)

            current_time_parts = list(map(float, current_time_str.split(':')))
            current_time = (
                current_time_parts[0] * 3600 +
                current_time_parts[1] * 60 +
                current_time_parts[2]
            )

            percentage = (current_time / total_duration) * 100
            return readable_size, percentage, current_time
    return None, 0, 0
