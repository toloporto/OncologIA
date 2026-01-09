# Instrucciones de Instalación - Rate Limiting y Validación de Archivos

## 📋 Resumen

Se han creado dos nuevos módulos de seguridad para proteger la aplicación:

1. **`file_validator.py`** - Validación estricta de archivos subidos
2. **`rate_limiter.py`** - Protección contra ataques DoS

## 🔧 Paso 1: Instalar Dependencias

Abre PowerShell o CMD en la carpeta del proyecto y ejecuta:

```powershell
cd c:\ortho-web3-project\backend
pip install slowapi==0.1.9 python-magic==0.4.27 python-magic-bin==0.4.14 pydicom==2.4.4
```

### Verificar Instalación

```powershell
python -c "import magic; print('✅ python-magic instalado correctamente')"
python -c "from slowapi import Limiter; print('✅ slowapi instalado correctamente')"
python -c "import pydicom; print('✅ pydicom instalado correctamente')"
```

## 📁 Archivos Creados

Los siguientes archivos ya han sido creados en `c:\ortho-web3-project\backend\`:

- ✅ `file_validator.py` - Módulo de validación de archivos
- ✅ `rate_limiter.py` - Configuración de rate limiting

## 🎯 Formatos Permitidos

### Imágenes Estándar

- **JPG/JPEG** - Fotos clínicas estándar
- **PNG** - Imágenes con transparencia

### Formatos Médicos/Dentales

- **DICOM (.dcm, .dicom)** - Estándar médico para radiografías y tomografías
- **TIFF (.tif, .tiff)** - Común en escáneres dentales de alta resolución
- **BMP (.bmp)** - Equipos dentales antiguos

### Tamaño Máximo

- **20 MB** por archivo (aumentado para soportar DICOM y panorámicas)

## 🛡️ Límites de Rate Limiting

| Tipo de Usuario | Límite Global | Límite de Upload |
| --------------- | ------------- | ---------------- |
| No autenticado  | 100/minuto    | 10/minuto        |
| Autenticado     | 100/minuto    | 20/minuto        |
| IPFS Upload     | -             | 5/minuto         |

## 🚀 Próximos Pasos (Ejecución Manual)

### Paso 2: Integrar en ortho_api.py

Necesitas editar manualmente `c:\ortho-web3-project\backend\ortho_api.py`:

#### A. Añadir imports (después de la línea 11)

```python
from backend.file_validator import validate_upload_file, FileValidationError
from backend.rate_limiter import limiter, rate_limit_exceeded_handler, UPLOAD_RATE_AUTHENTICATED, IPFS_RATE
from slowapi.errors import RateLimitExceeded
```

#### B. Configurar SlowAPI (después de la línea 224, antes de crear `app`)

```python
# Configurar rate limiter en la app
limiter.state = app.state
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

**NOTA:** Añade esto DESPUÉS de `app = FastAPI(...)` en la línea 220.

#### C. Actualizar endpoint `/analyze` (línea 482)

Encuentra esta línea:

```python
@app.post("/analyze", response_model=AnalysisResponse, tags=["Análisis"])
```

Cámbiala por:

```python
@app.post("/analyze", response_model=AnalysisResponse, tags=["Análisis"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
```

Dentro de la función, después de `image_bytes = await file.read()` (línea 495), añade:

```python
        # Validar archivo
        try:
            safe_filename, mime_type = validate_upload_file(image_bytes, file.filename)
            logger.info(f"✅ Archivo validado: {safe_filename} ({mime_type})")
        except FileValidationError as e:
            logger.warning(f"⚠️ Archivo rechazado: {e}")
            raise HTTPException(status_code=400, detail=str(e))
```

#### D. Actualizar endpoint `/analyze/explain` (línea 574)

Añade el decorator:

```python
@app.post("/analyze/explain", tags=["Análisis", "XAI"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
```

Y validación después de `image_bytes = await file.read()`:

