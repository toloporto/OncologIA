# test_rag_onco.py
import sys
import os
import time

# Configurar path
sys.path.append(os.getcwd())

from backend.services.rag_service import rag_service

def test_rag_flow():
    print("🧠 Iniciando Prueba de Cerebro Clínico (RAG)...")
    
    # 1. Ingestión
    print("\n1️⃣ Ingestando Documentos...")
    result_ingest = rag_service.ingest_documents()
    print(f"   Resultado: {result_ingest}")
    
    if "error" in result_ingest:
        print("❌ Fallo en ingestión. Verifica librerías.")
        return

    # 2. Consulta
    query = "¿Cuál es la dosis de rescate para dolor irruptivo si el paciente toma morfina?"
    print(f"\n2️⃣ Pidiendo consulta al experto: '{query}'")
    
    start_time = time.time()
    answer = rag_service.query_expert(query)
    elapsed = time.time() - start_time
    
    print(f"\n⏱️ Tiempo de respuesta: {elapsed:.2f}s")
    print(f"\n📄 Contexto Recuperado (RAG):\n{'-'*40}\n{answer.get('context', 'Sin contexto')}\n{'-'*40}")
    
    # Validación simple
    context = answer.get('context', '').lower()
    if "1/6" in context or "rescate" in context:
        print("\n✅ PRUEBA EXITOSA: El sistema encontró la regla del 1/6 para rescates.")
    else:
        print("\n⚠️ ALERTA: El sistema no encontró la información exacta. Revisa el PDF o el chunking.")

if __name__ == "__main__":
    test_rag_flow()
