# En backend/services/ai_service.py
import os
from typing import Dict, Optional

class AIService:
    """Servicio unificado de IA para OrthoWeb3"""
    
    def __init__(self):
        self.providers = []
        
        # Probar DeepSeek primero
        try:
            from .deepseek_service import deepseek_service
            if deepseek_service.is_active():
                self.providers.append(("deepseek", deepseek_service))
        except:
            pass
        
        # Si no, usar OpenAI
        try:
            from .openai_service import OpenAIService
            openai_service = OpenAIService()
            if openai_service.active:
                self.providers.append(("openai", openai_service))
        except:
            pass
    
    def analyze_dental_case(self, case_data: Dict) -> Dict:
        """Analiza con el primer proveedor disponible"""
        for provider_name, provider in self.providers:
            print(f"🔍 Usando proveedor: {provider_name}")
            try:
                result = provider.analyze_dental_case(case_data)
                if result.get("success"):
                    result["provider"] = provider_name
                    return result
            except:
                continue
        
        # Si todos fallan, respuesta de fallback
        return {
            "success": True,
            "provider": "fallback",
            "response": self._generate_fallback_response(case_data)
        }