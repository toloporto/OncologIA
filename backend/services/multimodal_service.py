
import logging
from PIL import Image
import io
import torch
import numpy as np

# Configuración de logging
logger = logging.getLogger(__name__)

class MultiModalService:
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cpu" # Default to CPU for safer deployment, can upgrade to 'cuda'
        self._is_loaded = False

    def is_available(self):
        return self._is_loaded

    def load_model(self):
        """
        Carga el modelo CLIP de HuggingFace de forma perezosa (Lazy Load).
        """
        if self._is_loaded:
            return

        try:
            logger.info("🔄 Cargando modelo Multimodal (CLIP)...")
            from transformers import CLIPProcessor, CLIPModel

            # Usamos un modelo 'base' de OpenAI, es un buon balance entre velocidad y precisión
            model_id = "openai/clip-vit-base-patch32"
            
            self.model = CLIPModel.from_pretrained(model_id)
            self.processor = CLIPProcessor.from_pretrained(model_id)
            
            self.model.to(self.device)
            self._is_loaded = True
            logger.info("✅ Modelo Multimodal (CLIP) cargado correctamente.")
            
        except ImportError:
            logger.error("❌ Error: Librerías 'transformers' o 'torch' no instaladas.")
            self._is_loaded = False
        except Exception as e:
            logger.error(f"❌ Error cargando CLIP: {e}")
            self._is_loaded = False

    def analyze_with_context(self, image_bytes, clinical_texts):
        """
        Analiza la imagen frente a una lista de textos clínicos (síntomas o diagnósticos posibles).
        Retorna la probabilidad de que la imagen coincida con cada texto.
        """
        if not self._is_loaded:
            self.load_model()
            if not self._is_loaded:
                raise RuntimeError("El modelo Multimodal no está disponible.")

        try:
            # 1. Preprocesar Imagen
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

            # 2. Preprocesar Entradas (Imagen + Texto)
            # Truncamos los textos si son muy largos y aseguramos padding
            inputs = self.processor(
                text=clinical_texts, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(self.device)

            # 3. Inferencia
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # 4. Calcular Probabilidades
            logits_per_image = outputs.logits_per_image  # similitud imagen-texto
            probs = logits_per_image.softmax(dim=1)  # softmax para obtener %

            # 5. Formatear Respuesta
            results = []
            probs_list = probs.cpu().numpy()[0]
            
            for text, prob in zip(clinical_texts, probs_list):
                results.append({
                    "description": text,
                    "confidence": float(prob),
                    "match_score": float(prob * 100)
                })
            
            # Ordenar por mayor coincidencia
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                "top_match": results[0],
                "all_matches": results
            }

        except Exception as e:
            logger.error(f"❌ Error en análisis multimodal: {e}")
            raise

# Instancia global (Singleton pattern)
multimodal_service = MultiModalService()
