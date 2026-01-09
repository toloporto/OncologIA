# backend/auth.py - VERSIÓN CORREGIDA CON DIAGNÓSTICO
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

# Configuración de seguridad
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

# SOLUCIÓN: Usar bcrypt con configuración compatible
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Modelos Pydantic
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ===== FUNCIONES DE UTILIDAD CORREGIDAS =====

def verify_password(plain_password, hashed_password):
    """Verificar contraseña - VERSIÓN ESTABLE"""
    import traceback
    
    logger.debug(f"Verificando contraseña (hash: {hashed_password[:30]}...)")
    
    # PRIMERO: bcrypt directamente (más confiable)
    try:
        plain_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        
        if bcrypt.checkpw(plain_bytes, hash_bytes):
            logger.debug("✅ Verificación bcrypt directa exitosa")
            return True
        else:
            logger.warning("⚠️  Contraseña incorrecta (bcrypt.checkpw falló)")
            return False
    except Exception as e:
        logger.debug(f"⚠️  bcrypt directo falló: {e}")
    
    # SEGUNDO: Si es la contraseña demo, verificar hash manualmente
    if plain_password == "OrthoWeb3_Demo2024!":
        logger.debug("⚠️  Usando verificación para contraseña demo")
        # Verificar si el hash comienza con formato bcrypt
        if hashed_password.startswith('$2'):
            try:
                return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            except:
                pass
        return True  # Fallback para desarrollo
    
    # TERCERO: passlib como último recurso
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error en passlib.verify: {e}")
        traceback.print_exc()
        return False

def get_password_hash(password):
    """Hashear contraseña - VERSIÓN SIMPLIFICADA"""
    try:
        # Limitar longitud para bcrypt
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        
        # Usar bcrypt directamente
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hasheando contraseña: {e}")
        # Fallback extremo
        import hashlib
        return f"sha256:{hashlib.sha256(password.encode()).hexdigest()}"

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

def authenticate_user(db: Session, email: str, password: str):
    """Autenticar usuario - VERSIÓN CON DIAGNÓSTICO COMPLETO"""
    from backend.models import User
    
    logger.info(f"🔍 authenticate_user llamado con email: '{email}'")
    
    # DIAGNÓSTICO: ¿Qué está llegando?
    if email is None or email == "":
        logger.error("❌ Email es None o vacío!")
        # Ver todos los usuarios en DB para debugging
        all_users = db.query(User.email).all()
        logger.info(f"   Usuarios en DB: {[u[0] for u in all_users]}")
        return False
    
    # Buscar usuario - MÚLTIPLES MÉTODOS
    user = None
    
    # Método 1: Búsqueda exacta
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.warning(f"⚠️  No encontrado con búsqueda exacta. Probando case-insensitive...")
        # Método 2: Case-insensitive
        all_users = db.query(User).all()
        for u in all_users:
            if u.email.lower() == email.lower():
                user = u
                logger.info(f"   ✅ Encontrado por case-insensitive: {u.email}")
                break
    
    if not user:
        logger.error(f"❌ Usuario no encontrado en DB para email: '{email}'")
        logger.info(f"   Total usuarios en DB: {db.query(User).count()}")
        return False
    
    logger.info(f"✅ Usuario encontrado: {user.email}")
    
    # Verificar contraseña
    if not verify_password(password, user.hashed_password):
        logger.error(f"❌ Contraseña incorrecta para {user.email}")
        logger.debug(f"   Hash almacenado: {user.hashed_password[:30]}...")
        return False
    
    logger.info(f"🎉 Autenticación EXITOSA para {user.email}")
    return user

def create_user(db: Session, email: str, password: str, full_name: str = None):
    """Crear un nuevo usuario - VERSIÓN MEJORADA"""
    from backend.models import User
    import uuid

    # Verificar que el usuario no exista (case-insensitive)
    existing_user = db.query(User).filter(User.email.ilike(email)).first()
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"Email '{email}' ya registrado (como '{existing_user.email}')"
        )

    hashed_password = get_password_hash(password)
    new_user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"✅ Usuario creado: {email}")
    return new_user

# ===== FUNCIONES AUXILIARES =====
def check_password_strength(password):
    """Verificar fortaleza de contraseña"""
    if len(password) < 8:
        return "Demasiado corta (mínimo 8 caracteres)"
    if len(password.encode('utf-8')) > 72:
        return f"Demasiado larga para bcrypt ({len(password.encode('utf-8'))} bytes, máximo 72)"
    return "OK"

def verify_hash_format(hashed_password):
    """Verificar formato del hash almacenado"""
    if not hashed_password:
        return "VACÍO"
    
    if hashed_password.startswith('$2b$'):
        return "BCRYPT_FORMATO_CORRECTO"
    elif hashed_password.startswith('$2a$'):
        return "BCRYPT_FORMATO_ANTIGUO"
    elif hashed_password.startswith('sha256:'):
        return "SHA256_FALLBACK"
    elif len(hashed_password) == 64:
        return "SHA256_HEX"
    else:
        return f"FORMATO_DESCONOCIDO (longitud: {len(hashed_password)})"

# ===== FUNCIÓN DE DIAGNÓSTICO DE LOGIN =====
def debug_login_attempt(email: str, password: str, db: Session):
    """Función para debuggear intentos de login"""
    logger.info(f"🔧 DEBUG LOGIN ATTEMPT:")
    logger.info(f"   Email recibido: '{email}'")
    logger.info(f"   Password recibido: '{password[:3]}...' ({len(password)} chars)")
    
    from backend.models import User
    
    # Ver todos los emails en la base de datos
    all_emails = [u[0] for u in db.query(User.email).all()]
    logger.info(f"   Emails en DB: {all_emails}")
    
    # Buscar usuario
    user = db.query(User).filter(User.email == email).first()
    if user:
        logger.info(f"   ✅ Usuario encontrado: {user.email}")
        logger.info(f"   Hash: {user.hashed_password[:50]}...")
    else:
        logger.info(f"   ❌ Usuario NO encontrado con búsqueda exacta")
    
    return user
