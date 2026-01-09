from typing import Dict, Any, List
import numpy as np
from datetime import datetime, timezone
import uuid
import json
from PIL import Image
import io


# Constantes movidas desde ortho_api.py
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


class AnalysisService:
    """Servicio de análisis dental completo"""
    
    def __init__(self, prediction_service, db_session):
        self.prediction_service = prediction_service
        self.db = db_session
    
    def analyze_dental_image(
        self,
        image_bytes: bytes,
        patient_did: str,
        user_id: str,
        filename: str,
        use_ensemble: bool = False
    ) -> Dict[str, Any]:
        """
        Análisis completo de imagen dental.
        
        Args:
            image_bytes: Imagen en bytes
            patient_did: DID del paciente
            user_id: ID del usuario
            filename: Nombre del archivo
            use_ensemble: Si True, utiliza el ensemble de modelos
            
        Returns:
            Dict con análisis completo y recomendaciones
        """
        # 1. Predicción
        pred_result = self.prediction_service.predict_classification(
            image_bytes, 
            use_ensemble=use_ensemble
        )
        
        # 2. Procesar resultados
        class_index = int(np.argmax(pred_result['class_pred']))
        confidence = float(np.max(pred_result['class_pred']))
        predicted_class = CLASS_NAMES[class_index]
        
        # 3. Calcular confidencias
        all_confidences = self._calculate_all_confidences(pred_result['class_pred'])
        
        # 4. Procesar landmarks y severidad
        landmarks = self._process_landmarks(pred_result['landmarks'], image_bytes)
        severity = self._process_severity(pred_result['severity'])
        
        # 5. Análisis Cefalométrico (GEOMETRÍA)
        # Solo si hay landmarks suficientes
        geometric_analysis = None
        if len(landmarks) > 0:
            from backend.services.cephalometric_service import cephalometric_service
            geometric_analysis = cephalometric_service.analyze_angles(landmarks)
        
        # 6. Generar recomendación
        recommendation = RECOMMENDATIONS.get(predicted_class, RECOMMENDATIONS["default"])
        
        # 7. Guardar en BD
        analysis_id = self._save_to_database(
            user_id=user_id,
            patient_did=patient_did,
            filename=filename,
            predicted_class=predicted_class,
            confidence=confidence,
            all_confidences=all_confidences,
            recommendation=recommendation
        )
        
        result = {
            'analysis_id': analysis_id,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'severity': severity,
            'all_confidences': all_confidences,
            'class_index': class_index,
            'landmarks': landmarks,
            'recommendation': recommendation,
            'geometric_analysis': geometric_analysis
        }

        # Añadir métricas del ensemble si están presentes
        if 'uncertainty' in pred_result:
            result['uncertainty'] = pred_result['uncertainty']
            result['consensus'] = pred_result['consensus']
            result['ensemble_active'] = True

        # 8. Active Learning (Aprendizaje Activo)
        # Si la confianza es baja o hay dudas, encolar para revisión humana
        try:
            from backend.services.active_learning_service import active_learning_service
            if active_learning_service.should_request_review(result):
                active_learning_service.queue_for_review(self.db, analysis_id, result)
                result['review_requested'] = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"⚠️ No se pudo encolar para Active Learning: {e}")

        # 9. Reporte Médico Generativo (IA Narrativa)
        try:
            from backend.services.report_service import report_service
            report_res = report_service.generate_clinical_report(result)
            if report_res.get('success'):
                result['narrative_report'] = report_res.get('report_text')
                result['llm_method'] = report_res.get('llm_method')
        except Exception as e:
            logging.getLogger(__name__).warning(f"⚠️ Error generando reporte narrativo: {e}")

        return result
    
    def _calculate_all_confidences(self, predictions) -> Dict[str, float]:
        """Calcula confidencias para todas las clases"""
        return {
            CLASS_NAMES[i]: float(predictions[0][i]) 
            for i in range(len(CLASS_NAMES))
        }
    
    def _process_landmarks(self, landmarks_pred, image_bytes) -> List[Dict]:
        """Procesa landmarks a formato estructurado"""
        if landmarks_pred is None:
            return []
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            formatted = []
            flat = landmarks_pred.flatten()
            for i in range(0, len(flat) - 1, 2):
                formatted.append({
                    "x": float(flat[i] * width),
                    "y": float(flat[i+1] * height),
                    "id": i//2
                })
            return formatted
        except Exception:
            return []
    
    def _process_severity(self, severity_pred) -> str:
        """Procesa severidad a categoría"""
        if severity_pred is None:
            return "No determinada"
        
        try:
            score = float(severity_pred[0][0]) if severity_pred.shape[-1] == 1 else 0
            if score < 0.3:
                return "Leve"
            elif score < 0.7:
                return "Moderada"
            else:
                return "Severa"
        except Exception:
            return "No determinada"
    
    def _save_to_database(self, **kwargs) -> str:
        """Guarda análisis en la base de datos"""
        from backend.models import AnalysisResult
        
        analysis_id = str(uuid.uuid4())
        new_analysis = AnalysisResult(
            id=analysis_id,
            user_id=kwargs['user_id'],
            patient_did=kwargs['patient_did'],
            image_filename=kwargs['filename'],
            predicted_class=kwargs['predicted_class'],
            confidence=kwargs['confidence'],
            recommendation=json.dumps(kwargs['recommendation']),
            all_confidences_json=json.dumps(kwargs['all_confidences']),
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(new_analysis)
        self.db.commit()
        
        return analysis_id
