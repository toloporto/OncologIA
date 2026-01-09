# Stage 1: Imagen base ligera
FROM python:3.10-slim

# Evitar que Python genere archivos .pyc y habilitar modo unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalamos dependencias del sistema necesarias para OpenCV y runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario de sistema para no correr como root
RUN addgroup --system appgroup && adduser --system --group appuser

# Establecemos el directorio de trabajo
WORKDIR /app

# Primero las dependencias para aprovechar la caché de capas
COPY backend/requirements.txt backend/requirements_auth.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_auth.txt

# Copiamos el resto del código del backend
COPY backend/ .

# Aseguramos que el directorio de imágenes públicas exista y tenga permisos
RUN mkdir -p /app/public_images && chown -R appuser:appgroup /app

# Copiamos los modelos (fuera de /app para seguir la convención del proyecto)
# NOTA: En producción real, estos deberían montarse como volumen o descargarse de un S3/Registry
COPY ml-models/ /ml-models/
RUN chown -R appuser:appgroup /ml-models

# Cambiar al usuario no-root
USER appuser

# Exponemos el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "ortho_api:app", "--host", "0.0.0.0", "--port", "8000"]
