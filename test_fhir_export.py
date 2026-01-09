import json
import os
from datetime import datetime
from backend.services.fhir_adapter import fhir_adapter

def main():
    print("🏥 Iniciando prueba de exportación FHIR R4...")
    
    # 1. Datos Simulados (Mock)
    mock_patient = {
        "id": "12345",
        "name": "Juan Perez",
        "gender": "male",
        "birth_date": "1980-05-20"
    }
    
    mock_transcription = "El paciente reporta ansiedad moderada y dificultad para dormir en las últimas dos semanas."
    
    # 2. Conversión a Recursos FHIR
    print("🔄 Convirtiendo Paciente...")
    fhir_patient = fhir_adapter.to_patient_resource(
        patient_id=mock_patient["id"],
        name=mock_patient["name"],
        gender=mock_patient["gender"],
        birth_date=mock_patient["birth_date"]
    )
    
    print("🔄 Convirtiendo Transcripción a Observación LOINC...")
    fhir_observation = fhir_adapter.to_observation_transcription(
        patient_id=mock_patient["id"],
        text=mock_transcription
    )
    
    # 3. Creación del Bundle
    print("📦 Empaquetando Bundle...")
    bundle = fhir_adapter.generate_bundle(fhir_patient, [fhir_observation])
    
    # 4. Exportar a Archivo
    filename = "fhir_export_test.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Exportación completada: {os.path.abspath(filename)}")
    print("\n--- Previsualización del JSON ---")
    print(json.dumps(bundle, indent=2))
    print("\n💡 Nota: Si ves 'resourceType' en el JSON, la estructura es correcta.")

if __name__ == "__main__":
    main()
