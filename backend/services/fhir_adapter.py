from datetime import datetime, timezone
import uuid
import json
from typing import Dict, List, Optional, Union

# Intentamos importar fhir.resources, si falla, usaremos diccionarios crudos (fallback)
# Esto permite que el código exista antes de instalar librerías.
try:
    from fhir.resources.patient import Patient
    from fhir.resources.observation import Observation
    from fhir.resources.bundle import Bundle
    from fhir.resources.bundle import BundleEntry
    from fhir.resources.coding import Coding
    from fhir.resources.codeableconcept import CodeableConcept
    from fhir.resources.codeablereference import CodeableReference
    # FHIRDate not available in new versions, using native types
    from fhir.resources.condition import Condition
    from fhir.resources.medicationrequest import MedicationRequest
    FHIR_AVAILABLE = True
except ImportError:
    FHIR_AVAILABLE = False

class FHIRAdapter:
    """
    Adaptador para convertir modelos internos de OncologIA a recursos HL7 FHIR R4.
    """
    
    SYSTEM_LOINC = "http://loinc.org"
    
    # LOINC Codes Relevantes
    CODE_TRANSCRIPTION = "11341-5" # History of present illness Narrative
    CODE_MOOD = "55283-6"          # Mood Narrative
    
    def __init__(self, org_name: str = "OncologIA Clinic"):
        self.org_name = org_name

    def to_patient_resource(self, patient_id: str, name: str, gender: str = "unknown", birth_date: str = None) -> Dict:
        """
        Convierte datos básicos de paciente a recurso FHIR Patient.
        """
        if not FHIR_AVAILABLE:
            return {
                "resourceType": "Patient",
                "id": patient_id,
                "name": [{"text": name}],
                "gender": gender,
                "birthDate": birth_date
            }
            
        patient = Patient.construct()
        patient.id = patient_id
        patient.name = [{"text": name, "family": name.split(" ")[-1] if " " in name else name}]
        patient.gender = gender
        if birth_date:
            patient.birthDate = birth_date
            
        return json.loads(patient.json())

    def to_observation_transcription(self, patient_id: str, text: str, timestamp: datetime = None) -> Dict:
        """
        Convierte una transcripción de voz a una FHIR Observation.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
            
        if not FHIR_AVAILABLE:
            return self._fallback_observation(patient_id, text, self.CODE_TRANSCRIPTION, "Transcription", timestamp)

        obs = Observation.construct()
        obs.status = "final"
        obs.id = str(uuid.uuid4())
        obs.subject = {"reference": f"Patient/{patient_id}"}
        obs.effectiveDateTime = timestamp.isoformat()
        
        # Coding LOINC
        code = CodeableConcept.construct()
        coding = Coding.construct()
        coding.system = self.SYSTEM_LOINC
        coding.code = self.CODE_TRANSCRIPTION
        coding.display = "History of present illness Narrative"
        code.coding = [coding]
        obs.code = code
        
        # Value (Text)
        obs.valueString = text
        
        return json.loads(obs.json())

    def _fallback_observation(self, patient_id, value, code, display, timestamp):
        """Generador manual de JSON si falla la librería"""
        return {
            "resourceType": "Observation",
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": code,
                    "display": display
                }]
            },
            "effectiveDateTime": timestamp.isoformat(),
            "valueString": value
        }

    def generate_bundle(self, patient: Dict, observations: List[Dict]) -> Dict:
        """
        Empaqueta todo en un FHIR Bundle (Transacción o Colección).
        """
        if not FHIR_AVAILABLE:
            entries = [{"resource": patient}] + [{"resource": obs} for obs in observations]
            return {"resourceType": "Bundle", "type": "collection", "entry": entries}

        bundle = Bundle.construct()
        bundle.type = "collection"
        bundle.timestamp = datetime.now(timezone.utc).isoformat()
        
        entries = []
        
        # Add Patient
        p_entry = BundleEntry.construct()
        p_resource = Patient.parse_obj(patient)
        p_entry.resource = p_resource
        entries.append(p_entry)
        
        # Add Observations
        for obs_dict in observations:
            o_entry = BundleEntry.construct()
            o_resource = Observation.parse_obj(obs_dict)
            o_entry.resource = o_resource
            entries.append(o_entry)
            
        bundle.entry = entries
        return json.loads(bundle.json())

    def to_condition_resource(self, patient_id: str, diagnosis_text: str, icd_code: str = None) -> Dict:
        """
        Crea un recurso FHIR Condition para el diagnóstico oncológico.
        """
        if not FHIR_AVAILABLE:
            return {"error": "Librería fhir.resources no instalada."}

        # Coding (ICD-10 por defecto para oncología)
        code = CodeableConcept.construct()
        coding = Coding.construct()
        coding.system = "http://hl7.org/fhir/sid/icd-10"
        coding.code = icd_code if icd_code else "C80.1"
        coding.display = diagnosis_text
        code.coding = [coding]
        code.text = diagnosis_text

        cond = Condition(
            id=str(uuid.uuid4()),
            subject={"reference": f"Patient/{patient_id}"},
            clinicalStatus={
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
            },
            verificationStatus={
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
            },
            code=code,
            recordedDate=datetime.now(timezone.utc).isoformat()
        )
        
        return json.loads(cond.json())

    def to_medication_request_resource(self, patient_id: str, medication_name: str, rxnorm_code: str = None) -> Dict:
        """
        Crea un recurso FHIR MedicationRequest para prescripción de opioides/analgésicos.
        """
        if not FHIR_AVAILABLE:
            return {"error": "Librería fhir.resources no instalada."}

        # Medication Concept
        med_concept = CodeableConcept.construct()
        coding = Coding.construct()
        coding.system = "http://www.nlm.nih.gov/research/umls/rxnorm"
        coding.code = rxnorm_code if rxnorm_code else "7052" 
        coding.display = medication_name
        med_concept.coding = [coding]
        med_concept.text = medication_name

        # R5 Compatibility: Wrap concept in CodeableReference
        med_reference = CodeableReference(concept=med_concept)

        med_req = MedicationRequest(
            id=str(uuid.uuid4()),
            status="active",
            intent="order",
            subject={"reference": f"Patient/{patient_id}"},
            medication=med_reference,
            authoredOn=datetime.now(timezone.utc).isoformat()
        )
        
        return json.loads(med_req.json())

    def create_oncology_bundle(self, patient_data: Dict, diagnosis: Dict, medication: Dict) -> Dict:
        """
        Genera un Bundle cohesionado con Paciente, Diagnóstico y Prescripción.
        """
        if not FHIR_AVAILABLE:
            return {"error": "FHIR library missing"}

        bundle = Bundle.construct()
        bundle.type = "transaction" # O 'collection'
        bundle.id = str(uuid.uuid4())
        bundle.timestamp = datetime.now(timezone.utc).isoformat()
        
        entries = []
        
        # 1. Patient
        p_entry = BundleEntry.construct()
        p_resource = Patient.parse_obj(patient_data)
        p_entry.resource = p_resource
        p_entry.request = {"method": "PUT", "url": f"Patient/{patient_data['id']}"}
        entries.append(p_entry)
        
        # 2. Condition
        c_entry = BundleEntry.construct()
        c_resource = Condition.parse_obj(diagnosis)
        c_entry.resource = c_resource
        c_entry.request = {"method": "POST", "url": "Condition"}
        entries.append(c_entry)
        
        # 3. MedicationRequest
        m_entry = BundleEntry.construct()
        m_resource = MedicationRequest.parse_obj(medication)
        m_entry.resource = m_resource
        m_entry.request = {"method": "POST", "url": "MedicationRequest"}
        entries.append(m_entry)
        
        bundle.entry = entries
        
        # Validación: Al llamar a .json(), pydantic valida la estructura
        return json.loads(bundle.json())

# Instancia global
fhir_adapter = FHIRAdapter()
