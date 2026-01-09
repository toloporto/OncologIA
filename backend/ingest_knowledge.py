
import os
import sys

# Ajustar path para importar módulos del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.rag_service import rag_service

def main():
    print("🧠 OncologIA Knowledge Ingestion")
    print("================================")
    print(f"Directorio de conocimiento: {rag_service.knowledge_path}")
    
    # Crear carpeta si no existe
    if not os.path.exists(rag_service.knowledge_path):
        os.makedirs(rag_service.knowledge_path)
        print(f"📂 Carpeta creada: {rag_service.knowledge_path}")
        print("ℹ️  Por favor, coloca tus PDFs (Guías Clínicas) en esa carpeta y vuelve a ejecutar este script.")
        return

    print("🔄 Iniciando proceso de ingesta...")
    result = rag_service.ingest_documents()
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    elif "message" in result:
        print(f"ℹ️  {result['message']}")
    else:
        print("✅ Ingesta completada con éxito!")
        print(f"   - Archivos procesados: {result.get('files_processed', 0)}")
        print(f"   - Fragmentos (chunks) generados: {result.get('chunks_added', 0)}")
        print("\nEl Asistente Clínico ahora tiene acceso a esta información.")

if __name__ == "__main__":
    main()
