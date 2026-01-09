import cv2
import mediapipe as mp
import numpy as np

# Configuración
mp_face_mesh = mp.solutions.face_mesh
image_path = "public_images/face.jpg"

# Índices de los LABIOS INTERNOS (Inner Lips) en MediaPipe
# Estos puntos definen el contorno de la boca abierta (donde están los dientes)
INNER_LIPS_INDICES = [
    78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 
    308, 324, 318, 402, 317, 14, 87, 178, 88, 95
]

print(f"Cargando imagen: {image_path}")
img = cv2.imread(image_path)
h, w = img.shape[:2]

with mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5) as face_mesh:

    # Procesar
    results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    if results.multi_face_landmarks:
        print("Rostro detectado. Generando máscara de la boca...")
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Obtener coordenadas (x, y) de los puntos de los labios
        lip_points = []
        for index in INNER_LIPS_INDICES:
            pt = landmarks[index]
            x = int(pt.x * w)
            y = int(pt.y * h)
            lip_points.append((x, y))
        
        lip_points = np.array(lip_points, dtype=np.int32)

        # 1. Crear una MÁSCARA (Imagen en blanco y negro)
        # Negro = Fondo, Blanco = Boca
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, [lip_points], 255)
        
        # Guardar la máscara para verla
        cv2.imwrite("public_images/test_mask.jpg", mask)
        print("✅ Máscara guardada en: public_images/test_mask.jpg")

        # 2. Visualizar el área detectada en la imagen original
        # Pintaremos de VERDE el área detectada para verificar
        preview = img.copy()
        # Crear una capa verde
        green_layer = np.zeros_like(img)
        green_layer[:] = (0, 255, 0) # Verde
        
        # Aplicar la máscara a la capa verde
        green_area = cv2.bitwise_and(green_layer, green_layer, mask=mask)
        
        # Mezclar con la imagen original
        final_preview = cv2.addWeighted(preview, 1, green_area, 0.5, 0)
        
        cv2.imwrite("public_images/test_segmentation_result.jpg", final_preview)
        print("✅ Resultado visual guardado en: public_images/test_segmentation_result.jpg")
        print("Abre 'test_segmentation_result.jpg' para ver si coloreamos correctamente los dientes.")

    else:
        print("❌ No se detectó rostro.")
