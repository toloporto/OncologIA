import sys
import os

# Añadir path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.report_service import report_service

def test_report_generation():
    print("🧪 Probando Generación de Reporte Médico (IA Narrativa)...")
    
    # 1. Simular datos de un análisis completo (Iniciativas 1, 2, 3)
    mock_data = {
        'patient_did': 'did:ortho:expert-test',
        'predicted_class': 'class_ii_division1',
        'confidence': 0.92,
        'severity': 'Moderada',
        'geometric_analysis': {
            'anb': {'label': 'Ángulo ANB', 'value': 6.2, 'status': 'Clase II (Maxilar adelantado)'},
            'sna': {'label': 'Ángulo SNA', 'value': 85.0, 'status': 'Prognatismo Maxilar'}
        }
    }
    
    print("⏳ Solicitando redacción clínica a la IA...")
    result = report_service.generate_clinical_report(mock_data)
    
    if result.get("success"):
        print("\n✅ REPORTE GENERADO:")
        print("-" * 50)
        print(result.get("report_text"))
        print("-" * 50)
        print(f"🤖 Método IA: {result.get('llm_method')}")
    else:
        print(f"❌ Error: {result.get('error')}")
        print("Fallback:", result.get("fallback"))

if __name__ == "__main__":
    test_report_generation()
