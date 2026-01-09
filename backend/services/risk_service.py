import numpy as np
from typing import List, Dict, Any

class RiskService:
    """
    Servicio de Análisis Predictivo de Riesgo (Detector de Recaídas).
    """

    def analyze_risk(self, patient_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza el historial de sesiones para detectar tendencias negativas.
        
        Args:
            patient_history: Lista de diccionarios, cada uno representando una sesión.
                             Se espera que tengan keys: 'date' y 'emotions' (dict con scores).
                             Ej: [{'date': '2025-01-01', 'emotions': {'sadness': 0.1, 'joy': 0.8}}]
        
        Returns:
            Dict con nivel de riesgo, justificación y sugerencias.
        """
        if not patient_history or len(patient_history) < 3:
            return {
                "risk_level": "LOW",
                "message": "Datos insuficientes para análisis de tendencia (se requieren mín. 3 sesiones)."
            }

        # Ordenar por fecha (aseguramos cronología)
        # Asumimos que la fecha viene en formato string ISO o datetime
        # Para simplificar, usamos el índice como eje X (tiempo)
        
        # Extraer series temporales de emociones clave
        dates = range(len(patient_history))
        sadness_scores = [s['emotions'].get('sadness', 0) for s in patient_history]
        anxiety_scores = [s['emotions'].get('fear', 0) for s in patient_history] # Usamos 'fear' como proxy de ansiedad si no hay 'anxiety' explícito
        joy_scores = [s['emotions'].get('joy', 0) for s in patient_history]

        # 1. Detección de Tendencia (Regresión Lineal: y = mx + b)
        # La pendiente 'm' nos dice la velocidad de cambio.
        # m > 0 : La emoción está creciendo.
        # m < 0 : La emoción está disminuyendo.
        
        trend_sadness = np.polyfit(dates, sadness_scores, 1)[0]
        trend_anxiety = np.polyfit(dates, anxiety_scores, 1)[0]
        trend_joy = np.polyfit(dates, joy_scores, 1)[0]

        risk_score = 0
        reasons = []

        # Reglas del "Detector de Humo"
        
        # A. Aumento rápido de tristeza
        if trend_sadness > 0.05: # Sube más de un 5% por sesión en promedio
            risk_score += 2
            reasons.append(f"Tendencia de tristeza en aumento rápido (+{trend_sadness:.2f}/sesión).")
        elif trend_sadness > 0.01:
            risk_score += 1
            reasons.append("Ligero aumento progresivo de la tristeza.")

        # B. Pérdida de anhedonia (Caída de alegría)
        if trend_joy < -0.05:
            risk_score += 2
            reasons.append("Pérdida marcada de emociones positivas (posible anhedonia).")
        
        # C. Ansiedad disparada
        if trend_anxiety > 0.08:
            risk_score += 2
            reasons.append(f"Niveles de miedo/ansiedad disparándose (+{trend_anxiety:.2f}/sesión).")

        # D. Evaluación Final
        # Promedio de las últimas 3 vs promedio histórico
        avg_sadness_recent = np.mean(sadness_scores[-3:])
        avg_sadness_global = np.mean(sadness_scores[:-3]) if len(sadness_scores) > 3 else 0
        
        if len(sadness_scores) > 3 and (avg_sadness_recent > avg_sadness_global * 1.5):
            risk_score += 1
            reasons.append("Las últimas 3 sesiones son un 50% más negativas que el historial previo.")

        # Determinar Nivel
        if risk_score >= 4:
            level = "HIGH"
            action = "🚨 Contactar al paciente. Programar sesión de urgencia."
        elif risk_score >= 2:
            level = "MEDIUM"
            action = "⚠️ Monitorear estrechamente en próxima sesión."
        else:
            level = "LOW"
            action = "✅ Evolución estable."

        return {
            "risk_level": level,
            "risk_score": risk_score,
            "trends": {
                "sadness_slope": float(trend_sadness),
                "joy_slope": float(trend_joy)
            },
            "reasons": reasons,
            "recommended_action": action
        }

risk_service = RiskService()
