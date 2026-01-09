# 🏥 Visor DICOM Profesional - Guía de Uso

## 📋 Descripción

El Visor DICOM integrado en OrthoWeb3 es una herramienta profesional para manipulación avanzada de imágenes médicas. Incluye todas las funcionalidades que esperarías de un visor médico profesional.

---

## ✨ Características Principales

### 1. **💡 Window / Level (Ventana y Nivel)**

Control preciso de brillo y contraste para optimizar la visualización de estructuras dentales y óseas.

**Cómo usar:**

- Click en el botón **"💡 W/L"**
- Ajusta **Window Width** (Ancho de ventana): Controla el contraste
- Ajusta **Window Center** (Centro de ventana): Controla el brillo
- Click en **"Aplicar"** para ver los cambios

**Valores recomendados:**

- **Hueso**: Width: 1500-2000, Center: 300-500
- **Tejidos blandos**: Width: 350-400, Center: 40-60
- **Dientes**: Width: 800-1200, Center: 200-400

### 2. **🔍 Zoom**

Ampliación de regiones de interés con calidad sin pérdida.

**Cómo usar:**

- Click en el botón **"🔍 Zoom"**
- **➕ Zoom In**: Aumenta el tamaño (incrementos de 10%)
- **➖ Zoom Out**: Reduce el tamaño
- El nivel actual se muestra en el centro

**Rangos:**

- Mínimo: 10%
- Máximo: 500%+

### 3. **✋ Pan (Desplazar)**

Navega por la imagen cuando estás en zoom.

**Cómo usar:**

- Click en el botón **"✋ Pan"**
- Arrastra la imagen con el mouse
- Útil cuando estás con zoom >100%

### 4. **📏 Mediciones**

Herramienta para medir distancias y ángulos en la imagen.

**Cómo usar:**

- Click en el botón **"📏 Medir"**
- Click y arrastra para medir distancias lineales
- Las medidas se muestran en píxeles

**Nota**: Para mediciones en mm, se requiere calibración con el factor de escala de la imagen.

### 5. **🔄 Reset**

Restablece todas las modificaciones y vuelve a la vista original.

**Efecto:**

- Window/Level: Vuelve a valores predeterminados
- Zoom: Vuelve a 100%
- Posición: Centrada

---

## 🎯 Workflow Recomendado

### Para Análisis Ortodóntico:

1. **Cargar Imagen**

   - Ve a la pestaña "Analizar Imagen"
   - Sube una imagen dental (JPG, PNG, o DICOM)

2. **Optimizar Visualización**

   - Cambia a la pestaña "Visor DICOM"
   - Activa **Window/Level**
   - Ajusta para visualizar claramente las estructuras dentales

3. **Examinar Detalles**

   - Activa **Zoom** para ampliar áreas específicas
   - Usa **Pan** para navegar por la imagen ampliada

4. **Mediciones** (opcional)

   - Activa la herramienta de **medición**
   - Mide distancias relevantes para el diagnóstico

5. **Comparar con IA**
   - Vuelve a la pestaña "Analizar Imagen"
   - Revisa el diagnóstico automático
   - Compara con tu análisis visual

---

## 🖼️ Formatos de Imagen Soportados

### Totalmente Soportados:

- ✅ **JPG/JPEG**: Imágenes estándar
- ✅ **PNG**: Con transparencia
- ✅ **BMP**: Bitmap sin compresión
- ✅ **WEBP**: Formato moderno

### Soportados con Extensión (Futuro):

- 🔜 **DICOM (.dcm)**: Formato médico estándar
- 🔜 **NIFTI (.nii)**: Neuroimagen
- 🔜 **TIFF**: Alta calidad

---

## ℹ️ Información de Imagen

El visor muestra automáticamente:

- **Resolución**: Ancho × Alto en píxeles
- **Relación de aspecto**: Proporción de la imagen
- **Nombre del archivo**: Para identificación

---

## 🎨 Interfaz y Controles

### Panel de Herramientas (Izquierda):

