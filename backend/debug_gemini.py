import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_gemini_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY no encontrada en .env")
        return

    print(f"🔍 Usando API Key: {api_key[:5]}...{api_key[-5:]}")
    client = genai.Client(api_key=api_key)
    
    try:
        print("📋 Modelos disponibles:")
        for model in client.models.list():
            # El objeto Model en el nuevo SDK puede tener atributos diferentes
            # Imprimimos el nombre y el objeto completo para depurar
            print(f" - {model}")
    except Exception as e:
        print(f"❌ Error al listar modelos: {e}")

if __name__ == "__main__":
    list_gemini_models()
