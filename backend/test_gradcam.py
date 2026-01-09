"""
Script de prueba para verificar Grad-CAM
Ejecutar: python backend/test_gradcam.py
"""

import sys
import os

# Añadir path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.explainability_service import explainability_service
import numpy as np

def test_gradcam():
    """Prueba básica del servicio de explicabilidad"""
    
    print("🧪 Probando Grad-CAM...")
    
    # 1. Cargar modelo
    print("\n1️⃣ Cargando modelo...")
    # Intentar varios paths de modelos
    model_paths = [
        'ml-models/trained_models/real_ortho_model.h5',
        'ml-models/models/ortho_efficientnetv2.h5',
        'best_ortho_model.h5'
    ]
    
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if not model_path:
        print(f"❌ No se encontró ningún modelo en:")
        for path in model_paths:
            print(f"   - {path}")
        print("ℹ️ Asegúrate de tener un modelo entrenado")
        return False
    
    print(f"📁 Usando modelo: {model_path}")
    
    success = explainability_service.load_model(model_path)
    if not success:
        print("❌ Error cargando modelo")
        return False
    
    print("✅ Modelo cargado correctamente")
    
    # 2. Crear imagen de prueba (simulada)
    print("\n2️⃣ Generando imagen de prueba...")
    test_image = np.random.rand(512, 512, 3).astype(np.float32)
    print(f"✅ Imagen de prueba creada: {test_image.shape}")
    
    # 3. Generar Grad-CAM
    print("\n3️⃣ Generando Grad-CAM...")
    heatmap = explainability_service.generate_gradcam(test_image, class_idx=0)
    
    if heatmap is None:
        print("❌ Error generando Grad-CAM")
        return False
    
    print(f"✅ Heatmap generado: {heatmap.shape}")
    print(f"   Rango de valores: [{heatmap.min():.3f}, {heatmap.max():.3f}]")
    
    # 4. Crear overlay
    print("\n4️⃣ Creando overlay...")
    original_uint8 = (test_image * 255).astype(np.uint8)
    overlay = explainability_service.overlay_heatmap(original_uint8, heatmap)
    
    if overlay is None:
        print("❌ Error creando overlay")
        return False
    
    print(f"✅ Overlay creado: {overlay.shape}")
    
    # 5. Identificar regiones influyentes
    print("\n5️⃣ Identificando regiones influyentes...")
    regions = explainability_service.get_top_influential_regions(heatmap, top_k=3)
    
    print(f"✅ Regiones encontradas: {len(regions)}")
    for i, region in enumerate(regions):
        print(f"   Región {i+1}: x={region['x']}, y={region['y']}, "
              f"w={region['width']}, h={region['height']}, "
              f"score={region['score']:.3f}")
    
    # 6. Explicación completa
    print("\n6️⃣ Generando explicación completa...")
    explanation = explainability_service.explain_prediction(test_image, class_idx=0)
    
    if not explanation.get('success'):
        print("❌ Error generando explicación completa")
        return False
    
    print("✅ Explicación completa generada")
    print(f"   Heatmap base64: {len(explanation['heatmap_base64'])} caracteres")
    print(f"   Regiones influyentes: {len(explanation['influential_regions'])}")
    print(f"   Entropía del heatmap: {explanation['heatmap_entropy']:.3f}")
    
    print("\n" + "="*50)
    print("✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
    print("="*50)
    
    return True


if __name__ == "__main__":
    try:
        success = test_gradcam()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
