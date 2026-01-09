"""
Endpoints de autenticación para OrthoWeb3
Incluye: registro, login, perfil de usuario
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from typing import Optional
import logging

from backend.database import get_db
from backend.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    decode_token
)
from backend.models import User

logger = logging.getLogger(__name__)

# Router para autenticación
auth_router = APIRouter(tags=["Autenticación"])

# Modelos Pydantic para request/response
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registrar un nuevo usuario
    
    - **email**: Email único del usuario
    - **password**: Contraseña (mínimo 6 caracteres)
    - **full_name**: Nombre completo (opcional)
    """
    # Validar longitud de contraseña
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres"
        )
    
    try:
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@auth_router.post("/login", response_model=Token)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Login de usuario
    
    Retorna un token JWT para autenticación
    """
    # Leer datos del formulario (username, password)
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    user = authenticate_user(db, username, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    # Crear token - usar email en lugar de id
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """
    Obtener información del usuario actual
    
    Requiere autenticación (token JWT en header Authorization)
    """
    try:
        # Obtener token del header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no proporcionado"
            )
        
        token = auth_header.replace("Bearer ", "")
        token_data = decode_token(token)
        
        if not token_data or not token_data.email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        user = db.query(User).filter(User.email == token_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en get_current_user_info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@auth_router.get("/verify")
async def verify_token(request: Request, db: Session = Depends(get_db)):
    """
    Verificar si el token es válido
    
    Retorna información básica del usuario si el token es válido.
    Si no hay token, retorna valid=False
    """
    from backend.auth import decode_token
    
    try:
        # Intentar obtener el token del header Authorization
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return {
                "valid": False,
                "user_id": None,
                "email": None,
                "message": "No token provided"
            }
        
        # Extraer el token
        token = auth_header.replace("Bearer ", "")
        
        # Decodificar el token
        token_data = decode_token(token)
        
        if not token_data:
            return {
                "valid": False,
                "user_id": None,
                "email": None,
                "message": "Invalid token"
            }
        
        # Buscar el usuario en la base de datos
        user = db.query(User).filter(User.email == token_data.email).first()
        
        if not user or not user.is_active:
            return {
                "valid": False,
                "user_id": None,
                "email": None,
                "message": "User not found or inactive"
            }
        
        return {
            "valid": True,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
        
    except Exception as e:
        logger.error(f"Error en verify_token: {e}")
        return {
            "valid": False,
            "user_id": None,
            "email": None,
            "message": str(e)
        }
