// frontend/src/components/DICOMViewer.jsx
import { useEffect, useRef, useState } from 'react';
import cornerstone from 'cornerstone-core';
import cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader';
import dicomParser from 'dicom-parser';
import './DICOMViewer.css';

// Inicializar Cornerstone WADO Image Loader
cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
cornerstoneWADOImageLoader.external.dicomParser = dicomParser;

// Configuración básica (sin web workers por simplicidad en este entorno, 
// en producción se deberían configurar los workers)
cornerstoneWADOImageLoader.configure({
  useWebWorkers: false,
});

/**
 * Visor DICOM Profesional v3.0 - Funcionalidad Completa
 * Herramientas: W/L, Zoom, Pan, Medir, Ángulos, Anotaciones, Export CSV
 * Soporte: Imágenes estándar (Canvas) y DICOM (Cornerstone)
 */
const DICOMViewer = ({ imageUrl, imageName }) => {
  const viewerRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const dicomElementRef = useRef(null);
  
  const [isDicom, setIsDicom] = useState(false);
  
  const [tools, setTools] = useState({
    windowLevel: false,
    zoom: false,
    pan: false,
    measure: false,
    angle: false,
    annotate: false,
  });
  
  const [imageInfo, setImageInfo] = useState(null);
  const [windowWidth, setWindowWidth] = useState(400);
  const [windowCenter, setWindowCenter] = useState(40);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [measurements, setMeasurements] = useState([]);
  const [angles, setAngles] = useState([]);
  const [annotations, setAnnotations] = useState([]);
  
  // Estados para interacciones
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [currentMeasurement, setCurrentMeasurement] = useState(null);
  const [currentAngle, setCurrentAngle] = useState(null);
  const [showTextInput, setShowTextInput] = useState(false);
  const [pendingAnnotation, setPendingAnnotation] = useState(null);
  const [annotationText, setAnnotationText] = useState('');

  // Estado para Landmarks (AI)
  const [landmarks, setLandmarks] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    if (imageUrl) {
      // Detectar si es DICOM
      const isDicomFile = imageUrl.toLowerCase().endsWith('.dcm') || imageUrl.startsWith('wadouri:');
      setIsDicom(isDicomFile);
      
      if (isDicomFile) {
        loadDicomImage();
      } else if (canvasRef.current) {
        loadImage();
      }
    }
  }, [imageUrl]);

  useEffect(() => {
    if (!isDicom) {
      drawOverlay();
    }
  }, [measurements, angles, annotations, currentMeasurement, currentAngle, isDicom]);

  // --- Lógica para Imágenes Estándar (Canvas) ---
  const loadImage = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      
      setImageInfo({
        width: img.width,
        height: img.height,
        aspectRatio: (img.width / img.height).toFixed(2),
      });
      
      setZoomLevel(100);
      setMeasurements([]);
      setAngles([]);
      setAnnotations([]);
      setLandmarks(null); // Resetear landmarks al cargar nueva imagen
    };
    
    img.src = imageUrl;
  };

  const drawOverlay = () => {
    const overlayCanvas = overlayCanvasRef.current;
    if (!overlayCanvas) return;
    
    const ctx = overlayCanvas.getContext('2d');
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    overlayCanvas.width = canvas.width;
    overlayCanvas.height = canvas.height;
    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    
    // Dibujar mediciones
    measurements.forEach((m, i) => drawMeasurementLine(ctx, m, i));
    if (currentMeasurement) drawMeasurementLine(ctx, currentMeasurement, -1, true);
    
    // Dibujar ángulos
    angles.forEach((a, i) => drawAngle(ctx, a, i));
    if (currentAngle) drawAngle(ctx, currentAngle, -1, true);
    
    // Dibujar anotaciones
    annotations.forEach((a, i) => drawAnnotation(ctx, a, i));

    // Dibujar Landmarks (AI)
    if (landmarks) {
      Object.entries(landmarks).forEach(([name, point]) => {
        drawLandmarkPoint(ctx, point, name);
      });
    }
  };

  // --- Lógica para DICOM (Cornerstone) ---
  const loadDicomImage = async () => {
    const element = dicomElementRef.current;
    if (!element) return;

    try {
      cornerstone.enable(element);
      
      // Prefijo wadouri para cargar desde HTTP
      const imageId = imageUrl.startsWith('http') ? `wadouri:${imageUrl}` : imageUrl;
      
      const image = await cornerstone.loadImage(imageId);
      cornerstone.displayImage(element, image);
      
      // Resetear herramientas y estado
      setMeasurements([]);
      setAngles([]);
      setAnnotations([]);
      
      setImageInfo({
        width: image.width,
        height: image.height,
        aspectRatio: (image.width / image.height).toFixed(2),
      });

    } catch (error) {
      console.error("Error loading DICOM:", error);
      alert("Error al cargar archivo DICOM. Asegúrate de que es un archivo válido.");
    }
  };



  // --- Funciones de IA ---
  const detectLandmarks = async () => {
    if (!imageUrl) return;
    
    try {
      setIsAnalyzing(true);
      
      // 1. Obtener el blob de la imagen actual
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      
      // 2. Preparar FormData
      const formData = new FormData();
      formData.append('file', blob, imageName || 'image.jpg');
      
      // 3. Enviar al backend
      const apiRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/analyze/landmarks`, {
        method: 'POST',
        body: formData
      });
      
      if (!apiRes.ok) throw new Error('Error en análisis');
      
      const data = await apiRes.json();
      
      if (data.success && data.landmarks) {
        setLandmarks(data.landmarks);
        // alert(`✅ ${Object.keys(data.landmarks).length} puntos detectados.`);
      }
      
    } catch (error) {
      console.error("Error detecting landmarks:", error);
      alert("Error al detectar landmarks. Revisa la consola.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // --- Funciones de Dibujo (Canvas) ---
  const drawLandmarkPoint = (ctx, point, name) => {
    // Punto
    ctx.fillStyle = '#00FF00'; // Verde brillante
    ctx.beginPath();
    ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
    ctx.fill();
    
    // Borde del punto
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Etiqueta
    ctx.font = 'bold 12px Arial';
    const textWidth = ctx.measureText(name).width;
    
    // Fondo etiqueta
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(point.x + 8, point.y - 10, textWidth + 6, 18);
    
    // Texto
    ctx.fillStyle = '#00FF00';
    ctx.textAlign = 'left';
    ctx.fillText(name, point.x + 11, point.y + 3);
  };
  const drawMeasurementLine = (ctx, measurement, index, isCurrent = false) => {
    const { start, end } = measurement;
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    ctx.strokeStyle = isCurrent ? '#00ff00' : '#00d4ff';
    ctx.lineWidth = 2;
    ctx.setLineDash([]);
    
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();
    
    ctx.fillStyle = isCurrent ? '#00ff00' : '#00d4ff';
    [start, end].forEach(point => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });
    
    const textX = (start.x + end.x) / 2;
    const textY = (start.y + end.y) / 2 - 10;
    
    ctx.fillStyle = '#000';
    ctx.fillRect(textX - 35, textY - 15, 70, 20);
    ctx.fillStyle = isCurrent ? '#00ff00' : '#00d4ff';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`${distance.toFixed(1)}px`, textX, textY);
    
    if (index >= 0) {
      ctx.fillStyle = '#000';
      ctx.fillRect(start.x - 15, start.y - 28, 30, 20);
      ctx.fillStyle = '#00d4ff';
      ctx.fillText(`M${index + 1}`, start.x, start.y - 14);
    }
  };

  const drawAngle = (ctx, angleData, index, isCurrent = false) => {
    const { p1, vertex, p2 } = angleData;
    
    if (!p1 || !vertex) return;
    
    const color = isCurrent ? '#ff00ff' : '#ffaa00';
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([]);
    
    // Línea 1
    ctx.beginPath();
    ctx.moveTo(vertex.x, vertex.y);
    ctx.lineTo(p1.x, p1.y);
    ctx.stroke();
    
    // Línea 2 (si existe)
    if (p2) {
      ctx.beginPath();
      ctx.moveTo(vertex.x, vertex.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
      
      // Calcular ángulo
      const angle1 = Math.atan2(p1.y - vertex.y, p1.x - vertex.x);
      const angle2 = Math.atan2(p2.y - vertex.y, p2.x - vertex.x);
      let angleDiff = Math.abs(angle2 - angle1) * (180 / Math.PI);
      if (angleDiff > 180) angleDiff = 360 - angleDiff;
      
      // Arco del ángulo
      const arcRadius = 30;
      ctx.beginPath();
      ctx.arc(vertex.x, vertex.y, arcRadius, angle1, angle2, angle2 < angle1);
      ctx.stroke();
      
      // Texto del ángulo
      const avgAngle = (angle1 + angle2) / 2;
      const textX = vertex.x + Math.cos(avgAngle) * (arcRadius + 20);
      const textY = vertex.y + Math.sin(avgAngle) * (arcRadius + 20);
      
      ctx.fillStyle = '#000';
      ctx.fillRect(textX - 25, textY - 15, 50, 20);
      ctx.fillStyle = color;
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${angleDiff.toFixed(1)}°`, textX, textY);
    }
    
    // Puntos
    ctx.fillStyle = color;
    [p1, vertex, p2].filter(p => p).forEach(point => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });
    
    // Número del ángulo
    if (index >= 0 && vertex) {
      ctx.fillStyle = '#000';
      ctx.fillRect(vertex.x - 15, vertex.y + 10, 30, 20);
      ctx.fillStyle = color;
      ctx.fillText(`A${index + 1}`, vertex.x, vertex.y + 24);
    }
  };

  const drawAnnotation = (ctx, annotation, index) => {
    const { position, text } = annotation;
    
    // Fondo
    ctx.font = '14px Arial';
    const textWidth = ctx.measureText(text).width + 16;
    const textHeight = 24;
    
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(position.x - 8, position.y - 18, textWidth, textHeight);
    
    // Borde
    ctx.strokeStyle = '#ffff00';
    ctx.lineWidth = 2;
    ctx.strokeRect(position.x - 8, position.y - 18, textWidth, textHeight);
    
    // Texto
    ctx.fillStyle = '#ffff00';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(text, position.x, position.y);
    
    // Punto
    ctx.fillStyle = '#ffff00';
    ctx.beginPath();
    ctx.arc(position.x, position.y + 10, 3, 0, 2 * Math.PI);
    ctx.fill();
    
    // Número
    ctx.fillStyle = '#000';
    ctx.fillRect(position.x - 8, position.y + 15, 24, 18);
    ctx.fillStyle = '#ffff00';
    ctx.font = 'bold 11px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`T${index + 1}`, position.x + 4, position.y + 28);
  };

  const getCanvasCoordinates = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  // --- Manejadores de Eventos (Canvas) ---
  const handleMouseDown = (e) => {
    if (isDicom) return; // Por ahora no implementamos herramientas custom en DICOM, usamos las de Cornerstone si las hubiera (pero aquí solo visualizamos)
    if (!canvasRef.current) return;
    
    const coords = getCanvasCoordinates(e);
    setIsDragging(true);
    setDragStart(coords);
    
    if (tools.measure) {
      setCurrentMeasurement({ start: coords, end: coords });
    } else if (tools.angle) {
      if (!currentAngle) {
        setCurrentAngle({ p1: coords, vertex: null, p2: null, clickCount: 1 });
      } else if (currentAngle.clickCount === 1) {
        setCurrentAngle({ ...currentAngle, vertex: coords, clickCount: 2 });
      } else if (currentAngle.clickCount === 2) {
        setCurrentAngle({ ...currentAngle, p2: coords, clickCount: 3 });
      }
    } else if (tools.annotate) {
      setPendingAnnotation(coords);
      setShowTextInput(true);
    }
  };

  const handleMouseMove = (e) => {
    if (isDicom) return;
    if (!isDragging) return;
    
    const coords = getCanvasCoordinates(e);
    
    if (tools.pan) {
      const dx = coords.x - dragStart.x;
      const dy = coords.y - dragStart.y;
      const viewerContainer = viewerRef.current;
      if (viewerContainer) {
        viewerContainer.scrollLeft -= dx / 10;
        viewerContainer.scrollTop -= dy / 10;
      }
    } else if (tools.measure && currentMeasurement) {
      setCurrentMeasurement({ ...currentMeasurement, end: coords });
    }
  };

  const handleMouseUp = (e) => {
    if (isDicom) return;
    if (!isDragging) return;
    
    if (tools.measure && currentMeasurement) {
      const coords = getCanvasCoordinates(e);
      const dx = coords.x - currentMeasurement.start.x;
      const dy = coords.y - currentMeasurement.start.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      if (distance > 5) {
        setMeasurements([...measurements, { start: currentMeasurement.start, end: coords }]);
      }
      setCurrentMeasurement(null);
    } else if (tools.angle && currentAngle && currentAngle.clickCount === 3) {
      setAngles([...angles, { p1: currentAngle.p1, vertex: currentAngle.vertex, p2: currentAngle.p2 }]);
      setCurrentAngle(null);
    }
    
    setIsDragging(false);
  };

  const handleAnnotationSubmit = () => {
    if (annotationText.trim() && pendingAnnotation) {
      setAnnotations([...annotations, { position: pendingAnnotation, text: annotationText.trim() }]);
      setAnnotationText('');
      setPendingAnnotation(null);
      setShowTextInput(false);
    }
  };

  const deleteMeasurement = (index) => {
    setMeasurements(measurements.filter((_, i) => i !== index));
  };

  const deleteAngle = (index) => {
    setAngles(angles.filter((_, i) => i !== index));
  };

  const deleteAnnotation = (index) => {
    setAnnotations(annotations.filter((_, i) => i !== index));
  };

  const exportToCSV = () => {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Tipo,ID,Datos,Valor\n";
    
    // Mediciones
    measurements.forEach((m, i) => {
      const dx = m.end.x - m.start.x;
      const dy = m.end.y - m.start.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      csvContent += `Medición,M${i + 1},"(${m.start.x.toFixed(1)},${m.start.y.toFixed(1)}) → (${m.end.x.toFixed(1)},${m.end.y.toFixed(1)})",${distance.toFixed(1)}px\n`;
    });
    
    // Ángulos
    angles.forEach((a, i) => {
      const angle1 = Math.atan2(a.p1.y - a.vertex.y, a.p1.x - a.vertex.x);
      const angle2 = Math.atan2(a.p2.y - a.vertex.y, a.p2.x - a.vertex.x);
      let angleDiff = Math.abs(angle2 - angle1) * (180 / Math.PI);
      if (angleDiff > 180) angleDiff = 360 - angleDiff;
      csvContent += `Ángulo,A${i + 1},"P1(${a.p1.x.toFixed(1)},${a.p1.y.toFixed(1)}) V(${a.vertex.x.toFixed(1)},${a.vertex.y.toFixed(1)}) P2(${a.p2.x.toFixed(1)},${a.p2.y.toFixed(1)})",${angleDiff.toFixed(1)}°\n`;
    });
    
    // Anotaciones
    annotations.forEach((ann, i) => {
      csvContent += `Anotación,T${i + 1},"${ann.text}" en (${ann.position.x.toFixed(1)},${ann.position.y.toFixed(1)}),N/A\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `mediciones_${imageName || 'imagen'}_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const applyWindowLevel = () => {
    if (isDicom) {
      // Implementar W/L para Cornerstone si se desea
      const element = dicomElementRef.current;
      if (element) {
        const viewport = cornerstone.getViewport(element);
        viewport.voi.windowWidth = windowWidth;
        viewport.voi.windowCenter = windowCenter;
        cornerstone.setViewport(element, viewport);
      }
      return;
    }

    if (!canvasRef.current || !imageInfo) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      ctx.drawImage(img, 0, 0);
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;
      
      const windowMin = windowCenter - windowWidth / 2;
      const windowMax = windowCenter + windowWidth / 2;
      
      for (let i = 0; i < data.length; i += 4) {
        const value = data[i];
        let newValue = 0;
        if (value <= windowMin) {
          newValue = 0;
        } else if (value >= windowMax) {
          newValue = 255;
        } else {
          newValue = ((value - windowMin) / windowWidth) * 255;
        }
        
        data[i] = newValue;
        data[i + 1] = newValue;
        data[i + 2] = newValue;
      }
      
      ctx.putImageData(imageData, 0, 0);
    };
    img.src = imageUrl;
  };

  const handleZoom = (direction) => {
    if (isDicom) {
      const element = dicomElementRef.current;
      if (element) {
        const viewport = cornerstone.getViewport(element);
        viewport.scale += (direction === 'in' ? 0.1 : -0.1);
        cornerstone.setViewport(element, viewport);
        setZoomLevel(Math.round(viewport.scale * 100));
      }
      return;
    }

    const newZoom = direction === 'in' ? zoomLevel + 10 : Math.max(10, zoomLevel - 10);
    setZoomLevel(newZoom);
  };

  const resetView = () => {
    setWindowWidth(400);
    setWindowCenter(40);
    setZoomLevel(100);
    setMeasurements([]);
    setAngles([]);
    setAnnotations([]);
    setCurrentMeasurement(null);
    setCurrentAngle(null);
    
    if (isDicom) {
      const element = dicomElementRef.current;
      if (element) cornerstone.reset(element);
    } else {
      loadImage();
    }
  };

  const toggleTool = (tool) => {
    const newTools = {
      windowLevel: tool === 'windowLevel' ? !tools.windowLevel : tools.windowLevel,
      zoom: tool === 'zoom' ? !tools.zoom : tools.zoom,
      pan: tool === 'pan' ? !tools[tool] : false,
      measure: tool === 'measure' ? !tools[tool] : false,
      angle: tool === 'angle' ? !tools[tool] : false,
      annotate: tool === 'annotate' ? !tools[tool] : false,
    };
    setTools(newTools);
    
    if (tool === 'angle' && !newTools.angle) {
      setCurrentAngle(null);
    }
  };

  const getCursorStyle = () => {
    if (tools.pan) return 'grab';
    if (tools.measure) return 'crosshair';
    if (tools.angle) return 'crosshair';
    if (tools.annotate) return 'text';
    if (isDragging && tools.pan) return 'grabbing';
    return 'default';
  };

  const totalItems = measurements.length + angles.length + annotations.length;

  return (
    <div className="dicom-viewer-container">
      {/* Toolbar */}
      <div className="dicom-toolbar">
        <div className="toolbar-section">
          <h3>🔧 Herramientas</h3>
          <div className="tool-buttons">
            <button
              className={`tool-btn ${tools.windowLevel ? 'active' : ''}`}
              onClick={() => toggleTool('windowLevel')}
              title="Ajustar Brillo/Contraste"
            >
              💡 W/L
            </button>
            <button
              className={`tool-btn ${tools.zoom ? 'active' : ''}`}
              onClick={() => toggleTool('zoom')}
              title="Zoom"
            >
              🔍 Zoom
            </button>
            <button
              className={`tool-btn ${tools.pan ? 'active' : ''}`}
              onClick={() => toggleTool('pan')}
              title="Desplazar"
            >
              ✋ Pan
            </button>
            {!isDicom && (
              <>
                <button
                  className={`tool-btn ${tools.measure ? 'active' : ''}`}
                  onClick={() => toggleTool('measure')}
                  title="Medir Distancia"
                >
                  📏 Medir
                </button>
                <button
                  className={`tool-btn ${tools.angle ? 'active' : ''}`}
                  onClick={() => toggleTool('angle')}
                  title="Medir Ángulo - 3 clicks"
                >
                  📐 Ángulo
                </button>
                <button
                  className={`tool-btn ${tools.annotate ? 'active' : ''}`}
                  onClick={() => toggleTool('annotate')}
                  title="Agregar Texto"
                >
                  📝 Texto
                </button>

                <div className="separator" style={{width: '1px', height: '24px', background: '#444', margin: '0 8px'}}></div>
                <button
                  className={`tool-btn ai-btn ${isAnalyzing ? 'loading' : ''} ${landmarks ? 'active' : ''}`}
                  onClick={detectLandmarks}
                  disabled={isAnalyzing}
                  title="Detectar Puntos Cefalométricos con IA"
                  style={{ background: landmarks ? 'rgba(0, 255, 0, 0.2)' : '' }}
                >
                  {isAnalyzing ? '⏳...' : '🧠 Landmarks'}
                </button>
              </>
            )}
          </div>
          <div className="tool-buttons" style={{ marginTop: '0.5rem' }}>
            <button
              className="tool-btn reset"
              onClick={resetView}
              title="Restablecer todo"
            >
              🔄 Reset
            </button>
            {totalItems > 0 && (
              <button
                className="tool-btn export"
                onClick={exportToCSV}
                title="Exportar a CSV"
              >
                💾 Export
              </button>
            )}
          </div>
        </div>

        {/* Window/Level */}
        {tools.windowLevel && (
          <div className="toolbar-section">
            <h3>💡 Window / Level</h3>
            <div className="wl-controls">
              <div className="control-group">
                <label>Window Width: {windowWidth}</label>
                <input
                  type="range"
                  min="1"
                  max="2000"
                  value={windowWidth}
                  onChange={(e) => setWindowWidth(Number(e.target.value))}
                  onMouseUp={applyWindowLevel}
                />
              </div>
              <div className="control-group">
                <label>Window Center: {windowCenter}</label>
                <input
                  type="range"
                  min="-1024"
                  max="3071"
                  value={windowCenter}
                  onChange={(e) => setWindowCenter(Number(e.target.value))}
                  onMouseUp={applyWindowLevel}
                />
              </div>
              <button onClick={applyWindowLevel} className="apply-btn">
                Aplicar
              </button>
            </div>
          </div>
        )}

        {/* Zoom */}
        {tools.zoom && (
          <div className="toolbar-section">
            <h3>🔍 Zoom</h3>
            <div className="zoom-controls">
              <button onClick={() => handleZoom('in')}>➕</button>
              <span className="zoom-level">{zoomLevel}%</span>
              <button onClick={() => handleZoom('out')}>➖</button>
            </div>
          </div>
        )}

        {/* Info */}
        {imageInfo && (
          <div className="toolbar-section">
            <h3>ℹ️ Información</h3>
            <div className="image-info">
              <p><strong>Tipo:</strong> {isDicom ? 'DICOM' : 'Estándar'}</p>
              <p><strong>Resolución:</strong> {imageInfo.width} × {imageInfo.height} px</p>
              <p><strong>Zoom:</strong> {zoomLevel}%</p>
            </div>
          </div>
        )}
      </div>

      {/* Viewport */}
      <div className="dicom-viewport" ref={viewerRef} style={{ cursor: getCursorStyle() }}>
        {imageUrl ? (
          <div 
            className="canvas-container"
            style={{ 
              transform: isDicom ? 'none' : `scale(${zoomLevel / 100})`,
              transformOrigin: 'center center',
              width: '100%',
              height: '100%'
            }}
          >
            {isDicom ? (
              <div 
                ref={dicomElementRef} 
                className="dicom-element" 
                style={{ width: '100%', height: '100%', backgroundColor: 'black' }}
              />
            ) : (
              <>
                <canvas ref={canvasRef} className="dicom-canvas" />
                <canvas
                  ref={overlayCanvasRef}
                  className="dicom-overlay"
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                />
              </>
            )}
          </div>
        ) : (
          <div className="empty-viewer">
            <p>📁 No hay imagen cargada</p>
            <p className="hint">Selecciona una imagen de la galería</p>
          </div>
        )}
      </div>

      {/* Modal de Texto */}
      {showTextInput && (
        <div className="text-modal-backdrop" onClick={() => setShowTextInput(false)}>
          <div className="text-modal" onClick={(e) => e.stopPropagation()}>
            <h3>📝 Agregar Anotación</h3>
            <input
              type="text"
              value={annotationText}
              onChange={(e) => setAnnotationText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAnnotationSubmit()}
              placeholder="Escribe tu anotación..."
              autoFocus
              maxLength={50}
            />
            <div className="modal-buttons">
              <button onClick={handleAnnotationSubmit} className="btn-primary">
                ✓ Agregar
              </button>
              <button onClick={() => {
                setShowTextInput(false);
                setAnnotationText('');
                setPendingAnnotation(null);
              }} className="btn-secondary">
                ✕ Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DICOMViewer;
