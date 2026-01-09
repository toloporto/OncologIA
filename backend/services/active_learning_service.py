"""
Servicio de Active Learning para OrthoWeb3
Gestiona la cola de revisión y la recolección de feedback para re-entrenamiento
"""

import logging
import uuid
import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.models import AnalysisReview

logger = logging.getLogger(__name__)

class ActiveLearningService:
    """Gestiona el ciclo de feedback y aprendizaje activo"""

    def should_request_review(self, prediction_data: Dict[str, Any]) -> bool:
        """
        Determina si un análisis debe ser revisado por un humano.
        Criterios:
        1. Confianza del modelo principal < 0.75
        2. Incertidumbre del Ensemble > 0.15
        3. Desacuerdo explícito (consensus = False)
        """
        confidence = prediction_data.get('confidence', 1.0)
        uncertainty = prediction_data.get('uncertainty', 0.0)
        consensus = prediction_data.get('consensus', True)

        if confidence < 0.75:
            logger.info(f"🔍 Active Learning: Baja confianza ({confidence:.2f})")
            return True
        
        if not consensus or uncertainty > 0.15:
            logger.info(f"🔍 Active Learning: Incertidumbre alta ({uncertainty:.2f}) o falta de consenso")
            return True

        return False

    def queue_for_review(self, db: Session, analysis_id: str, prediction_data: Dict[str, Any]):
        """Crea una entrada en la tabla de revisiones pendientes"""
        try:
            review = AnalysisReview(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                confidence_at_prediction=float(prediction_data.get('confidence', 0.0)),
                status="pending",
                created_at=datetime.datetime.utcnow()
            )
            db.add(review)
            db.commit()
            logger.info(f"📝 Análisis {analysis_id} encolado para revisión")
            return review.id
        except Exception as e:
            logger.error(f"❌ Error encolando para revisión: {e}")
            db.rollback()
            return None

    def submit_doctor_review(self, db: Session, review_id: str, correct_label: str, notes: Optional[str] = None):
        """Registra la corrección de un doctor"""
        try:
            review = db.query(AnalysisReview).filter(AnalysisReview.id == review_id).first()
            if not review:
                return False

            review.doctor_label = correct_label
            review.notes = notes
            review.status = "completed"
            review.reviewed_at = datetime.datetime.utcnow()
            review.is_correction = True # Asumimos que si lo revisa es para validar/corregir
            
            db.commit()
            logger.info(f"✅ Feedback recibido para revisión {review_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando revisión: {e}")
            db.rollback()
            return False

# Instancia global
active_learning_service = ActiveLearningService()
