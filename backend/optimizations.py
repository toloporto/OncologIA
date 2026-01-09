import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import tensorflow as tf
import numpy as np

class PerformanceOptimizer:
    """Optimizaciones de performance para la API"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.model_cache = {}
        
    @lru_cache(maxsize=10)
    def load_model_cached(self, model_path):
        """Cache de modelos para carga rápida"""
        logging.info(f"🔄 Cargando modelo: {model_path}")
        return tf.keras.models.load_model(model_path)
    
    async def async_predict(self, model, image_data):
        """Predicción asíncrona para no bloquear el event loop"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool, 
            self._sync_predict, 
            model, image_data
        )
    
    def _sync_predict(self, model, image_data):
        """Predicción síncrona ejecutada en thread separado"""
        return model.predict(image_data, verbose=0)
    
    def optimize_model(self, model):
        """Optimizaciones para el modelo TensorFlow"""
        # Configurar para inferencia
        model.run_eagerly = False
        
        # Optimizaciones de TensorFlow
        tf.config.optimizer.set_jit(True)
        tf.config.threading.set_intra_op_parallelism_threads(2)
        tf.config.threading.set_inter_op_parallelism_threads(2)
        
        return model

# Configuración de logging optimizada
def setup_optimized_logging():
    """Configuración de logging para producción"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('backend/app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Reducir log level de librerías verbose
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('uvicorn').setLevel(logging.INFO)