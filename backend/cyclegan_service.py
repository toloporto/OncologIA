"""
Servicio de CycleGAN para simulación de tratamiento ortodóntico
"""

# import tensorflow as tf # Lazy Import
# from tensorflow import keras # Lazy Import

import numpy as np
import cv2
import os
from pathlib import Path
import logging
import gc

logger = logging.getLogger(__name__)

class CycleGANService:
    def __init__(self, model_path=None):
        """
        Inicializa el servicio de CycleGAN
        
        Args:
            model_path: Ruta al modelo generador (A->B)
        """
        if model_path is None:
            # Ruta por defecto
            base_dir = Path(__file__).parent.parent
            model_path = base_dir / "ml-models" / "trained_models" / "cyclegan" / "generator_A_to_B.h5"
        
        self.model_path = str(model_path)
        self.generator = None
        self.img_size = (256, 256)
        # self.load_model() # REMOVED for Lazy Loading
    
    def load_model(self):
        """Carga el modelo generador"""
        try:
            # Lazy Import
            try:
                from tensorflow import keras
            except ImportError:
                import keras

            if not os.path.exists(self.model_path):
                logger.warning(f"Modelo CycleGAN no encontrado en: {self.model_path}")
                return False
            
            logger.info(f"Cargando modelo CycleGAN desde: {self.model_path}")
            self.generator = keras.models.load_model(self.model_path, compile=False)
            logger.info("✅ Modelo CycleGAN cargado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar modelo CycleGAN: {e}")
            self.generator = None
            return False
    
    def is_available(self):
        """Verifica si el modelo está disponible"""
        if self.generator is None:
             # Intentar cargar si no está cargado, pero sin forzar error si falla
             # Para is_available es mejor solo chequear si existe el archivo
             return os.path.exists(self.model_path)
        return self.generator is not None

    def _ensure_model_loaded(self):
        """Garantiza que el modelo esté cargado antes de usarlo"""
        if self.generator is None:
            logger.info("⏳ Detectada primera petición: Cargando modelo CycleGAN...")
            self.load_model()
            if self.generator is None:
                raise RuntimeError("No se pudo cargar el modelo CycleGAN")
    
    def preprocess_image(self, image_bytes):
        """
        Preprocesa una imagen para el generador.
        Valida que la imagen tenga el formato y dimensiones adecuadas.
        
        Args:
            image_bytes: Bytes de la imagen
            
        Returns:
            Imagen preprocesada como tensor
            
        Raises:
            ValueError: Si la imagen no puede ser decodificada, no es una imagen a color (RGB) 
                        o es demasiado pequeña.
        """
        try:
            # 1. Decodificar imagen
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 2. Validación básica
            if image is None:
                raise ValueError("No se pudo decodificar la imagen. El formato podría ser inválido o estar corrupto.")
            
            # 3. Validación de formato (debe ser color)
            if len(image.shape) != 3 or image.shape[2] != 3:
                raise ValueError(f"El formato de la imagen no es válido. Se esperaba una imagen a color (RGB con 3 canales), pero se recibió una con shape: {image.shape}")

            # 4. Validación de dimensiones mínimas
            min_height, min_width = 64, 64
            if image.shape[0] < min_height or image.shape[1] < min_width:
                 raise ValueError(f"La imagen es demasiado pequeña ({image.shape[0]}x{image.shape[1]}). Se requiere un tamaño mínimo de {min_height}x{min_width} píxeles.")

            # 5. Preprocesamiento
            # Convertir BGR a RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Redimensionar
            image = cv2.resize(image, self.img_size)
            
            # Normalizar a [-1, 1]
            image = (image.astype(np.float32) / 127.5) - 1.0
            
            # Añadir dimensión de batch
            return np.expand_dims(image, axis=0)
            
        except Exception as e:
            logger.error(f"Error al preprocesar imagen: {e}")
            raise
    
    def postprocess_image(self, generated_image):
        """
        Convierte la salida del generador a imagen visualizable
        
        Args:
            generated_image: Salida del generador
            
        Returns:
            Bytes de la imagen en formato JPEG
        """
        try:
            # Desnormalizar de [-1, 1] a [0, 255]
            image = (generated_image[0] + 1.0) * 127.5
            image = np.clip(image, 0, 255).astype(np.uint8)
            
            # Convertir RGB a BGR para OpenCV
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Codificar a JPEG
            success, encoded_image = cv2.imencode('.jpg', image)
            
            if not success:
                raise ValueError("No se pudo codificar la imagen")
            
            return encoded_image.tobytes()
            
        except Exception as e:
            logger.error(f"Error al postprocesar imagen: {e}")
            raise

    def warm_up(self):
        """
        Calienta el modelo cargándolo y procesando una imagen de prueba.
        """
        try:
            logger.info("🔥 Iniciando calentamiento del servicio CycleGAN...")

            # 1. Asegurarse de que el modelo está cargado
            self._ensure_model_loaded()
            if not self.is_available():
                logger.warning("El calentamiento no se pudo completar: el modelo no está disponible.")
                return

            # 2. Crear una imagen "fantasma" (negra)
            dummy_image_np = np.zeros((self.img_size[0], self.img_size[1], 3), dtype=np.uint8)

            # 3. Codificarla como si viniera de una petición
            success, encoded_image = cv2.imencode('.jpg', dummy_image_np)
            if not success:
                logger.error("Error durante el calentamiento: no se pudo codificar la imagen fantasma.")
                return
            
            image_bytes = encoded_image.tobytes()

            # 4. Procesarla para calentar el pipeline completo
            logger.info("Procesando imagen fantasma para calentar el pipeline...")
            self.generate_treatment_simulation(image_bytes)

            logger.info("✅ Servicio CycleGAN calentado y listo.")

        except Exception as e:
            logger.error(f"Ocurrió un error durante el calentamiento del servicio CycleGAN: {e}")
            # No relanzamos la excepción para no detener el arranque del servidor
    
    def generate_treatment_simulation(self, image_bytes):
        """
        Genera una simulación de tratamiento ortodóntico
        
        Args:
            image_bytes: Bytes de la imagen original
            
        Returns:
            Bytes de la imagen transformada
        """
        # Lazy Load Check
        self._ensure_model_loaded()

        if not self.is_available():
            raise RuntimeError("Modelo CycleGAN no disponible")
        
        try:
            # Preprocesar
            input_image = self.preprocess_image(image_bytes)
            
            # Generar transformación
            logger.info("Generando simulación de tratamiento...")
            generated = self.generator.predict(input_image, verbose=0)
            
            # Postprocesar
            output_bytes = self.postprocess_image(generated)

            # Limpieza explícita de memoria
            del input_image
            del generated
            gc.collect()
            
            logger.info("✅ Simulación generada correctamente")
            return output_bytes
            
        except Exception as e:
            logger.error(f"Error al generar simulación: {e}")
            raise

# Instancia global del servicio
cyclegan_service = CycleGANService()
