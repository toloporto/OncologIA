import os
import logging
from google import genai
from google.genai import types
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SOAPService:
    def __init__(self):
        # La API Key se cargará desde el entorno (.env)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self._select_best_model()
        else:
            logger.warning("⚠️ GEMINI_API_KEY no encontrada.")
            self.client = None
            self.model_id = None

    def _select_best_model(self):
        """Busca y selecciona el mejor modelo disponible."""
        try:
            # Prioridad de selección optimizada para el Free Tier
            # Los modelos 'Lite' suelen tener cuotas mucho más amplias (RPM)
            priorities = [
                'gemini-1.5-flash-001',
                'gemini-1.5-flash-8b',
                'gemini-1.5-pro-001',
                'gemini-1.0-pro'
            ]
            
            # Intentar con el primer modelo disponible
            selected = priorities[0]
            logger.info(f"✅ Seleccionado para PsychoWebAI: {selected}")
            self.model_id = selected
            
        except Exception as e:
            logger.error(f"❌ Error al configurar modelo: {e}")
            # Fallback forzado a un modelo lite
            self.model_id = 'gemini-2.0-flash-lite'

    def generate_note(self, raw_text: str, emotion_metrics: Dict[str, float]) -> str:
        """
        Genera una nota clínica en formato SOAP utilizando Gemini AI.
        """
        if not self.client or not self.model_id:
            return "Error: Servicio de IA no configurado (falta API Key)."

        # Formatear las métricas para el prompt
        metrics_str = ", ".join([f"{k}: {v:.2f}" for k, v in emotion_metrics.items()])

        system_instruction = (
            "Eres un Especialista en Cuidados Paliativos y Oncología con 20 años de experiencia.\n"
            "Tu objetivo es analizar la transcripción del paciente para monitorizar el control de síntomas y la calidad de vida.\n\n"
            "TAREA 1: EXTRACCIÓN ESAS (0-10)\n"
            "Del texto proporcionado, infiere y estima una puntuación numérica del 0 al 10 para los siguientes síntomas (si no se menciona, marca como 'No evaluable'):\n"
            "- Dolor, Cansancio, Náuseas, Depresión, Ansiedad, Somnolencia, Apetito, Bienestar, Falta de Aire.\n\n"
            "TAREA 2: INFORME SOAP PALIATIVO\n"
            "S (Subjetivo): Citas textuales sobre síntomas físicos y estado anímico. ¿Qué le preocupa más al paciente hoy?\n"
            "O (Objetivo): Lista los valores ESAS estimados. Menciona signos vitales si aparecen en el texto.\n"
            "A (Análisis): Evalúa si el dolor está controlado. Identifica interacciones medicamentosas potenciales si menciona fármacos. Evalúa el sufrimiento espiritual/existencial.\n"
            "P (Plan): Sugiere ajustes de titulación de opioides (basado en guías), medidas de confort, y cuándo avisar al médico.\n\n"
            "Tono: Profesional, clínico, empático. Idioma: Español de España."
        )

        user_content = (
            f"DATOS DE LA SESIÓN:\n"
            f"Texto del paciente: {raw_text}\n"
            f"Métricas de Emociones (IA): {metrics_str}\n"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7
                )
            )
            if response and response.text:
                return response.text
            return "Error: La IA devolvió una respuesta vacía."
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error llamando a Gemini: {e}")
            
            # Detectar error de cuota específicamente
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return (
                    "⚠️ LÍMITE DE CUOTA ALCANZADO\n\n"
                    "La API de Gemini ha alcanzado su límite de uso gratuito.\n\n"
                    "Opciones:\n"
                    "1. Espera unos minutos y vuelve a intentarlo\n"
                    "2. Configura tu propia API Key de Gemini en el archivo .env\n"
                    "3. Considera actualizar a un plan de pago para mayor capacidad\n\n"
                    f"Detalles técnicos: {error_msg[:200]}"
                )
            
            return f"Error en la generación del informe: {error_msg[:300]}"

# Instancia global para ser usada en los endpoints
soap_service = SOAPService()
