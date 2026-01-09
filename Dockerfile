# Usamos una imagen base oficial de Python y versión Slim para reducir tamaño
FROM python:3.10-slim

# 1. Configuración de variables de entorno para Python
# PYTHONDONTWRITEBYTECODE: Evita que Python escriba archivos .pyc
# PYTHONUNBUFFERED: Asegura que los logs de Python se envíen directos a la consola (vital para ver errores en Render)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2. Instalación de Dependencias del Sistema (CRÍTICO para Whisper & OpenCV)
# - ffmpeg: Necesario para que Whisper procese audio.
# - libsm6, libxext6: Librerías gráficas necesarias si usas OpenCV o Pillow avanzado.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*
    # rm -rf limpia la caché de apt para reducir el peso de la imagen final

# 3. Directorio de Trabajo
# Establecemos /app como el directorio raíz dentro del contenedor
WORKDIR /app

# 4. Copia y Instalación de Dependencias Python
# Copiamos primero requirements.txt para aprovechar la caché de capas de Docker
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/backend/requirements.txt

# 5. Copia del Código Fuente y Modelos
# Convertimos el root del contenedor en una réplica del root del proyecto
COPY backend /app/backend
COPY psycho_model_final /app/psycho_model_final
COPY knowledge_base /app/knowledge_base
# Opcional: Copiar la base de datos vectorial pre-calculada
COPY chroma_db /app/chroma_db

# 6. Exponer Puerto
# Render esperará tráfico en el puerto definido por la variable PORT (por defecto suele ser 10000 o 8000)
# Nosotros expondremos 8000 por defecto.
EXPOSE 8000

# 7. Comando de Arranque (Production Ready)
# Usamos Gunicorn como servidor de procesos + Uvicorn como workers
# --bind 0.0.0.0:8000 : Escucha en todas las interfaces
# --workers 4 : Paralelismo (Render Recomienda n_cores * 2 + 1, ajusta según plan)
# backend.psych_api:app : Ruta a tu instancia de FastAPI
CMD ["gunicorn", "backend.onco_api:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
