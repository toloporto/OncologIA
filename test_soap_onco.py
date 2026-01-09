# test_soap_onco.py
import sys
import os
import logging

# Configurar path para importar backend
sys.path.append(os.getcwd())

# Cargar variables de entorno (.env)
from dotenv import load_dotenv
load_dotenv()  # Carga .env del directorio actual

# Configurar logging
logging.basicConfig(level=logging.INFO)

print("💉 Iniciando prueba de Generación SOAP Oncológico (GenAI)...")

try:
    from backend.services.soap_service import soap_service
    
    # Caso Simulado: Paciente Paliativo
    # Texto transcrito (Whisper) simulado
    fake_transcript = (
        "Hola doctor. Hoy me siento un poco mejor de ánimo, pero el dolor "
        "en la espalda no me deja dormir. Diría que es un 8 sobre 10 a veces. "
        "También me ahogo un poco si camino al baño. "
        "He tomado la morfina extra que me dijo pero me da muchas náuseas."
    )
    
    # Métricas emocionales (simuladas del modelo antiguo, aunque el Prompt ESAS es lo importante)
    fake_emotions = {"sadness": 0.4, "fear": 0.6}
    
    print("\n📝 Texto del Paciente:")
    print(f"'{fake_transcript}'")
    print("\n🤖 Consultando a Gemini (Especialista Paliativo)...")
    
    # Generar Nota
    soap_note = soap_service.generate_note(fake_transcript, fake_emotions)
    
    print("\n" + "="*40)
    print("RESULTADO GENERADO (INFORME SOAP + ESAS)")
    print("="*40)
    print(soap_note)
    print("="*40)
    
    if "Error" in soap_note or "API Key" in soap_note:
        print("\n❌ PRUEBA FALLIDA: Revisa tu API KEY en .env")
    else:
        print("\n✅ PRUEBA EXITOSA: El sistema ha generado el informe oncológico.")

except ImportError as e:
    print(f"\n❌ Error de importación: {e}")
    print("Asegúrate de ejecutar esto desde la raíz del proyecto (C:\\Users\\antol\\OncologIA)")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")
