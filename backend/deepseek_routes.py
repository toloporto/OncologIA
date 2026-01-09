"""
Rutas para DeepSeek API integration - Versión actualizada con Selenium
CORREGIDA: Solo una importación de selenium_service
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
import logging

# ✅ SOLO UNA importación - usa UNA de estas opciones:

# OPCIÓN 1: Importar la instancia DIRECTAMENTE (si tu archivo selenium_service.py la tiene)
from backend.services.selenium_service import selenium_service

# OPCIÓN 2: O importar la clase y crear instancia (si prefieres)
# from services.selenium_service import SeleniumDeepSeekService
# selenium_service = SeleniumDeepSeekService()

# Importar autenticación
from backend.auth_simple import get_current_user  # Tu sistema de auth existente

router = APIRouter(prefix="/api/deepseek", tags=["DeepSeek AI"])
logger = logging.getLogger(__name__)

@router.post("/analyze-dental-selenium")
async def analyze_dental_selenium(
    case_data: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analiza caso dental usando DeepSeek vía Selenium
    
    Request body ejemplo:
    {
        "patient_info": {
            "age": 25,
            "gender": "female",
            "name": "Ana López"
        },
        "clinical_data": {
            "reason": "Dientes torcidos",
            "skeletal_class": "Class II",
            "overjet": "7mm",
            "overbite": "5mm",
            "crowding": "moderate",
            "specific_issues": "Canino incluido"
        }
    }
    """
    try:
        logger.info(f"🦷 Análisis dental solicitado por {current_user.get('username', 'anon')}")
        
        # Validar datos requeridos
        if not case_data.get("clinical_data", {}).get("reason"):
            raise HTTPException(
                status_code=400, 
                detail="El motivo de consulta es requerido"
            )
        
        # Usar servicio Selenium
        result = selenium_service.analyze_medical_case(case_data)
        
        if result["success"]:
            return {
                "status": "success",
                "user": current_user["username"],
                "analysis": result["analysis"],
                "service": result["service"],
                "raw_response_preview": result.get("raw_response", "")[:300] + "...",
                "has_fallback": False
            }
        else:
            # Si hay fallback analysis, devolverlo con warning
            if result.get("fallback_analysis"):
                return {
                    "status": "partial",
                    "warning": "Usando análisis de respaldo",
                    "analysis": result["fallback_analysis"],
                    "error": result.get("error"),
                    "service": result["service"]
                }
            
            raise HTTPException(
                status_code=503,
                detail=f"Análisis no disponible: {result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en análisis Selenium: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/selenium-health")
async def selenium_health_check():
    """Verifica estado del servicio Selenium"""
    return {
        "service": "DeepSeek Selenium",
        "status": "ready" if selenium_service.is_ready else "not_ready",
        "is_ready": selenium_service.is_ready,
        "config": {
            "headless": selenium_service.config["headless"],
            "timeout": selenium_service.config["timeout"]
        }
    }

@router.post("/start-selenium")
async def start_selenium_service(current_user: Dict = Depends(get_current_user)):
    """Inicia manualmente el servicio Selenium (para admin)"""
    # Puedes añadir validación de rol aquí
    try:
        success = selenium_service.start()
        return {
            "status": "started" if success else "failed",
            "is_ready": selenium_service.is_ready,
            "message": "Servicio Selenium iniciado" if success else "No se pudo iniciar"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-selenium")
async def stop_selenium_service(current_user: Dict = Depends(get_current_user)):
    """Detiene el servicio Selenium"""
    try:
        selenium_service.stop()
        return {
            "status": "stopped",
            "is_ready": False,
            "message": "Servicio Selenium detenido"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-dental")
async def test_dental_analysis():
    """Endpoint de prueba sin autenticación"""
    test_case = {
        "patient_info": {
            "age": 14,
            "gender": "female",
            "name": "Test Patient"
        },
        "clinical_data": {
            "reason": "Consulta por dientes torcidos y apiñados",
            "skeletal_class": "Class II",
            "overjet": "7mm",
            "overbite": "5mm",
            "crowding": "moderate",
            "specific_issues": "Canino incluido, mordida profunda"
        }
    }
    
    result = selenium_service.analyze_medical_case(test_case)
    
    return {
        "test": True,
        "case": test_case,
        "result": result
    }