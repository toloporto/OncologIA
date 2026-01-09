import React, { useState, useRef, useEffect } from 'react';
import './LandmarksViewer.css';

const LandmarksViewer = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [landmarks, setLandmarks] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [imageSrc, setImageSrc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const canvasRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onload = (e) => setImageSrc(e.target.result);
      reader.readAsDataURL(file);
      setLandmarks(null);
      setMetrics(null);
      setError(null);
    }
  };

  const analyzeLandmarks = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/analyze/landmarks`, {
        method: 'POST',
        body: formData
      });
      
      const data = await res.json();
      
      if (data.success && data.data.detected) {
        setLandmarks(data.data.landmarks);
        setMetrics(data.data.metrics);
      } else {
        setError('No se detectó ningún rostro en la imagen');
      }
    } catch (err) {
      console.error(err);
      setError('Error al analizar la imagen. Asegúrate de que el servidor esté corriendo.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setLandmarks(null);
    setMetrics(null);
    setImageSrc(null);
    setError(null);
  };

  useEffect(() => {
    if (landmarks && imageSrc && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const img = new Image();
      
      img.src = imageSrc;
      img.onload = () => {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Dibujar todos los puntos
        ctx.fillStyle = '#00ff00';
        landmarks.forEach(lm => {
          ctx.beginPath();
          ctx.arc(lm.pixel_x, lm.pixel_y, 1.5, 0, 2 * Math.PI);
          ctx.fill();
        });

        // Destacar puntos clave
        const keyPoints = [
          { id: 13, color: '#ff0000', label: 'Labio Superior' },
          { id: 14, color: '#ff0000', label: 'Labio Inferior' },
          { id: 61, color: '#0000ff', label: 'Comisura Izq' },
          { id: 291, color: '#0000ff', label: 'Comisura Der' },
          { id: 0, color: '#ffff00', label: 'Nariz' },
          { id: 17, color: '#ff00ff', label: 'Barbilla' }
        ];

        keyPoints.forEach(kp => {
          const lm = landmarks[kp.id];
          if (lm) {
            ctx.fillStyle = kp.color;
            ctx.beginPath();
            ctx.arc(lm.pixel_x, lm.pixel_y, 4, 0, 2 * Math.PI);
            ctx.fill();
          }
        });
      };
    }
  }, [landmarks, imageSrc]);

  return (
    <div className="landmarks-viewer">
      <div className="landmarks-header">
        <h2>📏 Análisis de Puntos Faciales</h2>
        <p>Detecta 478 puntos clave en el rostro para análisis ortodóntico</p>
      </div>

      <div className="upload-section">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          id="landmarks-file-input"
          className="file-input"
        />
        <label htmlFor="landmarks-file-input" className="file-label">
          📁 Seleccionar Imagen
        </label>
        
        {selectedFile && (
          <span className="file-name">{selectedFile.name}</span>
        )}
      </div>

      <div className="action-buttons">
        <button
          onClick={analyzeLandmarks}
          disabled={!selectedFile || loading}
          className="btn-analyze"
        >
          {loading ? '⏳ Analizando...' : '🔍 Analizar Landmarks'}
        </button>
        
        {(imageSrc || landmarks) && (
          <button onClick={handleReset} className="btn-reset">
            🔄 Reiniciar
          </button>
        )}
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {metrics && (
        <div className="metrics-panel">
          <h3>📊 Métricas Calculadas</h3>
          
          {/* Métricas Básicas */}
          <div className="metrics-section">
            <h4>Métricas Básicas</h4>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">Apertura de Boca:</span>
                <span className="metric-value">{(metrics.mouth_opening * 100).toFixed(2)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Ancho de Sonrisa:</span>
                <span className="metric-value">{(metrics.smile_width * 100).toFixed(2)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Puntos Detectados:</span>
                <span className="metric-value">{landmarks.length}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Resolución:</span>
                <span className="metric-value">{metrics.face_width} × {metrics.face_height}</span>
              </div>
            </div>
          </div>


          {/* Métricas Avanzadas */}
          {metrics.facial_symmetry !== undefined && (
            <div className="metrics-section advanced">
              <h4>✨ Métricas Avanzadas</h4>
              <div className="metrics-grid">
                <div className="metric-item highlight">
                  <span className="metric-label">Simetría Facial:</span>
                  <span className="metric-value">{metrics.facial_symmetry.toFixed(1)}%</span>
                  <span className={`metric-status ${metrics.symmetry_status.toLowerCase()}`}>
                    {metrics.symmetry_status}
                  </span>
                </div>
                <div className="metric-item highlight">
                  <span className="metric-label">Ángulo Mandibular:</span>
                  <span className="metric-value">{metrics.jaw_angle.toFixed(1)}°</span>
                  <span className={`metric-status ${metrics.jaw_angle_status.toLowerCase()}`}>
                    {metrics.jaw_angle_status}
                  </span>
                </div>
                <div className="metric-item highlight">
                  <span className="metric-label">Proporción Áurea:</span>
                  <span className="metric-value">{metrics.golden_ratio_score.toFixed(1)}%</span>
                  <span className={`metric-status ${metrics.golden_ratio_status.toLowerCase()}`}>
                    {metrics.golden_ratio_status}
                  </span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Ratio Facial:</span>
                  <span className="metric-value">{metrics.face_ratio.toFixed(3)}</span>
                  <span className="metric-info">(Ideal: 1.618)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="visualization-container">
        {imageSrc && !landmarks && (
          <img src={imageSrc} alt="Original" className="preview-image" />
        )}
        
        <canvas 
          ref={canvasRef} 
          className="landmarks-canvas"
          style={{ display: landmarks ? 'block' : 'none' }}
        />
      </div>

      {landmarks && (
        <div className="legend">
          <h4>Leyenda de Puntos Clave:</h4>
          <div className="legend-items">
            <div className="legend-item">
              <span className="legend-dot" style={{backgroundColor: '#ff0000'}}></span>
              <span>Labios</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{backgroundColor: '#0000ff'}}></span>
              <span>Comisuras</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{backgroundColor: '#ffff00'}}></span>
              <span>Nariz</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{backgroundColor: '#ff00ff'}}></span>
              <span>Barbilla</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{backgroundColor: '#00ff00'}}></span>
              <span>Otros (478 puntos)</span>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Detectando landmarks faciales...</p>
        </div>
      )}
    </div>
  );
};

export default LandmarksViewer;
