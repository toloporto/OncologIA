import sys
import os

# Añadir path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.cephalometric_service import cephalometric_service

def test_cephalometric_logic():
    print("🧪 Probando Lógica Cefalométrica...")
    
    # 1. Simular Puntos (Coordenadas XY)
    # Ejemplo de Clase I Esquelética
    landmarks_class_i = [
        {'id': 168, 'name': 'N', 'x': 0.5, 'y': 0.2},  # Nasion
        {'id': 164, 'name': 'A', 'x': 0.55, 'y': 0.5}, # Punto A
        {'id': 200, 'name': 'B', 'x': 0.53, 'y': 0.8}, # Punto B
    ]
    
    analysis = cephalometric_service.analyze_angles(landmarks_class_i)
    
    if 'anb' in analysis:
        val = analysis['anb']['value']
        status = analysis['anb']['status']
        print(f"✅ ANB calculado: {val:.2f}° ({status})")
        assert "Clase I" in status
    else:
        print("❌ Error: No se calculó el ángulo ANB")

    # 2. Simular Clase III (B adelantado respecto a A)
    landmarks_class_iii = [
        {'id': 168, 'name': 'N', 'x': 0.5, 'y': 0.2},
        {'id': 164, 'name': 'A', 'x': 0.52, 'y': 0.5},
        {'id': 200, 'name': 'B', 'x': 0.54, 'y': 0.8},
    ]
    
    analysis_iii = cephalometric_service.analyze_angles(landmarks_class_iii)
    val_iii = analysis_iii['anb']['value']
    status_iii = analysis_iii['anb']['status']
    print(f"✅ ANB Clase III: {val_iii:.2f}° ({status_iii})")
    assert val_iii < 0 or "Clase III" in status_iii

    print("\n✨ Pruebas matemáticas completadas con éxito.")

if __name__ == "__main__":
    test_cephalometric_logic()
