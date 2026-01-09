# import mediapipe as mp # Lazy Load
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

class LandmarksService:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
    def __init__(self):
        # self.mp_face_mesh = mp.solutions.face_mesh # Moved to _get_face_mesh
        self.face_mesh = None # Lazy initialization

    def _get_face_mesh(self):
        """Inicializa FaceMesh solo cuando se necesita"""
        if self.face_mesh is None:
            logger.info("⏳ Inicializando MediaPipe FaceMesh bajo demanda...")
            try:
                import mediapipe as mp # Lazy Import
                self.mp_face_mesh = mp.solutions.face_mesh
                
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
            except Exception as e:
                logger.error(f"Error fatal inicializando MediaPipe: {e}")
                # Re-lanzar o manejar gracefuly dependiendo de la necesidad
                raise e
        return self.face_mesh

    def process_image(self, image_bytes):
        try:
            # Decodificar imagen
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("No se pudo decodificar la imagen")

            # Convertir a RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width, _ = image.shape

            # Procesar con MediaPipe (Lazy Load)
            face_mesh = self._get_face_mesh()
            results = face_mesh.process(image_rgb)

            if not results.multi_face_landmarks:
                return None

            # Extraer puntos (landmarks)
            landmarks = []
            face_landmarks = results.multi_face_landmarks[0]
            
            for idx, lm in enumerate(face_landmarks.landmark):
                landmarks.append({
                    'id': idx,
                    'x': float(lm.x),
                    'y': float(lm.y),
                    'z': float(lm.z),
                    'pixel_x': int(lm.x * width),
                    'pixel_y': int(lm.y * height)
                })

            # Calcular métricas básicas
            # Puntos clave de labios: superior (13), inferior (14)
            upper_lip = landmarks[13]
            lower_lip = landmarks[14]
            
            mouth_opening = np.sqrt(
                (upper_lip['x'] - lower_lip['x'])**2 + 
                (upper_lip['y'] - lower_lip['y'])**2
            )

            # Comisuras de los labios: izquierda (61), derecha (291)
            left_corner = landmarks[61]
            right_corner = landmarks[291]
            
            smile_width = np.sqrt(
                (left_corner['x'] - right_corner['x'])**2 + 
                (left_corner['y'] - right_corner['y'])**2
            )

            # MÉTRICAS AVANZADAS
            
            # 1. SIMETRÍA FACIAL
            # Comparar distancias entre puntos homólogos (izquierda vs derecha)
            # Puntos de referencia: nariz (1), ojo izq (33), ojo der (263)
            nose_tip = landmarks[1]
            left_eye = landmarks[33]
            right_eye = landmarks[263]
            
            # Distancia nariz-ojo izquierdo
            dist_nose_left = np.sqrt(
                (nose_tip['x'] - left_eye['x'])**2 + 
                (nose_tip['y'] - left_eye['y'])**2
            )
            
            # Distancia nariz-ojo derecho
            dist_nose_right = np.sqrt(
                (nose_tip['x'] - right_eye['x'])**2 + 
                (nose_tip['y'] - right_eye['y'])**2
            )
            
            # Simetría (0-100%, 100% = perfecta simetría)
            symmetry = 100 * (1 - abs(dist_nose_left - dist_nose_right) / max(dist_nose_left, dist_nose_right))
            
            # 2. ÁNGULO MANDIBULAR
            # Puntos: barbilla (152), mandíbula izq (234), mandíbula der (454)
            chin = landmarks[152]
            jaw_left = landmarks[234]
            jaw_right = landmarks[454]
            
            # Vectores
            vec_left = np.array([jaw_left['x'] - chin['x'], jaw_left['y'] - chin['y']])
            vec_right = np.array([jaw_right['x'] - chin['x'], jaw_right['y'] - chin['y']])
            
            # Ángulo entre vectores (en grados)
            cos_angle = np.dot(vec_left, vec_right) / (np.linalg.norm(vec_left) * np.linalg.norm(vec_right))
            jaw_angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
            
            # 3. PROPORCIÓN ÁUREA (Golden Ratio = 1.618)
            # Distancia vertical: frente (10) a barbilla (152)
            forehead = landmarks[10]
            vertical_dist = np.sqrt(
                (forehead['x'] - chin['x'])**2 + 
                (forehead['y'] - chin['y'])**2
            )
            
            # Distancia horizontal: ojo izq (33) a ojo der (263)
            horizontal_dist = np.sqrt(
                (left_eye['x'] - right_eye['x'])**2 + 
                (left_eye['y'] - right_eye['y'])**2
            )
            
            # Ratio calculado
            face_ratio = vertical_dist / horizontal_dist if horizontal_dist > 0 else 0
            
            # Proximidad a la proporción áurea (0-100%, 100% = ratio perfecto)
            golden_ratio = 1.618
            golden_ratio_score = 100 * (1 - abs(face_ratio - golden_ratio) / golden_ratio)
            golden_ratio_score = max(0, min(100, golden_ratio_score))  # Limitar a 0-100

            return {
                "detected": True,
                "total_landmarks": len(landmarks),
                "landmarks": landmarks,
                "metrics": {
                    # Métricas básicas
                    "mouth_opening": float(mouth_opening),
                    "smile_width": float(smile_width),
                    "face_width": width,
                    "face_height": height,
                    
                    # Métricas avanzadas
                    "facial_symmetry": float(symmetry),
                    "jaw_angle": float(jaw_angle),
                    "golden_ratio_score": float(golden_ratio_score),
                    "face_ratio": float(face_ratio),
                    
                    # Interpretaciones
                    "symmetry_status": "Excelente" if symmetry >= 95 else "Buena" if symmetry >= 85 else "Moderada" if symmetry >= 75 else "Baja",
                    "jaw_angle_status": "Normal" if 120 <= jaw_angle <= 140 else "Amplio" if jaw_angle > 140 else "Estrecho",
                    "golden_ratio_status": "Ideal" if golden_ratio_score >= 90 else "Buena" if golden_ratio_score >= 75 else "Aceptable"
                }
            }

        except Exception as e:
            logger.error(f"Error en LandmarksService: {e}")
            raise

# Instancia global
landmarks_service = LandmarksService()