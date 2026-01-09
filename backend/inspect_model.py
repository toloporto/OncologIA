"""
Script para inspeccionar la arquitectura del modelo
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import tensorflow as tf
    from tensorflow import keras
except ImportError:
    import keras

# Cargar modelo
model_path = 'ml-models/trained_models/real_ortho_model.h5'
print(f"Cargando modelo: {model_path}")
model = keras.models.load_model(model_path)

print("\n" + "="*60)
print("ARQUITECTURA DEL MODELO")
print("="*60)

# Mostrar resumen
model.summary()

print("\n" + "="*60)
print("CAPAS DEL MODELO")
print("="*60)

for i, layer in enumerate(model.layers):
    print(f"\n[{i}] {layer.name}")
    print(f"    Tipo: {type(layer).__name__}")
    print(f"    Trainable: {layer.trainable}")
    
    # Si es un modelo anidado, mostrar sus capas
    if hasattr(layer, 'layers'):
        print(f"    Sub-capas:")
        for j, sublayer in enumerate(layer.layers):
            print(f"      [{j}] {sublayer.name} ({type(sublayer).__name__})")

print("\n" + "="*60)
print("BUSCANDO CAPAS CONVOLUCIONALES")
print("="*60)

conv_layers = []
for layer in model.layers:
    if 'conv' in layer.name.lower():
        conv_layers.append(layer.name)
        print(f"✓ {layer.name}")
    
    # Buscar en sub-capas
    if hasattr(layer, 'layers'):
        for sublayer in layer.layers:
            if 'conv' in sublayer.name.lower():
                conv_layers.append(f"{layer.name}/{sublayer.name}")
                print(f"✓ {layer.name}/{sublayer.name}")

print(f"\nTotal capas conv encontradas: {len(conv_layers)}")
if conv_layers:
    print(f"Última capa conv: {conv_layers[-1]}")
