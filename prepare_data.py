import re
from datasets import load_dataset
import pandas as pd
import json

def clean_text(text):
    """
    Normalización de texto clínica según la sección 2 de la estrategia.
    Elimina ruido de redes sociales y anonimiza.
    """
    # Eliminar menciones (@user)
    text = re.sub(r"@[A-Za-z0-9_]+", "", text)
    # Eliminar URLs
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
    # Eliminar hashtags (solo el símbolo)
    text = text.replace("#", "")
    # Normalizar espacios
    text = re.sub(r"\s+", " ", text).strip()
    return text

def map_labels(example, dataset_name):
    """
    Mapea etiquetas originales a categorías simplificadas para PsychoWebAI.
    Objetivo: Others, Joy, Sadness, Anger, Surprise, Disgust, Fear.
    """
    if dataset_name == 'emotion':
        # Labels: sadness (0), joy (1), love (2), anger (3), fear (4), surprise (5)
        mapping = {
            1: "joy", 
            2: "joy", # love -> joy para simplificar
            0: "sadness",
            3: "anger",
            4: "fear",
            5: "surprise"
        }
        example['label_name'] = mapping.get(example['label'], "others")
    
    elif dataset_name == 'go_emotions':
        # Go_emotions tiene 28 labels. Simplificamos las más críticas.
        # Solo mapeamos algunas para el ejemplo
        mapping = {
            20: "joy", # optimism
            15: "joy", # joy
            25: "sadness", # sadness
            2: "anger", # anger
            14: "fear", # fear
            26: "surprise", # surprise
            11: "disgust" # disgust
        }
        # go_emotions 'labels' es una lista
        main_label = example['labels'][0] if example['labels'] else -1
        example['label_name'] = mapping.get(main_label, "others")
        
    return example

def main():
    print("🚀 Iniciando preparación de datos...")

    # 1. Cargar Datasets
    print("📥 Descargando datasets desde HuggingFace...")
    ds_emotion = load_dataset("dair-ai/emotion")
    ds_go = load_dataset("go_emotions", "simplified")

    # 2. Limpiar y Mapear
    print("🧹 Limpiando texto y mapeando etiquetas...")
    
    # Procesar dair-ai/emotion
    processed_emotion = ds_emotion['train'].map(lambda x: {"text": clean_text(x['text'])})
    processed_emotion = processed_emotion.map(lambda x: map_labels(x, 'emotion'))

    # Procesar go_emotions
    processed_go = ds_go['train'].map(lambda x: {"text": clean_text(x['text'])})
    processed_go = processed_go.map(lambda x: map_labels(x, 'go_emotions'))

    # 3. Exportar para entrenamiento
    print("💾 Exportando a JSONL...")
    combined_df = pd.concat([
        pd.DataFrame(processed_emotion)[['text', 'label_name']],
        pd.DataFrame(processed_go)[['text', 'label_name']]
    ])
    
    output_file = "dataset_psycho_ready.jsonl"
    combined_df.to_json(output_file, orient='records', lines=True, force_ascii=False)
    
    print(f"✅ ¡Hecho! Dataset guardado en {output_file}")
    print(f"📊 Total de ejemplos: {len(combined_df)}")

if __name__ == "__main__":
    main()
