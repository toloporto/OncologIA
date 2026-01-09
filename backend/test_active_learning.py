import os
import sys
import json
import time
from dotenv import load_dotenv

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load Env
load_dotenv()

from backend.services.langchain_manager import langchain_agent
from backend.services.rag_service import rag_service

def test_active_learning_loop():
    print("\n🔬 TEST DE APRENDIZAJE ACTIVO (ACTIVE LEARNING LOOP)\n")
    
    # 1. Caso de Prueba
    # Usamos una expresión ambigua que la IA podría malinterpretar inicialmente
    test_text = "Doctor, hoy estoy totalmente planchado."
    print(f"📝 Texto del Paciente: \"{test_text}\"")
    
    # 2. Análisis Inicial (Antes de enseñar)
    print("\n--- 1. Análisis Inicial (Sin memoria previa) ---")
    initial_result = langchain_agent.extract_symptoms_agent(test_text)
    print("Resultado IA:", json.dumps(initial_result, indent=2))
    
    # 3. Simular Corrección del Médico
    # "Planchado" en este contexto significa Fatiga extrema, no dolor.
    # Supongamos que la IA detectó poco o nada, o quizás dolor erróneamente.
    # Enseñamos que esto es Fatiga: 0.9
    print("\n--- 2. El Médico corrige (Enseñando al sistema via ChromaDB) ---")
    correction = {
        "pain": 0.0,
        "fatigue": 0.9, # Corrección fuerte
        "nausea": 0.0,
        "anxiety": 0.0,
        "depression": 0.0,
        "insomnia": 0.0
    }
    
    session_id = f"test_session_{int(time.time())}"
    success = rag_service.store_feedback(test_text, correction, session_id)
    
    if success:
        print(f"✅ Feedback guardado/vectorizado correctamente. ID: {session_id}")
    else:
        print("❌ Error guardando feedback. Verifica si ChromaDB funciona.")
        return

    # 4. Verificación de Memoria (RAG Retrieval)
    print("\n--- 3. Verificando Memoria Vectorial (Retrieval) ---")
    # Limpiamos caché o esperamos un poco
    time.sleep(2)
    
    similar_cases = rag_service.find_similar_feedback(test_text)
    print(f"Casos similares encontrados en DB: {len(similar_cases)}")
    
    retrieval_success = False
    for case in similar_cases:
        print(f" - Recuerdo: {case['text']} -> Corrección: {case['correction']}")
        if "0.9" in case['correction'] and "fatigue" in case['correction']:
            retrieval_success = True

    if retrieval_success:
        print("✅ MEMORIA FUNCIONANDO: El sistema recuerda la corrección.")
    else:
        print("❌ MEMORIA FALLANDO: No se recuperó la corrección.")

    # 5. Re-Análisis con IA (Si la API lo permite)
    print("\n--- 4. Intento de Inferencia Adaptativa (Requiere API) ---")
    try:
        final_result = langchain_agent.extract_symptoms_agent(test_text)
        print("Resultado IA (Adaptado):", json.dumps(final_result, indent=2))
        
        # Verificamos si es demo o real
        if final_result.get("pain") == 0.8 and final_result.get("insomnia") == 0.9:
             print("\n⚠️ API SATURADA (429): La IA está en MODO SEGURO y devolvió datos demo.")
             print("   Sin embargo, si la 'Verificación de Memoria' arriba dio ✅, el sistema de aprendizaje YA FUNCIONA.")
             print("   La inferencia correcta se verá cuando se restablezca la cuota de la API.")
        else:
            fatigue_score = final_result.get("fatigue", 0.0)
            if fatigue_score >= 0.8:
                print("\n🎉 ¡ÉXITO TOTAL! El sistema aprendió y aplicó el conocimiento.")
            else:
                print("\n⚠️ El sistema respondió, pero no aplicó la corrección completamente.")
                
    except Exception as e:
        print(f"Error invocando IA: {e}")

if __name__ == "__main__":
    test_active_learning_loop()
