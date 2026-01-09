# login_universal.py - Funciona con AMBAS formas
import requests

def login_universal():
    BASE_URL = "http://localhost:8004"
    
    # Método 1: Form-data (el que SÍ funciona)
    print("Método 1: Form-data (OAuth2 estándar)")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "test@ortho.com", "password": "OrthoWeb3_Demo2024!"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login exitoso (form-data)")
        return token
    
    # Método 2: Intentar JSON por si acaso
    print("Método 2: JSON")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "test@ortho.com", "password": "OrthoWeb3_Demo2024!"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login exitoso (JSON)")
        return token
    
    print("❌ Ambos métodos fallaron")
    return None

# Prueba de evolución temporal
def test_evolution(token):
    if not token:
        return
    
    BASE_URL = "http://localhost:8004"
    headers = {"Authorization": f"Bearer {token}"}
    
    patient_did = "did:ortho:test_patient_001"
    print(f"\n📈 Consultando evolución para {patient_did}...")
    
    response = requests.get(
        f"{BASE_URL}/patients/{patient_did}/evolution",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Evolución obtenida!")
        
        if data.get("can_calculate_trend", False):
            trend = data["trend"]
            print(f"   Tendencia: {trend['status']}")
            print(f"   Descripción: {trend['description']}")
        else:
            print(f"   Mensaje: {data.get('message', 'Sin tendencia')}")
        
        timeline = data.get("timeline", [])
        print(f"\n📅 Línea de tiempo ({len(timeline)} registros):")
        for item in timeline[:3]:  # Mostrar primeros 3
            print(f"   - {item['date'][:10]}: {item['diagnosis']} (Severidad: {item['severity']})")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    token = login_universal()
    if token:
        test_evolution(token)