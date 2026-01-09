
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OncologyEvolutionService:
    """
    Servicio para analizar la evolución temporal de síntomas oncológicos (ESAS).
    Detecta tendencias de empeoramiento y genera alertas clínicas.
    """

    # Síntomas clave ESAS (Edmonton Symptom Assessment System)
    # Se espera que los valores estén normalizados 0-10 o 0-1
    TRACKED_SYMPTOMS = {
        'pain': 'Dolor',
        'fatigue': 'Fatiga',
        'anxiety': 'Ansiedad',
        'depression': 'Depresión',
        'nausea': 'Náuseas',
        'shortness_of_breath': 'Falta de Aire'
    }

    def analyze_evolution(self, session_logs: List[Any]) -> Dict[str, Any]:
        """
        Analiza el historial de sesiones y calcula tendencias.
        
        Args:
            session_logs: Lista de objetos SessionLog (ORM)
            
        Returns:
            Dict con timeline estructurado y alertas.
        """
        if not session_logs:
            return {"timeline": [], "alerts": [], "status": "insufficient_data"}

        # 1. Construir Timeline Estructurado
        timeline = []
        # Ordenar por fecha (antiguo -> nuevo)
        sorted_logs = sorted(session_logs, key=lambda x: x.created_at)
        
        for log in sorted_logs:
            entry = {
                "date": log.created_at.isoformat(),
                "timestamp": log.created_at.timestamp(),
                "symptoms": {}
            }
            
            # Extraer síntomas del JSON emotion_analysis
            analysis = log.emotion_analysis or {}
            
            for key, label in self.TRACKED_SYMPTOMS.items():
                # Intentar buscar la key exacta o variaciones
                val = analysis.get(key, analysis.get(key.lower(), 0))
                
                # Normalizar a float (manejar strings o ints)
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    val = 0.0
                
                entry["symptoms"][key] = val
                
            timeline.append(entry)

        # 2. Calcular Tendencias (Regresión Lineal por Síntoma)
        trends = self._calculate_trends(timeline)
        
        # 3. Generar Alertas
        alerts = self._generate_alerts(timeline, trends)

        return {
            "timeline": timeline,
            "trends": trends,
            "alerts": alerts,
            "status": "success" if len(timeline) >= 2 else "insufficient_history"
        }

    def _calculate_trends(self, timeline: List[Dict]) -> Dict[str, float]:
        """Calcula la pendiente de cambio para cada síntoma (puntos/día)."""
        trends = {}
        
        if len(timeline) < 2:
            return {k: 0.0 for k in self.TRACKED_SYMPTOMS}

        # Eje X: Días desde el primer registro
        start_time = timeline[0]["timestamp"]
        x = np.array([(t["timestamp"] - start_time) / 86400.0 for t in timeline]) # Días
        
        for key in self.TRACKED_SYMPTOMS:
            y = np.array([t["symptoms"][key] for t in timeline])
            
            # Si todos los valores son 0, pendiente 0
            if np.all(y == 0):
                trends[key] = 0.0
                continue
                
            # Regresión Lineal Simple (y = mx + b)
            # m es la pendiente (cambio de severidad por día)
            try:
                slope, _ = np.polyfit(x, y, 1)
                trends[key] = slope
            except Exception:
                trends[key] = 0.0
                
        return trends

    def _generate_alerts(self, timeline: List[Dict], trends: Dict[str, float]) -> List[Dict]:
        """Genera alertas basadas en niveles actuales y tendencias negativas."""
        alerts = []
        latest = timeline[-1]["symptoms"]
        
        for key, label in self.TRACKED_SYMPTOMS.items():
            current_val = latest.get(key, 0)
            slope = trends.get(key, 0)
            
            # A. Alerta de Umbral Crítico (Severidad > 7/10 o > 0.7/1.0)
            # Asumimos que la escala puede ser 0-10 o 0-1.
            # Normalizamos mentalmente: si es > 1, asumimos escala 10. Si es <= 1, asumimos escala 1.
            CRITICAL_THRESHOLD = 7.0 if current_val > 1.0 else 0.7
            
            if current_val >= CRITICAL_THRESHOLD:
                alerts.append({
                    "type": "critical_level",
                    "severity": "high",
                    "symptom": label,
                    "message": f"Nivel crítico de {label} detectado ({current_val:.1f}). Requiere atención inmediata.",
                    "date": timeline[-1]["date"]
                })
            
            # B. Alerta de Tendencia de Empeoramiento (Pendiente Positiva)
            # Si sube más de 0.5 puntos por día (o 0.05 en escala 1)
            SLOPE_THRESHOLD = 0.2 if current_val > 1.0 else 0.02
            
            if slope > SLOPE_THRESHOLD:
                alerts.append({
                    "type": "worsening_trend",
                    "severity": "medium",
                    "symptom": label,
                    "message": f"Tendencia negativa: {label} está aumentando rápidamente.",
                    "trend_slope": slope
                })
                
        return alerts

oncology_evolution_service = OncologyEvolutionService()
