
import os
import json
import logging

logger = logging.getLogger(__name__)

FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'feedback_data.json')

def infer_label_from_symptoms(symptoms):
    """
    Deduce la etiqueta de sentimiento (0, 1, 2) basándose en la gravedad de los síntomas corregidos.
    
    Reglas Heurísticas:
    - Si algún síntoma negativo (dolor, ansiedad, etc.) > 0.4 -> MALESTAR (0)
    - Si todos los síntomas son muy bajos (< 0.1) -> BIENESTAR (2)
    - En caso contrario -> NEUTRO (1)
    """
    # Lista de claves que indican malestar
    negative_keys = ["pain", "anxiety", "fatigue", "nausea", "depression", "insomnia", "shortness_of_breath"]
    
    max_severity = 0.0
    for k, v in symptoms.items():
        if k in negative_keys and isinstance(v, (int, float)):
            if v > max_severity:
                max_severity = v
    
    if max_severity > 0.4:
        return 0 # MALESTAR
    elif max_severity < 0.15:
        return 2 # BIENESTAR
    else:
        return 1 # NEUTRO

def save_feedback(text, corrected_symptoms):
    """
    Guarda el texto y la etiqueta inferida en un dataset JSON.
    """
    label = infer_label_from_symptoms(corrected_symptoms)
    
    entry = {
        "text": text,
        "label": label,
        "source": "doctor_feedback"
    }
    
    data = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
    
    # Evitar duplicados exactos
    if not any(d['text'] == text for d in data):
        data.append(entry)
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Feedback guardado para re-entrenamiento. Etiqueta inferida: {label}")
        return True
    return False

def load_feedback_data():
    """
    Carga los datos de feedback para ser usados en el entrenamiento.
    Retorna X (textos), y (labels).
    """
    if not os.path.exists(FEEDBACK_FILE):
        return [], []
        
    try:
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        X = [d['text'] for d in data]
        y = [d['label'] for d in data]
        logger.info(f"📚 Cargados {len(X)} ejemplos de feedback médico.")
        return X, y
    except Exception as e:
        logger.error(f"Error cargando feedback: {e}")
        return [], []