```python
        # Validar archivo
        try:
            safe_filename, mime_type = validate_upload_file(image_bytes, file.filename)
        except FileValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
```

#### E. Actualizar endpoint `/simulate/treatment` (línea 621 y 780)

Hay dos funciones con este nombre. Actualiza ambas:

```python
@app.post("/simulate/treatment", tags=["Simulación"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
```

Y añade validación en ambas.

#### F. Actualizar endpoint `/analyze/landmarks` (línea 666)

```python
@app.post("/analyze/landmarks", tags=["Análisis"])
@limiter.limit(UPLOAD_RATE_AUTHENTICATED)
```

### Paso 3: Integrar en ipfs_routes.py

Edita `c:\ortho-web3-project\backend\ipfs_routes.py`:

#### A. Añadir imports (al inicio del archivo)

```python
from backend.file_validator import validate_upload_file, FileValidationError
from backend.rate_limiter import limiter, IPFS_RATE
```

#### B. Actualizar endpoint `/upload` (busca la función `upload_to_ipfs`)

Añade decorator:

```python
@ipfs_router.post("/upload")
@limiter.limit(IPFS_RATE)
```

Añade validación después de `file_bytes = await file.read()`:

```python
    # Validar archivo
    try:
        safe_filename, mime_type = validate_upload_file(file_bytes, file.filename)
        logger.info(f"✅ Archivo validado para IPFS: {safe_filename}")
    except FileValidationError as e:
        logger.warning(f"⚠️ Archivo rechazado en IPFS: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

### Paso 4: Reiniciar la API

```powershell
# Si la API está corriendo, presiona Ctrl+C para detenerla

# Reiniciar con las nuevas protecciones
cd c:\ortho-web3-project\backend
uvicorn ortho_api:app --host 0.0.0.0 --port 8004 --reload
```

## ✅ Verificar que Funciona

### Test 1: Rate Limiting

Desde el frontend, intenta hacer más de 10 uploads en un minuto. Deberías ver un error 429.

### Test 2: Validación de Archivo Inválido

Intenta subir un archivo .txt renombrado a .jpg. Debería rechazarse con:

```
Tipo de archivo no permitido
```

### Test 3: Archivo Válido

Sube una imagen JPG, PNG o DICOM válida. Debería funcionar normalmente.

### Test 4: Archivo Grande

Intenta subir un archivo >20MB. Debería rechazarse con:

```
Archivo demasiado grande
```

## 📊 Logs de Seguridad

Los siguientes eventos se registran en los logs:

- ✅ Archivo validado correctamente
- ⚠️ Archivo rechazado por tipo inválido
- ⚠️ Archivo rechazado por tamaño
- ⚠️ Rate limit excedido

Revisa los logs ejecutando:

```powershell
# Los logs aparecen en la consola donde corre uvicorn
```

## 🔧 Configuración Personalizada

Si necesitas ajustar los límites, edita `backend/rate_limiter.py`:

```python
# Más estricto (producción)
UPLOAD_RATE = "5/minute"

# Más permisivo (desarrollo)
UPLOAD_RATE = "30/minute"
```

Para cambiar tamaño máximo, edita `backend/file_validator.py`:

```python
MAX_FILE_SIZE_MB = 50  # Para imágenes DICOM muy grandes
```

## 🆘 Solución de Problemas

### Error: "No module named 'magic'"

```powershell
pip install python-magic python-magic-bin
```

### Error: "No module named 'slowapi'"

```powershell
pip install slowapi
```

### Error: "limiter not defined"

Asegúrate de haber añadido los imports correctamente en `ortho_api.py`.

### La API no inicia

Revisa la consola para ver errores de sintaxis en las modificaciones.

## 📖 Referencias

- [SlowAPI Documentation](https://github.com/laurentS/slowapi)
- [python-magic Documentation](https://github.com/ahupp/python-magic)
- [DICOM Standard](https://www.dicomstandard.org/)
- [pydicom Documentation](https://pydicom.github.io/)
