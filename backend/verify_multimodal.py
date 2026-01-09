
import requests
import json
import os
import sys

# URL base de la API
BASE_URL = "http://localhost:8004"

def verify_multimodal():
    print("🔬 Verificando Endpoint de IA Multimodal...")

    # 1. Login para obtener token
    print("\n🔐 Autenticando...")
    try:
        auth_response = requests.post(
            f"{BASE_URL}/auth/login",
            data={"username": "test@ortho.com", "password": "OrthoWeb3_Demo2024!"}
        )
        if auth_response.status_code != 200:
            print(f"❌ Error Login: {auth_response.text}")
            return
        
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login exitoso.")
    except Exception as e:
        print(f"❌ Error conectando con API: {e}")
        print("⚠️ Asegúrate de que el servidor esté corriendo (uvicorn backend.ortho_api:app ...)")
        return

    # 2. Preparar Datos de Prueba
    # Usaremos una imagen de ejemplo o crearemos una dummy si no existe
    image_path = "public_images/test_image.jpg"
    if not os.path.exists(image_path):
        # Crear imagen dummy roja (que CLIP podría asociar con inflamación/sangrado)
        from PIL import Image
        img = Image.new('RGB', (512, 512), color = (255, 100, 100))
        if not os.path.exists("public_images"):
            os.makedirs("public_images")
        img.save(image_path)
        print("🖼️ Imagen de prueba creada.")

    clinical_prompts = [
        "Dientes sanos y alineados",
        "Encías inflamadas y rojas",
        "Dientes apiñados",
        "Presencia de caries profunda"
    ]
    
    print(f"\n🧠 Enviando análisis con prompts: {clinical_prompts}")

    # 3. Enviar Petición
    try:
        with open(image_path, "rb") as f:
            files = {"file": ("test_image.jpg", f, "image/jpeg")}
            data = {
                "clinical_context": json.dumps(clinical_prompts)
            }
            
            response = requests.post(
                f"{BASE_URL}/analyze/multimodal",
                headers=headers,
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Análisis Exitoso!")
                print("-" * 30)
                matches = result["multimodal_result"]["all_matches"]
                for match in matches:
                    print(f"📝 {match['description']}: {match['match_score']:.2f}%")
                print("-" * 30)
                print(f"🏆 Mejor coincidencia: {result['multimodal_result']['top_match']['description']}")
            else:
                print(f"❌ Error en endpoint: {response.text}")

    except Exception as e:
         print(f"❌ Error ejecutando prueba: {e}")

if __name__ == "__main__":
    verify_multimodal()
