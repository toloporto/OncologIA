import cv2
import mediapipe as mp
import numpy as np

# Configuración de MediaPipe
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

import os
# Cargar imagen de prueba
# Usar ruta absoluta basada en la ubicación del script
base_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(base_dir, "public_images", "face.jpg")
print(f"Cargando imagen desde: {image_path}")

img = cv2.imread(image_path)
if img is None:
    print("Error: No se encontró la imagen. Asegúrate de que existe.")
    exit()

# Convertir a RGB (MediaPipe usa RGB)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Inicializar Face Mesh
print("Iniciando detección de Face Mesh...")
with mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5) as face_mesh:

    # Procesar imagen
    results = face_mesh.process(img_rgb)

    # Dibujar resultados
    if results.multi_face_landmarks:
        print(f"¡Rostro detectado! Encontrados {len(results.multi_face_landmarks)} rostros.")
        
        annotated_image = img.copy()
        for face_landmarks in results.multi_face_landmarks:
            print("Dibujando malla facial...")
            
            # Dibujar la malla (tesselation)
            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
            
            # Dibujar contornos (ojos, labios, cara)
            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style())

        # Guardar resultado
        output_path = "public_images/test_mediapipe_result.jpg"
        cv2.imwrite(output_path, annotated_image)
        print(f"✅ Resultado guardado en: {output_path}")
        print("Abre esa imagen para ver la malla facial detectada.")
    else:
        print("❌ No se detectó ningún rostro en la imagen.")
