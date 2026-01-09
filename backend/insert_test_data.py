# insert_test_data.py
import sqlite3
from datetime import datetime, timedelta
import uuid

# Conectar a la base de datos en la raíz
conn = sqlite3.connect('psico.db')
cursor = conn.cursor()

patient_did = "did:psych:test_patient_001"
patient_name = "Juan Pérez (Paciente de Prueba)"

# 1. Obtener user_id (Médico)
cursor.execute("SELECT id FROM users WHERE email = 'test@psych.com'")
user = cursor.fetchone()
if user:
    user_id = user[0]
    print(f"✅ Médico encontrado: {user_id}")
else:
    print("❌ Médico no encontrado. Inicia el servidor primero para que se cree el usuario.")
    exit()

# 2. Asegurar que el paciente existe en la tabla 'patients'
cursor.execute("SELECT id FROM patients WHERE did = ?", (patient_did,))
patient = cursor.fetchone()
if not patient:
    patient_uuid = str(uuid.uuid4())
    cursor.execute("INSERT INTO patients (id, did, full_name, created_at) VALUES (?, ?, ?, ?)",
                   (patient_uuid, patient_did, patient_name, datetime.now().isoformat()))
    print(f"✅ Paciente de prueba creado: {patient_name}")
else:
    patient_uuid = patient[0]
    print(f"✅ Paciente ya existente: {patient_name}")

# 3. Eliminar logs previos para este paciente
cursor.execute("DELETE FROM session_logs WHERE patient_id = ?", (patient_uuid,))
print("🧹 Sesiones previas eliminadas")

# 4. Insertar sesiones clínicas
sessions = [
    ("Sesión inicial: El paciente muestra signos de alegría y entusiasmo por el nuevo tratamiento.", '{"joy": 0.8, "sadness": 0.05, "anger": 0.02}', False),
    ("Segunda sesión: Reporta un episodio de ira tras un conflicto laboral.", '{"joy": 0.1, "sadness": 0.2, "anger": 0.7}', False),
    ("Tercera sesión: El paciente se siente abrumado y con miedo al futuro.", '{"joy": 0.05, "sadness": 0.4, "fear": 0.5}', False)
]

for i, (text, emotions_json, risk) in enumerate(sessions):
    log_id = str(uuid.uuid4())
    log_date = (datetime.now() - timedelta(days=(3-i)*15)).isoformat()
    cursor.execute('''
        INSERT INTO session_logs 
        (id, patient_id, created_at, raw_text, emotion_analysis, risk_flag)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (log_id, patient_uuid, log_date, text, emotions_json, risk))

print(f"✅ Insertadas {len(sessions)} sesiones clínicas de prueba")
conn.commit()
conn.close()