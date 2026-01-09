import sys
import os
import numpy as np
import io
from PIL import Image
from unittest.mock import MagicMock

# Añadir path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.analysis_service import AnalysisService
from backend.services.prediction_service import PredictionService

# Mock de ModelManager para simular el comportamiento global de ortho_api
class MockModelManager:
    def get_classification_model(self):
        # Retornamos None para forzar el modo simulación si no hay modelo cargado
        return None

def test_ensemble_logic():
    print("🧪 Probando Lógica de ENSEMBLE (Service Layer)...")
    
    # 1. Preparar Dependencias
    model_manager = MockModelManager()
    prediction_service = PredictionService(model_manager)
    mock_db = MagicMock() # Mock de la sesión de base de datos
    
    # Iniciar servicio con dependencias requeridas
    analysis_service = AnalysisService(
        prediction_service=prediction_service,
        db_session=mock_db
    )
    
    # 2. Crear imagen sintética y convertir a BYTES (lo que espera el servicio)
    print("📸 Generando imagen sintética y convirtiendo a bytes...")
    synthetic_array = (np.random.rand(512, 512, 3) * 255).astype(np.uint8)
    image = Image.fromarray(synthetic_array)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    image_bytes = img_byte_arr.getvalue()
    
    # 3. Ejecutar análisis directo
    print("⚙️ Ejecutando análisis con Ensemble=True...")
    try:
        # Analizamos (esto invocará internamente al ensemble_service)
        result = analysis_service.analyze_dental_image(
            image_bytes=image_bytes, 
            patient_did="did:ortho:test_ensemble_local",
            user_id="test_user_id",
            filename="synthetic_test.jpg",
            use_ensemble=True
        )
        
        print("\n✅ Análisis completado con éxito")
        print(f"📊 Clase Predicha: {result.get('predicted_class')}")
        print(f"🎯 Confianza: {result.get('confidence'):.4f}")
        
        if 'uncertainty' in result:
            print(f"⚠️ Incertidumbre: {result.get('uncertainty'):.4f}")
            print(f"🤝 Consenso: {result.get('consensus')}")
            print(f"🧬 Ecosistema Operativo: {result.get('ensemble_active')}")
            
            print("\n" + "="*50)
            print("✅ VERIFICACIÓN DE ENSEMBLE COMPLETADA")
            print("="*50)
        else:
            print("\n⚠️ El análisis terminó pero no se detectaron métricas de ensemble.")
            print("ℹ️ Nota: Si el ensemble_service no tiene múltiples modelos cargados en")
            print("   ml-models/models/, se comportará como un modelo único.")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ensemble_logic()
