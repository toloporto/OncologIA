import os
import sys
import tensorflow as tf
import numpy as np

# Configurar rutas absolutas
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_DIR = os.path.join(BASE_DIR, 'ml-models', 'trained_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'real_ortho_model.h5')
SEG_PATH = os.path.join(MODEL_DIR, 'unet_dental_model.h5')

print(f"Python Version: {sys.version}")
print(f"TensorFlow Version: {tf.__version__}")
print(f"Ruta Base: {BASE_DIR}")
print("-" * 50)

def check_file(path, name):
    if os.path.exists(path):
        size = os.path.getsize(path) / (1024 * 1024)
        print(f"✅ Archivo {name} encontrado: {path}")
        print(f"   Tamaño: {size:.2f} MB")
        return True
    else:
        print(f"❌ Archivo {name} NO encontrado en: {path}")
        return False

def load_test_model(path, name):
    print(f"🔄 Intentando cargar {name}...")
    try:
        model = tf.keras.models.load_model(path, compile=False)
        print(f"✅ {name} cargado EXITOSAMENTE")
        return True
    except Exception as e:
        print(f"❌ Error cargando {name}: {str(e)}")
        return False

# 1. Verificar archivos
files_ok = True
files_ok &= check_file(MODEL_PATH, "Modelo Clasificación")
files_ok &= check_file(SEG_PATH, "Modelo Segmentación")

if not files_ok:
    print("\n❌ ERROR: Faltan archivos de modelo. No se puede continuar.")
    sys.exit(1)

# 2. Cargar modelos
print("-" * 50)
load_test_model(MODEL_PATH, "Modelo Clasificación")
load_test_model(SEG_PATH, "Modelo Segmentación")
