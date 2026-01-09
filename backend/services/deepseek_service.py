"""
DeepSeek Integration Service for OrthoWeb3
Versión con búsqueda flexible de .env
"""
import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_env_file():
    """Busca el archivo .env en ubicaciones posibles"""
    possible_locations = [
        # 1. En la raíz del proyecto (desde backend/services)
        Path(__file__).parent.parent.parent / ".env",
        # 2. En el directorio actual
        Path.cwd() / ".env",
        # 3. En el directorio del script
        Path(__file__).parent / ".env",
        # 4. En el directorio padre (backend)
        Path(__file__).parent.parent / ".env",
        # 5. En el directorio de trabajo del usuario
        Path.home() / ".env",
    ]
    
    print("🔍 Buscando archivo .env...")
    for env_path in possible_locations:
        if env_path.exists():
            print(f"   ✅ Encontrado en: {env_path}")
            return str(env_path)
        else:
            print(f"   ❌ No en: {env_path}")
    
    print("⚠️  No se encontró archivo .env en ninguna ubicación")
    return None

class DeepSeekService:
    """Servicio para integrar DeepSeek API en OrthoWeb3"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa el servicio DeepSeek
        """
        print("\n" + "=" * 60)
        print("🦷 INICIALIZANDO SERVICIO DEEPSEEK")
        print("=" * 60)
        
        # Buscar y cargar .env
        env_path = find_env_file()
        
        if env_path:
            load_dotenv(dotenv_path=env_path)
            print(f"📂 .env cargado desde: {env_path}")
        else:
            print("⚠️  No se pudo cargar .env, usando variables de entorno del sistema")
            load_dotenv()  # Intentar cargar desde variables del sistema
        
        # Obtener API key
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        
        if not self.api_key:
            print("\n❌ DEEPSEEK_API_KEY no encontrada.")
            print("\n🔍 Variables de entorno disponibles con 'DEEPSEEK' o 'API':")
            found_vars = False
            for key, value in os.environ.items():
                key_upper = key.upper()
                if 'DEEPSEEK' in key_upper or 'API' in key_upper or 'KEY' in key_upper:
                    found_vars = True
                    masked_value = '*' * len(value) if value else '[vacía]'
                    print(f"   {key}: {masked_value}")
            
            if not found_vars:
                print("   (No se encontraron variables relacionadas)")
            
            print("\n💡 PARA SOLUCIONAR:")
            print("   1. Crea un archivo .env en la raíz del proyecto (C:\\ortho-web3-project\\.env)")
            print("   2. Añade esta línea: DEEPSEEK_API_KEY=tu_clave_aquí")
            print("   3. Obtén tu API key gratis en: https://platform.deepseek.com/api_keys")
            print("   4. Reinicia la terminal después de crear/modificar .env")
            
            self.active = False
        else:
            self.active = True
            print(f"\n✅ DeepSeek API Key encontrada")
            print(f"   Primeros 8 caracteres: {self.api_key[:8]}...")
            print(f"   Longitud: {len(self.api_key)} caracteres")
            print("🎯 Servicio DeepSeek ACTIVADO")
        
        # Configurar URLs
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.3"))
        
        if self.active:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            print(f"\n⚙️  Configuración:")
            print(f"   Modelo: {self.model}")
            print(f"   Máx tokens: {self.max_tokens}")
            print(f"   Temperatura: {self.temperature}")
            print(f"   URL Base: {self.base_url}")
        
        # Estadísticas
        self.stats = {
            "total_calls": 0,
            "total_tokens": 0,
            "successful_calls": 0,
            "failed_calls": 0
        }
        
        # Directorio para logs
        self.logs_dir = Path("logs/deepseek")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        print("=" * 60 + "\n")
    
    def is_active(self) -> bool:
        """Verifica si el servicio está activo"""
        return self.active
    
    def analyze_dental_case(self, 
                          case_data: Dict, 
                          image_analysis: str = None) -> Dict:
        """
        Analiza un caso dental usando DeepSeek
        
        Args:
            case_data: Datos del caso dental
            image_analysis: Análisis previo de imágenes (opcional)
        
        Returns:
            Dict con análisis completo
        """
        if not self.active:
            return self._inactive_response()
        
        prompt = self._build_dental_analysis_prompt(case_data, image_analysis)
        
        return self._call_api(
            prompt=prompt,
            system_message="Eres un ortodoncista experto con 20 años de experiencia.",
            function_name="analyze_dental_case"
        )
    
    def generate_treatment_plan(self, 
                              diagnosis: Dict,
                              patient_info: Dict) -> Dict:
        """
        Genera un plan de tratamiento personalizado
        
        Args:
            diagnosis: Diagnóstico del paciente
            patient_info: Información del paciente
        
        Returns:
            Dict con plan de tratamiento
        """
        if not self.active:
            return self._inactive_response()
        
        prompt = f"""
        Basándote en el siguiente diagnóstico, genera un plan de tratamiento detallado:
        
        DIAGNÓSTICO:
        {json.dumps(diagnosis, indent=2)}
        
        INFORMACIÓN DEL PACIENTE:
        - Edad: {patient_info.get('age', 'N/A')}
        - Género: {patient_info.get('gender', 'N/A')}
        - Historial: {patient_info.get('medical_history', 'N/A')}
        
        Proporciona:
        1. Objetivos del tratamiento
        2. Fases del tratamiento
        3. Duración estimada
        4. Aparatología recomendada
        5. Citas de seguimiento
        6. Posibles complicaciones
        """
        
        return self._call_api(
            prompt=prompt,
            system_message="Eres un planificador de tratamientos de ortodoncia.",
            function_name="generate_treatment_plan"
        )
    
    def explain_to_patient(self, 
                         diagnosis: Dict,
                         patient_age: int,
                         language: str = "es") -> Dict:
        """
        Explica el diagnóstico en términos simples al paciente
        
        Args:
            diagnosis: Diagnóstico médico
            patient_age: Edad del paciente
            language: Idioma para la explicación
        
        Returns:
            Dict con explicación paciente-amigable
        """
        if not self.active:
            return self._inactive_response()
        
        complexity = "muy simple" if patient_age < 12 else "simple"
        
        prompt = f"""
        Explica este diagnóstico de ortodoncia en {language} para un paciente de {patient_age} años.
        Nivel de complejidad: {complexity}
        
        DIAGNÓSTICO:
        {json.dumps(diagnosis, indent=2)}
        
        La explicación debe incluir:
        1. Qué significa en términos simples
        2. Cómo afecta a su sonrisa y salud
        3. Qué podemos hacer para corregirlo
        4. Qué esperar durante el tratamiento
        
        Usa analogías apropiadas para la edad.
        """
        
        return self._call_api(
            prompt=prompt,
            system_message="Eres un comunicador médico experto en explicar conceptos complejos.",
            function_name="explain_to_patient"
        )
    
    def generate_medical_report(self,
                              case_data: Dict,
                              analysis_results: Dict,
                              dentist_info: Dict) -> Dict:
        """
        Genera un informe médico formal
        
        Args:
            case_data: Datos del caso
            analysis_results: Resultados del análisis
            dentist_info: Información del dentista
        
        Returns:
            Dict con informe médico completo
        """
        if not self.active:
            return self._inactive_response()
        
        prompt = f"""
        Genera un informe médico profesional basado en los siguientes datos:
        
        DATOS DEL PACIENTE:
        {json.dumps(case_data.get('patient_info', {}), indent=2)}
        
        ANÁLISIS REALIZADO:
        {json.dumps(analysis_results, indent=2)}
        
        DATOS CLÍNICOS:
        {json.dumps(case_data.get('clinical_data', {}), indent=2)}
        
        DENTISTA:
        {json.dumps(dentist_info, indent=2)}
        
        Formato del informe:
        1. Encabezado con datos del paciente y dentista
        2. Antecedentes médicos relevantes
        3. Hallazgos clínicos
        4. Diagnóstico
        5. Plan de tratamiento recomendado
        6. Pronóstico
        7. Observaciones
        8. Firma y fecha
        
        Usa formato médico profesional.
        """
        
        return self._call_api(
            prompt=prompt,
            system_message="Eres un redactor de informes médicos profesionales.",
            function_name="generate_medical_report",
            max_tokens=3000
        )
    
    def compare_treatment_options(self,
                                diagnosis: Dict,
                                options: List[Dict]) -> Dict:
        """
        Compara diferentes opciones de tratamiento
        
        Args:
            diagnosis: Diagnóstico del paciente
            options: Lista de opciones de tratamiento a comparar
        
        Returns:
            Dict con comparación detallada
        """
        if not self.active:
            return self._inactive_response()
        
        prompt = f"""
        Compara las siguientes opciones de tratamiento para este diagnóstico:
        
        DIAGNÓSTICO:
        {json.dumps(diagnosis, indent=2)}
        
        OPCIONES DE TRATAMIENTO:
        {json.dumps(options, indent=2)}
        
        Para cada opción, proporciona:
        1. Efectividad esperada
        2. Duración del tratamiento
        3. Costo estimado
        4. Inconvenientes
        5. Tasa de éxito
        6. Recomendación (alta/mediana/baja)
        
        Proporciona una recomendación final basada en la mejor opción.
        """
        
        return self._call_api(
            prompt=prompt,
            system_message="Eres un consultor de tratamientos de ortodoncia.",
            function_name="compare_treatment_options"
        )
    
    def _build_dental_analysis_prompt(self, case_data: Dict, image_analysis: str = None) -> str:
        """Construye prompt para análisis dental"""
        
        patient_info = case_data.get('patient_info', {})
        clinical_data = case_data.get('clinical_data', {})
        
        prompt = f"""
        Analiza el siguiente caso de ortodoncia:
        
        PACIENTE:
        - Edad: {patient_info.get('age', 'N/A')}
        - Género: {patient_info.get('gender', 'N/A')}
        - Motivo de consulta: {clinical_data.get('reason', 'N/A')}
        
        DATOS CLÍNICOS:
        - Clase esquelética: {clinical_data.get('skeletal_class', 'N/A')}
        - Overjet: {clinical_data.get('overjet', 'N/A')} mm
        - Overbite: {clinical_data.get('overbite', 'N/A')} mm
        - Apiñamiento: {clinical_data.get('crowding', 'N/A')}
        - Problemas específicos: {clinical_data.get('specific_issues', 'N/A')}
        """
        
        if image_analysis:
            prompt += f"\nANÁLISIS DE IMÁGENES:\n{image_analysis}\n"
        
        prompt += """
        Proporciona tu análisis en formato JSON con la siguiente estructura:
        {
            "diagnosis": "Diagnóstico principal",
            "severity": "leve/moderada/severa",
            "confidence": "alta/media/baja",
            "key_findings": ["hallazgo1", "hallazgo2", ...],
            "functional_impact": "Descripción del impacto funcional",
            "aesthetic_impact": "Descripción del impacto estético",
            "treatment_urgency": "alta/media/baja",
            "recommendations": ["recomendación1", "recomendación2", ...]
        }
        
        Sé preciso y conservador en el diagnóstico.
        """
        
        return prompt
    
    def _call_api(self, 
                 prompt: str, 
                 system_message: str,
                 function_name: str,
                 max_tokens: int = None) -> Dict:
        """Llamada genérica a la API de DeepSeek"""
        
        self.stats["total_calls"] += 1
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": self.temperature
            }
            
            print(f"\n📤 Enviando solicitud a DeepSeek ({function_name})...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            self._log_request(function_name, payload, response)
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                
                self.stats["successful_calls"] += 1
                self.stats["total_tokens"] += usage.get("total_tokens", 0)
                
                print(f"✅ Respuesta recibida ({usage.get('total_tokens', 0)} tokens)")
                
                # Intentar parsear JSON si está presente
                try:
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                        parsed_content = json.loads(json_str)
                    else:
                        # Buscar JSON directamente
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            parsed_content = json.loads(json_match.group())
                        else:
                            parsed_content = {"text": content}
                except json.JSONDecodeError as e:
                    print(f"⚠️  No se pudo parsear JSON: {e}")
                    parsed_content = {"raw_response": content}
                
                return {
                    "success": True,
                    "data": parsed_content,
                    "raw_response": content,
                    "usage": usage,
                    "function": function_name
                }
            else:
                self.stats["failed_calls"] += 1
                print(f"❌ Error {response.status_code}: {response.text[:100]}...")
                return {
                    "success": False,
                    "error": f"API Error {response.status_code}",
                    "details": response.text[:500],
                    "function": function_name
                }
                
        except requests.exceptions.Timeout:
            self.stats["failed_calls"] += 1
            error_msg = "Timeout: La solicitud tardó demasiado"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "function": function_name
            }
        except requests.exceptions.ConnectionError:
            self.stats["failed_calls"] += 1
            error_msg = "Connection error: No se pudo conectar a DeepSeek"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "function": function_name
            }
        except Exception as e:
            self.stats["failed_calls"] += 1
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "function": function_name
            }
    
    def _log_request(self, function_name: str, payload: Dict, response):
        """Registra la solicitud y respuesta"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "function": function_name,
            "request": {
                "model": payload["model"],
                "tokens_requested": payload["max_tokens"],
                "temperature": payload["temperature"]
            },
            "response": {
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
        }
        
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"Error al guardar log: {str(e)}")
    
    def _inactive_response(self) -> Dict:
        """Respuesta cuando el servicio no está activo"""
        return {
            "success": False,
            "error": "DeepSeek service is not active. Set DEEPSEEK_API_KEY in .env file",
            "data": None
        }
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del servicio"""
        free_quota = 100000  # Tokens gratis por mes
        tokens_used = self.stats["total_tokens"]
        
        return {
            **self.stats,
            "active": self.active,
            "tokens_remaining": max(0, free_quota - tokens_used),
            "quota_percentage": (tokens_used / free_quota) * 100 if free_quota > 0 else 0,
            "free_quota": free_quota
        }
    
    def test_connection(self) -> Dict:
        """Prueba la conexión con DeepSeek API"""
        if not self.active:
            return self._inactive_response()
        
        print("\n🧪 Probando conexión con DeepSeek API...")
        
        result = self._call_api(
            prompt="Responde con '✅ Conexión exitosa' si recibes este mensaje.",
            system_message="Eres un asistente de prueba.",
            function_name="test_connection",
            max_tokens=10
        )
        
        if result["success"]:
            print("✅ Conexión con DeepSeek API establecida correctamente")
        else:
            print(f"❌ Error en la conexión: {result.get('error')}")
        
        return result


# Singleton para uso global
deepseek_service = DeepSeekService()