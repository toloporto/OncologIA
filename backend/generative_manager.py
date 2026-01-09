import cv2
import numpy as np
import base64
import io
from PIL import Image, ImageEnhance
# import mediapipe as mp # Lazy Load

class GenerativeTreatmentManager:
    def __init__(self):
        self.model_loaded = True
    def __init__(self):
        self.model_loaded = True
        self.face_mesh = None # Lazy initialization
        self.mp_face_mesh = None

    def _get_face_mesh(self):
        if self.face_mesh is None:
            import mediapipe as mp # Lazy Import
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            )
        return self.face_mesh
        # Índices de labios internos (boca abierta)
        self.INNER_LIPS_INDICES = [
            78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 
            308, 324, 318, 402, 317, 14, 87, 178, 88, 95
        ]
        
    def simulate_treatment(self, image_data, treatment_type="aligner"):
        """
        Simula un resultado de tratamiento usando IA (MediaPipe) para realismo.
        """
        try:
            # 1. Decodificar imagen
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("No se pudo decodificar la imagen")

            # 2. Detectar Rostro y Dientes
            landmarks = self._get_landmarks(img)
            
            if landmarks:
                # MODO REALISTA (Con detección facial)
                mask = self._create_teeth_mask(img, landmarks)
                
                if treatment_type == "whitening":
                    img_result = self._apply_whitening_realistic(img, mask)
                    desc = "Simulación IA: Blanqueamiento Dental (Segmentación Precisa)"
                elif treatment_type == "brackets":
                    img_result = self._apply_brackets_realistic(img, landmarks)
                    desc = "Simulación IA: Ortodoncia (Arco Ajustado a Sonrisa)"
                else: # aligner
                    img_result = self._apply_aligners_realistic(img, mask)
                    desc = "Simulación IA: Alineadores (Efecto Gloss en Dientes)"
            else:
                # MODO FALLBACK (Sin detección facial - Efectos globales)
                print("⚠️ No se detectó rostro. Usando modo fallback.")
                if treatment_type == "whitening":
                    img_result = self._apply_whitening_fallback(img)
                elif treatment_type == "brackets":
                    img_result = self._apply_brackets_fallback(img)
                else:
                    img_result = self._apply_aligners_fallback(img)
                desc = "Simulación Básica (Rostro no detectado)"

            # 3. Añadir marca de agua
            self._add_watermark(img_result, f"SIMULACION: {treatment_type.upper()}")

            # 4. Generar resultado
            _, buffer = cv2.imencode('.jpg', img_result)
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "success": True,
                "treatment_type": treatment_type,
                "after_image_base64": img_b64,
                "description": desc
            }

        except Exception as e:
            print(f"Error en simulación generativa: {e}")
            raise e

    def _get_landmarks(self, img):
        """Detecta landmarks faciales"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    def _get_landmarks(self, img):
        """Detecta landmarks faciales"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_mesh = self._get_face_mesh()
        results = face_mesh.process(img_rgb)
        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0].landmark
        return None

    def _create_teeth_mask(self, img, landmarks):
        """Crea una máscara binaria de la zona de los dientes (labios internos)"""
        h, w = img.shape[:2]
        lip_points = []
        for index in self.INNER_LIPS_INDICES:
            pt = landmarks[index]
            x = int(pt.x * w)
            y = int(pt.y * h)
            lip_points.append((x, y))
        
        lip_points = np.array(lip_points, dtype=np.int32)
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [lip_points], 255)
        return mask

    # --- EFECTOS REALISTAS (Con Máscara/Landmarks) ---

    def _apply_whitening_realistic(self, img, mask):
        """Blanquea SOLO el área de los dientes"""
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(img_hsv)

        # Aumentar brillo (V) y reducir saturación (S) solo en la máscara
        # Esto quita el tono amarillo y hace los dientes más blancos
        s = np.where(mask == 255, cv2.multiply(s, 0.7).astype(np.uint8), s) # Menos amarillo
        v = np.where(mask == 255, cv2.add(v, 40).astype(np.uint8), v)       # Más brillo

        final_hsv = cv2.merge([h, s, v])
        img_result = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        
        # Añadir un ligero tinte azulado solo a los dientes para efecto "blanco polar"
        blue_tint = img_result.copy()
        blue_tint[:, :, 0] = cv2.add(blue_tint[:, :, 0], 20) # Canal Azul
        
        # Mezclar usando la máscara
        img_final = np.where(mask[:, :, None] == 255, blue_tint, img_result)
        return img_final

    def _apply_brackets_realistic(self, img, landmarks):
        """Dibuja brackets realistas usando distribución geométrica confiable"""
        img_cv = img.copy()
        h, w = img_cv.shape[:2]
        
        # Usar landmarks de las comisuras de la boca para determinar el ancho
        # 61 = comisura izquierda, 291 = comisura derecha
        left_corner = landmarks[61]
        right_corner = landmarks[291]
        
        # Labio superior centro
        upper_lip_center = landmarks[13]
        
        # Calcular posiciones
        mouth_left_x = int(left_corner.x * w)
        mouth_right_x = int(right_corner.x * w)
        mouth_y = int(upper_lip_center.y * h)
        
        # Ajustar Y para que esté justo encima del labio superior (donde están los dientes)
        teeth_y = mouth_y - 8
        
        # Generar 8 posiciones equidistantes para los brackets
        num_brackets = 8
        mouth_width = mouth_right_x - mouth_left_x
        
        # Añadir margen para no poner brackets en las comisuras
        margin = mouth_width * 0.1
        usable_width = mouth_width - (2 * margin)
        spacing = usable_width / (num_brackets - 1)
        
        points = []
        for i in range(num_brackets):
            x = int(mouth_left_x + margin + (i * spacing))
            y = teeth_y
            points.append((x, y))
        
        # 1. Generar textura de bracket
        bracket_texture = self._create_bracket_texture(size=(12, 12))
        
        # 2. Dibujar alambre (curva suave)
        self._draw_orthodontic_wire(img_cv, points)
        
        # 3. Aplicar brackets
        for i, pt in enumerate(points):
            # Calcular ángulo basado en la curvatura del arco dental
            # Los dientes centrales están más rectos, los laterales más inclinados
            center_index = num_brackets / 2
            distance_from_center = abs(i - center_index)
            angle = distance_from_center * 3  # Inclinación gradual
            if i < center_index:
                angle = -angle  # Invertir para el lado izquierdo
            
            # Añadir sombra
            self._add_bracket_shadow(img_cv, pt, 12)
            
            # Aplicar bracket
            self._apply_perspective_bracket(img_cv, pt, angle, bracket_texture)
        
        return img_cv
    
    def _create_bracket_texture(self, size=(16, 16)):
        """Genera una textura realista de bracket metálico"""
        bracket = np.ones((size[1], size[0], 3), dtype=np.uint8) * 180
        
        # Gradiente vertical para simular curvatura
        for y in range(size[1]):
            factor = 1.0 - abs(y - size[1]//2) / (size[1]//2) * 0.3
            bracket[y, :] = (bracket[y, :] * factor).astype(np.uint8)
        
        # Borde oscuro (sombra)
        cv2.rectangle(bracket, (0, 0), (size[0]-1, size[1]-1), (80, 80, 80), 1)
        
        # Highlight central (reflejo)
        cv2.ellipse(bracket, (size[0]//2, size[1]//3), 
                    (size[0]//3, size[1]//4), 0, 0, 360, (220, 220, 230), -1)
        
        # Slot central (ranura para alambre)
        slot_y = size[1] // 2
        cv2.rectangle(bracket, (2, slot_y-1), (size[0]-3, slot_y+1), (60, 60, 60), -1)
        
        return bracket
    
    def _calculate_tooth_angle(self, points, index):
        """Calcula el ángulo de inclinación del diente"""
        if index == 0 or index >= len(points) - 1:
            return 0
        
        # Vector entre puntos adyacentes
        p_prev, p_curr, p_next = points[index-1], points[index], points[index+1]
        
        # Tangente promedio
        dx = (p_next[0] - p_prev[0]) / 2
        dy = (p_next[1] - p_prev[1]) / 2
        
        angle = np.degrees(np.arctan2(dy, dx))
        return angle
    
    def _add_bracket_shadow(self, img, center, size):
        """Añade sombra suave alrededor del bracket"""
        x, y = center
        shadow_radius = size // 2 + 2
        
        # Crear máscara de sombra con gradiente radial
        overlay = img.copy()
        cv2.circle(overlay, (x, y+1), shadow_radius, (0, 0, 0), -1)
        
        # Blend con baja opacidad
        cv2.addWeighted(overlay, 0.15, img, 0.85, 0, img)
    
    def _apply_perspective_bracket(self, img, center, angle, bracket_texture):
        """Aplica bracket con rotación y perspectiva"""
        h, w = bracket_texture.shape[:2]
        
        # Matriz de rotación
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
        rotated = cv2.warpAffine(bracket_texture, M, (w, h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=(0, 0, 0))
        
        # Posicionar en la imagen
        x, y = center
        x1, y1 = max(0, x - w//2), max(0, y - h//2)
        x2, y2 = min(img.shape[1], x + w//2), min(img.shape[0], y + h//2)
        
        # Calcular región válida
        bx1, by1 = max(0, w//2 - x), max(0, h//2 - y)
        bx2, by2 = bx1 + (x2 - x1), by1 + (y2 - y1)
        
        if bx2 > bx1 and by2 > by1:
            # Crear máscara alpha simple (bordes suaves)
            bracket_region = rotated[by1:by2, bx1:bx2]
            
            # Detectar píxeles negros (fondo) para transparencia
            mask = np.all(bracket_region == [0, 0, 0], axis=-1)
            
            # Blend con la imagen original
            for c in range(3):
                img[y1:y2, x1:x2, c] = np.where(
                    mask,
                    img[y1:y2, x1:x2, c],
                    bracket_region[:, :, c]
                )
        
        return img
    
    def _draw_orthodontic_wire(self, img, points):
        """Dibuja alambre con curva suave y sombreado"""
        # Convertir a array numpy
        pts = np.array(points, dtype=np.int32)
        
        # Dibujar sombra (offset hacia abajo)
        shadow_pts = pts + np.array([1, 2])
        cv2.polylines(img, [shadow_pts], False, (60, 60, 60), 3, cv2.LINE_AA)
        
        # Dibujar alambre principal (metálico)
        cv2.polylines(img, [pts], False, (140, 140, 140), 2, cv2.LINE_AA)
        
        # Highlight superior (reflejo)
        highlight_pts = pts - np.array([0, 1])
        cv2.polylines(img, [highlight_pts], False, (180, 180, 190), 1, cv2.LINE_AA)

    def _apply_aligners_realistic(self, img, mask):
        """Aplica efecto gloss/plástico solo a los dientes"""
        # Suavizar solo el área de los dientes
        img_blur = cv2.bilateralFilter(img, 9, 75, 75)
        
        # Aumentar brillo (reflejos)
        img_bright = cv2.add(img_blur, np.array([30.0]))
        
        # Combinar: Fondo original + Dientes procesados
        img_final = np.where(mask[:, :, None] == 255, img_bright, img)
        
        # Añadir grid sutil solo en dientes
        overlay = img_final.copy()
        h, w = img.shape[:2] # Get h, w here
        step = 20
        for x in range(0, w, step):
            cv2.line(overlay, (x, 0), (x, h), (255, 255, 255), 1)
            
        # Mezclar grid solo en la máscara
        alpha = 0.15
        img_grid = cv2.addWeighted(overlay, alpha, img_final, 1 - alpha, 0)
        img_final = np.where(mask[:, :, None] == 255, img_grid, img_final)
        
        return img_final

    # --- MODOS FALLBACK (Código anterior mejorado) ---

    def _apply_whitening_fallback(self, img):
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Brightness(pil_img)
        pil_img = enhancer.enhance(1.4)
        img_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        img_cv[:, :, 0] = cv2.add(img_cv[:, :, 0], 30) 
        return img_cv

    def _apply_brackets_fallback(self, img):
        img_cv = img.copy()
        h, w = img_cv.shape[:2]
        y_pos = h // 2
        cv2.line(img_cv, (0, y_pos), (w, y_pos), (100, 100, 100), 2)
        num_brackets = 8
        step = w // num_brackets
        for i in range(num_brackets):
            x = (i * step) + (step // 2)
            cv2.rectangle(img_cv, (x-10, y_pos-10), (x+10, y_pos+10), (192, 192, 192), -1)
        return img_cv

    def _apply_aligners_fallback(self, img):
        img_cv = cv2.bilateralFilter(img, 9, 75, 75)
        return cv2.add(img_cv, np.array([20.0]))

    def _add_watermark(self, img, text):
        """Añade texto sobre la imagen"""
        h, w = img.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.8
        thickness = 2
        color = (0, 255, 255) # Amarillo
        (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
        x = (w - text_w) // 2
        y = h - 20
        cv2.putText(img, text, (x+2, y+2), font, scale, (0,0,0), thickness+1)
        cv2.putText(img, text, (x, y), font, scale, color, thickness)

# Alias para compatibilidad
GenerativeManager = GenerativeTreatmentManager
