
import os
import joblib
import numpy as np
import logging
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SENTIMENT_LABELS = {
    0: 'MALESTAR (Negativo)',
    1: 'NEUTRO',
    2: 'BIENESTAR (Positivo)'
}

def get_evaluation_data():
    """
    Dataset de PRUEBA separado (No usado en entrenamiento)
    para evaluar la capacidad de generalización.
    """
    X_test = [
        # Negativos (Malestar) - Casos complejos
        "Siento que no puedo más con esto",
        "El dolor es constante y no me deja dormir",
        "Tengo miedo de los efectos secundarios",
        "Me siento muy sola en el hospital",
        "Estoy furiosa porque el tratamiento se retrasó",
        "No tengo apetito y todo me da asco",
        "Siento una presión en el pecho horrible",
        
        # Neutros
        "La enfermera vino a las 3",
        "Tengo cita el lunes que viene",
        "Me recetaron paracetamol",
        "El doctor revisó mis análisis",
        "Estoy esperando en la sala",
        "Hablé con la secretaria",
        "Llené el formulario de ingreso",

        # Positivos (Bienestar)
        "Hoy pude comer sin vomitar",
        "Me siento mucho mejor que ayer",
        "Gracias a mi familia por el apoyo",
        "Tengo fe en que voy a salir de esta",
        "El dolor ha disminuido bastante",
        "Disfruté la visita de mis nietos",
        "Me siento tranquila y en paz"
    ]
    
    # Etiquetas reales (Ground Truth)
    y_test = [0]*7 + [1]*7 + [2]*7
    
    return X_test, y_test

def evaluate():
    print("\n" + "="*60)
    print("📊 REPORTE DE EVALUACIÓN DE MODELO (OncologIA)")
    print("="*60 + "\n")
    
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models_ml', 'public_emotion_model.joblib'))
    
    if not os.path.exists(model_path):
        logger.error(f"❌ No se encontró el modelo en: {model_path}")
        return

    try:
        model = joblib.load(model_path)
        logger.info(f"✅ Modelo cargado correctamente.")
    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        return

    # Obtener datos de prueba
    X_test, y_test = get_evaluation_data()
    
    # Predecir
    logger.info(f"🧪 Evaluando con {len(X_test)} casos clínicos nuevos...\n")
    y_pred = model.predict(X_test)
    
    # Métricas
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"🎯 EXACTITUD GLOBAL (Accuracy): {accuracy:.2%}\n")
    print("-" * 60)
    print("📈 DETALLE POR CLASE:")
    
    target_names = [SENTIMENT_LABELS[0], SENTIMENT_LABELS[1], SENTIMENT_LABELS[2]]
    print(classification_report(y_test, y_pred, target_names=target_names))
    
    print("-" * 60)
    print("🧩 MATRIZ DE CONFUSIÓN (Real vs Predicho):")
    cm = confusion_matrix(y_test, y_pred)
    
    print(f"{'':<20} | Pred: NEG | Pred: NEU | Pred: POS |")
    print("-" * 60)
    for i, label in enumerate(target_names):
        print(f"Real: {label.split(' ')[0]:<14} | {cm[i][0]:^9} | {cm[i][1]:^9} | {cm[i][2]:^9} |")
    print("-" * 60)
    
    # Análisis de errores
    if accuracy < 1.0:
        print("\n🔍 ANÁLISIS DE ERRORES (¿Dónde falló?):")
        for i, (real, pred, text) in enumerate(zip(y_test, y_pred, X_test)):
            if real != pred:
                print(f"   ❌ '{text}'")
                print(f"      Era: {SENTIMENT_LABELS[real]} -> Predijo: {SENTIMENT_LABELS[pred]}")

if __name__ == "__main__":
    evaluate()
