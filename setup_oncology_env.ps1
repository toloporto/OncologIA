# setup_oncology_env.ps1
# Script de configuración para transformar PsicowebAI en OncologIA

Write-Host "💉 Iniciando Configuración de Entorno Oncológico..." -ForegroundColor Cyan

# 1. Reestructuración de Knowledge Base (RAG)
$kbPath = "C:\Users\antol\OncologIA\knowledge_base"

Write-Host "📂 Creando estructura de directorios en $kbPath..."
New-Item -ItemType Directory -Force -Path "$kbPath\pain_management" | Out-Null
New-Item -ItemType Directory -Force -Path "$kbPath\palliative_care" | Out-Null
New-Item -ItemType Directory -Force -Path "$kbPath\drug_interactions" | Out-Null
New-Item -ItemType Directory -Force -Path "$kbPath\patient_education" | Out-Null

Write-Host "✅ Carpetas creadas: pain_management, palliative_care, drug_interactions, patient_education" -ForegroundColor Green

# 2. Instalación de dependencias Python
Write-Host "💊 Instalando librerías Python necesarias..." -ForegroundColor Cyan
# fhir.resources: Manejo estricto de FHIR R4
# pint: Cálculo de dosis y unidades
# pandas: Si no está, útil para manejo de datos clínicos tabulares
pip install fhir.resources pint pandas --quiet
Write-Host "✅ Dependencias instaladas." -ForegroundColor Green

# 3. Generación de Script de Prueba (Risk Detector)
$testPyContent = @'
# test_onco_risk.py
import time

def check_oncology_risk(text):
    """Simulación de la lógica de guardián para Oncología"""
    keywords = {
        "disnea": ["no puedo respirar", "falta de aire", "ahogo", "asfixia"],
        "dolor_crisis": ["dolor insoportable", "eva 10", "gritos de dolor", "no aguanto el dolor"],
        "hemorragia": ["sangre", "vomitando sangre", "sangrado activo"],
        "sepsis": ["fiebre alta", "tiritona", "escalofríos intensos"],
        "compresion_medular": ["no siento las piernas", "piernas dormidas", "incontinencia"]
    }
    
    print(f"\n🩺 Analizando síntoma: '{text}'")
    risk_found = False
    
    text_lower = text.lower()
    
    for category, kws in keywords.items():
        for kw in kws:
            if kw in text_lower:
                print(f"   🚨 ALERTA ROJA ({category.upper()}): Detectado '{kw}'")
                risk_found = True
                
    if not risk_found:
        print("   ✅ Triaje: Estable / Sin riesgo vital inmediato.")

# Ejecutar pruebas
print("--- TEST DE SISTEMA DE ALERTA ONCOLÓGICA ---")
check_oncology_risk("Hoy me siento un poco más cansado de lo normal")
check_oncology_risk("Ayuda, tengo un dolor insoportable que no cede con la morfina")
check_oncology_risk("Mi padre dice que no puede respirar bien")
print("----------------------------------------------")
'@

Set-Content -Path "test_onco_risk.py" -Value $testPyContent
Write-Host "✅ Script de prueba generado: test_onco_risk.py" -ForegroundColor Green

# 4. Ejecución de prueba
Write-Host "🧪 Ejecutando prueba preliminar..." -ForegroundColor Yellow
python test_onco_risk.py

Write-Host "`n✅ PROCESO COMPLETADO. El sistema está listo para recibir los PDFs y modificaciones de código." -ForegroundColor Magenta
