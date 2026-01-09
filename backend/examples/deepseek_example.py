"""
Ejemplo de uso del servicio DeepSeek en OrthoWeb3 - Versión corregida
"""
import sys
import os
from pathlib import Path

# Agregar el directorio actual al path para importaciones
current_dir = Path(__file__).parent.absolute()
backend_dir = current_dir.parent
project_root = backend_dir.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

def example_analysis():
    """Ejemplo de análisis de caso dental"""
    
    print("\n" + "=" * 60)
    print("🦷 EJEMPLO DE USO - DEEPSEEK EN ORTHOWEB3")
    print("=" * 60)
    
    # Importar después de configurar el path
    from services.deepseek_service import deepseek_service
    
    # 1. Verificar si el servicio está activo
    if not deepseek_service.is_active():
        print("\n⚠️  DeepSeek service is not active.")
        print("💡 Solución: Crea un archivo .env en la raíz del proyecto con:")
        print("   DEEPSEEK_API_KEY=tu_clave_aquí")
        print("💡 Obtén tu API key gratis en: https://platform.deepseek.com/api_keys")
        return
    
    print("\n✅ DeepSeek service is active")
    
    # 2. Probar conexión
    print("\n🔌 Probando conexión...")
    test_result = deepseek_service.test_connection()
    
    if not test_result["success"]:
        print(f"❌ No se pudo conectar: {test_result.get('error')}")
        return
    
    # 3. Datos de ejemplo para un caso dental
    case_data = {
        "patient_info": {
            "age": 14,
            "gender": "female",
            "name": "María López"
        },
        "clinical_data": {
            "reason": "Consulta por dientes torcidos",
            "skeletal_class": "Class II",
            "overjet": "7mm",
            "overbite": "5mm",
            "crowding": "moderate",
            "specific_issues": "Canino incluido, apiñamiento anterior"
        }
    }
    
    # 4. Análisis del caso
    print("\n🔍 Analizando caso dental...")
    result = deepseek_service.analyze_dental_case(case_data)
    
    if result["success"]:
        analysis = result["data"]
        print(f"\n📋 RESULTADO DEL ANÁLISIS:")
        print(f"   ✅ Diagnóstico: {analysis.get('diagnosis', 'N/A')}")
        print(f"   📊 Severidad: {analysis.get('severity', 'N/A')}")
        print(f"   🎯 Confianza: {analysis.get('confidence', 'N/A')}")
        print(f"   📝 Hallazgos clave:")
        for finding in analysis.get('key_findings', [])[:3]:  # Mostrar primeros 3
            print(f"      • {finding}")
        print(f"   🔧 Recomendaciones:")
        for rec in analysis.get('recommendations', [])[:3]:  # Mostrar primeros 3
            print(f"      • {rec}")
        print(f"   🔢 Tokens usados: {result['usage'].get('total_tokens', 0)}")
    else:
        print(f"\n❌ Error en el análisis: {result.get('error')}")
    
    # 5. Generar explicación para el paciente
    print("\n👨‍👩‍👧‍👦 Generando explicación para paciente...")
    explanation = deepseek_service.explain_to_patient(
        diagnosis={"diagnosis": "Clase II", "severity": "moderada"},
        patient_age=14
    )
    
    if explanation["success"]:
        print(f"\n📝 EXPLICACIÓN PARA PACIENTE (14 años):")
        exp_text = explanation["data"].get("text", explanation["data"].get("raw_response", ""))
        if isinstance(exp_text, str):
            # Mostrar primeros 300 caracteres
            print(exp_text[:300] + "..." if len(exp_text) > 300 else exp_text)
        print(f"\n   🔢 Tokens usados: {explanation['usage'].get('total_tokens', 0)}")
    
    # 6. Mostrar estadísticas
    print("\n📈 ESTADÍSTICAS DEL SERVICIO:")
    stats = deepseek_service.get_stats()
    print(f"   📞 Total llamadas: {stats['total_calls']}")
    print(f"   ✅ Exitosas: {stats['successful_calls']}")
    print(f"   ❌ Fallidas: {stats['failed_calls']}")
    print(f"   🔤 Tokens usados: {stats['total_tokens']}")
    print(f"   💰 Tokens restantes: {stats['tokens_remaining']}")
    print(f"   📊 Porcentaje usado: {stats['quota_percentage']:.1f}%")
    
    print("\n" + "=" * 60)
    print("🎉 Ejemplo completado exitosamente!")
    print("=" * 60)

if __name__ == "__main__":
    example_analysis()