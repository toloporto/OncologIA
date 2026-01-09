"""
Servicio de Cefalometría para OrthoWeb3
Calcula ángulos médicos y diagnósticos geométricos
"""

import numpy as np
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class CephalometricService:
    """Calcula medidas cefalométricas y ángulos ortodónticos"""

    def calculate_angle(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> float:
        """
        Calcula el ángulo formado por tres puntos (p1, p2, p3) donde p2 es el vértice.
        Retorna el ángulo en grados.
        """
        try:
            v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
            v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
            
            unit_v1 = v1 / (np.linalg.norm(v1) + 1e-10)
            unit_v2 = v2 / (np.linalg.norm(v2) + 1e-10)
            
            dot_product = np.dot(unit_v1, unit_v2)
            angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
            
            return float(np.degrees(angle))
        except Exception as e:
            logger.error(f"Error calculando ángulo: {e}")
            return 0.0

    def analyze_angles(self, landmarks: List[Dict]) -> Dict[str, Any]:
        """
        Calcula los ángulos estándar SNA, SNB y ANB.
        Asume que los landmarks traen IDs específicos o descriptivos.
        """
        # Intentar mapear puntos por ID o nombre
        # Nasion (N), Sella (S), Punto A, Punto B
        pts = {lm.get('name', str(lm.get('id'))): (lm['x'], lm['y']) for lm in landmarks}
        
        # Mapeo por ID (Ajustar según lo que devuelva el modelo o MediaPipe)
        # Aproximación MediaPipe: N=168, A=164, B=200. Sella es difícil sin rayos X.
        # Si no hay Sella (S), no podemos calcular SNA/SNB directamente, 
        # pero podemos calcular otros o aproximar S.
        
        n = pts.get('N') or pts.get('168')
        a = pts.get('A') or pts.get('164')
        b = pts.get('B') or pts.get('200')
        s = pts.get('S') # Sella turcica (punto interno)
        
        results = {}
        
        if n and a and b:
            # Ángulo ANB (Relación entre maxilar y mandíbula respecto a Nasion)
            # En cefalometría real es el ángulo en N entre NA y NB
            anb = self.calculate_angle(a, n, b)
            
            # Convención: Si A está por delante de B, ANB es positivo (+)
            # Si B está por delante de A (Clase III), ANB suele considerarse negativo o menor.
            # Aquí ajustamos el signo por posición relativa en X
            if a[0] < b[0]: # En imágenes, X suele aumentar hacia la derecha
                 anb = -anb
            
            results['anb'] = {
                'value': anb,
                'status': self._interpret_anb(anb),
                'label': 'Ángulo ANB'
            }

        if s and n and a:
            sna = self.calculate_angle(s, n, a)
            results['sna'] = {
                'value': sna,
                'status': 'Normal' if 80 <= sna <= 84 else 'Prognatismo' if sna > 84 else 'Retrognatismo',
                'label': 'Ángulo SNA'
            }

        if s and n and b:
            snb = self.calculate_angle(s, n, b)
            results['snb'] = {
                'value': snb,
                'status': 'Normal' if 78 <= snb <= 82 else 'Prognatismo' if snb > 82 else 'Retrognatismo',
                'label': 'Ángulo SNB'
            }

        return results

    def _interpret_anb(self, anb: float) -> str:
        """Interpretación clínica del ángulo ANB"""
        if 0 <= anb <= 4:
            return "Clase I (Esquelética Normal)"
        elif anb > 4:
            return "Clase II (Maxilar adelantado / Mandíbula retraída)"
        else:
            return "Clase III (Mandíbula adelantada / Prognatismo)"

# Instancia global
cephalometric_service = CephalometricService()
