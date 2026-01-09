import sys
import os
import datetime
from datetime import timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir path para importar backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar servicio (mockeando DB para prueba aislada)
from backend.services.temporal_service import TemporalAnalysisService
from backend.models import AnalysisResult

def create_mock_analysis(date, severity, diagnosis_id):
    """Factory de objetos AnalysisResult falsos"""
    return AnalysisResult(
        id=f"mock_{diagnosis_id}",
        timestamp=date,
        predicted_class="custom_class", # El servicio recalculará severidad, así que lo "hackeamos" abajo
        severity=severity, # Inyectamos severidad directamente si el servicio lo soporta o modificamos SEVERITY_MAP
        # Nota: Como temporal_service.get_severity_score usa un mapa, necesitamos
        # simular que la clase predicha corresponde a esa severidad.
        # Para simplificar el test, vamos a MONKEY PATCHEAR get_severity_score temporalmente
        # o asumimos que 'custom_class' devolverá un default.
        # Mejor estrategia: Modificamos el objeto devuelto por _build_timeline que es lo que realmente usa la lógica.
        # Pero _build_timeline lee de AnalysisResult.
        # Haremos un truco: Usaremos diagnosis conocidos cercanos a la severidad deseada.
    )

class MockTemporalService(TemporalAnalysisService):
    """Sobreescribimos método auxiliar para inyectar severidad exacta sin depender del mapa de clases"""
    def _build_timeline(self, history):
        timeline = []
        for i, item in enumerate(history):
            # Usamos un atributo temporal inyectado 'severity_override' si existe
            sev = getattr(item, 'severity_override', 5)
            timeline.append({
                "date": item.timestamp.isoformat(),
                "timestamp": item.timestamp,
                "diagnosis": "mock_diagnosis",
                "severity": sev,
                "analysis_id": item.id,
                "image": "mock.jpg"
            })
        # Ordenar como lo hace el real
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline

def test_temporal_analysis():
    print("🚀 Iniciando Test de Lógica Temporal Híbrida (Lineal + LSTM)...")
    
    service = MockTemporalService()
    
    # CASO 1: Insuficientes datos (< 5) -> Debe usar Regresión Lineal
    print("\n🧪 CASO 1: Historial Corto (3 puntos) - Esperado: Regresión Lineal")
    history_short = []
    start_date = datetime.datetime.now() - timedelta(days=60)
    sevs = [8, 6, 4] # Mejora lineal rápida
    for i, s in enumerate(sevs):
        r = AnalysisResult(id=str(i), timestamp=start_date + timedelta(days=i*30))
        r.severity_override = s
        history_short.append(r)
        
    result_short = service.analyze_progress(history_short)
    tr = result_short['trend']
    print(f"   Pendiente: {tr['slope']:.2f}")
    print(f"   Predicción (30d): {tr['predicted_severity_next_month']:.2f}")
    print(f"   Método Usado: {tr.get('prediction_method', 'unknown')}")
    
    if tr.get('prediction_method') == 'linear_regression':
        print("   ✅ Fallback a Lineal correcto.")
    else:
        print("   ❌ Error: Debería haber usado regresión lineal.")

    # CASO 2: Suficientes datos (>= 5) pero LINEAL -> LSTM debería coincidir aprox con Lineal
    print("\n🧪 CASO 2: Historial Largo Lineal (6 puntos)")
    history_linear = []
    sevs_long = [9, 8, 7, 6, 5, 4] # Mejora constante perfecta
    for i, s in enumerate(sevs_long):
        r = AnalysisResult(id=str(i), timestamp=start_date + timedelta(days=i*30))
        r.severity_override = s
        history_linear.append(r)
        
    result_linear = service.analyze_progress(history_linear)
    tr = result_linear['trend']
    print(f"   Predicción IA (30d): {tr['predicted_severity_next_month']:.2f}")
    print(f"   Método Usado: {tr.get('prediction_method', 'unknown')}")
    
    # CASO 3: RECUPERACIÓN COMPLEJA (Rápida mejora -> Estancamiento)
    # Típico en ortodoncia: primeros meses mucho movimiento, luego ajuste fino lento.
    print("\n🧪 CASO 3: Historia Compleja (Logarítmica/Estancada)")
    history_complex = []
    
    # Mes 0-2: Mejora rápida (8 -> 3)
    # Mes 3-5: Estancamiento (3 -> 3 -> 2.8)
    sevs_complex = [8, 6, 4, 3, 3, 2.8] 
    
    for i, s in enumerate(sevs_complex):
        r = AnalysisResult(id=str(i), timestamp=start_date + timedelta(days=i*30))
        r.severity_override = s
        history_complex.append(r)

    result_complex = service.analyze_progress(history_complex)
    tr = result_complex['trend']
    
    print(f"   Pendiente Global (Lineal): {tr['slope']:.4f}")
    print(f"   Predicción IA (30d): {tr['predicted_severity_next_month']:.2f}")
    print(f"   Método Usado: {tr.get('prediction_method', 'unknown')}")
    print(f"   Estado: {tr['status']}")
    print(f"   Desc: {tr['description']}")
    
    # Verificación
    if tr.get('prediction_method') == 'lstm_neural_network':
        print("   ✅ LSTM activada correctamente para historial complejo.")
    else:
        print("   ⚠️ LSTM no activada (posible error de importación o falta de datos).")

if __name__ == "__main__":
    test_temporal_analysis()
