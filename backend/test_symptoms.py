
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from backend.services.langchain_manager import langchain_agent

def test_symptom_extraction():
    # Test Cases
    cases = [
        "Siento mucho dolor en la espalda, como un 8 de 10, y anoche no pude dormir nada.",
        "Estoy muy cansado todo el tiempo, no tengo energia, pero no me duele nada.",
        "Tengo miedo de que el tratamiento no funcione, me siento muy nervioso.",
        "Todo está bien, hoy tuve un buen día."
    ]

    print("\n🔬 TEST DE EXTRACCIÓN DE SÍNTOMAS ONCOLÓGICOS (ESAS)\n")
    
    for i, text in enumerate(cases):
        print(f"--- Caso {i+1} ---")
        print(f"Texto: \"{text}\"")
        try:
            result = langchain_agent.extract_symptoms_agent(text)
            print("Resultado:", result)
        except Exception as e:
            print("ERROR:", e)
        print("\n")

if __name__ == "__main__":
    test_symptom_extraction()
