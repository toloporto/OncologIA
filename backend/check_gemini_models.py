import os
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Intentar cargar desde el .env de la raíz si estamos en backend
    load_dotenv("../.env")
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No se encontró GEMINI_API_KEY en el entorno.")
else:
    print(f"🔑 API Key encontrada: {api_key[:5]}...{api_key[-5:]}")
    try:
        genai.configure(api_key=api_key)
        print("🔍 Listando modelos disponibles...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ Modelo: {m.name}")
    except Exception as e:
        print(f"❌ ERROR al conectar con Google AI: {e}")
