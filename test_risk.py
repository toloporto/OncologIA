from backend.services.risk_service import risk_service
import random

def main():
    print("📉 Iniciando Simulación de Riesgo Predictivo...")

    # Caso 1: Paciente Estable
    print("\n🟢 Caso 1: Paciente Estable")
    history_stable = []
    for i in range(10):
        history_stable.append({
            "date": f"2025-01-{i+1:02d}",
            "emotions": {
                "sadness": random.uniform(0.1, 0.2), # Siempre bajo
                "joy": random.uniform(0.6, 0.8),     # Siempre alto
                "fear": 0.1
            }
        })
    result = risk_service.analyze_risk(history_stable)
    print(f"   Riesgo: {result['risk_level']}")
    print(f"   Acción: {result['recommended_action']}")

    # Caso 2: Paciente en Deterioro (Recaída Simulada)
    print("\n🚨 Caso 2: Paciente en Deterioro Rápido")
    history_relapse = []
    # Generamos una curva donde la tristeza sube escalonadamente 0.1 cada sesión
    for i in range(10):
        sadness = 0.1 + (i * 0.08) # Empieza en 0.1, acaba en 0.9!!
        if sadness > 0.9: sadness = 0.9
        
        joy = 0.9 - (i * 0.08)     # Empieza feliz, acaba hundido
        if joy < 0.1: joy = 0.1

        history_relapse.append({
            "date": f"2025-02-{i+1:02d}",
            "emotions": {
                "sadness": sadness,
                "joy": joy,
                "fear": 0.2
            }
        })
        
    print("   Analizando tendencia de 10 sesiones...")
    result = risk_service.analyze_risk(history_relapse)
    
    print(f"   Riesgo Calculado: {result['risk_level']}")
    print(f"   Motivos Detectados:")
    for reason in result['reasons']:
        print(f"    - {reason}")
    print(f"   Acción Recomendada: {result['recommended_action']}")

if __name__ == "__main__":
    main()
