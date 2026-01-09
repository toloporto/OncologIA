"""
Módulo de validación estricta de archivos para OrthoWeb3.
Implementa validación de tipo mágico, tamaño y sanitización de nombres.
"""

import os
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    import mimetypes
    MAGIC_AVAILABLE = False
    logger.warning("⚠️ Libmagic no encontrado. Usando detección por extensión (mimetypes) como fallback.")

# Configuración de validación
MAX_FILE_SIZE_MB = 20  # Aumentado para imágenes DICOM y panorámicas
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Extensiones permitidas: formatos médicos/dentales y estándar
ALLOWED_EXTENSIONS = {
    # Formatos estándar
    'jpg', 'jpeg', 'png',
    # Formatos médicos/dentales
    'dcm',  # DICOM (Digital Imaging and Communications in Medicine)
    'dicom',
    'tif', 'tiff',  # TIFF (común en escáneres dentales)
    'bmp',  # BMP (equipos dentales antiguos)
}

# MIME types permitidos
ALLOWED_MIMES = [
    # Formatos estándar
    'image/jpeg',
    'image/png',
    # Formatos médicos/dentales
    'application/dicom',  # DICOM estándar
    'image/dicom',  # DICOM alternativo
    'image/x-dicom',  # DICOM variante
    'image/tiff',  # TIFF
    'image/bmp',  # BMP
    'image/x-ms-bmp',  # BMP variante Windows
]

# Excepciones personalizadas
class FileValidationError(Exception):
    """Excepción base para errores de validación de archivos"""
    pass

class InvalidFileTypeError(FileValidationError):
    """El tipo de archivo no está permitido"""
    pass

class FileTooLargeError(FileValidationError):
    """El archivo excede el tamaño máximo permitido"""
    pass

class InvalidFileNameError(FileValidationError):
    """El nombre de archivo contiene caracteres no válidos"""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre de archivo para prevenir ataques de path traversal.
    
    Args:
        filename: Nombre del archivo a sanitizar
        
    Returns:
        Nombre de archivo seguro
        
    Raises:
        InvalidFileNameError: Si el nombre no puede ser sanitizado
    """
    if not filename:
        raise InvalidFileNameError("Nombre de archivo vacío")
    
    # Obtener solo el nombre base (sin path)
    filename = os.path.basename(filename)
    
    # Remover caracteres peligrosos
    # Permitir solo alfanuméricos, guiones, guiones bajos y puntos
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Prevenir nombres ocultos en Unix
    if safe_filename.startswith('.'):
        safe_filename = '_' + safe_filename
    
    # Prevenir nombres vacíos después de sanitización
    if not safe_filename or safe_filename == '.':
        raise InvalidFileNameError(f"Nombre de archivo inválido después de sanitización: {filename}")
    
    logger.info(f"📝 Nombre sanitizado: {filename} → {safe_filename}")
    return safe_filename


def get_file_mime_type(file_bytes: bytes, filename: str = None) -> str:
    """
    Obtiene el tipo MIME real del archivo usando magic numbers.
    Si magic no está disponible, usa mimetypes basado en extensión.
    
    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre del archivo (opcional, para fallback)
        
    Returns:
        Tipo MIME del archivo
    """
    # 1. Intentar con python-magic (Lo más fiable)
    if MAGIC_AVAILABLE:
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file_bytes)
            return mime_type
        except Exception as e:
            logger.error(f"❌ Error detectando tipo MIME con magic: {e}")

    # 2. Fallback: mimetypes (Basado en extensión)
    if filename:
        import mimetypes
        # Asegurarse de que mimetypes conozca los tipos comunes
        if not mimetypes.inited:
            mimetypes.init()
        
        # Añadir tipos personalizados si no existen
        mimetypes.add_type('application/dicom', '.dcm')
        mimetypes.add_type('application/dicom', '.dicom')
        
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            return mime_type

    # 3. Último recurso
    return "application/octet-stream"


def validate_file_size(file_bytes: bytes, max_size_mb: int = MAX_FILE_SIZE_MB) -> None:
    """
    Valida que el tamaño del archivo no exceda el máximo permitido.
    
    Args:
        file_bytes: Contenido del archivo en bytes
        max_size_mb: Tamaño máximo permitido en MB
        
    Raises:
        FileTooLargeError: Si el archivo es demasiado grande
    """
    file_size = len(file_bytes)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        raise FileTooLargeError(
            f"Archivo demasiado grande: {size_mb:.2f}MB. Máximo permitido: {max_size_mb}MB"
        )
    
    logger.info(f"✅ Tamaño válido: {file_size / 1024:.2f}KB")


def validate_file_type(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """
    Valida que el tipo de archivo sea permitido usando magic numbers.
    
    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre del archivo (para logging)
        
    Returns:
        Tupla (es_válido, tipo_mime)
        
    Raises:
        InvalidFileTypeError: Si el tipo de archivo no está permitido
    """
    mime_type = get_file_mime_type(file_bytes, filename)
    
    if mime_type not in ALLOWED_MIMES:
        raise InvalidFileTypeError(
            f"Tipo de archivo no permitido: {mime_type}. "
            f"Solo se permiten: {', '.join(ALLOWED_MIMES)}"
        )
    
    logger.info(f"✅ Tipo MIME válido: {mime_type} para {filename}")
    return True, mime_type


def validate_file_extension(filename: str) -> None:
    """
    Valida que la extensión del archivo esté en la lista permitida.
    
    Args:
        filename: Nombre del archivo
        
    Raises:
        InvalidFileTypeError: Si la extensión no está permitida
    """
    if '.' not in filename:
        raise InvalidFileTypeError("Archivo sin extensión")
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"Extensión no permitida: .{ext}. "
            f"Solo se permiten: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    logger.info(f"✅ Extensión válida: .{ext}")


def validate_image_file(
    file_bytes: bytes,
    filename: str,
    max_size_mb: int = MAX_FILE_SIZE_MB
) -> Tuple[str, str]:
    """
    Realiza validación completa de un archivo de imagen.
    
    Validaciones:
    1. Tamaño del archivo
    2. Extensión del archivo
    3. Tipo MIME real (magic numbers)
    4. Sanitización del nombre
    
    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre del archivo
        max_size_mb: Tamaño máximo en MB
        
    Returns:
        Tupla (nombre_sanitizado, tipo_mime)
        
    Raises:
        FileValidationError: Si alguna validación falla
    """
    logger.info(f"🔍 Validando archivo: {filename}")
    
    # 1. Validar tamaño
    validate_file_size(file_bytes, max_size_mb)
    
    # 2. Sanitizar nombre
    safe_filename = sanitize_filename(filename)
    
    # 3. Validar extensión
    validate_file_extension(safe_filename)
    
    # 4. Validar tipo real con magic numbers
    is_valid, mime_type = validate_file_type(file_bytes, safe_filename)
    
    logger.info(f"✅ Archivo validado exitosamente: {safe_filename}")
    return safe_filename, mime_type


# Función de conveniencia para usar en endpoints
def validate_upload_file(file_bytes: bytes, filename: str) -> Tuple[str, str]:
    """
    Alias para validate_image_file con configuración predeterminada.
    
    Args:
        file_bytes: Contenido del archivo
        filename: Nombre del archivo
        
    Returns:
        Tupla (nombre_sanitizado, tipo_mime)
        
    Raises:
        FileValidationError: Si la validación falla
    """
    return validate_image_file(file_bytes, filename)
