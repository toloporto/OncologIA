
import sys
import os
import datetime
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.services.oncology_evolution_service import oncology_evolution_service

# Mock para SessionLog
@dataclass
class MockLog:
    created_at: datetime.datetime
    emotion_analysis: dict

def test_evolution_service():
    print("\n" + "="*60)
    print("📈 VERIFICACIÓN: Monitor de Evolución Oncológica")
    print("="*60 + "\n")
    
    # Simular historial de un paciente (últimos 4 días)
    # Caso: Dolor empeorando (3 -> 5 -> 7 -> 9)
    # Caso: Ansiedad estable (2 -> 2 -> 2 -> 2)
    base_time = datetime.datetime.now()
    
    history = [
        MockLog(
            created_at=base_time - datetime.timedelta(days=3),
            emotion_analysis={"pain": 3.0, "anxiety": 2.0}
        ),
        MockLog(
            created_at=base_time - datetime.timedelta(days=2),
            emotion_analysis={"pain": 5.0, "anxiety": 2.1}
        ),
        MockLog(
            created_at=base_time - datetime.timedelta(days=1),
            emotion_analysis={"pain": 7.0, "anxiety": 1.9}
        ),
        MockLog(
            created_at=base_time,
            emotion_analysis={"pain": 9.0, "anxiety": 2.0}
        )
    ]
    
    print("🧠 Analizando historial simulado...")
    result = oncology_evolution_service.analyze_evolution(history)
    
    # Verificar Resultados
    alerts = result['alerts']
    trends = result['trends']
    
    print(f"\n📊 Tendencias Calculadas (Pendiente):")
    for symptom, slope in trends.items():
        if slope != 0:
            print(f"   - {symptom.capitalize()}: {slope:.2f} pts/día")
            
    print(f"\n🚨 Alertas Generadas:")
    for alert in alerts:
        icon = "🔴" if alert['severity'] == 'high' else "⚠️"
        print(f"   {icon} {alert['message']}")

    # Validaciones Automáticas
    pain_slope = trends.get('pain', 0)
    has_critical_alert = any(a['type'] == 'critical_level' for a in alerts)
    
    if pain_slope > 1.5 and has_critical_alert:
        print("\n✅ PRUEBA EXITOSA: Se detectó el empeoramiento del dolor y se generó alerta crítica.")
    else:
        print("\n❌ PRUEBA FALLIDA: No se detectaron las tendencias esperadas.")

if __name__ == "__main__":
    test_evolution_service()
