import React, { useState, useRef, useEffect } from 'react';
import { Upload, Activity, Layers, Eye, AlertCircle, CheckCircle } from 'lucide-react';
import * as api from '../services/api';
import './DiagnosticDashboard.css';

const DiagnosticDashboard = ({ initialFile = null, initialUrl = null }) => {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  
  // Estados de visualización (Toggles)
  const [showLandmarks, setShowLandmarks] = useState(true);
  const [showSegmentation, setShowSegmentation] = useState(true);
  const [showGradCAM, setShowGradCAM] = useState(false);
  const [gradCAMData, setGradCAMData] = useState(null);
  const [isGeneratingXAI, setIsGeneratingXAI] = useState(false);
  const [useEnsemble, setUseEnsemble] = useState(false);

  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  // Manejar subida de archivo
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreviewUrl(URL.createObjectURL(selectedFile));
      setResults(null); // Resetear resultados anteriores
      setGradCAMData(null); // Resetear XAI anterior
      setShowGradCAM(false);
      performAnalysis(selectedFile);
    }
  };

  // Función real de análisis (subida de archivo)
  const performAnalysis = async (file) => {
    setIsAnalyzing(true);
    setResults(null);
    
    try {
      const patientDid = localStorage.getItem("patientDID") || `did:key:z${Math.random().toString(36).substring(2)}`;
      const data = await api.analyzeImage(file, patientDid, useEnsemble);
      
      const formattedResults = {
        diagnosis: {
          class: data.predicted_class || "Desconocido",
          confidence: data.confidence || 0,
          severity: data.severity || "No determinada",
          description: data.recommendation?.diagnosis || "Sin descripción"
        },
        landmarks: data.landmarks || [],
        segmentation: data.segmentation?.polygons || [],
        // Nuevos campos de IA Avanzada
        ensemble: {
          active: data.ensemble_active || false,
          consensus: data.consensus || false,
          uncertainty: data.uncertainty || 0
        },
        angles: data.geometric_analysis || null,
        report: data.narrative_report || null
      };

      setResults(formattedResults);
    } catch (error) {
      console.error("Error en análisis:", error);
      alert("Error al analizar la imagen: " + error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Función para analizar imágenes de galería (sin subir archivo)
  const performGalleryAnalysis = async (imageUrl) => {
    setIsAnalyzing(true);
    setResults(null);
    
    try {
      const patientDid = localStorage.getItem("patientDID") || `did:key:z${Math.random().toString(36).substring(2)}`;
      const filename = imageUrl.split('/').pop();
      const data = await api.analyzeGalleryImage(filename, patientDid, useEnsemble);
      
      const formattedResults = {
        diagnosis: {
          class: data.predicted_class || "Desconocido",
          confidence: data.confidence || 0,
          severity: data.severity || "No determinada",
          description: data.recommendation?.diagnosis || "Sin descripción"
        },
        landmarks: data.landmarks || [],
        segmentation: data.segmentation?.polygons || [],
        // Nuevos campos de IA Avanzada
        ensemble: {
          active: data.ensemble_active || false,
          consensus: data.consensus || false,
          uncertainty: data.uncertainty || 0
        },
        angles: data.geometric_analysis || null,
        report: data.narrative_report || null
      };

      setResults(formattedResults);
    } catch (error) {
      console.error("Error en análisis de galería:", error);
      alert("Error al analizar la imagen de galería: " + error.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Efecto para manejar cambios en las props (cuando se selecciona desde galería)
  useEffect(() => {
    if (initialUrl && initialUrl !== previewUrl) {
      setPreviewUrl(initialUrl);
      setFile(initialFile);
      setResults(null);
      
      // Si hay archivo, análisis normal; si no, análisis de galería
      if (initialFile) {
        performAnalysis(initialFile);
      } else if (initialUrl) {
        performGalleryAnalysis(initialUrl);
      }
    }
  }, [initialFile, initialUrl]);
  
  // Función para obtener explicación Grad-CAM
  const handleToggleGradCAM = async (active) => {
    if (active && !gradCAMData && file) {
      setIsGeneratingXAI(true);
      try {
        const data = await api.explainAnalysis(file);
        setGradCAMData(data);
        setShowGradCAM(true);
      } catch (error) {
        console.error("Error obteniendo Grad-CAM:", error);
        alert("No se pudo generar la explicación de IA.");
        setShowGradCAM(false);
      } finally {
        setIsGeneratingXAI(false);
      }
    } else {
      setShowGradCAM(active);
    }
  };


  // Helper para generar landmarks random para la demo
  const generateMockLandmarks = () => {
    const points = [];
    for(let i=0; i<68; i++) {
        points.push({ x: 150 + Math.random()*200, y: 150 + Math.random()*200 });
    }
    return points;
  };

  // Actualizar tamaño de imagen para escalar overlays
  const updateImageSize = () => {
    if (imageRef.current) {
      setImageSize({
        width: imageRef.current.offsetWidth,
        height: imageRef.current.offsetHeight,
        naturalWidth: imageRef.current.naturalWidth,
        naturalHeight: imageRef.current.naturalHeight
      });
    }
  };

  useEffect(() => {
    window.addEventListener('resize', updateImageSize);
    return () => window.removeEventListener('resize', updateImageSize);
  }, []);

  // Dibujar Landmarks en Canvas
  useEffect(() => {
    if (!results?.landmarks || !canvasRef.current || !showLandmarks || !imageSize.width) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Ajustar canvas al tamaño visual de la imagen
    canvas.width = imageSize.width;
    canvas.height = imageSize.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Escalar puntos de coordenadas originales a tamaño visual
    const scaleX = imageSize.width / imageSize.naturalWidth;
    const scaleY = imageSize.height / imageSize.naturalHeight;

    ctx.fillStyle = '#00ff00';
    results.landmarks.forEach(point => {
      ctx.beginPath();
      // Asumiendo que los landmarks vienen en coordenadas originales de la imagen
      // Si vienen normalizados (0-1), multiplicar por width/height
      ctx.arc(point.x * scaleX, point.y * scaleY, 3, 0, 2 * Math.PI);
      ctx.fill();
    });

  }, [results, showLandmarks, imageSize]);

  return (
    <div className="diagnostic-dashboard">
      {/* Panel Izquierdo: Visualización */}
      <div className="image-viewport">
        {!previewUrl ? (
          <div className="upload-placeholder">
            <input 
                type="file" 
                id="dash-upload" 
                hidden 
                onChange={handleFileChange}
                accept="image/*"
            />
            <label htmlFor="dash-upload" className="upload-area">
                <Upload size={48} color="#94a3b8" />
                <p>Arrastra una imagen o haz clic para subir</p>
            </label>
          </div>
        ) : (
          <div className="viewport-container">
            <img 
                ref={imageRef}
                src={previewUrl} 
                alt="Análisis" 
                className="main-image"
                onLoad={updateImageSize}
            />
            
            {/* Capa de Landmarks (Canvas) */}
            <canvas 
                ref={canvasRef}
                className="overlay-layer landmarks-canvas"
                style={{ display: showLandmarks && results ? 'block' : 'none' }}
            />

            {/* Capa de Segmentación (SVG) */}
            {showSegmentation && results?.segmentation && (
                <svg 
                    className="overlay-layer segmentation-svg"
                    viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                >
                    {results.segmentation.map((poly, idx) => {
                        // Escalar puntos
                        const scaleX = imageSize.width / imageSize.naturalWidth || 1;
                        const scaleY = imageSize.height / imageSize.naturalHeight || 1;
                        const pointsStr = poly.map(p => `${p[0]*scaleX},${p[1]*scaleY}`).join(' ');
                        
                        return (
                            <polygon 
                                key={idx} 
                                points={pointsStr} 
                                className="segmentation-polygon" 
                            />
                        );
                    })}
                </svg>
            )}

            {/* Capa de Grad-CAM (Heatmap) */}
            {showGradCAM && gradCAMData && (
                <div className="overlay-layer gradcam-overlay">
                    <img 
                        src={gradCAMData.explanation_image} 
                        alt="Grad-CAM" 
                        style={{ width: '100%', height: '100%', objectFit: 'contain', opacity: 0.7 }}
                    />
                    <div className="gradcam-legend">
                        <div className="legend-item"><span className="dot red"></span> Importancia Alta</div>
                        <div className="legend-item"><span className="dot yellow"></span> Importancia Media</div>
                    </div>
                </div>
            )}

            {isGeneratingXAI && (
                <div className="analyzing-overlay xai-loading">
                    <div className="spinner"></div>
                    <p>Calculando Explicibilidad (Grad-CAM)...</p>
                </div>
            )}

            {isAnalyzing && (

                <div className="analyzing-overlay">
                    <div className="spinner"></div>
                    <p>Analizando con IA...</p>
                </div>
            )}
          </div>
        )}
      </div>

      {/* Panel Derecho: Controles y Resultados */}
      <div className="diagnostic-sidebar">
        <div className="sidebar-header">
            <h2>Diagnóstico IA</h2>
            <p className="text-sm text-gray-500">Análisis integral de ortodoncia</p>
        </div>

        {/* CONFIGURACIÓN (Siempre visible para configurar antes del análisis) */}
        <div className="result-card config-card">
            <h3>⚙️ Configuración IA</h3>
            <div className="toggle-row">
                <div className="toggle-label">
                    <Activity size={18} color="#f59e0b" />
                    Modo Ensemble (Multimodelo)
                </div>
                <label className="switch">
                    <input 
                        type="checkbox" 
                        checked={useEnsemble}
                        onChange={(e) => setUseEnsemble(e.target.checked)}
                    />
                    <span className="slider"></span>
                </label>
            </div>
            {useEnsemble && (
                <p className="config-help">
                    * Activa el análisis redundante con múltiples redes neuronales.
                </p>
            )}
        </div>

        {results ? (
            <>
                {/* Tarjeta de Diagnóstico Principal */}
                <div className="result-card">
                    <h3><Activity size={18} /> Diagnóstico Principal</h3>
                    <div className="diagnosis-value">{results.diagnosis.class}</div>
                    <div className="confidence-bar">
                        <div 
                            className="confidence-fill" 
                            style={{ width: `${results.diagnosis.confidence * 100}%` }}
                        ></div>
                    </div>
                    <div className="text-xs text-right mt-1 text-gray-500">
                        Confianza: {(results.diagnosis.confidence * 100).toFixed(1)}%
                    </div>
                </div>

                {/* Badge de Consenso (Iniciativa 2) */}
                {results.ensemble?.active && (
                    <div className={`consensus-badge ${results.ensemble.consensus ? 'success' : 'warning'}`}>
                        {results.ensemble.consensus ? (
                            <><CheckCircle size={14} /> Consenso Superior Alcanzado</>
                        ) : (
                            <><AlertCircle size={14} /> Incertidumbre Detectada ({results.ensemble.uncertainty.toFixed(2)})</>
                        )}
                    </div>
                )}

                {/* Controles de Visualización */}
                <div className="controls-group">
                    <h3>Visualización IA</h3>
                    
                    <div className="toggle-row">
                        <div className="toggle-label">
                            <Activity size={18} color="#22c55e" />
                            Landmarks (Puntos)
                        </div>
                        <label className="switch">
                            <input 
                                type="checkbox" 
                                checked={showLandmarks}
                                onChange={(e) => setShowLandmarks(e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>

                    <div className="toggle-row">
                        <div className="toggle-label">
                            <Layers size={18} color="#3b82f6" />
                            Segmentación
                        </div>
                        <label className="switch">
                            <input 
                                type="checkbox" 
                                checked={showSegmentation}
                                onChange={(e) => setShowSegmentation(e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>

                    <div className="toggle-row">
                        <div className="toggle-label">
                            <Eye size={18} color="#a855f7" />
                            Explicación IA (Grad-CAM)
                        </div>
                        <label className="switch">
                            <input 
                                type="checkbox" 
                                checked={showGradCAM}
                                onChange={(e) => handleToggleGradCAM(e.target.checked)}
                                disabled={isGeneratingXAI}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>
                </div>

                {/* Análisis Cefalométrico (Iniciativa 3) */}
                {results.angles && (
                    <div className="result-card cepha-card">
                        <h3>📐 Análisis Cefalométrico</h3>
                        <div className="angles-grid">
                            {Object.entries(results.angles).map(([key, data]) => (
                                <div key={key} className="angle-item">
                                    <span className="angle-label">{data.label}</span>
                                    <span className="angle-value">{data.value.toFixed(1)}°</span>
                                    <span className={`angle-status ${data.status.toLowerCase().includes('clase i') ? 'status-ok' : 'status-alert'}`}>
                                        {data.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Reporte Médico Generativo (Iniciativa 5) */}
                {results.report && (
                    <div className="result-card report-card">
                        <h3>📄 Informe Clínico IA</h3>
                        <div className="report-content">
                            {results.report}
                        </div>
                    </div>
                )}

                {/* Detalles Adicionales */}
                <div className="result-card">
                    <h3><AlertCircle size={18} /> Detalles</h3>
                    <p className="text-sm text-gray-700">
                        <strong>Severidad:</strong> {results.diagnosis.severity}
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                        {results.diagnosis.description}
                    </p>
                </div>
            </>
        ) : (
            <div className="empty-state">
                <p className="text-gray-400 text-center">
                    Sube una imagen para ver el diagnóstico detallado.
                </p>
            </div>
        )}
      </div>
    </div>
  );
};

export default DiagnosticDashboard;
