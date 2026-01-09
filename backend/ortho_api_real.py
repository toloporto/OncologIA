# c:\ortho-web3-project\backend\ortho_api_real.py

import os
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import json
from datetime import datetime
import uuid
import cv2 # Importar OpenCV

from deepseek_routes import router as deepseek_router

# Importar router de autenticación
from backend.auth_routes import auth_router

# Importar router de IPFS
from backend.ipfs_routes import ipfs_router

# --- Integración Web3 (TEMPORALMENTE DESACTIVADA) ---
# from ssi.did import DID, DIDMethod
# from ssi.vc import VerifiableCredential
# import didkit

# Añadir la ruta del modelo al path del sistema
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = FastAPI(
    title="OrthoWeb3 Real AI API",
    description="API para diagnóstico de maloclusiones usando un modelo de IA real con autenticación e IPFS.",
    version="2.2.0"
)

# Registrar routers
app.include_router(auth_router)
app.include_router(ipfs_router)

app.include_router(deepseek_router)

# También puedes añadir un endpoint de bienvenida que muestre los servicios:
@app.get("/")
async def root():
    return {
        "app": "OrthoWeb3",
        "version": "1.0.0",
        "services": {
            "deepseek_selenium": selenium_service.is_ready,
            "endpoints": {
                "dental_analysis": "/api/deepseek/analyze-dental-selenium",
                "health_check": "/api/deepseek/selenium-health",
                "test": "/api/deepseek/test-dental"
            }
        }
    }



# Configuración de CORS para permitir peticiones desde el frontend de React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # URL de desarrollo de Vite/React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Variables Globales ---
model = None
segmentation_model = None # Nueva variable para el modelo de segmentación
model_metrics = {}
class_descriptions = {
    "clase_i_normal": "Oclusión dental normal donde la cúspide del primer molar superior ocluye en el surco del primer molar inferior.",
    "clase_ii_division1": "Maloclusión donde el molar inferior está distalmente posicionado en relación al superior, con incisivos superiores protruidos.",
    "clase_ii_division2": "Maloclusión donde el molar inferior está distalmente posicionado, con incisivos superiores retroinclinados.",
    "clase_iii": "Maloclusión donde el molar inferior está mesialmente posicionado en relación al superior (prognatismo mandibular).",
    "mordida_abierta": "Falta de contacto vertical entre los dientes anteriores o posteriores cuando la mandíbula está en oclusión céntrica.",
    "mordida_cruzada": "Relación transversal anormal de los dientes, donde los dientes superiores ocluyen por dentro de los inferiores.",
    "mordida_profunda": "Sobreoclusión vertical excesiva de los incisivos superiores sobre los inferiores.",
    "caries": "Lesión destructiva del tejido dental causada por la desmineralización ácida de la placa bacteriana.",
    "apiñamiento": "Falta de espacio para que los dientes se alineen correctamente en el arco dental."
}

@app.on_event("startup")
def load_models_and_metrics():
    """Cargar los modelos y las métricas al iniciar la API."""
    global model, segmentation_model, model_metrics
    
    # Cargar modelo de clasificación
    model_path = "ml-models/trained_models/real_ortho_model.h5"
    metrics_path = "ml-models/trained_models/real_ortho_model_metrics.json"
    
    try:
        if os.path.exists(model_path):
            model = tf.keras.models.load_model(model_path, compile=False)
            model.compile(metrics=['accuracy']) # Re-compilar para tener métricas
            print("✅ Modelo de IA de clasificación cargado exitosamente.")
        else:
            print("❌ ERROR: Archivo del modelo de clasificación no encontrado en", model_path)

        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                model_metrics = json.load(f)
            print("✅ Métricas del modelo cargadas.")
        else:
            print("⚠️ Advertencia: Archivo de métricas no encontrado.")

    except Exception as e:
        print(f"❌ Error crítico al cargar el modelo de clasificación: {e}")
        model = None

    # Cargar modelo de segmentación
    seg_model_path = "ml-models/trained_models/unet_dental_model.h5"
    try:
        if os.path.exists(seg_model_path):
            segmentation_model = tf.keras.models.load_model(seg_model_path, compile=False)
            print("✅ Modelo de IA de segmentación cargado exitosamente.")
        else:
            print("❌ ERROR: Archivo del modelo de segmentación no encontrado en", seg_model_path)
    except Exception as e:
        print(f"❌ Error crítico al cargar el modelo de segmentación: {e}")
        segmentation_model = None

