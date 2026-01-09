import os
import joblib
import logging
import numpy as np

logger = logging.getLogger(__name__)

class EmotionMLService:
    def __init__(self):
        self.model = None
        self.model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models_ml', 'public_emotion_model.joblib'))
        # Actualizado a Etiquetas de Sentimiento (CardiffNLP Spanish)
        self.labels = {
            0: 'malestar (negativo)',
            1: 'neutro',
            2: 'bienestar (positivo)'
        }

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"✅ Modelo de Ánimo (Español) cargado correctmente.")
                return True
            except Exception as e:
                logger.error(f"❌ Error cargando modelo ML: {e}")
                return False
        return False

    def reload_model(self):
        """Fuerza la recarga del modelo desde disco (usado tras re-entrenamiento)."""
        logger.info("🔄 Recargando modelo de emociones...")
        self.model = None # Limpiar referencia anterior
        return self.load_model()

    def predict_emotion(self, text: str):
        if not self.model:
            if not self.load_model():
                return None

        try:
            prediction_idx = self.model.predict([text])[0]
            probability = np.max(self.model.predict_proba([text]))
            label = self.labels.get(prediction_idx, 'desconocido')
            
            # XAI: Generar Explicación
            explanation = self._explain_prediction(text, prediction_idx)

            return {
                "emotion": label, 
                "confidence": float(probability),
                "model": "Public Spanish Dataset (CardiffNLP)",
                "explanation": explanation
            }
        except Exception as e:
            logger.error(f"Error en predicción ML: {e}")
            return None

    def _explain_prediction(self, text, predicted_class_idx):
        """
        Explica por qué el modelo eligió esta clase usando los coeficientes de Regresión Logística.
        Retorna las palabras más influyentes encontradas en el texto.
        """
        try:
            # Acceder a los componentes del Pipeline
            tfidf = self.model.named_steps['tfidf']
            clf = self.model.named_steps['clf']
            
            # Obtener feature names (palabras) y sus coeficientes para la clase predicha
            feature_names = tfidf.get_feature_names_out()
            
            # En multiclass, coef_ es (n_classes, n_features). 
            # Si es binario, es (1, n_features) y se usa signo para distinguir.
            # Aquí asumimos multiclass (3 clases) basado en nuestro entrenamiento.
            if clf.coef_.shape[0] > 1:
                class_coefficients = clf.coef_[predicted_class_idx]
            else:
                # Caso binario (no debería ocurrir aquí con 3 clases, pero por robustez)
                class_coefficients = clf.coef_[0] if predicted_class_idx == 1 else -clf.coef_[0]

            # Analizar el texto de entrada
            # Transformamos solo este texto para ver qué features están presentes (tfidf > 0)
            text_vector = tfidf.transform([text])
            feature_index = text_vector.indices # Índices de palabras presentes en el texto
            
            explanation_data = []
            for idx in feature_index:
                word = feature_names[idx]
                weight = class_coefficients[idx]
                
                # Solo nos importa lo que SUMA a la predicción (peso positivo para esta clase)
                # Opcional: mostrar también lo que resta (peso negativo)
                if weight > 0.1: # Filtro de ruido
                    explanation_data.append({
                        "word": word,
                        "impact": float(weight) # Qué tanto "empujó" hacia esta clase
                    })
            
            # Ordenar por impacto descendente
            explanation_data.sort(key=lambda x: x['impact'], reverse=True)
            return explanation_data
            
        except Exception as e:
            logger.warning(f"⚠️ No se pudo generar explicación XAI: {e}")
            return []
        except Exception as e:
            logger.error(f"Error en predicción ML: {e}")
            return None

emotion_ml_service = EmotionMLService()
