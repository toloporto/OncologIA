
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.services.emotion_ml_service import emotion_ml_service

def test_integration():
    print("\n" + "="*50)
    print("🧪 VERIFICACIÓN DE INTEGRACIÓN: Modelo Público")
    print("="*50 + "\n")
    
    # Textos de prueba clínicos/emocionales
    tests = [
        "Siento un miedo terrible a que la quimio no funcione.",
        "Estoy muy contento hoy porque salí a caminar.",
        "Tengo mucha rabia de por qué me pasó esto a mí."
    ]
    
    print("Cargando modelo y realizando inferencias...\n")
    
    success = True
    for text in tests:
        try:
            result = emotion_ml_service.predict_emotion(text)
            if result:
                print(f"📝 Texto: '{text}'")
                print(f"   ► Emoción: {result['emotion'].upper()} ({result['confidence']:.2%})")
                if "explanation" in result:
                    expl = result["explanation"]
                    expl_str = ", ".join([f"{item['word']} ({item['impact']:.2f})" for item in expl])
                    print(f"   ℹ️ Explicación (XAI): [{expl_str}]")
                print(f"   ► Modelo: {result['model']}\n")
            else:
                print(f"❌ Falló predicción para: '{text}'")
                success = False
        except Exception as e:
            print(f"❌ Error crítico: {e}")
            success = False
            
    if success:
        print("✅ INTEGRACIÓN EXITOSA: El servicio carga y usa el modelo correctamente.")
    else:
        print("❌ FALLA EN INTEGRACIÓN.")

if __name__ == "__main__":
    test_integration()
