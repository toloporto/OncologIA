"""
Servicio DeepSeek gratuito para OrthoWeb3
Usa métodos alternativos cuando la API falla
"""
import os
import json
import requests
from typing import Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class OrthoDeepSeekFree:
    """Servicio DeepSeek con fallback a métodos gratuitos"""
    
    def __init__(self):
        self.methods = [
            self._try_official_api,      # Método 1: API oficial
            self._try_web_interface,     # Método 2: Interfaz web
            self._try_openrouter,        # Método 3: OpenRouter
            self._try_local_fallback     # Método 4: Fallback local
        ]
        
        self.current_method = None
    
    def analyze_dental_case(self, case_data: Dict) -> Dict:
        """Analiza caso dental con el primer método que funcione"""
        
        for i, method in enumerate(self.methods):
            method_name = method.__name__.replace('_try_', '').title()
            logger.info(f"Intentando método {i+1}: {method_name}")
            
            try:
                result = method(case_data)
                if result.get("success"):
                    self.current_method = method_name
                    logger.info(f"✅ Método exitoso: {method_name}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️  Método {method_name} falló: {e}")
                continue
        
        # Si todos fallan
        return {
            "success": False,
            "error": "Todos los métodos fallaron",
            "fallback_response": self._generate_fallback_response(case_data)
        }
    
    def _try_official_api(self, case_data: Dict) -> Dict:
        """Intenta con la API oficial de DeepSeek"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not api_key:
            raise ValueError("No API key configured")
        
        prompt = self._build_prompt(case_data)
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Eres un ortodoncista experto."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "method": "official_api",
                "response": data["choices"][0]["message"]["content"],
                "parsed": self._parse_response(data["choices"][0]["message"]["content"])
            }
        else:
            raise Exception(f"API error {response.status_code}: {response.text[:100]}")
    
    def _try_web_interface(self, case_data: Dict) -> Dict:
        """Intenta con la interfaz web de DeepSeek"""
        prompt = self._build_prompt(case_data)
        
        # Simular navegador
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Referer": "https://chat.deepseek.com/"
        }
        
        response = requests.post(
            "https://chat.deepseek.com/api/chat",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "deepseek-chat",
                "stream": False
            },
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "method": "web_interface",
                "response": data.get("content", ""),
                "parsed": self._parse_response(data.get("content", ""))
            }
        else:
            raise Exception(f"Web interface error {response.status_code}")
    
    def _try_openrouter(self, case_data: Dict) -> Dict:
        """Usa OpenRouter como fallback"""
        prompt = self._build_prompt(case_data)
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer free",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-flash-1.5-8b",
                "messages": [
                    {"role": "system", "content": "Eres un ortodoncista experto."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "method": "openrouter",
                "response": data["choices"][0]["message"]["content"],
                "parsed": self._parse_response(data["choices"][0]["message"]["content"])
            }
        else:
            raise Exception(f"OpenRouter error {response.status_code}")
    
    def _try_local_fallback(self, case_data: Dict) -> Dict:
        """Fallback local cuando nada funciona"""
        # Generar respuesta básica basada en reglas
        return {
            "success": True,
            "method": "local_fallback",
            "response": self._generate_fallback_response(case_data),
            "parsed": {"source": "local_fallback"}
        }
    
    def _build_prompt(self, case_data: Dict) -> str:
        """Construye prompt para análisis dental"""
        # Si ya viene un prompt personalizado (ej: desde ReportService)
        if "custom_prompt" in case_data:
            return case_data["custom_prompt"]

        patient = case_data.get("patient_info", {})
        clinical = case_data.get("clinical_data", {})
        
        return f"""
        Como ortodoncista, analiza este caso:
        
        Paciente: {patient.get('age', 'N/A')} años, {patient.get('gender', 'N/A')}
        Motivo: {clinical.get('reason', 'N/A')}
        Hallazgos: {clinical.get('findings', 'N/A')}
        
        Proporciona análisis y recomendaciones.
        """
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parsea la respuesta en formato estructurado"""
        # Implementación simple
        return {
            "analysis": response_text,
            "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text
        }
    
    def _generate_fallback_response(self, case_data: Dict) -> str:
        """Genera respuesta cuando todos los métodos fallan"""
        return f"""
        [ANÁLISIS AUTOMÁTICO - MODO OFFLINE]
        
        Basado en los datos proporcionados:
        - Paciente: {case_data.get('patient_info', {}).get('age', 'N/A')} años
        - Motivo de consulta: {case_data.get('clinical_data', {}).get('reason', 'No especificado')}
        
        Recomendación general:
        1. Evaluación clínica completa por especialista
        2. Documentación fotográfica
        3. Modelos de estudio si es necesario
        4. Plan de tratamiento personalizado
        
        Nota: Este es un análisis automático básico.
        Consulte con un ortodoncista certificado para diagnóstico preciso.
        """

# Uso en tu proyecto
if __name__ == "__main__":
    service = OrthoDeepSeekFree()
    
    # Ejemplo de caso
    case_data = {
        "patient_info": {
            "age": 14,
            "gender": "female"
        },
        "clinical_data": {
            "reason": "Dientes torcidos",
            "findings": "Apiñamiento moderado, clase II"
        }
    }
    
    print("🔍 Analizando caso dental con métodos alternativos...")
    result = service.analyze_dental_case(case_data)
    
    print(f"\n✅ Método usado: {result.get('method', 'N/A')}")
    print(f"\n📋 Respuesta:")
    print(result.get("response", "No response"))