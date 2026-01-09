# test_fhir_onco.py
import json
from backend.services.fhir_adapter import fhir_adapter

def test_oncology_fhir():
    print("🏥 Iniciando Test FHIR Oncológico...\n")
    
    # 1. Datos Simulados
    patient_id = "patient-123"
    diagnosis_text = "Neoplasia maligna de bronquios o del pulmón, parte no especificada"
    medication_name = "Morfina oral 10mg"
    
    # 2. Generar Recursos Individuales
    print("🔹 Generando Recurso Patient...")
    patient = fhir_adapter.to_patient_resource(patient_id, "Juan Pérez", "male", "1955-05-20")
    
    print("🔹 Generando Recurso Condition (Diagnóstico)...")
    condition = fhir_adapter.to_condition_resource(
        patient_id=patient_id,
        diagnosis_text=diagnosis_text,
        icd_code="C34.9" # ICD-10 para Cáncer de Pulmón
    )
    
    print("🔹 Generando Recurso MedicationRequest (Opiodes)...")
    medication = fhir_adapter.to_medication_request_resource(
        patient_id=patient_id,
        medication_name=medication_name,
        rxnorm_code="7052" # Morfina
    )
    
    # 3. Crear Bundle Oncológico
    print("🔹 Empaquetando en Bundle Oncológico...")
    try:
        bundle = fhir_adapter.create_oncology_bundle(patient, condition, medication)
        print("✅ Bundle creado exitosamente.")
        
        # Guardar para inspección
        filename = "fhir_oncology_bundle.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON guardado en: {filename}")
        
        # Validaciones clave
        assert bundle["resourceType"] == "Bundle"
        assert len(bundle["entry"]) == 3
        print("✨ Validaciones básicas pasadas.")
        
    except Exception as e:
        print(f"❌ Error creando Bundle: {e}")

if __name__ == "__main__":
    test_oncology_fhir()
