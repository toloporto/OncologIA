import tensorflow as tf
from tensorflow import keras
import os

def inspect_ortho_model():
    model_path = 'ml-models/trained_models/real_ortho_model.h5'
    if not os.path.exists(model_path):
        print(f"❌ Modelo no encontrado en {model_path}")
        return

    print(f"🔍 Inspeccionando modelo: {model_path}")
    try:
        model = keras.models.load_model(model_path, compile=False)
        print(f"✅ Tipo de modelo: {type(model)}")
        print(f"✅ Configuración de entrada: {model.input_shape}")
        
        print("\n📋 Listado de capas:")
        print("-" * 60)
        conv_layers = []
        for i, layer in enumerate(model.layers):
            is_conv = 'conv' in layer.name.lower()
            if is_conv:
                conv_layers.append(layer.name)
            print(f"{i:3d} | {layer.name:30s} | {type(layer).__name__:20s} {'🔥' if is_conv else ''}")
        print("-" * 60)
        
        if conv_layers:
            print(f"\n✅ Capas convolucionales encontradas ({len(conv_layers)}):")
            print(f"   Primera: {conv_layers[0]}")
            print(f"   Última:  {conv_layers[-1]}")
        else:
            print("\n❌ No se encontraron capas convolucionales.")

    except Exception as e:
        print(f"❌ Error inspeccionando: {e}")

if __name__ == "__main__":
    inspect_ortho_model()
