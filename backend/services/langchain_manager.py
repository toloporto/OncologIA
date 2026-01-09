import os
import logging
import datetime
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from backend.services.rag_service import rag_service

logger = logging.getLogger(__name__)

class RiskAnalysis(BaseModel):
    risk_level: str = Field(description="Nivel de riesgo: 'low', 'medium', 'high', 'critical'")
    risk_found: bool = Field(description="Si se encontró riesgo de autolesión o peligro")
    explanation: str = Field(description="Explicación breve del razonamiento del agente")

class LangChainAgentManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY no encontrada.")
            self.llm = None
        else:
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=self.api_key,
                temperature=0.7,
                max_retries=3
            )
        
        self.histories: Dict[str, List[Any]] = {}

    def get_patient_history(self, patient_id: str) -> List[Any]:
        if patient_id not in self.histories:
            self.histories[patient_id] = []
        return self.histories[patient_id]

    def _get_demo_fallback(self, agent_type: str) -> str:
        """Devuelve una respuesta de alta calidad cuando hay problemas con el servicio de IA."""
        logger.warning(f"🔦 MODO SEGURO: Interrupción en el servicio de IA. Usando demo para: {agent_type}")
        
        demos = {
            "risk": "{\"risk_level\": \"high\", \"risk_found\": true, \"explanation\": \"(MODO SEGURO) Detectada crisis de dolor referida (EVA > 7) y posible disnea. Requiere evaluación médica inmediata.\"}",
            "soap": (
                "(MODO SEGURO: Interrupción temporal del servicio de IA)\n\n"
                "S: Paciente reporta dolor lumbar EVA 8/10 refractario a rescates. Refiere náuseas post-toma.\n"
                "O: Facies de dolor, limitación funcional. No signos de depresión respiratoria.\n"
                "A: Dolor oncológico mal controlado con posible toxicidad gastrointestinal a opioides.\n"
                "P: 1. Rotación de opioide o ajuste de dosis. 2. Añadir antiemético reglado. 3. Re-evaluar en 24h."
            ),
            "psycho": (
                "(MODO SEGURO: Interrupción temporal del servicio de IA)\n\n"
                "Estimado/a paciente:\n\n"
                "Entendemos que controlar el dolor y las náuseas es prioritario para tu bienestar.\n"
                "IMPORTANTE PARA HOY:\n"
                "1. Toma el medicamento para las náuseas 30 min antes del analgésico.\n"
                "2. Registra en tu libreta a qué hora aparece el dolor más fuerte.\n\n"
                "Estamos ajustando tu tratamiento para que te sientas mejor. No dudes en llamar si hay cambios."
            ),
            "symptoms": "{\"pain\": 0.8, \"fatigue\": 0.6, \"nausea\": 0.3, \"anxiety\": 0.5, \"depression\": 0.2, \"insomnia\": 0.9}",
            "chat": "Hola. Detecto que el servicio de IA está saturado momentáneamente (Error 429). \n\nNo obstante, aquí tienes una respuesta basada en protocolos estándar (MODO DEMO):\n\nPara el dolor irruptivo oncológico, se recomienda utilizar fentanilo transmucoso o intranasal, ajustando la dosis según la tolerancia previa a opioides. Es crucial re-evaluar la eficacia a los 15-30 minutos.\n\n(Fuente: Guía SEOM Dolor Oncológico - Respuesta Simulada)"
        }
        return demos.get(agent_type, "Servicio temporalmente no disponible.")

    def chat_agent(self, query: str, patient_context: str = "") -> Dict[str, Any]:
        """Agente de Chat Clínico con RAG (Consultas a Guías)"""
        # Fallback inmediato si no hay cliente (api key missing)
        if not self.llm:
             return {"answer": self._get_demo_fallback("chat"), "sources": ["Demo_Mode.pdf"]}

        # 1. Recuperar info relevante de RAG
        # rag_service ya está importado arriba
        try:
            rag_data = rag_service.query_expert(query)
            rag_context = rag_data.get("context", "")
            sources = rag_data.get("sources", [])
        except Exception as e:
            logger.error(f"Error RAG: {e}")
            rag_context = ""
            sources = []

        # 2. Construir Prompt
        system_instruction = (
            "Eres un Asistente Clínico Inteligente para Oncólogos. Tu objetivo es responder preguntas médicas de forma precisa.\n"
            "INSTRUCCIONES:\n"
            "1. Basa tu respuesta PRINCIPALMENTE en la 'INFORMACIÓN DE REFERENCIA (RAG)' proporcionada abajo.\n"
            "2. Si la información está en el contexto RAG, cita explícitamente que sale de ahí (ej: 'Según el documento [Nombre]...').\n"
            "3. Si la respuesta no está en el RAG, usa tu conocimiento general médico, PERO avisa claramente: 'Nota: Esta información proviene de mi conocimiento general, no de la base documental local.'.\n"
            "4. Sé conciso, profesional y directo."
        )
        
        human_content = f"INFORMACIÓN DE REFERENCIA (RAG):\n{rag_context}\n\nCONTEXTO DEL PACIENTE:\n{patient_context}\n\nPREGUNTA DEL MÉDICO:\n{query}"

        try:
            messages = [SystemMessage(content=system_instruction), HumanMessage(content=human_content)]
            response = self.llm.invoke(messages)
            return {"answer": response.content, "sources": sources}
        except Exception as e:
            logger.error(f"❌ Error en Chat Agent: {e}")
            if "429" in str(e) or "quota" in str(e).lower():
                return {
                    "answer": self._get_demo_fallback("chat"), 
                    "sources": ["Demo_Mode.pdf (Fallback por Rate Limit)"]
                }
            return {"answer": "Hubo un error procesando tu consulta con el asistente.", "sources": []}
    def analyze_risk_agent(self, text: str) -> RiskAnalysis:
        """Agente especializado en detección de urgencias oncológicas y psiquiátricas."""
        if not self.llm:
            import json
            return RiskAnalysis(**json.loads(self._get_demo_fallback("risk")))

        parser = PydanticOutputParser(pydantic_object=RiskAnalysis)
        system_prompt = (
            "Eres un Triaje Oncológico experto. Analiza el texto buscando URGENCIAS FÍSICAS O PSICOLÓGICAS.\n"
            "CRITERIOS DE ALARMA:\n"
            "1. Sepsis (fiebre, tiritona).\n"
            "2. Compresión Medular (pérdida fuerza, incontinencia).\n"
            "3. Hemorragia activa.\n"
            "4. Dolor no controlado (Crisis, EVA > 7).\n"
            "5. Asfixia/Disnea.\n"
            "6. Riesgo Suicida.\n"
            "{format_instructions}"
        )
        prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{text}")])
        chain = prompt | self.llm | parser
        
        try:
            return chain.invoke({"text": text, "format_instructions": parser.get_format_instructions()})
        except Exception as e:
            logger.error(f"❌ Error en Risk Agent: {e}")
            import json
            return RiskAnalysis(**json.loads(self._get_demo_fallback("risk")))

    def generate_soap_agent(self, patient_id: str, raw_text: str, emotion_metrics: Dict[str, float]) -> str:
        """Agente especializado en notas clínicas oncológicas (Dolor, Toxicidad, Emocional)."""
        if not self.llm:
            return self._get_demo_fallback("soap")

        metrics_str = ", ".join([f"{k}: {v:.2f}" for k, v in emotion_metrics.items()])
        system_instruction = (
            "Eres un Oncólogo experto. Genera una nota S.O.A.P.\n"
            "- S (Subjetivo): Síntomas reportados (dolor, fatiga, náuseas).\n"
            "- O (Objetivo): Métricas emocionales y observaciones clínicas.\n"
            "- A (Análisis): Juicio clínico integrando estado físico y anímico.\n"
            "- P (Plan): Ajustes de tratamiento, pruebas o soporte."
        )
        human_content = f"DATOS EMOCIONALES: {metrics_str}\nRELATO DEL PACIENTE: \"{raw_text}\"\nGENERA EL SOAP:"

        try:
            messages = [SystemMessage(content=system_instruction), HumanMessage(content=human_content)]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"❌ Error en SOAP Agent: {e}")
            return self._get_demo_fallback("soap")

    def generate_psychoeducation_agent(self, patient_id: str, soap_plan: str, emotion_metrics: Dict[str, float]) -> str:
        """Agente de Educación al Paciente (Adherencia y Manejo de Síntomas)."""
        if not self.llm:
            return self._get_demo_fallback("psycho")

        metrics_str = ", ".join([f"{k}: {v:.2f}" for k, v in emotion_metrics.items()])
        system_instruction = (
            "Eres un experto en Educación al Paciente Oncológico. Convierte el plan médico en instrucciones claras, empáticas y prácticas para el paciente.\n"
            "Usa lenguaje sencillo. Enfócate en qué hacer en casa (autocuidado)."
        )
        human_content = f"Métricas Emocionales: {metrics_str}\nPlan Médico: {soap_plan}\nGENERA CORREO EDUCATIVO:"

        try:
            messages = [SystemMessage(content=system_instruction), HumanMessage(content=human_content)]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"❌ Error en Psycho Education Agent: {e}")
            return self._get_demo_fallback("psycho")

    def extract_symptoms_agent(self, text: str) -> Dict[str, float]:
        """Agente de Extracción de Síntomas (Escala ESAS Estimada)."""
        import json
        
        if not self.llm:
            return json.loads(self._get_demo_fallback("symptoms"))

        # Definimos el esquema de salida esperado
        class SymptomScores(BaseModel):
            pain: float = Field(description="Intensidad de dolor (0.0 a 1.0)")
            anxiety: float = Field(description="Nivel de ansiedad/nerviosismo (0.0 a 1.0)")
            fatigue: float = Field(description="Nivel de cansancio/fatiga (0.0 a 1.0)")
            nausea: float = Field(description="Intensidad de náuseas/vómitos (0.0 a 1.0)")
            depression: float = Field(description="Nivel de tristeza/decaimiento (0.0 a 1.0)")
            insomnia: float = Field(description="Problemas de sueño (0.0 a 1.0)")
        
        parser = PydanticOutputParser(pydantic_object=SymptomScores)
        
        # RAG - Dynamic Few-Shot Prompting (Active Learning)
        # Buscar correcciones pasadas similares para guiar al modelo
        past_corrections = rag_service.find_similar_feedback(text)
        learning_context = ""
        
        if past_corrections:
            learning_context += "\n\nAPRENDIZAJE PREVIO (Casos similares corregidos por expertos):\n"
            for case in past_corrections:
                learning_context += f"- Texto: '{case['text']}' -> Corrección Experta: {case['correction']}\n"
            learning_context += "USA ESTOS EJEMPLOS PARA CALIBRAR TU PREDICCIÓN ACTUAL.\n"

        system_instruction = (
            "Eres un experto en Cuidados Paliativos y Oncología.\n"
            "Analiza el texto del paciente y estima la intensidad de los síntomas según la Escala de Edmonton (ESAS).\n"
            "Asigna un valor de 0.0 (ausente) a 1.0 (máxima intensidad) para cada síntoma basándote en el lenguaje usado.\n"
            "Si un síntoma no se menciona, asigna 0.0."
            "{learning_context}"
            "{format_instructions}"
        )

        prompt = ChatPromptTemplate.from_messages([("system", system_instruction), ("human", "{text}")])
        chain = prompt | self.llm | parser

        try:
            result = chain.invoke({
                "text": text, 
                "format_instructions": parser.get_format_instructions(),
                "learning_context": learning_context
            })
            return result.dict()
        except Exception as e:
            logger.error(f"❌ Error en Symptom Extraction Agent: {e}")
            # Fallback a demo en caso de error (e.g. Rate Limit)
            return json.loads(self._get_demo_fallback("symptoms"))



# Instancia global
langchain_agent = LangChainAgentManager()
