"""
Orquestador unificado de servicios de IA para OrthoWeb3
"""
import logging
from typing import Dict, Optional
from .selenium_deepseek import deepseek_selenium_service

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """Coordina diferentes servicios de IA"""
    
    def __init__(self):
        self.services = {
            "deepseek_selenium": deepseek_selenium_service
        }
        self.active_service = "deepseek_selenium"
        
        # Iniciar servicios
        self._initialize_services()
    
    def _initialize_services(self):
        """Inicializa todos los servicios de IA"""
        logger.info("🔄 Inicializando servicios de IA...")
        
        # Iniciar DeepSeek Selenium
        if self.services["deepseek_selenium"].start_service():
            logger.info("✅ DeepSeek Selenium service iniciado")
        else:
            logger.warning("⚠️ DeepSeek Selenium no pudo iniciarse")
    
    def analyze_orthodontic_case(self, case_data: Dict, user_id: str = None) -> Dict:
        """
        Punto de entrada principal para análisis de casos
        
        Args:
            case_data: Datos estructurados del caso
            user_id: ID del usuario para contexto
        
        Returns:
            Análisis unificado
        """
        logger.info(f"🔍 Analizando caso para usuario {user_id or 'anon'}")
        
        # Usar servicio activo
        service = self.services.get(self.active_service)
        
        if not service or not service.is_ready:
            return self._fallback_response(case_data)
        
        try:
            # Enriquecer datos del caso
            enriched_data = self._enrich_case_data(case_data)
            
            # Ejecutar análisis
            result = service.analyze_dental_case(enriched_data, user_id)
            
            # Añadir metadatos de servicio
            if result.get("success"):
                result["service_used"] = self.active_service
                result["service_version"] = "1.0.0"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en análisis: {e}")
            return self._fallback_response(case_data, str(e))
    
    def chat_with_ai(self, message: str, context: Dict, user_id: str) -> Dict:
        """Chat interactivo con IA"""
        service = self.services.get(self.active_service)
        
        if not service or not service.is_ready:
            return {
                "success": False,
                "error": "Servicio de IA no disponible",
                "response": "Por favor, intente más tarde."
            }
        
        return service.chat_with_patient(message, context, user_id)
    
    def _enrich_case_data(self, case_data: Dict) -> Dict:
        """Enriquece datos del caso con información adicional"""
        # Puedes añadir lógica aquí para procesar imágenes, etc.
        return {
            **case_data,
            "analysis_timestamp": self._get_timestamp(),
            "case_complexity": self._estimate_complexity(case_data)
        }
    
    def _estimate_complexity(self, case_data: Dict) -> str:
        """Estima complejidad del caso"""
        # Lógica simple de estimación
        issues = case_data.get("clinical_data", {}).get("specific_issues", "")
        if "sever" in issues.lower() or "complej" in issues.lower():
            return "alta"
        elif "moder" in issues.lower():
            return "media"
        return "baja"
    
    def _fallback_response(self, case_data: Dict, error: str = None) -> Dict:
        """Respuesta cuando fallan todos los servicios"""
        return {
            "success": False,
            "error": error or "Servicios de IA no disponibles",
            "fallback_analysis": {
                "diagnosis": "Evaluación pendiente",
                "recommendations": [
                    "Consulta especializada requerida",
                    "Se recomienda evaluación clínica presencial",
                    "Documentación completa del caso necesaria"
                ],
                "notes": "El sistema de IA asistente no está disponible temporalmente."
            },
            "metadata": {
                "service_used": "fallback",
                "timestamp": self._get_timestamp()
            }
        }
    
    def _get_timestamp(self):
        """Timestamp formateado"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def shutdown(self):
        """Apaga todos los servicios de forma ordenada"""
        logger.info("🔌 Apagando servicios de IA...")
        for name, service in self.services.items():
            try:
                service.stop_service()
                logger.info(f"✅ {name} detenido")
            except Exception as e:
                logger.error(f"Error deteniendo {name}: {e}")


# Instancia global
ai_orchestrator = AIOrchestrator()