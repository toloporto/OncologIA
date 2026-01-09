# debug_auth.py
import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG)

def test_all_login_methods():
    BASE_URL = "http://localhost:8004"
    email = "test@ortho.com"
    password = "OrthoWeb3_Demo2024!"
    
    print("🧪 PROBANDO TODOS LOS MÉTODOS DE LOGIN")
    print("=" * 50)
    
    # Método 1: JSON normal (como verify_multimodal.py)
    print("\n1. requests.post con json=")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Método 2: Form data (como OAuth2 espera)
    print("\n2. requests.post con data= (form-urlencoded)")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": email, "password": password},  # OAuth2 usa 'username' no 'email'
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Método 3: Con headers explícitos
    print("\n3. Con headers Content-Type explícito")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_all_login_methods()