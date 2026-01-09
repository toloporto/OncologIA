"""
Servicio de Explicabilidad para OrthoWeb3
Genera visualizaciones Grad-CAM para explicar predicciones del modelo
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
import cv2
from typing import Optional, Dict
import logging
import base64
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)


class ExplainabilityService:
    """Servicio para generar explicaciones visuales de predicciones"""
  
    def __init__(self):
        self.model = None
        self.last_conv_layer_name = None
  
    def load_model(self, model_path: Optional[str] = None):
        """Cargar modelo entrenado buscando en rutas comunes"""
        import os
      
        # Lista de rutas potenciales (orden de preferencia)
        potential_paths = [
            model_path,
            'ml-models/trained_models/real_ortho_model.h5',
            'ml-models/models/ortho_efficientnetv2.h5',
            'best_ortho_model.h5',
            'ml-models/models/best_ortho_model.h5'
        ]
      
        # Limpiar None
        potential_paths = [p for p in potential_paths if p is not None]
      
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    logger.info(f"🔄 Intentando cargar modelo desde: {path}")
                    self.model = keras.models.load_model(path, compile=False)
                  
                    # IMPORTANTE: Hacer una predicción dummy para construir el grafo
                    dummy_input = np.zeros((1, 512, 512, 3), dtype=np.float32)
                    _ = self.model.predict(dummy_input, verbose=0)
                  
                    # Detectar última capa convolucional
                    self.last_conv_layer_name = self._find_last_conv_layer()
                    logger.info(f"✅ Modelo cargado desde {path}. Capa conv: {self.last_conv_layer_name}")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando {path}: {e}")
                    continue
      
        logger.error("❌ No se encontró ningún modelo válido para Grad-CAM")
        return False

    def set_model(self, model):
        """Establecer el modelo directamente (si ya está cargado)"""
        if model:
            self.model = model
            # No es necesario llamar a predict si el modelo ya está cargado y en uso
            if not self.last_conv_layer_name:
                self.last_conv_layer_name = self._find_last_conv_layer()
            return True
        return False
  
    def _find_last_conv_layer(self) -> str:
        """Encuentra la última capa convolucional del modelo"""
        # Para EfficientNet, la última capa conv suele ser 'top_conv'
        for layer in reversed(self.model.layers):
            if 'conv' in layer.name.lower():
                return layer.name
        return None
  
    def generate_gradcam(
        self,
        image: np.ndarray,
        class_idx: int = None
    ) -> Optional[np.ndarray]:
        """
        Genera mapa de calor Grad-CAM con soporte para múltiples arquitecturas
        """
        if self.model is None:
            logger.error("❌ Modelo no cargado")
            return None
      
        try:
            # 1. Asegurar que tenemos el nombre de la capa conv
            if not self.last_conv_layer_name:
                self.last_conv_layer_name = self._find_last_conv_layer()
          
            if not self.last_conv_layer_name:
                logger.error("❌ No se encontró capa convolucional")
                return None

            # 2. Crear modelo de gradientes (Enfoque robusto para Keras 3)
            try:
                # Usar los tensores de entrada y salida del modelo ya cargado
                # Esto maneja correctamente modelos complejos (Functional o Sequential)
                grad_model = keras.Model(
                    inputs=self.model.inputs,
                    outputs=[
                        self.model.get_layer(self.last_conv_layer_name).output,
                        self.model.output
                    ]
                )
                logger.info(f"✅ Sub-modelo de gradientes listo. Capa: {self.last_conv_layer_name}")
                
            except Exception as e:
                logger.error(f"❌ No se pudo crear el sub-modelo de gradientes: {e}")
                # Fallback final: Si falla la creación del modelo, no podemos generar Grad-CAM
                return None

            # 3. Preparar imagen
            img_array = np.expand_dims(image, axis=0).astype(np.float32)
            img_tensor = tf.constant(img_array)

            # 4. Calcular gradientes con GradientTape
            with tf.GradientTape(persistent=True) as tape:
                tape.watch(img_tensor)
                conv_outputs, predictions = grad_model(img_tensor, training=False)
                
                # Si predictions es una lista (modelos multi-head), tomamos el primero
                if isinstance(predictions, list):
                    predictions = predictions[0]
                
                if class_idx is None:
                    class_idx = tf.argmax(predictions[0])
                
                # Obtener score de la clase objetivo
                class_output = predictions[:, class_idx]

            # 5. Gradientes de la clase respecto a la última capa conv
            grads = tape.gradient(class_output, conv_outputs)
            del tape

            if grads is None:
                logger.error("❌ Los gradientes son None. La ruta de diferenciación está rota.")
                # Intentar inspeccionar por qué
                return None

            # Pooling de gradientes (importancia global de cada canal)
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

            # Ponderar canales del output por importancia
            output = conv_outputs[0]
            heatmap = output @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)

            # Relu y Normalización
            heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-10)
            heatmap_np = heatmap.numpy()
           
            # --- Robustez de forma para OpenCV ---
            if len(heatmap_np.shape) == 0:
                heatmap_np = np.array([[heatmap_np]], dtype=np.float32)
            elif len(heatmap_np.shape) == 1:
                heatmap_np = np.expand_dims(heatmap_np, axis=0)
           
            heatmap_np = np.nan_to_num(heatmap_np)
           
            logger.info(f"📊 Heatmap generado: shape={heatmap_np.shape}, max={np.max(heatmap_np)}")
            return heatmap_np
          
        except Exception as e:
            logger.error(f"❌ Error crítico en Grad-CAM: {e}")
            import traceback
            traceback.print_exc()
            return None
  
    def overlay_heatmap(
        self,
        original_image: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.4,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Superpone heatmap sobre imagen original
      
        Args:
            original_image: Imagen original (H, W, 3), valores 0-255
            heatmap: Mapa de calor (H', W'), valores 0-1
            alpha: Transparencia del heatmap (0-1)
            colormap: Mapa de colores OpenCV
          
        Returns:
            Imagen con overlay (H, W, 3)
        """
        try:
            if heatmap is None or original_image is None or heatmap.size == 0:
                return original_image

            # Asegurar que sea float32
            heatmap = heatmap.astype(np.float32)
            h, w = original_image.shape[:2]
           
            # Redimensionar heatmap al tamaño de la imagen original
            heatmap_resized = cv2.resize(heatmap, (w, h))
          
            # Convertir heatmap a uint8 y aplicar colormap
            heatmap_uint8 = np.uint8(255 * heatmap_resized)
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, colormap)
          
            # Convertir BGR a RGB (OpenCV usa BGR)
            heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
          
            # Asegurar que original_image esté en uint8
            if original_image.dtype != np.uint8:
                original_image = np.uint8(original_image * 255)
          
            # Superponer
            superimposed = cv2.addWeighted(original_image, 1 - alpha, heatmap_colored, alpha, 0)
          
            return superimposed
          
        except Exception as e:
            logger.error(f"❌ Error en overlay: {e}")
            return original_image
  
    def get_top_influential_regions(
        self,
        heatmap: np.ndarray,
        top_k: int = 3
    ) -> list:
        """
        Identifica las regiones más influyentes
      
        Args:
            heatmap: Mapa de calor (H, W)
            top_k: Número de regiones a retornar
          
        Returns:
            Lista de diccionarios con coordenadas y scores
        """
        try:
            # Umbral para considerar región "influyente"
            threshold = 0.7
          
            # Binarizar heatmap
            binary_map = (heatmap > threshold).astype(np.uint8)
          
            # Encontrar contornos
            contours, _ = cv2.findContours(binary_map, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
          
            # Calcular score de cada región
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                region_score = np.mean(heatmap[y:y+h, x:x+w])
              
                regions.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'score': float(region_score)
                })
          
            # Ordenar por score y retornar top_k
            regions.sort(key=lambda r: r['score'], reverse=True)
            return regions[:top_k]
          
        except Exception as e:
            logger.error(f"❌ Error identificando regiones: {e}")
            return []
  
    def encode_image_to_base64(self, image: np.ndarray) -> str:
        """Convierte imagen numpy a base64 para enviar al frontend"""
        try:
            # Convertir a PIL Image
            pil_img = Image.fromarray(image.astype(np.uint8))
          
            # Guardar en buffer
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
          
            # Codificar a base64
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
          
        except Exception as e:
            logger.error(f"❌ Error codificando imagen: {e}")
            return ""
  
    def explain_prediction(
        self,
        image: np.ndarray,
        class_idx: int = None
    ) -> Dict:
        """
        Genera explicación completa de una predicción
      
        Args:
            image: Imagen preprocesada (normalizada)
            class_idx: Clase a explicar
          
        Returns:
            Diccionario con heatmap, overlay y regiones influyentes
        """
        # Generar Grad-CAM
        heatmap = self.generate_gradcam(image, class_idx)
      
        if heatmap is None:
            return {'success': False, 'error': 'Failed to generate Grad-CAM'}
      
        # Desnormalizar imagen para overlay (0-1 -> 0-255)
        original_image = (image * 255).astype(np.uint8)
      
        # Crear overlay
        overlay = self.overlay_heatmap(original_image, heatmap)
      
        # Identificar regiones influyentes
        regions = self.get_top_influential_regions(heatmap)
       
        return {
            'success': True,
            'heatmap_base64': self.encode_image_to_base64(overlay),
            'influential_regions': regions,
            'heatmap_entropy': float(np.std(heatmap))  # Medida de dispersión
        }


# Instancia global
explainability_service = ExplainabilityService()
