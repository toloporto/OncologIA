# test_evolution_detailed.py
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8004"

print("🔐 Autenticando...")
login_data = {"email": "test@ortho.com", "password": "OrthoWeb3_Demo2024!"}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)

if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Login exitoso")
    
    # Primero, insertar datos CON DIAGNÓSTICOS VÁLIDOS
    patient_did = "did:ortho:test_patient_001"
    
    # Lista de diagnósticos que el sistema entiende (de temporal_service.py)
    valid_diagnoses = ["class_i_normal", "class_ii_division1", "class_iii", "crowding", "open_bite"]
    
    print(f"\n📊 Insertando historial con diagnósticos válidos para: {patient_did}")
    
    # Fechas: empeorando -> mejorando
    dates = [
        (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        datetime.now().strftime("%Y-%m-%d")
    ]
    
    # Diagnósticos: Empeora (8) -> Intermedio (4) -> Mejora (0)
    diagnoses = ["class_iii", "class_ii_division1", "class_i_normal"]
    
    for i, (date, diagnosis) in enumerate(zip(dates, diagnoses)):
        # Simular inserción de análisis (depende de cómo sea tu API)
        print(f"  - {date}: {diagnosis} (Severidad esperada: {[8, 4, 0][i]})")
    
    # Consultar evolución
    print(f"\n📈 Consultando evolución...")
    evolution_response = requests.get(
        f"{BASE_URL}/patients/{patient_did}/evolution",
        headers=headers
    )
    
    if evolution_response.status_code == 200:
        data = evolution_response.json()
        print("✅ Evolución obtenida exitosamente!")
        
        print(f"\n📋 Resultado Completo:")
        print(f"Estado: {data.get('status', 'N/A')}")
        print(f"Tendencia: {data.get('trend', {}).get('status', 'N/A')}")
        
        trend = data.get('trend', {})
        if trend:
            print(f"Descripción: {trend.get('description', 'N/A')}")
            print(f"Tasa de mejora: {trend.get('improvement_rate', 'N/A')} pts/mes")
            print(f"Severidad actual: {trend.get('current_severity', 'N/A')}")
            print(f"Proyección 30 días: {trend.get('projection_30d', 'N/A')}")
        
        timeline = data.get('timeline', [])
        print(f"\n📅 Línea de tiempo ({len(timeline)} registros):")
        for entry in timeline:
            print(f"  - {entry.get('date')}: {entry.get('diagnosis', 'N/A')} " +
                  f"(Severidad: {entry.get('severity', 'N/A')})")
    else:
        print(f"❌ Error: {evolution_response.status_code}")
        print(evolution_response.text)
else:
    print(f"❌ Login falló: {response.status_code}")