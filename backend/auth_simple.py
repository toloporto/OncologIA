# backend/auth_simple.py - Versión COMPLETA con get_current_user
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib

# Configuración de seguridad
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Modelos Pydantic
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: str  # UUID string
    email: str
    full_name: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Funciones de utilidad (usando SHA256 en lugar de bcrypt)
def verify_password(plain_password, hashed_password):
    """Verificar contraseña usando SHA256"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    """Hashear contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=email)
    except JWTError:
        return None

# ⭐⭐ FUNCIÓN QUE FALTABA ⭐⭐
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Obtiene el usuario actual a partir del token JWT
    Dependencia para FastAPI endpoints
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # ⚠️ IMPORTANTE: Esto es un placeholder
    # En producción, DEBES buscar el usuario real en tu base de datos
    # usando token_data.email
    
    # Por ahora, devolvemos un usuario dummy
    return {
        "email": token_data.email,
        "username": token_data.email.split('@')[0],
        "user_id": f"user_{abs(hash(token_data.email)) % 10000:04d}",
        "full_name": f"User {token_data.email.split('@')[0]}",
        "role": "user",
        "is_active": True,
        "authenticated": True
    }

# Versión alternativa para desarrollo (sin token requerido)
async def get_current_user_dev():
    """
    Versión para desarrollo - sin verificación real
    """
    return {
        "email": "developer@orthoweb3.com",
        "username": "orthodev",
        "user_id": "dev_001",
        "full_name": "OrthoWeb3 Developer",
        "role": "developer",
        "is_active": True,
        "authenticated": True
    }
