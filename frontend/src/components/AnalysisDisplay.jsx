// frontend/src/components/AnalysisDisplay.jsx
import React, { useRef, useState, useLayoutEffect } from 'react';
import { CheckCircle2 } from 'lucide-react';
import './AnalysisDisplay.css';

const AnalysisDisplay = ({ previewUrl, analysisResult, segmentationPolygons }) => {
  const imageRef = useRef(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });

  // Hook para medir el tamaño de la imagen una vez que se carga
  useLayoutEffect(() => {
    const updateSize = () => {
      if (imageRef.current) {
        setImageSize({
          width: imageRef.current.offsetWidth,
          height: imageRef.current.offsetHeight,
        });
      }
    };

    const imgElement = imageRef.current;
    if (imgElement?.complete) {
        updateSize();
    }
    
    imgElement?.addEventListener('load', updateSize);
    window.addEventListener('resize', updateSize);
    
    return () => {
        imgElement?.removeEventListener('load', updateSize);
        window.removeEventListener('resize', updateSize);
    };
  }, [previewUrl]);

  // Escalar los polígonos al tamaño de la imagen mostrada
  const scalePolygons = (polygons, originalSize = 512) => {
    if (!imageSize.width || !imageSize.height) return [];

    const scaleX = imageSize.width / originalSize;
    const scaleY = imageSize.height / originalSize;

    return polygons.map(polygon => 
      polygon.map(point => [point[0] * scaleX, point[1] * scaleY])
    );
  };

  const scaledPolygons = segmentationPolygons ? scalePolygons(segmentationPolygons) : [];

  return (
    <div className="analysis-container">
      {previewUrl && (
        <div className="image-display">
          <img ref={imageRef} src={previewUrl} alt="Vista previa del análisis" />
          {scaledPolygons.length > 0 && (
            <svg className="segmentation-overlay" width={imageSize.width} height={imageSize.height}>
              {scaledPolygons.map((polygon, polyIndex) => (
                <polygon
                  key={polyIndex}
                  points={polygon.map(p => p.join(',')).join(' ')}
                  className="segmentation-polygon"
                />
              ))}
            </svg>
          )}
        </div>
      )}

      {analysisResult && (
        <div className="result-panel">
          <h3>
            <CheckCircle2 />
            Diagnóstico Principal
          </h3>
          <p>
            <strong>Condición:</strong>{' '}
            {analysisResult.prediction.class}
          </p>
          <p>
            <strong>Confianza:</strong>{' '}
            {(analysisResult.prediction.confidence * 100).toFixed(1)}%
          </p>
          <p>
            <strong>Descripción:</strong>{' '}
            {analysisResult.prediction.class_description}
          </p>
          <p>
            <strong>Recomendación:</strong>{' '}
            {analysisResult.analysis.treatment_recommendations.main_recommendation}
          </p>
        </div>
      )}
    </div>
  );
};

export default AnalysisDisplay;
