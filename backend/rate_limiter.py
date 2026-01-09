"""
Configuración de Rate Limiting para OrthoWeb3.
Protege contra ataques de denegación de servicio (DoS).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Función para obtener la clave de rate limiting
# Prioriza usuario autenticado sobre IP
def get_rate_limit_key(request: Request) -> str:
    """
    Obtiene la clave para rate limiting.
    Usa el email del usuario si está autenticado, sino la IP.
    """
    # Intentar obtener usuario autenticado
    if hasattr(request.state, 'user') and request.state.user:
        key = f"user:{request.state.user.email}"
        logger.debug(f"🔑 Rate limit key: {key}")
        return key
    
    # Fallback a IP
    ip = get_remote_address(request)
    logger.debug(f"🔑 Rate limit key (IP): {ip}")
    return ip


# Inicializar limiter
limiter = Limiter(
    key_func=get_remote_address,  # Por defecto usa IP
    default_limits=["100/minute"],  # Límite global
    storage_uri="memory://",  # En producción, usar Redis: "redis://localhost:6379"
    strategy="fixed-window"  # Estrategia de ventana fija
)

# Configuración de límites
GLOBAL_RATE = "100/minute"
UPLOAD_RATE = "10/minute"  # Para usuarios no autenticados
UPLOAD_RATE_AUTHENTICATED = "20/minute"  # Para usuarios autenticados
ANALYSIS_RATE = "15/minute"  # Para análisis intensivos
IPFS_RATE = "5/minute"  # IPFS es más costoso


# Handler para errores de rate limit
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Manejador personalizado para errores de rate limit excedido.
    Registra el evento y devuelve respuesta informativa.
    """
    logger.warning(
        f"⚠️ Rate limit excedido - "
        f"IP: {get_remote_address(request)} - "
        f"Path: {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Demasiadas solicitudes",
            "message": "Has excedido el límite de solicitudes permitidas. Por favor, espera un momento.",
            "retry_after": exc.detail if hasattr(exc, 'detail') else "60 segundos",
            "type": "rate_limit_exceeded"
        },
        headers={
            "Retry-After": "60",  # Indica cuándo reintentar
            "X-RateLimit-Limit": str(exc.detail) if hasattr(exc, 'detail') else "unknown"
        }
    )


# Función auxiliar para aplicar rate limiting condicional
def get_upload_rate_limit(request: Request) -> str:
    """
    Retorna el límite de rate apropiado según si el usuario está autenticado.
    """
    if hasattr(request.state, 'user') and request.state.user:
        return UPLOAD_RATE_AUTHENTICATED
    return UPLOAD_RATE


# Decorador personalizado para rate limiting dinámico (opcional, para uso futuro)
def dynamic_rate_limit(request: Request):
    """
    Permite aplicar diferentes límites según el usuario.
    
    Ejemplo de uso en endpoint:
    @app.post("/upload")
    @limiter.limit(dynamic_rate_limit)
    async def upload(request: Request):
        ...
    """
    if hasattr(request.state, 'user') and request.state.user:
        # Usuario autenticado: límite más alto
        if hasattr(request.state.user, 'is_premium') and request.state.user.is_premium:
            return "50/minute"  # Premium users
        return UPLOAD_RATE_AUTHENTICATED
    
    # Usuario no autenticado: límite estricto
    return UPLOAD_RATE


# Logging de configuración al importar
logger.info("🛡️ Rate Limiter configurado:")
logger.info(f"  - Global: {GLOBAL_RATE}")
logger.info(f"  - Uploads (no autenticado): {UPLOAD_RATE}")
logger.info(f"  - Uploads (autenticado): {UPLOAD_RATE_AUTHENTICATED}")
logger.info(f"  - IPFS: {IPFS_RATE}")
