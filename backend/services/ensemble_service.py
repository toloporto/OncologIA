"""
Servicio de Ensemble para OrthoWeb3
Combina múltiples modelos para mejorar precisión e identificar incertidumbre
"""

import logging
import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EnsembleService:
    """Gestiona un conjunto de modelos y combina sus predicciones"""

    def __init__(self):
        self.models = {}
        self.weights = {
            'backbone': 0.6,
            'secondary': 0.4
        }
        self.is_initialized = False

    def initialize_models(self, main_model=None):
        """Inicializa los modelos del ensemble"""
        try:
            if main_model:
                self.models['backbone'] = main_model
                logger.info("✅ Modelo principal inyectado al Ensemble")
            
            # Intentar cargar un segundo modelo para el ensemble real
            secondary_path = 'ml-models/trained_models/final_ortho_model.h5'
            if os.path.exists(secondary_path):
                logger.info(f"🔄 Cargando modelo secundario: {secondary_path}")
                self.models['secondary'] = keras.models.load_model(
                    secondary_path, 
                    compile=False
                )
                logger.info("✅ Modelo secundario cargado exitosamente")
            
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando Ensemble: {e}")
            return False

    def predict_with_uncertainty(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Produce una predicción combinada y un score de incertidumbre.
        
        El score de incertidumbre alto indica que los modelos no coinciden.
        """
        if not self.models:
            return None

        predictions = []
        
        # 1. Obtener predicciones de todos los modelos activos
        for name, model in self.models.items():
            try:
                # Comprobar si el modelo requiere redimensionado
                expected_shape = model.input_shape[1:3] if hasattr(model, 'input_shape') else (224, 224)
                current_shape = img_array.shape[1:3]
                
                if expected_shape != current_shape:
                    logger.info(f"🔄 Redimensionando para {name}: {current_shape} -> {expected_shape}")
                    # Usar tf.image.resize para mantener el grafo si es necesario
                    resized_img = tf.image.resize(img_array[0], expected_shape)
                    model_input = np.expand_dims(resized_img.numpy(), axis=0)
                else:
                    model_input = img_array

                pred = model.predict(model_input, verbose=0)
                
                # Manejar modelos multi-salida
                if isinstance(pred, list):
                    pred = pred[0]
                
                predictions.append(pred[0])
                logger.info(f"🔮 Predicción {name}: {pred[0]}")
            except Exception as e:
                logger.error(f"❌ Error en predicción de modelo {name}: {e}")
                continue

        # 2. Si solo hay un modelo, no hay "ensemble" real todavía
        if len(predictions) == 1:
            main_pred = predictions[0]
            return {
                'combined_prediction': main_pred.tolist(),
                'uncertainty': 0.0,
                'consensus': True,
                'individual_predictions': {'backbone': main_pred.tolist()}
            }

        # 3. Combinación ponderada (Weighted Average)
        # Por ahora simulamos con 2 modelos si solo hay uno real
        # (En una implementación real cargaríamos el segundo modelo .h5)
        
        avg_pred = np.mean(predictions, axis=0)
        
        # Calcular Incertidumbre (Desviación Típica entre modelos)
        # Si los modelos dan resultados muy distintos, std será alto.
        uncertainty = np.mean(np.std(predictions, axis=0))

        return {
            'combined_prediction': avg_pred.tolist(),
            'uncertainty': float(uncertainty),
            'consensus': bool(uncertainty < 0.15),
            'model_count': len(predictions)
        }

# Instancia global
ensemble_service = EnsembleService()