@app.get("/health", summary="Verificar estado de la API")
def health_check():
    """Endpoint para verificar que la API y el modelo están funcionando."""
    return {
        "status": "healthy",
        "classification_model_loaded": model is not None,
        "segmentation_model_loaded": segmentation_model is not None, # Nuevo estado
        "class_count": len(model_metrics.get('classes', [])),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/model-info", summary="Obtener información del modelo")
def get_model_info():
    """Devuelve las métricas de entrenamiento y las clases que el modelo puede predecir."""
    if not model_metrics:
        raise HTTPException(status_code=404, detail="Información del modelo no disponible.")
    
    return {
        "training_metrics": model_metrics,
        "class_count": len(model_metrics.get('classes', [])),
        "classes": model_metrics.get('classes', []),
        "class_descriptions": class_descriptions
    }

def preprocess_image(image_data: bytes, target_size=(512, 512), color_mode='RGB'):
    """Preprocesar la imagen para que coincida con la entrada de un modelo."""
    img = Image.open(io.BytesIO(image_data))
    if color_mode == 'L': # Grayscale for segmentation
        img = img.convert('L')
    else: # RGB for classification
        img = img.convert('RGB')
        
    img = img.resize(target_size)
    img_array = tf.keras.utils.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0
    return img_array

def get_segmentation_polygons(image_data: bytes):
    """Ejecuta el modelo de segmentación y devuelve los polígonos."""
    if segmentation_model is None:
        return None

    try:
        # Preprocesar para el modelo de segmentación (escala de grises)
        processed_image = preprocess_image(image_data, target_size=(512, 512), color_mode='L')
        
        # Predicción de la máscara
        pred_mask = segmentation_model.predict(processed_image, verbose=0)[0]
        
        # Post-proceso: binarizar y encontrar contornos
        pred_mask_binary = (pred_mask > 0.5).astype(np.uint8) * 255
        pred_mask_binary = pred_mask_binary.squeeze()

        # Encontrar contornos
        contours, _ = cv2.findContours(pred_mask_binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        polygons = []
        for contour in contours:
            # Simplificar el contorno para reducir el número de puntos
            if len(contour) > 0:
                # Aproximar el contorno a un polígono
                epsilon = 0.005 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Convertir a una lista de puntos [[x1, y1], [x2, y2], ...]
                polygons.append(approx.squeeze().tolist())
        
        return polygons
    except Exception as e:
        print(f"Error durante la segmentación: {e}")
        return None


@app.post("/analyze", summary="Analizar una imagen dental")
async def analyze_image(file: UploadFile = File(...), patient_did: str = None):
    """Recibe una imagen, la procesa con los modelos de IA y devuelve el diagnóstico y la segmentación."""
    if model is None:
        raise HTTPException(status_code=503, detail="El modelo de IA de clasificación no está cargado.")

    image_data = await file.read()
    
    # --- Clasificación ---
    processed_image_class = preprocess_image(image_data, target_size=(512, 512), color_mode='RGB')
    predictions = model.predict(processed_image_class)[0]
    predicted_class_index = np.argmax(predictions)
    confidence = float(predictions[predicted_class_index])
    
    classes = model_metrics.get('classes', [])
    if not classes or predicted_class_index >= len(classes):
        raise HTTPException(status_code=500, detail="Las clases del modelo no están configuradas correctamente.")
        
    predicted_class_name = classes[predicted_class_index]
    
    # --- Segmentación ---
    polygons = get_segmentation_polygons(image_data)
    
    # --- Generación de Credencial Verificable (Placeholder) ---
    vc_jwt = None
    
    results = {
        "analysis_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "prediction": {
            "class": predicted_class_name,
            "confidence": confidence,
            "class_description": class_descriptions.get(predicted_class_name, "Descripción no disponible.")
        },
        "segmentation_polygons": polygons, # Añadir los polígonos
        "analysis": {
            "primary_diagnosis": {"urgency": "medium"},
            "differential_diagnosis": [],
            "treatment_recommendations": {
                "main_recommendation": "Consultar con un ortodoncista para una evaluación completa.",
                "next_steps": ["Tomar radiografías panorámicas y cefalométricas.", "Realizar modelos de estudio."],
                "treatment_options": ["Ortodoncia fija (brackets)", "Ortodoncia removible (alineadores)"]
            }
        },
        "verifiable_credential_jwt": vc_jwt
    }

    return {"success": True, "results": results}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Backend Real de OrthoWeb3...")
    uvicorn.run(app, host="0.0.0.0", port=8004)
