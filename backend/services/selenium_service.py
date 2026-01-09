# backend/services/selenium_service_fixed.py
"""
Servicio Selenium para DeepSeek - VERSIÓN CORREGIDA
"""
import os
import json
import time
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

# Importaciones Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class SeleniumDeepSeekService:
    """Servicio para integrar DeepSeek via Selenium en OrthoWeb3"""
    
    def __init__(self):
        self.driver = None
        self.is_ready = False
        self.config = {
            "headless": True,  # Cambia a False para debug
            "base_url": "https://chat.deepseek.com",
            "timeout": 90,
            "user_data_dir": None
        }
        
        # Selectores optimizados para DeepSeek
        self.selectors = {
            "chat_input": "textarea, [contenteditable='true'], [role='textbox']",
            "response_container": "div, article, section, [class*='message'], [class*='prose'], [class*='markdown']",
            "typing_indicator": "[class*='typing'], [class*='cursor'], [class*='animate']"
        }
        
        logger.info("🦷 SeleniumDeepSeekService inicializado para OrthoWeb3")
    
    def start(self):
        """Inicia el servicio"""
        if self.is_ready:
            return True
        
        try:
            logger.info("🚀 Iniciando servicio Selenium...")
            
            chrome_options = Options()
            if self.config["headless"]:
                chrome_options.add_argument("--headless=new")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # User agent real
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Navegar a DeepSeek
            self.driver.get(self.config["base_url"])
            time.sleep(5)
            
            self.is_ready = True
            logger.info("✅ Servicio Selenium listo")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando servicio: {e}")
            return False
    
    def analyze_medical_case(self, case_data: Dict) -> Dict:
        """
        Analiza un caso médico (ortodoncia)
        
        Args:
            case_data: {
                "patient_info": {"age": 25, "gender": "female", ...},
                "clinical_data": {"reason": "...", "findings": "..."}
            }
        
        Returns:
            Dict con análisis
        """
        if not self.is_ready and not self.start():
            return self._error_response("Servicio no disponible")
        
        try:
            # Construir prompt médico
            prompt = self._build_medical_prompt(case_data)
            
            # Enviar mensaje
            self._send_message(prompt)
            
            # Esperar respuesta
            response = self._wait_for_response()
            
            if response:
                return {
                    "success": True,
                    "analysis": self._parse_medical_response(response),
                    "raw_response": response,
                    "response_time": time.time(),
                    "service": "deepseek_selenium"
                }
            else:
                return self._error_response("No se recibió respuesta")
                
        except Exception as e:
            logger.error(f"Error analizando caso: {e}")
            return self._error_response(str(e))
    
    def _send_message(self, message: str):
        """Envía mensaje al chat"""
        try:
            # Buscar textarea o campo de entrada
            textarea = self.driver.find_element(By.CSS_SELECTOR, self.selectors["chat_input"])
            textarea.clear()
            
            # Escribir carácter por carácter (más natural)
            for char in message:
                textarea.send_keys(char)
                time.sleep(0.01)
            
            time.sleep(0.5)
            textarea.send_keys(Keys.RETURN)
            logger.debug("Mensaje enviado")
            
        except Exception as e:
            raise Exception(f"Error enviando mensaje: {e}")
    
    def _wait_for_response(self) -> Optional[str]:
        """Espera y obtiene respuesta"""
        max_wait = self.config["timeout"]
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Buscar todos los elementos posibles
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            
            # Filtrar elementos visibles con texto
            visible_texts = []
            for elem in reversed(all_elements[-100:]):  # Últimos 100 elementos
                try:
                    if elem.is_displayed() and elem.text.strip():
                        text = elem.text.strip()
                        if len(text) > 50:  # Respuesta significativa
                            visible_texts.append(text)
                except:
                    continue
            
            # Si encontramos textos, tomar el más reciente/largo
            if visible_texts:
                # Ordenar por longitud (respuestas suelen ser más largas)
                visible_texts.sort(key=len, reverse=True)
                logger.debug(f"Respuesta encontrada ({len(visible_texts[0])} chars)")
                return visible_texts[0]
            
            # Verificar si está escribiendo
            try:
                typing = self.driver.find_elements(
                    By.CSS_SELECTOR, self.selectors["typing_indicator"]
                )
                if typing:
                    logger.debug("DeepSeek está escribiendo...")
            except:
                pass
            
            time.sleep(3)  # Esperar entre chequeos
        
        return None
    
    def _build_medical_prompt(self, case_data: Dict) -> str:
        """Construye prompt para análisis dental"""
        patient = case_data.get("patient_info", {})
        clinical = case_data.get("clinical_data", {})
        
        return f"""
        Como ortodoncista experto, analiza este caso:

        DATOS DEL PACIENTE:
        • Edad: {patient.get('age', 'N/A')}
        • Sexo: {patient.get('gender', 'N/A')}
        • Motivo: {clinical.get('reason', 'No especificado')}

        HALLAZGOS:
        • Clase esquelética: {clinical.get('skeletal_class', 'No evaluada')}
        • Overjet: {clinical.get('overjet', 'No medido')}
        • Overbite: {clinical.get('overbite', 'No medido')}
        • Apiñamiento: {clinical.get('crowding', 'No evaluado')}
        • Problemas: {clinical.get('specific_issues', 'Ninguno')}

        PROPORCIONA:
        1. Diagnóstico principal
        2. Severidad (leve/moderada/severa)
        3. Plan de tratamiento recomendado
        4. Duración estimada
        5. Recomendaciones específicas

        Formato profesional y claro.
        """
    
    def _parse_medical_response(self, response: str) -> Dict:
        """Parsea respuesta en estructura JSON"""
        return {
            "diagnosis": self._extract_by_keywords(response, ["diagnóstico", "diagnosis"]),
            "severity": self._extract_by_keywords(response, ["severidad", "gravedad", "severity"]),
            "treatment_plan": self._extract_by_keywords(response, ["tratamiento", "plan", "treatment"]),
            "recommendations": self._extract_by_keywords(response, ["recomendación", "sugerencia", "recommendation"]),
            "notes": "Análisis generado por DeepSeek AI"
        }
    
    def _extract_by_keywords(self, text: str, keywords: list) -> str:
        """Extrae sección basada en palabras clave"""
        text_lower = text.lower()
        for keyword in keywords:
            idx = text_lower.find(keyword.lower())
            if idx != -1:
                # Tomar 200 caracteres después de la palabra clave
                return text[idx:idx+200].strip()
        return text[:150].strip()  # Default: primeros 150 chars
    
    def _error_response(self, error_msg: str) -> Dict:
        """Respuesta de error estandarizada"""
        return {
            "success": False,
            "error": error_msg,
            "fallback_analysis": {
                "diagnosis": "Requiere evaluación clínica completa",
                "recommendations": [
                    "Consulta presencial con especialista",
                    "Documentación fotográfica completa",
                    "Evaluación con modelos de estudio"
                ]
            },
            "service": "deepseek_selenium",
            "timestamp": datetime.now().isoformat()
        }
    
    def stop(self):
        """Detiene el servicio"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Navegador cerrado")
            except Exception as e:
                logger.error(f"Error cerrando navegador: {e}")
        self.is_ready = False


# ✅ INSTANCIA GLOBAL EXPORTADA - ESTO ES LO QUE FALTA
selenium_service = SeleniumDeepSeekService()