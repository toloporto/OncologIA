# import tensorflow as tf # Lazy Import
import numpy as np
import cv2
import matplotlib.cm as cm

class GradCAM:
    def __init__(self, model, class_idx, layer_name=None):
        """
        Inicializa GradCAM.
        
        Args:
            model: Modelo TensorFlow/Keras.
            class_idx: Índice de la clase para la cual generar la explicación.
            layer_name: Nombre de la última capa convolucional. Si es None, se busca automáticamente.
        """
        self.model = model
        self.class_idx = class_idx
        self.layer_name = layer_name or self.find_target_layer()
        
        if self.layer_name is None:
            raise ValueError("No se pudo encontrar una capa convolucional objetivo.")

    def find_target_layer(self):
        """Busca la última capa convolucional 4D (batch, h, w, channels)."""
        # En Keras 3.x, buscamos capas Conv2D directamente
        for layer in reversed(self.model.layers):
            # Buscar capas convolucionales (Conv2D, DepthwiseConv2D, etc.)
            layer_type = type(layer).__name__
            if 'Conv' in layer_type and '2D' in layer_type:
                return layer.name
        return None

    def compute_heatmap(self, image, eps=1e-8):
        """
        Calcula el mapa de calor Grad-CAM.
        
        Args:
            image: Imagen preprocesada (batch_size, h, w, c).
            eps: Pequeño valor para evitar división por cero.
            
        Returns:
            heatmap: Mapa de calor (h, w) con valores entre 0 y 1.
        """
        # Lazy Import
        import tensorflow as tf
        
        # En Keras 3.x, necesitamos construir el modelo primero
        # Esto se hace automáticamente al pasarle una entrada
        if not self.model.built:
            self.model.build(input_shape=image.shape)
        
        # Para Keras 3.x, usamos un enfoque diferente: crear el modelo de gradientes
        # usando la entrada directamente en lugar de model.inputs
        try:
            # Intentar obtener la capa objetivo
            target_layer = self.model.get_layer(self.layer_name)
        except:
            raise ValueError(f"No se pudo encontrar la capa {self.layer_name}")
        
        # Crear un modelo funcional que va desde la entrada hasta la capa objetivo y la salida final
        # En lugar de usar model.inputs, creamos una nueva entrada
        inp = tf.keras.Input(shape=image.shape[1:])
        
        # Pasar la entrada a través del modelo para obtener las salidas
        x = inp
        for layer in self.model.layers:
            x = layer(x)
            if layer.name == self.layer_name:
                conv_output = x
        
        final_output = x
        
        # Crear el modelo de gradientes
        grad_model = tf.keras.Model(inputs=inp, outputs=[conv_output, final_output])

        with tf.GradientTape() as tape:
            # Castear la imagen a float32 para asegurar compatibilidad
            inputs = tf.cast(image, tf.float32)
            
            # Obtener las salidas
            (conv_outputs, predictions) = grad_model(inputs)
            
            # Obtener la pérdida (score) para la clase objetivo
            loss = predictions[:, self.class_idx]

        # Calcular gradientes de la salida respecto a los mapas de características
        grads = tape.gradient(loss, conv_outputs)

        # Global Average Pooling de los gradientes (pesos de importancia)
        guided_grads = tf.cast(conv_outputs > 0, "float32") * tf.cast(grads > 0, "float32") * grads
        weights = tf.reduce_mean(guided_grads, axis=(0, 1, 2))

        # Multiplicar mapas de características por pesos
        conv_outputs = conv_outputs[0]
        heatmap = tf.reduce_sum(tf.multiply(weights, conv_outputs), axis=-1)

        # Aplicar ReLU al heatmap (solo nos interesan las contribuciones positivas)
        heatmap = tf.maximum(heatmap, 0)
        
        # Normalizar
        if tf.reduce_max(heatmap) != 0:
            heatmap /= tf.reduce_max(heatmap)
            
        return heatmap.numpy()

    def overlay_heatmap(self, heatmap, original_image, alpha=0.4, colormap=cv2.COLORMAP_JET):
        """
        Superpone el mapa de calor en la imagen original.
        
        Args:
            heatmap: Mapa de calor generado por compute_heatmap.
            original_image: Imagen original (h, w, 3) en rango [0, 255] o [0, 1].
            alpha: Transparencia del heatmap.
            colormap: Mapa de color de OpenCV.
            
        Returns:
            superimposed_img: Imagen con el heatmap superpuesto.
        """
        # Redimensionar heatmap al tamaño de la imagen original
        heatmap = cv2.resize(heatmap, (original_image.shape[1], original_image.shape[0]))
        
        # Convertir heatmap a RGB (0-255)
        heatmap = np.uint8(255 * heatmap)
        heatmap = cv2.applyColorMap(heatmap, colormap)
        
        # Asegurar que la imagen original sea uint8 [0, 255]
        if original_image.dtype != np.uint8:
            original_image = np.uint8(255 * original_image)
            
        # Superponer
        superimposed_img = cv2.addWeighted(heatmap, alpha, original_image, 1 - alpha, 0)
        
        return superimposed_img
