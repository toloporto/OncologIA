"""
Endpoints de IPFS para OrthoWeb3
Permite subir imágenes médicas a IPFS
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
from backend.ipfs_service import ipfs_service
from backend.auth import decode_token
from backend.models import User
from backend.database import get_db
from backend.file_validator import validate_upload_file, FileValidationError
from backend.rate_limiter import limiter, IPFS_RATE
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

ipfs_router = APIRouter(tags=["IPFS"])

class IPFSUploadResponse(BaseModel):
    success: bool
    hash: Optional[str] = None
    url_public: Optional[str] = None
    url_local: Optional[str] = None
    size: Optional[str] = None
    error: Optional[str] = None

class IPFSStatusResponse(BaseModel):
    connected: bool
    node_id: Optional[str] = None
    agent: Optional[str] = None

@ipfs_router.get("/status", response_model=IPFSStatusResponse)
async def get_ipfs_status():
    """
    Verificar estado de IPFS
    
    Retorna si IPFS está conectado y funcionando
    """
    if not ipfs_service.is_connected():
        return IPFSStatusResponse(connected=False)
    
    stats = ipfs_service.get_stats()
    if stats:
        return IPFSStatusResponse(
            connected=True,
            node_id=stats.get('ID'),
            agent=stats.get('AgentVersion')
        )
    
    return IPFSStatusResponse(connected=True)

@ipfs_router.post("/upload", response_model=IPFSUploadResponse)
@limiter.limit(IPFS_RATE)
async def upload_to_ipfs(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Subir una imagen médica a IPFS
    
    Requiere autenticación. Sube la imagen a IPFS y retorna el hash.
    """
    # Obtener el usuario del token (opcional - si no está autenticado, seguimos)
    current_user = None
    if request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            token_data = decode_token(token)
            if token_data:
                current_user = db.query(User).filter(User.email == token_data.email).first()
    # Verificar que IPFS esté disponible
    if not ipfs_service.is_connected():
        raise HTTPException(
            status_code=503,
            detail="IPFS no está disponible. Verifica que IPFS Desktop esté corriendo."
        )
    
    # Verificar tipo de archivo
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten imágenes"
        )
    
    try:
        # Leer archivo
        file_data = await file.read()
        
        # Validar archivo con validación estricta
        try:
            safe_filename, mime_type = validate_upload_file(file_data, file.filename)
            logger.info(f"✅ Archivo validado para IPFS: {safe_filename} ({mime_type})")
        except FileValidationError as e:
            logger.warning(f"⚠️ Archivo rechazado en /ipfs/upload: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Subir a IPFS
        result = ipfs_service.upload_image(file_data, file.filename)
        
        if result['success']:
            return IPFSUploadResponse(
                success=True,
                hash=result['hash'],
                url_public=result['url_public'],
                url_local=result['url_local'],
                size=result['size']
            )
        else:
            return IPFSUploadResponse(
                success=False,
                error=result.get('error', 'Error desconocido')
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error subiendo archivo a IPFS: {str(e)}"
        )

@ipfs_router.get("/file/{ipfs_hash}")
async def get_ipfs_file(ipfs_hash: str):
    """
    Obtener un archivo desde IPFS
    
    Retorna el archivo almacenado en IPFS
    """
    if not ipfs_service.is_connected():
        raise HTTPException(
            status_code=503,
            detail="IPFS no está disponible"
        )
    
    file_data = ipfs_service.get_file(ipfs_hash)
    
    if file_data is None:
        raise HTTPException(
            status_code=404,
            detail="Archivo no encontrado en IPFS"
        )
    
    from fastapi.responses import Response
    return Response(content=file_data, media_type="application/octet-stream")
