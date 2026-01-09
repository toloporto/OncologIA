"""
Servicio de Generación de Reportes Médicos Generativos
"""

import logging
from typing import Dict, Any
from backend.ortho_deepseek_free import OrthoDeepSeekFree

logger = logging.getLogger(__name__)

class ReportGenerationService:
    """Genera reportes médicos profesionales usando LLMs"""

    def __init__(self):
        self.llm_service = OrthoDeepSeekFree()

    def generate_clinical_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un reporte redactado por IA basado en los datos del análisis
        """
        try:
            # Preparar datos para el prompt
            case_data = {
                "patient_info": {
                    "did": analysis_data.get('patient_did', 'N/A'),
                },
                "clinical_data": {
                    "classification": analysis_data.get('predicted_class'),
                    "confidence": f"{analysis_data.get('confidence', 0)*100:.1f}%",
                    "severity": analysis_data.get('severity'),
                    "angles": analysis_data.get('geometric_analysis', {}),
                    "timestamp": analysis_data.get('timestamp')
                }
            }

            # Construir prompt especializado
            prompt = self._build_report_prompt(case_data)
            
            # Llamar al servicio LLM (DeepSeek/Gemini)
            llm_result = self.llm_service.analyze_dental_case({"custom_prompt": prompt})
            
            if llm_result.get("success"):
                return {
                    "success": True,
                    "report_text": llm_result.get("response"),
                    "llm_method": llm_result.get("method")
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo generar el reporte narrativo",
                    "fallback": llm_result.get("fallback_response")
                }

        except Exception as e:
            logger.error(f"Error en ReportGenerationService: {e}")
            return {"success": False, "error": str(e)}

    def _build_report_prompt(self, data: Dict) -> str:
        """Construye un prompt clínico detallado"""
        clinical = data["clinical_data"]
        angles = clinical["angles"]
        
        # Formatear ángulos si existen
        angles_str = ""
        if angles:
            for k, v in angles.items():
                angles_str += f"- {v.get('label')}: {v.get('value'):.2f}° ({v.get('status')})\n"

        return f"""
        Actúa como un Ortodoncista Senior con 20 años de experiencia. 
        Tu tarea es redactar un informe clínico formal basado en los hallazgos de una IA de visión.

        DATOS DEL ANÁLISIS:
        - Clasificación: {clinical['classification']}
        - Confianza IA: {clinical['confidence']}
        - Severidad: {clinical['severity']}
        
        MEDIDAS GEOMÉTRICAS (CEFALOMETRÍA):
        {angles_str if angles_str else "No detectadas"}
        
        REQUISITOS DEL INFORME:
        1. **Resumen Ejecutivo**: Descripción técnica de la maloclusión.
        2. **Análisis Geométrico**: Interpretación de los ángulos (SNA, SNB, ANB) si están presentes.
        3. **Plan de Acción Tentativo**: Pasos sugeridos (estudios adicionales, tipos de aparatología).
        4. **Lenguaje**: Profesional, preciso pero comprensible para el paciente.
        
        Escribe el informe en ESPAÑOL. No incluyas placeholders. Firma como "Sistema de Soporte de Decisiones Clínicas OrthoWeb3".
        """

# Instancia global
report_service = ReportGenerationService()
