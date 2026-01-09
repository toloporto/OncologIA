
import os
import sys
import logging
import datetime
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Database & Models
from backend.database import SessionLocal, engine, get_db
from backend.models import Base, User, Patient, SessionLog, AnalysisFeedback
from backend.auth import get_password_hash, oauth2_scheme, decode_token
from backend.auth_routes import auth_router
from backend.services.langchain_manager import langchain_agent
from backend.services.rag_service import rag_service

# -----------------------------------------------------------------------------
# Configuration & Logging
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# Model Manager (The "AI Brain")
# -----------------------------------------------------------------------------
class ModelManager:
    def __init__(self):
        self.nlp_pipeline = None

    def load_nlp_model(self):
        """Carga el modelo NLP experto en Psicología Clínica (Fine-tuned)."""
        if self.nlp_pipeline is None:
            # Get the root directory of the project
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            
            # Try different possible paths for the model
            possible_paths = [
                os.path.join(root_dir, "psycho_model_final", "psycho_model", "psycho_model_final"),
                os.path.join(root_dir, "psycho_model_final"),
                os.path.join(os.getcwd(), "psycho_model_final"),
                "./psycho_model_final"
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    model_path = path
                    break
            
            if not model_path:
                logger.error("❌ No se encontró la carpeta del modelo 'psycho_model_final'.")
                return None

            logger.info(f"🧠 Cargando Cerebro Experto desde {model_path}...")
            try:
                from transformers import pipeline
                self.nlp_pipeline = pipeline(
                    "text-classification",
                    model=model_path,
                    tokenizer=model_path,
                    top_k=None
                )
                logger.info("✅ ¡Cerebro Experto de OncologIA cargado satisfactoriamente!")
            except Exception as e:
                logger.error(f"❌ Error loading NLP model: {e}")
                self.nlp_pipeline = None
        return self.nlp_pipeline

    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyzes the text and returns a dictionary of emotions and their scores.
        Example: {'joy': 0.1, 'sadness': 0.8, ...}
        """
        pipeline = self.load_nlp_model()
        if not pipeline:
            return {"error": "Model not available"}

        try:
            # The pipeline returns a list of lists of dicts e.g. [[{'label': 'joy', 'score': 0.9}, ...]]
            results = pipeline(text)
            # Flatten/Format results
            # output of return_all_scores=True is usually [[{'label': 'LB', 'score': SC}, ...]]
            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], list):
                # Flatten the first list
                scores = {item['label']: float(item['score']) for item in results[0]}
                return scores
            elif isinstance(results, list):
                 # Handle cases where return_all_scores might work differently or be singular
                 return {item['label']: float(item['score']) for item in results}
            return {}
        except Exception as e:
            logger.error(f"❌ NLP Analysis failed: {e}")
            return {"error": str(e)}

model_manager = ModelManager()

# -----------------------------------------------------------------------------
# Safety Layer
# -----------------------------------------------------------------------------
CRITICAL_KEYWORDS = [
    # Riesgo Suicida / Psicológico
    "matarme", "suicidio", "acabar con todo", "morir", "muerte", "no quiero vivir",
    # Urgencias Oncológicas
    "no puedo respirar", "falta de aire", "ahogo", "asfixia",  # Disnea
    "dolor insoportable", "gritos de dolor", "no aguanto el dolor", # Crisis de dolor
    "sangrando", "hemorragia", "sangre", # Sangrado
    "fiebre alta", "tiritona" # Neutropenia/Sepsis
]

def check_risk_keywords(text: str):
    """
    Scans text for critical keywords indicating self-harm or immediate danger.
    Returns: (is_risky: bool, alert_message: str|None)
    """
    text_lower = text.lower()
    for keyword in CRITICAL_KEYWORDS:
        if keyword in text_lower:
            return True, f"⚠️ ALERTA: Palabra clave detectada '{keyword}'. Protocolo de seguridad activado."
    return False, None

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    """
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

# -----------------------------------------------------------------------------
# FastAPI App Setup
# -----------------------------------------------------------------------------
app = FastAPI(
    title="OncologIA API",
    description="Plataforma de IA para Oncología, Cuidados Paliativos y Salud Mental",
    version="2.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Se ejecuta al iniciar el servidor. Pre-carga el modelo de IA."""
    logger.info("🚀 Iniciando servicios de OncologIA...")
    # Pre-cargar el modelo de IA para que esté listo desde el primer segundo
    model_manager.load_nlp_model()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth Router
app.include_router(auth_router, prefix="/auth", tags=["Autenticación"])

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class SessionInput(BaseModel):
    patient_id: str
    text: str

class SessionResponse(BaseModel):
    success: bool
    session_id: str
    timestamp: str
    risk_flag: bool
    alert: Optional[str] = None
    emotion_analysis: Dict[str, float]

# -----------------------------------------------------------------------------
# Test User Init
# -----------------------------------------------------------------------------
def create_test_user_if_not_exists():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "test@psych.com").first():
            new_user = User(
                id=str(uuid.uuid4()),
                email="test@psych.com",
                hashed_password=get_password_hash("Psycho2025!"),
                full_name="Dr. Test",
                is_active=True
            )
            db.add(new_user)
            db.commit()
            logger.info("✅ Usuario de prueba creado: test@psych.com")
    except Exception as e:
        logger.error(f"Error init user: {e}")
    finally:
        db.close()

create_test_user_if_not_exists()

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/model-info", tags=["Estatus"])
def get_model_info():
    """Devuelve metadatos del modelo NLP activo."""
    return {
        "model_name": "OncologIA Expert Model (v1.0)",
        "type": "NLP - Psycho-Oncology Fine-tuned",
        "class_count": 7,
        "class_names": ["others", "joy", "sadness", "anger", "surprise", "disgust", "fear"],
        "model_loaded": model_manager.nlp_pipeline is not None,
        "device": "cpu"
    }

@app.get("/history", tags=["Historial"])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el historial de sesiones analizadas."""
    logs = db.query(SessionLog).order_by(SessionLog.created_at.desc()).all()
    # Mapear para que el frontend lo entienda
    return [
        {
            "id": log.id,
            "patient_id": log.patient_id,
            "timestamp": log.created_at.isoformat(),
            "raw_text": log.raw_text[:100] + "..." if len(log.raw_text) > 100 else log.raw_text,
            "emotion_analysis": log.emotion_analysis,
            "risk_flag": log.risk_flag,
            "soap_report": log.soap_report
        } for log in logs
    ]

@app.get("/gallery/images", tags=["Pacientes"])
def get_patients_gallery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reutiliza el endpoint de galería para listar pacientes en OncologIA."""
    patients = db.query(Patient).all()
    return [
        {
            "id": p.id,
            "filename": p.did,
            "path": f"/patients/{p.id}",
            "full_name": p.full_name,
            "created_at": p.created_at.isoformat()
        } for p in patients

    ]

@app.get("/patient/{patient_id}/evolution", tags=["Pacientes"])
def get_patient_evolution(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la evolución de los síntomas oncológicos (ESAS) del paciente.
    Devuelve tendencias de Dolor, Fatiga, Ansiedad, etc., y alertas de recaída.
    """
    # 1. Obtener logs verificando que pertenezcan al paciente (o que el médico tenga acceso)
    # Por ahora asumimos médico admin puede ver todo.
    logs = db.query(SessionLog).filter(SessionLog.patient_id == patient_id).all()
    
    if not logs:
        return {"status": "no_data", "timeline": [], "alerts": []}
    
    # 2. Llamar al servicio de evolución oncológica
    try:
        from backend.services.oncology_evolution_service import oncology_evolution_service
        result = oncology_evolution_service.analyze_evolution(logs)
        return result
    except Exception as e:
        logger.error(f"Error analizando evolución oncológica: {e}")
        raise HTTPException(status_code=500, detail="Error analizando evolución del paciente")

# --- Asistente Clínico (RAG) ---

class ChatRequest(BaseModel):
    query: str
    patient_id: Optional[str] = None

@app.post("/api/chat", tags=["Asistente Clínico"])
def chat_clinical_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat con el asistente clínico (RAG + Contexto Paciente).
    Busca en guías clínicas (PDFs) y usa datos básicos del paciente.
    """
    patient_context = ""
    if request.patient_id:
        # Recuperar resumen básico del paciente
        patient = db.query(Patient).filter(Patient.did == request.patient_id).first()
        if patient:
            patient_context = f"Paciente: {patient.full_name} (ID: {patient.did})."
            # Opcional: Podríamos añadir diagnósticos recientes aquí
    
    from backend.services.langchain_manager import langchain_agent
    result = langchain_agent.chat_agent(request.query, patient_context)
    return result

@app.get("/health", tags=["Estatus"])
def health_check():
    """Verifica el estado del sistema y la carga del modelo."""
    return {
        "status": "online",
        "timestamp": datetime.datetime.now().isoformat(),
        "model_loaded": model_manager.nlp_pipeline is not None,
        "app": "OncologIA"
    }

@app.post("/session/analyze", response_model=SessionResponse, tags=["Clinical Core"])
def analyze_session(
    input_data: SessionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recibe texto de sesión/diario, analiza emociones y detecta riesgos con agentes LangChain.
    """
    # 1. AI Risk Analysis (LangChain Agent)
    try:
        risk_data = langchain_agent.analyze_risk_agent(input_data.text)
        risk_flag = risk_data.risk_found
        risk_msg = risk_data.explanation if risk_flag else None
    except Exception as e:
        logger.error(f"Error en Risk Analysis: {e}")
        status_code = 503
        if "429" in str(e) or "quota" in str(e).lower():
            status_code = 429
        raise HTTPException(status_code=status_code, detail=f"Error de IA: {str(e)}")
    
    
    # 2. Local Emotion Analysis -> Replaced by Symptom Extraction (ESAS) for Oncology
    # emotions = model_manager.analyze_text(input_data.text)
    
    # NEW: Use LangChain Agent to extract clinical symptoms (Pain, Fatigue, etc.)
    try:
        emotions = langchain_agent.extract_symptoms_agent(input_data.text)
        
        # INTEGRACIÓN ML PÚBLICO: Complementar con detección de emociones del modelo entrenado
        try:
            from backend.services.emotion_ml_service import emotion_ml_service
            ml_prediction = emotion_ml_service.predict_emotion(input_data.text)
            if ml_prediction:
                # Merge or add to emotions dict
                emotions['detected_mood_ml'] = ml_prediction['emotion']
                emotions['mood_confidence'] = ml_prediction['confidence']
        except Exception as ml_e:
            logger.warning(f"ML Public Model prediction failed: {ml_e}")

    except Exception as e:
        logger.error(f"Error extracting symptoms: {e}")
        # Fallback to empty if fails, or try model_manager as last resort if loaded
        emotions = {}
    
    # 3. Create Session Log
    new_log = SessionLog(
        id=str(uuid.uuid4()),
        patient_id=input_data.patient_id,
        raw_text=input_data.text,
        emotion_analysis=emotions,
        risk_flag=risk_flag,
        created_at=datetime.datetime.utcnow()
    )
    
    try:
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving session: {e}")
        raise HTTPException(status_code=500, detail="Error guardando sesión")
        
    return {
        "success": True,
        "session_id": new_log.id,
        "timestamp": new_log.created_at.isoformat(),
        "risk_flag": risk_flag,
        "alert": risk_msg,
        "emotion_analysis": emotions
    }

@app.post("/api/reports/generate_soap/{session_id}", tags=["Generative AI"])
def generate_soap_note(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera un informe clínico en formato SOAP con memoria usando Agentes LangChain.
    """
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    # 1. Preparar datos
    raw_text = session.raw_text
    emotion_metrics = session.emotion_analysis or {}
    
    # 2. Generar Nota con Agente LangChain
    try:
        logger.info(f"✨ Agente LangChain: Generando SOAP para {session_id}...")
        soap_note = langchain_agent.generate_soap_agent(
            session.patient_id, 
            raw_text, 
            emotion_metrics
        )
        
        # 3. Persistir en DB
        session.soap_report = soap_note
        db.commit()
        db.refresh(session)
        logger.info(f"✅ Informe SOAP (LangChain) guardado.")
        
        return {
            "success": True,
            "session_id": session_id,
            "soap_report": soap_note
        }
    except Exception as e:
        logger.error(f"Error en generación SOAP: {e}")
        status_code = 503
        if "429" in str(e) or "quota" in str(e).lower():
            status_code = 429
        raise HTTPException(status_code=status_code, detail=f"Error de IA: {str(e)}")


@app.post("/api/reports/psychoeducation/{session_id}", tags=["Generative AI"])
def generate_psychoeducation(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agente TCC: Genera material educativo y tareas para el paciente.
    """
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    if not session.soap_report:
        raise HTTPException(status_code=400, detail="Primero debes generar el reporte SOAP")

    try:
        logger.info(f"✨ Agente TCC: Generando material educativo para {session_id}...")
        # Tomamos métricas y el SOAP ya generado para coherencia
        draft = langchain_agent.generate_psychoeducation_agent(
            session.patient_id,
            session.soap_report,
            session.emotion_analysis or {}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "psychoeducation_draft": draft
        }
    except Exception as e:
        logger.error(f"Error en generación TCC: {e}")
        status_code = 503
        if "429" in str(e) or "quota" in str(e).lower():
            status_code = 429
        raise HTTPException(status_code=status_code, detail=f"Error de IA: {str(e)}")



# Endpoint helper to create a patient quickly for testing from Postman
class PatientCreate(BaseModel):
    full_name: str
    did: str

@app.post("/patients", tags=["Pacientes"])
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra un nuevo paciente en el sistema."""
    # Verificar si el DID ya existe
    existing = db.query(Patient).filter(Patient.did == patient.did).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El paciente con ID '{patient.did}' ya está registrado.")
    
    try:
        new_p = Patient(
            id=str(uuid.uuid4()), 
            did=patient.did, 
            full_name=patient.full_name,
            created_at=datetime.datetime.utcnow()
        )
        db.add(new_p)
        db.commit()
        db.refresh(new_p)
        return {
            "success": True, 
            "id": new_p.id,
            "full_name": new_p.full_name,
            "did": new_p.did
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error registrando paciente: {e}")
        raise HTTPException(status_code=500, detail="Error interno al registrar paciente")

from fastapi import UploadFile, File
from backend.services.voice_service import voice_service

@app.post("/api/transcribe", tags=["Voice Analysis"])
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Recibe un archivo de audio (blob), lo procesa con Whisper y devuelve el texto.
    """
    logger.info(f"🎤 Recibiendo audio para transcripción: {file.filename}")
    
    try:
        # Leer contenido del archivo
        audio_bytes = await file.read()
        
        # Guardar temporalmente para que ffmpeg lo lea (whisper carga desde archivo path o numpy array)
        # Para simplificar y soportar varios formatos (webm, mp3), guardamos a disco temporalmente.
        temp_filename = f"temp_{uuid.uuid4()}.webm" # Asumimos webm del navegador
        with open(temp_filename, "wb") as f:
            f.write(audio_bytes)
            
        logger.info(f"  - Guardado temporal en {temp_filename}")
        
        # Cargar modelo (si no está)
        voice_service.load_model()
        
        # Transcribir usando la ruta del archivo (Whisper usa ffmpeg internamente para abrirlo)
        result = voice_service.model.transcribe(temp_filename, language="es")
        text = result.get("text", "").strip()
        
        # Limpieza
        os.remove(temp_filename)
        
        logger.info(f"✅ Transcripción: {text[:50]}...")
        return {"success": True, "text": text}
        
    except Exception as e:
        logger.error(f"❌ Error en transcripción API: {e}")
        # Intentar limpiar si falló
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")

# -----------------------------------------------------------------------------
# Active Learning Endpoints
# -----------------------------------------------------------------------------
class FeedbackInput(BaseModel):
    session_id: str
    original_ai_output: Dict[str, float]
    doctor_corrected_output: Dict[str, float]
    comments: Optional[str] = None

from fastapi import UploadFile, File, BackgroundTasks

@app.post("/learning/feedback", tags=["Active Learning"])
def submit_clinical_feedback(
    feedback: FeedbackInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recibe correcciones del médico (Human-in-the-Loop) para mejorar la IA.
    Guarda el feedback y (futuro) lo indexa en ChromaDB.
    """
    try:
        # Verificar que la sesión existe
        session_log = db.query(SessionLog).filter(SessionLog.id == feedback.session_id).first()
        if not session_log:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

        new_feedback = AnalysisFeedback(
            session_id=feedback.session_id,
            original_ai_output=feedback.original_ai_output,
            doctor_corrected_output=feedback.doctor_corrected_output,
            comments=feedback.comments
        )
        
        db.add(new_feedback)
        db.commit()
        logger.info(f"🧠 Feedback clínico guardado para sesión {feedback.session_id}")
        
        # Ingesta en Vector DB (Chroma) para Active Learning
        # Recuperamos el texto original de la sesión
        rag_service.store_feedback(
            text=session_log.raw_text,
            correction=feedback.doctor_corrected_output,
            session_id=feedback.session_id
        )

        # --- ACTIVE LEARNING (MODELO ML) ---
        # Guardamos para re-entrenar el clasificador de emociones
        try:
            from backend.learning.feedback_manager import save_feedback
            if save_feedback(session_log.raw_text, feedback.doctor_corrected_output):
                # Si hubo un cambio real, disparamos re-entrenamiento en background
                background_tasks.add_task(retrain_and_reload_model)
        except Exception as e:
            logger.error(f"Error guardando feedback ML: {e}")
        # -----------------------------------
        
        return {"success": True, "message": "Feedback recibido. El sistema aprenderá de esto automáticamente."}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando feedback: {e}")
        raise HTTPException(status_code=500, detail="Error interno procesando feedback")

def retrain_and_reload_model():
    """Función helper para re-entrenar y recargar sin bloquear el API"""
    try:
        from backend.learning.train_public_emotion import train
        from backend.services.emotion_ml_service import emotion_ml_service
        
        logger.info("⚡ Background Task: Iniciando re-entrenamiento automático...")
        train(verbose=False) # Entrenar sin spam en consola
        emotion_ml_service.reload_model() # Recargar en caliente
        logger.info("✅ Background Task: Modelo actualizado y recargado.")
    except Exception as e:
        logger.error(f"❌ Error en re-entrenamiento automático: {e}")
