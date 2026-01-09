import os
import logging
import torch
import whisper
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self, model_size: str = "base"):
        """
        Inicializa el servicio de voz cargando el modelo Whisper localmente.
         Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large'. 
                        'base' es un buen equilibrio velocidad/precisión para CPU.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_size = model_size
        self.model = None
        logger.info(f"🎤 VoiceService: Configurado para usar dispositivo '{self.device}'")

    def load_model(self):
        """Carga el modelo en memoria si no está cargado aún."""
        if self.model is None:
            logger.info(f"⏳ Cargando modelo Whisper '{self.model_size}' en memoria...")
            try:
                self.model = whisper.load_model(self.model_size, device=self.device)
                logger.info("✅ Modelo Whisper cargado correctamente.")
            except Exception as e:
                logger.error(f"❌ Error fatal cargando Whisper: {e}")
                raise e
    
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe un segmento de audio raw.
        Args:
            audio_data: Array de numpy con el audio (float32).
            sample_rate: Tasa de muestreo (Whisper espera 16000Hz).
        Returns:
            Texto transcrito.
        """
        self.load_model()
        
        # Whisper espera audio en float32 y 16k mono.
        # Si viene en otro formato, podría requerir pre-procesamiento, 
        # pero asumiremos que el capturador (micrófono) ya nos da el formato correcto.
        
        try:
            # Transcribir sin timestamps para mayor velocidad en frases cortas
            result = self.model.transcribe(
                audio_data, 
                fp16=(self.device == "cuda"), # Solo usar FP16 si hay GPU
                language="es" # Forzar español para mejorar precisión en este contexto
            )
            text = result.get("text", "").strip()
            return text
        except Exception as e:
            logger.error(f"⚠️ Error transcribiendo segmento: {e}")
            return ""

# Singleton instance para uso fácil
voice_service = VoiceService()
