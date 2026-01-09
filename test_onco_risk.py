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
