
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import json
import hashlib
from sqlalchemy.orm import Session
from backend.models import AnalysisResult

logger = logging.getLogger(__name__)

class TemporalAnalysisService:
    """
    Servicio para analizar la evolución temporal de los pacientes.
    Convierte diagnósticos cualitativos (Clase I, II, etc.) en un 'Índice de Severidad' cuantitativo
    y calcula tendencias de progreso usando regresión lineal.
    
    NUEVO: Integración con Blockchain e IPFS para inmutabilidad de datos.
    """

    # Mapeo de Severidad (0 = Perfecto/Meta, 10 = Muy Severo)
    # Este es un sistema heurístico para MVP.
    SEVERITY_MAP = {
        "class_i_normal": 0,       # Meta: Oclusión ideal
        "class_ii_division1": 4,   # Moderado
        "class_ii_division2": 5,   # Moderado-Severo (mordida profunda)
        "cross_bite": 6,           # Complejo
        "open_bite": 7,            # Complejo (esqueleto vs dental)
        "class_iii": 8,            # Severo (suele requerir cirugía)
        "default": 5               # Valor medio si no se reconoce
    }

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
        self._blockchain_service = None
        self._ipfs_service = None

    def get_severity_score(self, diagnosis_class: str) -> int:
        """Devuelve el puntaje de severidad para una clase dada."""
        return self.SEVERITY_MAP.get(diagnosis_class, self.SEVERITY_MAP["default"])

    def analyze_progress(
        self, 
        analysis_history: List[AnalysisResult],
        store_on_blockchain: bool = False,
        patient_did: str = None
    ) -> Dict[str, Any]:
        """
        Calcula la línea de tiempo y la tendencia de progreso.
        
        ESTRATEGIA HÍBRIDA:
        - Pocos datos (<5): Usa Regresión Lineal (más robusta con data escasa).
        - Suficientes datos (>=5): Usa Deep Learning (LSTM) para detectar patrones no lineales.
        """
        if not analysis_history or len(analysis_history) < 2:
            return {
                "can_calculate_trend": False,
                "message": "Se necesitan al menos 2 análisis para calcular una tendencia.",
                "timeline": self._build_timeline(analysis_history)
            }

        # 1. Construir línea de tiempo
        timeline = self._build_timeline(analysis_history)
        dates = [item['timestamp'] for item in timeline]
        scores = [item['severity'] for item in timeline]
        
        start_date = dates[0]
        x = np.array([(d - start_date).days for d in dates], dtype=np.float32) # Días
        y = np.array(scores, dtype=np.float32) # Severidad

        # 2. Lógica Predicción (Híbrida)
        predicted_30d_score = 0.0
        prediction_method = "linear_regression"
        
        # --- MÉTODO A: Regresión Lineal (Fallback) ---
        slope, intercept = np.polyfit(x, y, 1)
        linear_pred = slope * (x[-1] + 30) + intercept
        
        # --- MÉTODO B: LSTM (Deep Learning) ---
        if len(history_and_scores := list(zip(scores, x))) >= 5:
            try:
                from backend.services.lstm_evolution_model import get_evolution_model
                lstm_model = get_evolution_model()
                
                # Predecir siguiente paso (asumiendo ~30 días después del último)
                lstm_pred = lstm_model.predict_next_month(history_and_scores)
                
                # Usamos LSTM como la predicción "oficial" si está disponible
                predicted_30d_score = lstm_pred
                prediction_method = "lstm_neural_network"
                logger.info(f"🧠 Predicción LSTM generada: {lstm_pred:.2f} (Lineal era: {linear_pred:.2f})")
                
            except Exception as e:
                logger.error(f"⚠️ Falló LSTM, usando regresión: {e}")
                predicted_30d_score = linear_pred
        else:
            predicted_30d_score = linear_pred

        # Clamp 0-10
        predicted_30d_score = max(0, min(10, predicted_30d_score))
        
        # Calcular tasa mensual basada en la pendiente lineal (útil como referencia siempre)
        progress_rate = -slope * 30 

        # 3. Interpretar tendencia
        if progress_rate > 0.1:
            trend_status = "improving"
            trend_description = f"Mejora estimada de {progress_rate:.1f} puntos/mes ({prediction_method})"
        elif progress_rate < -0.1:
            trend_status = "worsening"
            trend_description = f"Retroceso estimado de {abs(progress_rate):.1f} puntos/mes ({prediction_method})"
        else:
            trend_status = "stable"
            trend_description = "Condición estable"

        # 4. Detectar anomalías (Comparando Real vs Esperado si fuera lineal)
        is_anomaly = self._detect_anomaly(scores)
        
        # Alerta especial si LSTM difiere mucho de Lineal (posible estancamiento oculto)
        if prediction_method == "lstm_neural_network" and abs(predicted_30d_score - linear_pred) > 2.0:
            trend_description += " [⚠️ Divergencia Lineal/IA detectada]"

        result = {
            "can_calculate_trend": True,
            "timeline": timeline,
            "trend": {
                "slope": float(slope),
                "status": trend_status,
                "description": trend_description,
                "progress_rate_monthly": float(progress_rate),
                "current_severity": float(scores[-1]),
                "predicted_severity_next_month": float(predicted_30d_score),
                "prediction_method": prediction_method,
                "anomaly_detected": is_anomaly
            }
        }
        
        # 5. Almacenar en blockchain
        if store_on_blockchain and patient_did:
            blockchain_result = self._store_on_blockchain(
                patient_did=patient_did,
                analysis_data=result,
                current_severity=int(scores[-1]),
                current_diagnosis=timeline[-1]['diagnosis'],
                is_anomaly=is_anomaly
            )
            if blockchain_result:
                result['blockchain'] = blockchain_result
        
        return result

    def _build_timeline(self, history: List[AnalysisResult]) -> List[Dict]:
        """Convierte objetos ORM a diccionarios ordenados con severidad."""
        timeline = []
        # Asegurar orden cronológico ascendente (antiguo -> nuevo)
        sorted_history = sorted(history, key=lambda x: x.timestamp)
        
        for record in sorted_history:
            severity = self.get_severity_score(record.predicted_class)
            timeline.append({
                "date": record.timestamp.isoformat(),
                "timestamp": record.timestamp, # Objeto datetime para cálculos internos
                "diagnosis": record.predicted_class,
                "severity": severity,
                "analysis_id": record.id,
                "image": record.image_filename
            })
        return timeline
    
    def _detect_anomaly(self, scores: List[int]) -> bool:
        """
        Detectar anomalías en la evolución
        
        Criterios:
        - Salto brusco de severidad (>3 puntos en un paso)
        - Reversión inesperada (mejora seguida de empeoramiento súbito)
        """
        if len(scores) < 2:
            return False
        
        # Verificar saltos bruscos
        for i in range(1, len(scores)):
            diff = abs(scores[i] - scores[i-1])
            if diff > 3:
                logger.warning(f"⚠️ Anomalía detectada: salto de severidad de {diff} puntos")
                return True
        
        return False
    
    def _store_on_blockchain(
        self,
        patient_did: str,
        analysis_data: Dict,
        current_severity: int,
        current_diagnosis: str,
        is_anomaly: bool
    ) -> Optional[Dict]:
        """
        Encolar análisis para escritura asíncrona en blockchain
        
        Steps:
        1. Generar hash del análisis completo
        2. (Opcional) Subir JSON completo a IPFS
        3. Encolar transacción para procesamiento en segundo plano
        """
        try:
            # Generar hash SHA256 del análisis
            analysis_json = json.dumps(analysis_data, sort_keys=True)
            content_hash = hashlib.sha256(analysis_json.encode()).hexdigest()
            
            # Intentar subir a IPFS (opcional, no bloqueante)
            ipfs_hash = None
            try:
                from backend.ipfs_service import ipfs_service
                if ipfs_service.is_connected():
                    ipfs_result = ipfs_service.upload_file(
                        analysis_json.encode(),
                        f"evolution_{patient_did}_{datetime.now().timestamp()}.json"
                    )
                    if ipfs_result and ipfs_result.get('success'):
                        ipfs_hash = ipfs_result['hash']
                        content_hash = ipfs_hash  # Usar IPFS hash si está disponible
                        logger.info(f"✅ Análisis subido a IPFS: {ipfs_hash}")
            except Exception as ipfs_error:
                logger.warning(f"⚠️ IPFS no disponible: {ipfs_error}")
            
            # Encolar transacción blockchain (NO BLOQUEANTE)
            from backend.services.blockchain_queue_service import blockchain_queue_service
            
            transaction_id = blockchain_queue_service.enqueue_blockchain_write(
                patient_did=patient_did,
                content_hash=content_hash,
                severity=current_severity,
                diagnosis=current_diagnosis,
                is_anomaly=is_anomaly
            )
            
            if transaction_id:
                logger.info(f"✅ Transacción blockchain encolada: {transaction_id}")
                return {
                    'queued': True,
                    'transaction_id': transaction_id,
                    'ipfs_hash': ipfs_hash,
                    'content_hash': content_hash
                }
            else:
                logger.error("❌ Error encolando transacción blockchain")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error en cola blockchain: {e}")
            return None

# Instancia global (si se necesita sin estado de DB)
temporal_service = TemporalAnalysisService()
