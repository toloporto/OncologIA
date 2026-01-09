# test_temporal_fixed.py CORREGIDO
import requests

def test_temporal_fixed():
    BASE_URL = "http://localhost:8004"
    
    print("🔐 Autenticando con FORM-DATA (no JSON)...")
    
    # USAR FORM-DATA, no JSON
    login_data = {
        "username": "test@ortho.com",  # ¡IMPORTANTE: 'username' no 'email'!
        "password": "OrthoWeb3_Demo2024!"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,  # ¡data= no json=!
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Login exitoso! Token: {token[:30]}...")
        
        # Resto del código...
    else:
        print(f"❌ Login falló: {response.text}")