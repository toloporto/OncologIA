import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
USER_EMAIL = "test@psych.com"
USER_PASS = "Psycho2025!"

def print_step(msg):
    print(f"\n\033[96m{msg}\033[0m")

def print_success(msg):
    print(f"   \033[92m✅ {msg}\033[0m")

def print_error(msg):
    print(f"   \033[91m❌ {msg}\033[0m")

def main():
    # 1. Login
    print_step("1. Iniciando sesión...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": USER_EMAIL, "password": USER_PASS})
        if resp.status_code != 200:
            print_error(f"Fallo Login: {resp.text}")
            return
        token = resp.json().get("access_token")
        print_success("Login exitoso. Token recibido.")
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Patient
    print_step("2. Creando/Verificando paciente...")
    patient_did = "patient_test_py"
    requests.post(f"{BASE_URL}/patients", json={"full_name": "Test Python", "did": patient_did}, headers=headers)
    print_success(f"Paciente usado: {patient_did}")

    # 3. Analyze Normal
    print_step("3. Análisis NLP (Normal)...")
    text_normal = "Me siento tranquilo y enfocado en mis metas."
    try:
        resp = requests.post(f"{BASE_URL}/session/analyze", json={"patient_id": patient_did, "text": text_normal}, headers=headers)
        data = resp.json()
        print(f"   Emociones: {data.get('emotion_analysis')}")
        if not data.get('risk_flag'):
             print_success("Correcto: Sin riesgo detectado.")
        else:
             print_error("Inesperado: Riesgo detectado en texto normal.")
    except Exception as e:
        print_error(f"Error: {e}")

    # 4. Analyze Risk
    print_step("4. Análisis NLP (Riesgo)...")
    text_risk = "Ya no puedo más, quiero suicidio y acabar con todo."
    try:
        resp = requests.post(f"{BASE_URL}/session/analyze", json={"patient_id": patient_did, "text": text_risk}, headers=headers)
        data = resp.json()
        if data.get('risk_flag'):
             print_success(f"Alerta activada: {data.get('alert')}")
        else:
             print_error("FALLO: No se detectó riesgo en texto peligroso.")
    except Exception as e:
        print_error(f"Error: {e}")

if __name__ == "__main__":
    main()
