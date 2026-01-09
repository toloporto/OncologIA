from typing import Dict, Any, Optional
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


class ModelNotAvailableError(Exception):
    """Excepción cuando el modelo no está disponible"""
    pass


class PredictionService:
    """Servicio para manejar predicciones de modelos ML"""
    
    def __init__(self, model_manager):
        self.model_manager = model_manager
    
    def predict_classification(
        self,
        image_bytes: bytes,
        use_ensemble: bool = False
    ) -> Dict[str, Any]:
        """
        Realiza predicción de clasificación dental.
        
        Args:
            image_bytes: Imagen en bytes
            use_ensemble: Si True, utiliza el ensemble de modelos
            
        Returns:
            Dict con class_pred, landmarks, severity y opcionalmente uncertainty
        """
        # Preprocesar
        processed = self._preprocess_image(image_bytes)
        
        if use_ensemble:
            logger.info("🧪 Ejecutando predicción con ENSEMBLE")
            from backend.services.ensemble_service import ensemble_service
            
            # Asegurar inicialización
            if not ensemble_service.is_initialized:
                main_model = self.model_manager.get_classification_model()
                ensemble_service.initialize_models(main_model)
            
            ensemble_result = ensemble_service.predict_with_uncertainty(processed)
            if ensemble_result:
                # Mapear resultado del ensemble al formato estándar
                result = self._parse_predictions(np.array([ensemble_result['combined_prediction']]))
                result['uncertainty'] = ensemble_result['uncertainty']
                result['consensus'] = ensemble_result['consensus']
                result['model_count'] = ensemble_result.get('model_count', 1)
                return result

        # Predicción normal con un solo modelo
        model = self.model_manager.get_classification_model()
        if model is None:
            logger.warning("⚠️ MODO SIMULACIÓN: Modelo no cargado. Devolviendo fake prediction.")
            fake_prediction = np.array([[0.8, 0.1, 0.05, 0.05, 0.0, 0.0]])
            return self._parse_predictions(fake_prediction)
        
        predictions = model.predict(processed, verbose=0)
        return self._parse_predictions(predictions)
    
    def predict_with_explanation(
        self,
        image_bytes: bytes,
        include_explanation: bool = True
    ) -> Dict[str, Any]:
        """
        Realiza predicción con explicación opcional (Grad-CAM).
        
        Args:
            image_bytes: Imagen en bytes
            include_explanation: Si True, genera Grad-CAM
        
        Returns:
            Dict con prediction y opcionalmente heatmap
        """
        # Predicción normal
        result = self.predict_classification(image_bytes)
        
        # Si no se solicita explicación, retornar solo predicción
        if not include_explanation:
            return result
        
        # Generar explicación con Grad-CAM
        try:
            from backend.services.explainability_service import explainability_service
            
            # Intentar usar el modelo ya cargado en ModelManager para evitar recargas
            if explainability_service.model is None:
                current_model = self.model_manager.get_classification_model()
                if current_model is not None:
                    logger.info("⚡ Usando modelo ya cargado en ModelManager para Grad-CAM")
                    explainability_service.set_model(current_model)
                else:
                    # Si no hay modelo cargado, intentar cargar por defecto
                    logger.info("🔍 Intentando carga perezosa del modelo para Grad-CAM")
                    if not explainability_service.load_model():
                        # Si falla todo, retornar sin explicación
                        result['explanation'] = None
                        return result
            
            # Preprocesar imagen
            processed = self._preprocess_image(image_bytes)
            
            # Obtener índice de clase predicha
            class_pred = result.get('class_pred')
            if class_pred is not None:
                class_idx = int(np.argmax(class_pred))
            else:
                class_idx = None
            
            # Generar explicación
            explanation = explainability_service.explain_prediction(
                processed[0],  # Remover dimensión de batch
                class_idx
            )
            
            result['explanation'] = explanation
            
        except Exception as e:
            import logging
            logging.error(f"❌ Error generando explicación: {e}")
            result['explanation'] = None
        
        return result

    
    def _preprocess_image(self, image_bytes: bytes, target_size=(512, 512)) -> np.ndarray:
        """Preprocesa imagen para el modelo (Usa 512x512 por defecto para el modelo principal)"""
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image = image.resize(target_size)
        image_array = np.array(image)
        image_array = image_array / 255.0  # Normalizar
        return np.expand_dims(image_array, axis=0)
    
    def _parse_predictions(self, predictions) -> Dict[str, Any]:
        """Parsea las predicciones del modelo"""
        if isinstance(predictions, list):
            return {
                'class_pred': predictions[0],
                'landmarks': predictions[1] if len(predictions) > 1 else None,
                'severity': predictions[2] if len(predictions) > 2 else None
            }
        else:
            return {
                'class_pred': predictions,
                'landmarks': None,
                'severity': None
            }
