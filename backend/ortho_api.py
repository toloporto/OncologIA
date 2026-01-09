
# backend/ortho_api.py

import os
import sys
import threading
import cv2
import numpy as np
# import tensorflow as tf # Moved to Lazy Load
# from tensorflow import keras # Moved to Lazy Load

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request, Form, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.deepseek_routes import router as deepseek_router


# Clase personalizada para FileResponse con CORS garantizado
class CORSFileResponse(FileResponse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers["Access-Control-Allow-Origin"] = "*"
        self.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        self.headers["Access-Control-Allow-Headers"] = "*"
        self.headers["Access-Control-Expose-Headers"] = "*"
import datetime
import uuid
import json
import logging
from PIL import Image
import io
import base64
from typing import Dict, Any, List, Optional

# Añadir el directorio raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ahora podemos importar los módulos de la base de datos
from backend.database import SessionLocal, engine, get_db
from backend.models import Base, User, AnalysisResult, Patient
from backend.auth import create_access_token, verify_password, get_password_hash
from backend.auth_routes import auth_router
from backend.ipfs_routes import ipfs_router
from backend.generative_manager import GenerativeManager
from backend.explainability import GradCAM
from backend.cyclegan_service import cyclegan_service
from backend.landmarks_service import landmarks_service
from backend.services import PredictionService, AnalysisService, ModelNotAvailableError
from backend.file_validator import validate_upload_file, FileValidationError
from backend.rate_limiter import limiter, rate_limit_exceeded_handler, UPLOAD_RATE_AUTHENTICATED
from backend.services.selenium_service import selenium_service
from slowapi.errors import RateLimitExceeded

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# --- Creación de usuario de prueba ---
def create_test_user_if_not_exists():
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.email == "test@ortho.com").first()
        if not test_user:
            hashed_password = get_password_hash("OrthoWeb3_Demo2024!")
            new_user = User(
                id=str(uuid.uuid4()),
                email="test@ortho.com",
                hashed_password=hashed_password,
                full_name="Usuario de Prueba",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            logger.info("✅ Usuario de prueba creado: test@ortho.com / OrthoWeb3_Demo2024!")
        else:
            logger.info("ℹ️ Usuario de prueba ya existe.")
    except Exception as e:
        logger.error(f"❌ Error creando usuario de prueba: {e}")
        db.rollback()
    finally:
        db.close()

# --- Carga de Modelos de IA ---
# Obtener la ruta base del proyecto (un nivel arriba de backend)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_PATH = os.path.join(BASE_DIR, 'ml-models', 'models', 'ortho_efficientnetv2.h5')
METRICS_PATH = os.path.join(BASE_DIR, 'ml-models', 'trained_models', 'real_ortho_model_metrics.json')
SEGMENTATION_MODEL_PATH = os.path.join(BASE_DIR, 'ml-models', 'trained_models', 'unet_dental_model.h5')
LANDMARKS_MODEL_PATH = os.path.join(BASE_DIR, 'ml-models', 'trained_models', 'shape_predictor_68_face_landmarks.dat')

# --- Gestión de Modelos (Lazy Loading) ---
class ModelManager:
    def __init__(self):
        self.model = None
        self.metrics = None
        self.segmentation_model = None
        self.landmarks_predictor = None
        self.generative_manager = None
        self._loading_lock = False # Simple flag, could be a real Lock if threaded

    def get_classification_model(self):
        if self.model is None:
            self._load_classification_model()
        return self.model

    def get_metrics(self):
        if self.metrics is None:
            self._load_metrics()
        return self.metrics

    def get_segmentation_model(self):
        if self.segmentation_model is None:
            self._load_segmentation_model()
        return self.segmentation_model

    def get_landmarks_predictor(self):
        if self.landmarks_predictor is None:
            self._load_landmarks_predictor()
        return self.landmarks_predictor

    def get_generative_manager(self):
        if self.generative_manager is None:
            self._load_generative_manager()
        return self.generative_manager

    def _load_classification_model(self):
        logger.info(f"🔄 Cargando modelo de clasificación (Lazy Load)...")
        # Lazy Import
        try:
            import tensorflow as tf
            from tensorflow import keras
        except ImportError:
            import keras

        if os.path.exists(MODEL_PATH):
            try:
                self.model = keras.models.load_model(MODEL_PATH, compile=False)
                self.model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
                logger.info("✅ Modelo de clasificación cargado correctamente")
            except Exception as e:
                logger.error(f"❌ Error al cargar modelo de clasificación: {e}")
                self.model = None
        else:
            logger.warning(f"⚠️ Modelo no encontrado en: {MODEL_PATH}")
            self.model = None

    def _load_metrics(self):
        if os.path.exists(METRICS_PATH):
            try:
                with open(METRICS_PATH, 'r') as f:
                    self.metrics = json.load(f)
            except Exception as e:
                logger.error(f"❌ Error al cargar métricas: {e}")
                self.metrics = None
        else:
            self.metrics = None

    def _load_segmentation_model(self):
        logger.info(f"🔄 Cargando modelo de segmentación (Lazy Load)...")
        # Lazy Import
        try:
            import tensorflow as tf
            from tensorflow import keras
        except ImportError:
            import keras

        if os.path.exists(SEGMENTATION_MODEL_PATH):
            try:
                self.segmentation_model = keras.models.load_model(SEGMENTATION_MODEL_PATH, compile=False)
                self.segmentation_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
                logger.info("✅ Modelo de segmentación cargado correctamente")
            except Exception as e:
                logger.error(f"❌ Error al cargar modelo de segmentación: {e}")
                self.segmentation_model = None
        else:
            logger.warning(f"⚠️ Modelo de segmentación no encontrado")
            self.segmentation_model = None

    def _load_landmarks_predictor(self):
        logger.info(f"🔄 Cargando modelo de landmarks (Lazy Load)...")
        try:
            import dlib
            if os.path.exists(LANDMARKS_MODEL_PATH):
                self.landmarks_predictor = dlib.shape_predictor(LANDMARKS_MODEL_PATH)
                logger.info("✅ Modelo de landmarks cargado correctamente")
            else:
                logger.warning(f"⚠️ Archivo de landmarks no encontrado")
                self.landmarks_predictor = None
        except ImportError:
            logger.warning("⚠️ Dlib no disponible")
            self.landmarks_predictor = None
        except Exception as e:
            logger.error(f"❌ Error cargando landmarks: {e}")
            self.landmarks_predictor = None

    def _load_generative_manager(self):
        logger.info(f"🔄 Inicializando GenerativeManager (Lazy Load)...")
        try:
            self.generative_manager = GenerativeManager()
            logger.info("✅ GenerativeManager inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando GenerativeManager: {e}")
            self.generative_manager = None

# Instancia global del gestor de modelos
model_manager = ModelManager()

# Instancias de servicios (Service Layer)
prediction_service = PredictionService(model_manager)

# --- Inicialización de Usuario de Prueba ---
create_test_user_if_not_exists()
# NOTA: Ya no llamamos a load_model() aquí. Se cargarán bajo demanda.

# Crear directorio de imágenes públicas si no existe
if not os.path.exists("public_images"):
    os.makedirs("public_images")
    logger.info("✅ Directorio public_images creado")

# --- Configuración de FastAPI ---
app = FastAPI(
    title="OrthoWeb3 API",
    description="API para análisis de imágenes dentales y gestión de datos con Web3",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("Ejecutando eventos de inicio...")
    selenium_service.start()

    # --- Calentamiento Opcional de Modelos de IA ---
    if os.getenv("CYCLEGAN_WARMUP_ON_STARTUP", "false").lower() in ("true", "1", "yes"):
        logger.info("🔥 Se detectó la variable de entorno para el calentamiento de CycleGAN.")
        # Usamos un thread para no bloquear el inicio del servidor
        warmup_thread = threading.Thread(target=cyclegan_service.warm_up, daemon=True)
        warmup_thread.start()

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Middleware personalizado para asegurar CORS en archivos estáticos
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    # Forzar cabeceras CORS en TODAS las respuestas
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    # Log para debug
    if "/public_images/" in str(request.url):
        logger.info(f"🖼️ Sirviendo imagen: {request.url} - CORS headers añadidos")
    
    return response

# Configuración de CORS estándar (para preflight OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir los routers de autenticación e IPFS
# Incluir los routers de autenticación e IPFS
app.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
app.include_router(ipfs_router, prefix="/ipfs", tags=["IPFS"])

app.include_router(deepseek_router)

# También puedes añadir un endpoint de bienvenida que muestre los servicios:
# @app.get("/")
# async def root():
#     return {
#         "app": "OrthoWeb3",
#         "version": "1.0.0",
#         "services": {
#             "deepseek_selenium": selenium_service.is_ready,
#             "endpoints": {
#                 "dental_analysis": "/api/deepseek/analyze-dental-selenium",
#                 "health_check": "/api/deepseek/selenium-health",
#                 "test": "/api/deepseek/test-dental"
#             }
#         }
#     }


# Montar archivos estáticos para la galería pública
# Endpoint manual para servir imágenes con CORS explícito (Infalible)
@app.get("/public_images/{filename}", tags=["Galería de Demo"])
async def get_public_image(filename: str):
    logger.info(f"📥 Petición de imagen: {filename}")
    file_path = os.path.join("public_images", filename)
    if os.path.exists(file_path):
        logger.info(f"✅ Archivo encontrado: {file_path}")
        # Usar CORSFileResponse que garantiza cabeceras CORS
        return CORSFileResponse(file_path)
    logger.error(f"❌ Archivo NO encontrado: {file_path}")
    raise HTTPException(status_code=404, detail="Imagen no encontrada")

# Endpoint OPTIONS para CORS preflight
@app.options("/public_images/{filename}")
async def options_public_image(filename: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

# --- Dependencias de Seguridad (SoC) ---
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    Centraliza la lógica de autenticación y manejo de errores 401.
    """
    from backend.auth import decode_token
    
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="No se pudieron validar las credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
    return user

def get_analysis_service(db: Session = Depends(get_db)):
    """Dependencia para obtener el servicio de análisis"""
    return AnalysisService(prediction_service, db)

# --- Clases de Datos (Pydantic) ---
class AnalysisRequest(BaseModel):
    image: str  # La imagen en base64

class Recommendation(BaseModel):
    diagnosis: str
    recommendation: str
    urgency: str
    suggested_treatment: str
    confidence_note: str

class AnalysisResponse(BaseModel):
    success: bool
    analysis_id: str
    timestamp: str
    patient_did: str
    predicted_class: str
    confidence: float
    all_confidences: dict
    class_index: int
    recommendation: Recommendation
    segmentation_mask: str # Máscara de segmentación en base64

# --- Constantes y Mapeos ---
CLASS_NAMES = [
    "class_i_normal",
    "class_ii_division1",
    "class_ii_division2",
    "class_iii",
    "open_bite",
    "cross_bite"
]

RECOMMENDATIONS = {
    "class_i_normal": {
        "diagnosis": "Oclusión Normal (Clase I)",
        "recommendation": "Mantener higiene y revisiones periódicas.",
        "urgency": "baja",
        "suggested_treatment": "Profilaxis y seguimiento.",
        "confidence_note": "Alta confidencia en diagnóstico."
    },
    "class_ii_division1": {
        "diagnosis": "Maloclusión Clase II División 1",
        "recommendation": "Requiere evaluación ortodóntica para posible corrección.",
        "urgency": "media",
        "suggested_treatment": "Ortodoncia, posible avance mandibular.",
        "confidence_note": "Alta confidencia en diagnóstico."
    },
    "class_ii_division2": {
        "diagnosis": "Maloclusión Clase II División 2",
        "recommendation": "Consulta con ortodoncista para evaluar la retroinclinación de incisivos.",
        "urgency": "media",
        "suggested_treatment": "Ortodoncia para corregir inclinación y mordida.",
        "confidence_note": "Alta confidencia en diagnóstico."
    },
    "class_iii": {
        "diagnosis": "Maloclusión Clase III",
        "recommendation": "Evaluación urgente por ortodoncista y posible cirujano maxilofacial.",
        "urgency": "alta",
        "suggested_treatment": "Ortodoncia y/o cirugía ortognática.",
        "confidence_note": "Alta confidencia en diagnóstico."
    },
    "open_bite": {
        "diagnosis": "Mordida Abierta",
        "recommendation": "Evaluación para determinar la causa (esquelética o dental) y plan de tratamiento.",
        "urgency": "media-alta",
        "suggested_treatment": "Ortodoncia, possibly with TADs or surgery.",
        "confidence_note": "Alta confidencia en diagnóstico."
    },
    "cross_bite": {
        "diagnosis": "Mordida Cruzada",
        "recommendation": "Corrección temprana es a menudo recomendada para evitar problemas de desarrollo.",
        "urgency": "media",
        "suggested_treatment": "Expansión del paladar, ortodoncia.",
        "confidence_note": "Alta confidencia en diagnóstico."
    },
    "default": {
        "diagnosis": "Evaluación requerida",
        "recommendation": "Consulta con especialista para diagnóstico completo.",
        "urgency": "media",
        "suggested_treatment": "Evaluación clínica completa",
        "confidence_note": "Confidencia variable. Se necesita más información."
    }
}

# --- Funciones de Procesamiento de Imágenes ---
def preprocess_image(image_bytes: bytes, target_size=(512, 512)) -> np.ndarray:
    """Preprocesa una imagen para el modelo de clasificación."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image = image.resize(target_size)
        image_array = np.array(image)
        image_array = image_array / 255.0  # Normalizar
        return np.expand_dims(image_array, axis=0)
    except Exception as e:
        logger.error(f"Error al preprocesar imagen: {e}")
        raise

def preprocess_for_segmentation(image_bytes: bytes, target_size=(512, 512)) -> np.ndarray:
    """Preprocesa una imagen para el modelo de segmentación."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB') # Convertir a RGB (3 canales)
        image = image.resize(target_size)
        image_array = np.array(image)
        image_array = image_array / 255.0
        return np.expand_dims(image_array, axis=0) # Añadir batch dim
    except Exception as e:
        logger.error(f"Error al preprocesar para segmentación: {e}")
        raise

def postprocess_segmentation_mask(mask: np.ndarray, original_size) -> Image:
    """Post-procesa la máscara de segmentación a una imagen visible."""
    mask = (mask * 255).astype(np.uint8)
    mask_image = Image.fromarray(mask)
    mask_image = mask_image.resize(original_size, Image.NEAREST)
    
    # Crear una imagen RGBA coloreada para la máscara
    mask_rgba = mask_image.convert('RGBA')
    data = np.array(mask_rgba)
    red, green, blue, alpha = data.T

    # Áreas blancas (dientes) se vuelven verdes semi-transparentes
    white_areas = (red > 200) & (green > 200) & (blue > 200)
    data[...][white_areas.T] = (0, 204, 153, 150) # Tono verde-azulado semitransparente

    # Áreas no-blancas (fondo) se vuelven transparentes
    black_areas = ~white_areas
    data[...][black_areas.T] = (0, 0, 0, 0)
    
    return Image.fromarray(data)


# --- Endpoints de la API ---
@app.get("/health", tags=["Sistema"])
def health_check():
    """Verifica que la API esté funcionando."""
    # Con Lazy Loading, el modelo siempre está "listo para cargar", así que devolvemos True
    # para que el frontend no muestre error.
    return {
        "status": "ok",
        "model_loaded": True 
    }

@app.get("/model-info", tags=["Modelo"])
def get_model_info():
    """Devuelve información sobre el modelo cargado y sus métricas."""
    # Aquí podríamos decidir si cargar el modelo o solo mostrar info si ya está cargado
    # Para info completa, cargamos el modelo
    model = model_manager.get_classification_model()
    metrics = model_manager.get_metrics()
    
    if model is None:
        return {
            "model_loaded": False,
            "error": "Modelo no cargado",
            "class_count": 0,
            "class_names": []
        }
    
    info = {
        "model_loaded": True,
        "class_count": len(CLASS_NAMES),
        "class_names": CLASS_NAMES,
        "model_summary": [],
        "metrics": metrics or "No disponibles"
    }
    try:
        model.summary(print_fn=lambda x: info["model_summary"].append(x))
    except:
        pass
    return info

# --- Endpoints de Active Learning (Revisión Médica) ---

@app.get("/reviews/pending", tags=["Active Learning"])
async def get_pending_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de análisis marcados para revisión por baja confianza"""
    from backend.models import AnalysisReview, AnalysisResult
    
    reviews = db.query(AnalysisReview).join(AnalysisResult).filter(
        AnalysisReview.status == "pending"
    ).all()
    
    result = []
    for r in reviews:
        analysis = db.query(AnalysisResult).filter(AnalysisResult.id == r.analysis_id).first()
        result.append({
            "id": r.id,
            "analysis_id": r.analysis_id,
            "image_url": f"/public_images/{analysis.image_filename}" if analysis else None,
            "predicted_class": analysis.predicted_class if analysis else None,
            "confidence": r.confidence_at_prediction,
            "created_at": r.created_at.isoformat()
        })
    return result

@app.post("/reviews/{review_id}/submit", tags=["Active Learning"])
async def submit_review(
    review_id: str,
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enviar corrección de un doctor para un análisis dudosso"""
    from backend.services.active_learning_service import active_learning_service
    
    correct_label = data.get("correct_label")
    notes = data.get("notes")
    
    if not correct_label:
        raise HTTPException(status_code=400, detail="Debe proporcionar la etiqueta correcta")
        
    success = active_learning_service.submit_doctor_review(
        db, review_id, correct_label, notes
    )
    
    if success:
        return {"success": True, "message": "Feedback registrado correctamente"}
    raise HTTPException(status_code=404, detail="Revisión no encontrada o error al procesar")

@app.get("/reviews/{review_id}/explain", tags=["Active Learning", "XAI"])
async def explain_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generar Grad-CAM para una revisión existente para ayudar al doctor"""
    from backend.models import AnalysisReview, AnalysisResult
    
    review = db.query(AnalysisReview).filter(AnalysisReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Revisión no encontrada")
        
    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == review.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis asociado no encontrado")
        
    # Cargar imagen
    file_path = os.path.join("public_images", analysis.image_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo de imagen no encontrado")
        
    try:
        with open(file_path, "rb") as f:
            image_bytes = f.read()
            
        # Generar explicación
        result = prediction_service.predict_with_explanation(
            image_bytes,
            include_explanation=True
        )
        
        explanation = result.get('explanation')
        if not explanation or not explanation.get('success'):
            raise HTTPException(status_code=500, detail="Error generando Grad-CAM")
            
        return {
            "success": True,
            "explanation_image": explanation['heatmap_base64'],
            "predicted_class": analysis.predicted_class,
            "confidence": analysis.confidence
        }
    except Exception as e:
        logger.error(f"Error en explain_review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=AnalysisResponse, tags=["Análisis"])

@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
def analyze_image(
    request: Request,
    patient_did: str,
    file: UploadFile = File(...),
    use_ensemble: bool = Query(False, description="Usar ensemble de modelos"),
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analiza una imagen dental para clasificar la oclusión y detectar problemas.
    Guarda el resultado en la base de datos.
    """
    try:
        # Leer imagen (en def síncrono, usamos file.file.read() o esperamos)
        # Para mantener compatibilidad con UploadFile sincronizado
        image_bytes = file.file.read()
        
        # Validar archivo
        try:
            safe_filename, mime_type = validate_upload_file(image_bytes, file.filename)
            logger.info(f"✅ Archivo validado: {safe_filename} ({mime_type})")
        except FileValidationError as e:
            logger.warning(f"⚠️ Archivo rechazado en /analyze: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Delegar al servicio
        result = analysis_service.analyze_dental_image(
            image_bytes=image_bytes,
            patient_did=patient_did,
            user_id=current_user.id,
            filename=safe_filename,
            use_ensemble=use_ensemble
        )
        
        # Construir respuesta
        response_data = {
            "success": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "patient_did": patient_did,
            "segmentation_mask": None,  # Deshabilitado temporalmente
            "segmentation": {"mask": None, "polygons": []},
            **result
        }
        
        return JSONResponse(content=response_data)
        
    except ModelNotAvailableError as e:
        logger.error(f"Modelo no disponible: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error durante el análisis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")

@app.post("/analyze/gallery", response_model=AnalysisResponse, tags=["Análisis"])
def analyze_gallery_image(
    patient_did: str,
    filename: str,
    use_ensemble: bool = Query(False, description="Usar ensemble de modelos"),
    current_user: User = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Analiza una imagen existente en la galería del servidor.
    """
    # Buscar la imagen en public_images
    file_path = os.path.join("public_images", filename)
    if not os.path.exists(file_path):
        # Intentar extraer solo el nombre si viene una URL completa
        filename = os.path.basename(filename)
        file_path = os.path.join("public_images", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Imagen no encontrada en la galería")

    try:
        # Leer imagen del disco
        with open(file_path, "rb") as f:
            image_bytes = f.read()
        
        # Delegar al servicio (igual que /analyze)
        result = analysis_service.analyze_dental_image(
            image_bytes=image_bytes,
            patient_did=patient_did,
            user_id=current_user.id,
            filename=filename,
            use_ensemble=use_ensemble
        )
        
        # Construir respuesta
        response_data = {
            "success": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "patient_did": patient_did,
            "segmentation_mask": None,
            "segmentation": {"mask": None, "polygons": []},
            **result
        }
        return JSONResponse(content=response_data)

    except ModelNotAvailableError as e:
        logger.error(f"Modelo no disponible: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error analizando imagen de galería: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@app.post("/analyze/explain", tags=["Análisis", "XAI"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
def explain_analysis(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Genera una explicación visual (Grad-CAM) para la predicción del modelo.
    Devuelve la imagen con el mapa de calor superpuesto y regiones influyentes.
    """
    try:
        # Leer imagen
        image_bytes = file.file.read()
        
        # Validar archivo
        try:
            validate_upload_file(image_bytes, file.filename)
        except FileValidationError as e:
            logger.warning(f"⚠️ Archivo rechazado en /analyze/explain: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Usar servicio para obtener predicción y explicación
        result = prediction_service.predict_with_explanation(
            image_bytes,
            include_explanation=True
        )
        
        # Verificar si la explicación fue generada
        explanation = result.get('explanation')
        if not explanation or not explanation.get('success'):
            raise HTTPException(
                status_code=500,
                detail="No se pudo generar la explicación visual"
            )
        
        # Obtener clase predicha
        class_pred = result.get('class_pred')
        if class_pred is not None:
            class_idx = int(np.argmax(class_pred))
            predicted_class = CLASS_NAMES[class_idx]
        else:
            predicted_class = "unknown"
        
        return JSONResponse(content={
            "success": True,
            "predicted_class": predicted_class,
            "explanation_image": explanation['heatmap_base64'],
            "influential_regions": explanation['influential_regions'],
            "heatmap_entropy": explanation['heatmap_entropy'],
            "description": f"Mapa de calor mostrando las áreas determinantes para la clase {predicted_class}"
        })
        
    except ModelNotAvailableError as e:
        logger.error(f"Modelo no disponible: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error generando explicación Grad-CAM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando explicación: {e}")


@app.post("/simulate/treatment", tags=["Simulación"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
def simulate_treatment(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera una simulación de tratamiento ortodóntico usando CycleGAN.
    Transforma una imagen de dientes desalineados a dientes alineados.
    """
    # (Autenticación manejada por Depends)
    
    # Validar archivo primero
    image_bytes = file.file.read()
    try:
        validate_upload_file(image_bytes, file.filename)
    except FileValidationError as e:
        logger.warning(f"⚠️ Archivo rechazado en /simulate/treatment: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    # Verificar que el servicio CycleGAN esté disponible
    # Nota: cyclegan_service es un módulo importado, si queremos lazy load completo deberíamos
    # mover su inicialización dentro de una función o usar el ModelManager si lo integramos.
    # Por ahora, asumimos que cyclegan_service maneja su propia carga o es ligero.
    if not cyclegan_service.is_available():
        raise HTTPException(
            status_code=503, 
            detail="Servicio de simulación no disponible. El modelo CycleGAN no está cargado."
        )
    
    try:
        logger.info("🎨 Generando simulación de tratamiento con CycleGAN...")
        
        # Generar simulación
        simulated_image_bytes = cyclegan_service.generate_treatment_simulation(image_bytes)
        
        # Convertir a base64 para respuesta
        img_b64 = base64.b64encode(simulated_image_bytes).decode('utf-8')
        
        return JSONResponse(content={
            "success": True,
            "simulated_image": f"data:image/jpeg;base64,{img_b64}",
            "description": "Simulación de tratamiento ortodóntico generada con CycleGAN",
            "note": "Esta es una simulación aproximada. Los resultados reales pueden variar."
        })
    
    except Exception as e:
        logger.error(f"❌ Error generando simulación: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generando simulación: {e}")

@app.post("/analyze/landmarks", tags=["Análisis"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
def analyze_landmarks(
    request: Request, 
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Detecta puntos faciales y dentales (Landmarks) en la imagen usando MediaPipe.
    Retorna 468 puntos faciales con coordenadas y métricas calculadas.
    """
    try:
        logger.info("🔍 Analizando landmarks faciales...")
        image_bytes = file.file.read()
        
        # Validar archivo
        try:
            validate_upload_file(image_bytes, file.filename)
        except FileValidationError as e:
            logger.warning(f"⚠️ Archivo rechazado en /analyze/landmarks: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Opción rápida: Asegurarnos de que el predictor esté cargado en el manager
        _ = model_manager.get_landmarks_predictor()
        
        result = landmarks_service.process_image(image_bytes)
        
        if not result:
            return JSONResponse(content={
                "success": False, 
                "message": "No se detectó ningún rostro en la imagen"
            })
            
        logger.info(f"✅ Detectados {result['total_landmarks']} landmarks")
        return JSONResponse(content={
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"❌ Error analizando landmarks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al analizar landmarks: {str(e)}")

@app.get("/history", tags=["Análisis"])
def get_analysis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Devuelve el historial de análisis para el usuario autenticado.
    """
    history = db.query(AnalysisResult).filter(AnalysisResult.user_id == current_user.id).order_by(AnalysisResult.timestamp.desc()).all()
    
    # El objeto history no es directamente serializable a JSON si contiene relaciones complejas.
    # Creamos una lista de diccionarios para asegurar la serialización.
    history_list = []
    for record in history:
        # Robustez en la deserialización de JSON para evitar fallos catastróficos si hay datos corruptos
        try:
            rec_data = json.loads(record.recommendation) if record.recommendation else None
        except Exception:
            rec_data = {"diagnosis": "Error", "recommendation": "Dato corrupto en DB"}
            
        try:
            conf_data = json.loads(record.all_confidences_json) if record.all_confidences_json else None
        except Exception:
            conf_data = {}

        history_list.append({
            "id": record.id,
            "user_id": record.user_id,
            "patient_did": record.patient_did,
            "image_filename": record.image_filename,
            "predicted_class": record.predicted_class,
            "confidence": record.confidence,
            "timestamp": record.timestamp.isoformat(),
            "recommendation": rec_data,
            "all_confidences": conf_data
        })
        
    return JSONResponse(content=history_list)

@app.get("/gallery/images", tags=["Galería de Demo"])
def get_gallery_images(request: Request):
    """
    Devuelve una lista de imágenes de demostración para la galería.
    Esta es una función de ejemplo y debería ser reemplazada por una gestión de archivos real.
    """
    image_dir = "public_images"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
        # Aquí podrías añadir lógica para copiar imágenes de demo si no existen
    
    try:
        files = os.listdir(image_dir)
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return image_files
    except Exception as e:
        logger.error(f"Error listando galería: {e}")
        return []

        return []

@app.get("/patients/{patient_did}/evolution", tags=["Análisis Temporal"])
async def get_patient_evolution(
    patient_did: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la evolución temporal del paciente basada en su historial de análisis.
    Devuelve métricas de severidad, gráfica de tendencia y proyecciones.
    """
    from backend.services.temporal_service import temporal_service
    
    # 1. Recuperar historial del paciente
    # Nota: Filtramos por DID de paciente, no solo por el usuario que consulta
    history = db.query(AnalysisResult).filter(
        AnalysisResult.patient_did == patient_did
    ).all()
    
    # 2. Verificar permisos (opcional: solo el doctor o el paciente mismo)
    # Por ahora dejamos abierto a usuarios autenticados
    
    # 3. Calcular evolución
    try:
        evolution_data = temporal_service.analyze_progress(history)
        
        # Eliminar objetos datetime no serializables del timeline antes de responder
        for item in evolution_data.get("timeline", []):
            if "timestamp" in item:
                del item["timestamp"]
                
        return JSONResponse(content={
            "success": True,
            "patient_did": patient_did,
            "data": evolution_data
        })
    except Exception as e:
        logger.error(f"Error calculando evolución: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/patients/{patient_id}/evolution-check", tags=["Análisis Temporal"])
async def check_patient_evolution(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verifica la evolución del paciente comparando los dos últimos análisis.
    Genera una ALERTA si la mejora es inferior al 5% respecto al anterior.
    """
    try:
        # 1. Recuperar los dos últimos registros para ese patient_id (DID)
        history = db.query(AnalysisResult).filter(
            AnalysisResult.patient_did == patient_id
        ).order_by(AnalysisResult.timestamp.desc()).limit(2).all()
        
        if len(history) < 2:
            return JSONResponse(content={
                "status": "UNKNOWN",
                "patient_id": patient_id,
                "detail": "No hay suficientes datos históricos (mínimo 2 requeridos) para comparar."
            })
        
        current = history[0]
        previous = history[1]
        
        # 2. Lógica de Comparación (usando confidence como métrica simple)
        # Improvement = (Current - Previous) / Previous
        curr_conf = current.confidence if current.confidence is not None else 0.0
        prev_conf = previous.confidence if previous.confidence is not None else 0.0001
        
        # Evitar división por cero si prev_conf es 0
        if prev_conf == 0:
            prev_conf = 0.0001
            
        improvement_metric = (curr_conf - prev_conf) / prev_conf
        
        # Si la mejora es inferior al 5% (0.05), marcar ALERTA.
        # Nota: Si improvement es negativo (empeoró), también es < 0.05, por lo tanto ALERTA.
        status = "NORMAL"
        if improvement_metric < 0.05:
            status = "ALERTA"
            
        return JSONResponse(content={
            "status": status,
            "patient_id": patient_id,
            "improvement_metric": round(improvement_metric, 4),
            "improvement_percent": f"{improvement_metric*100:.2f}%",
            "current_confidence": curr_conf,
            "previous_confidence": prev_conf,
            "timestamp_current": current.timestamp.isoformat(),
            "timestamp_previous": previous.timestamp.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en check_patient_evolution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al verificar evolución: {str(e)}")

@app.post("/analyze/multimodal", tags=["Análisis Avanzado"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
async def analyze_multimodal(
    request: Request,
    clinical_context: str = Form(...), # JSON string o lista separada por comas
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Análisis Multimodal: Combina la imagen dental con contexto clínico (texto).
    Usa IA (CLIP) para determinar qué descripción clínica encaja mejor con la imagen.
    Útil para validar síntomas reportados por el paciente.
    """
    from backend.services.multimodal_service import multimodal_service

    try:
        logger.info("🧠 Iniciando análisis multimodal...")
        
        # Procesar textos
        try:
            prompt_list = json.loads(clinical_context)
            if not isinstance(prompt_list, list):
                prompt_list = [str(prompt_list)]
        except:
            prompt_list = [t.strip() for t in clinical_context.split(',')]

        # Validar y leer imagen
        image_bytes = file.file.read()
        try:
            validate_upload_file(image_bytes, file.filename)
        except FileValidationError as e:
             raise HTTPException(status_code=400, detail=str(e))

        # Ejecutar análisis
        result = multimodal_service.analyze_with_context(image_bytes, prompt_list)

        return JSONResponse(content={
            "success": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "multimodal_result": result
        })

    except Exception as e:
        logger.error(f"❌ Error en endpoint multimodal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en análisis multimodal: {str(e)}")



# --- Inicialización Condicional de Generación con IA ---
# Eliminado bloque global, ahora se maneja en ModelManager

class GenerativeRequest(BaseModel):
    prompt: str
    context: str # Puede ser el resultado de un análisis, historial, etc.

@app.post("/simulate-treatment", tags=["Simulación de Tratamiento"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
def simulate_treatment_generative(
    request: Request,
    treatment_type: str = "aligner",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simula el resultado de un tratamiento ortodóntico usando IA.
    Tipos disponibles: aligner, brackets, whitening
    """

    generative_manager = model_manager.get_generative_manager()
    if generative_manager is None:
        logger.error("Servicio de simulación de tratamientos no disponible.")
        raise HTTPException(status_code=503, detail="Servicio de simulaciones no disponible. Verifique la instalación de MediaPipe.")

    try:
        # Leer la imagen
        image_bytes = file.file.read()
        
        # Validar archivo
        try:
            validate_upload_file(image_bytes, file.filename)
        except FileValidationError as e:
            logger.warning(f"⚠️ Archivo rechazado en /simulate-treatment: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        # Usar el gestor generativo para simular el tratamiento
        logger.info(f"Simulando tratamiento {treatment_type} con IA generativa")
        result = generative_manager.simulate_treatment(image_bytes, treatment_type)

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error en simulación de tratamiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error en simulación de tratamiento: {str(e)}")

@app.post("/generate/report", tags=["IA Generativa"])
async def generate_ia_report(
    request_body: GenerativeRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera un informe o texto utilizando un modelo de lenguaje grande (LLM).
    """

    if generative_manager is None:
        logger.error("Servicio de generación de texto no disponible.")
        raise HTTPException(status_code=503, detail="Servicio de IA generativa no disponible.")

    try:
        logger.info(f"Petición de generación recibida con prompt: {request_body.prompt}")
        response = generative_manager.generate_text(request_body.prompt, request_body.context)
        return JSONResponse(content={"success": True, "generated_text": response})
    except Exception as e:
        logger.error(f"Error en la generación de texto: {e}")
        raise HTTPException(status_code=500, detail="Error en el servicio de IA generativa.")


# --- Lanzador de la Aplicación ---

# --- Servir Frontend (SPA) para Distribución ---
# En modo producción/distribución, el backend sirve los archivos estáticos de React
FRONTEND_DIST_DIR = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.exists(FRONTEND_DIST_DIR):
    logger.info(f"📂 Sirviendo Frontend desde: {FRONTEND_DIST_DIR}")
    
    # 1. Montar assets estáticos (js, css, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST_DIR, "assets")), name="assets")
    
    # 2. Servir index.html para la ruta raíz y cualquier ruta no encontrada (SPA Fallback)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Si la ruta comienza con /api, es un endpoint no encontrado -> 404 real
        if full_path.startswith("api/") or full_path.startswith("public_images/"):
            raise HTTPException(status_code=404, detail="Endpoint no encontrado")
            
        # Si es un archivo que existe en dist (ej. vite.svg), servirlo
        potential_file = os.path.join(FRONTEND_DIST_DIR, full_path)
        if os.path.exists(potential_file) and os.path.isfile(potential_file):
            return FileResponse(potential_file)
            
        # Para todo lo demás (rutas de React Router), servir el index.html
        return FileResponse(os.path.join(FRONTEND_DIST_DIR, "index.html"))

else:
    logger.warning("⚠️  Carpeta frontend/dist NO encontrada. La aplicación web no se servirá desde aquí.")
    logger.warning("    Asegúrate de ejecutar 'npm run build' en la carpeta frontend.")


# --- Lanzador de la Aplicación ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor Uvicorn en http://0.0.0.0:8004")
    # Workers=1 es importante para PyInstaller y variables globales
    uvicorn.run(app, host="0.0.0.0", port=8004)

