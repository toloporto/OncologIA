import os
from reportlab.pdfgen import canvas
from backend.services.rag_service import rag_service

def create_dummy_pdf(filename="knowledge_base/protocolo_ansiedad.pdf"):
    """Crea un PDF médico de prueba si no existe."""
    if not os.path.exists("knowledge_base"):
        os.makedirs("knowledge_base")
        
    if os.path.exists(filename):
        return

    print(f"📄 Creando PDF de prueba: {filename}")
    c = canvas.Canvas(filename)
    c.drawString(100, 800, "PROTOCOLO DE ACTUACIÓN EN ANSIEDAD SEVERA (v2025)")
    c.drawString(100, 780, "1. Evaluación Inicial: Aplicar escala GAD-7.")
    c.drawString(100, 760, "2. Intervención Farmacológica: En caso de crisis aguda sin respuesta")
    c.drawString(100, 740, "   a técnicas de relajación, considerar Benzodiazepinas de vida media corta.")
    c.drawString(100, 720, "3. Intervención Psicológica: La Terapia Cognitivo Conductual (TCC)")
    c.drawString(100, 700, "   es el tratamiento de primera elección.")
    c.drawString(100, 680, "4. Criterios de Derivación: Ideación suicida persistente requiere")
    c.drawString(100, 660, "   derivación inmediata a urgencias psiquiátricas.")
    c.save()

def main():
    print("🧠 Iniciando Prueba de Cerebro Clínico (RAG)...")
    
    # 1. Crear datos de prueba
    create_dummy_pdf()
    
    # 2. Ingestar documentos
    print("\n📚 Leyendo y 'memorizando' documentos...")
    ingest_result = rag_service.ingest_documents()
    print(f"   Resultado: {ingest_result}")
    
    if "error" in ingest_result:
        print("❌ Error crítico en ingestión. Verifica dependencias.")
        return

    # 3. Consultar al experto
    query = "¿Cuál es el tratamiento de primera elección para la ansiedad?"
    print(f"\n❓ Pregunta: {query}")
    
    print("⏳ Pensando y buscando en la base de conocimientos...")
    result = rag_service.query_expert(query)
    
    print("\n💡 RESPUESTA DEL CEREBRO:")
    print("-" * 50)
    print(f"Contexto Recuperado:\n{result.get('context', 'Sin contexto')}")
    print("-" * 50)
    print(f"Fuentes: {result.get('sources')}")

if __name__ == "__main__":
    # Asegúrate de instalar reportlab para generar el PDF de prueba
    # pip install reportlab
    main()