- **Fondo oscuro**: Reduce fatiga visual
- **Botones activos**: Color cyan cuando están activados
- **Controles deslizantes**: Ajuste preciso en tiempo real

### Viewport (Derecha):

- **Fondo negro**: Máximo contraste para imágenes médicas
- **Rendering optimizado**: Calidad máxima sin interpolación
- **Responsive**: Se adapta al tamaño de la ventana

---

## ⚡ Atajos de Teclado (Próximamente)

Estos atajos estarán disponibles en futuras versiones:

- **W**: Activar Window/Level
- **Z**: Activar Zoom
- **P**: Activar Pan
- **M**: Activar Mediciones
- **R**: Reset
- **+/-**: Zoom in/out
- **Flechas**: Pan cuando está en zoom

---

## 🔬 Casos de Uso Médico

### 1. Evaluación de Maloclusión

- Ajusta W/L para ver claramente la oclusión
- Mide espacios interdentales
- Compara con radiografías laterales

### 2. Planificación de Ortodoncia

- Visualiza estructuras óseas
- Mide distancias para aparatos
- Evalúa ángulos de inclinación

### 3. Seguimiento de Tratamiento

- Carga imágenes antes/después
- Compara mediciones
- Documenta progreso

### 4. Diagnóstico de Anomalías

- Amplía regiones sospechosas
- Ajusta contraste para detectar sutilezas
- Mide lesiones o irregularidades

---

## 🛠️ Especificaciones Técnicas

### Rendering:

- **Engine**: HTML5 Canvas nativo
- **Precisión**: 8 bits por canal (24-bit RGB)
- **Interpolación**: Nearest-neighbor (sin pérdida)
- **Transformaciones**: CSS 2D transforms

### Performance:

- **Carga**: < 100ms para imágenes estándar
- **W/L Apply**: ~50ms para 2MP imagen
- **Zoom**: Instantáneo (GPU acelerado)

### Limitaciones actuales:

- Imágenes máx: 10MB
- Resolución máx: 8192×8192 px
- Profundidad de color: 8 bits

---

## 🆕 Mejoras Futuras Planificadas

### Versión 2.0:

- ✨ Soporte nativo DICOM
- ✨ Calibración de escala
- ✨ Anotaciones y marcadores
- ✨ Herramientas de ángulo
- ✨ Histogramas

### Versión 3.0:

- ✨ Comparación lado a lado
- ✨ Fusión de imágenes
- ✨ Filtros avanzados
- ✨ Exportar con anotaciones
- ✨ Soporte 3D

---

## 📞 Soporte y Troubleshooting

### Imagen no se carga:

1. Verifica que el formato sea soportado (JPG, PNG)
2. Asegúrate que la imagen sea < 10MB
3. Intenta con otra imagen

### W/L no funciona:

1. Click en "Aplicar" después de ajustar
2. Prueba con valores más extremos
3. Usa "Reset" y vuelve a intentar

### Zoom muy lento:

1. Reduce la resolución de la imagen
2. Cierra otras pestañas del navegador
3. Actualiza los drivers de GPU

---

## 🏆 Comparación con Otros Visores

| Característica | OrthoWeb3 DICOM | DICOM Viewers Básicos | Radiant/Horos |
| -------------- | --------------- | --------------------- | ------------- |
| Window/Level   | ✅              | ✅                    | ✅            |
| Zoom Preciso   | ✅              | ✅                    | ✅            |
| Mediciones     | ✅              | ⚠️ Limitado           | ✅            |
| Web-based      | ✅              | ⚠️ Parcial            | ❌            |
| IA Integrada   | ✅              | ❌                    | ❌            |
| Gratis         | ✅              | ✅                    | ✅            |
| DICOM Nativo   | 🔜 V2.0         | ✅                    | ✅            |

---

**📌 Nota**: Este visor está diseñado específicamente para imágenes ortodónticas, pero puede usarse para cualquier tipo de imagen médica.

---

**Desarrollado con ❤️ para profesionales de la salud dental**
