import React, { useState, useRef, useEffect } from 'react';
import './ImageComparisonSlider.css';
import { MoveHorizontal } from 'lucide-react';

const ImageComparisonSlider = ({ beforeImage, afterImage }) => {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    const percentage = (x / rect.width) * 100;

    setSliderPosition(percentage);
  };

  // Soporte para pantallas táctiles
  const handleTouchMove = (e) => {
    if (!isDragging || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const touch = e.touches[0];
    const x = Math.max(0, Math.min(touch.clientX - rect.left, rect.width));
    const percentage = (x / rect.width) * 100;
    
    setSliderPosition(percentage);
  };

  useEffect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('touchend', handleMouseUp);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchend', handleMouseUp);
    };
  }, []);

  return (
    <div 
      className="comparison-slider-container" 
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onTouchMove={handleTouchMove}
    >
      {/* Imagen del "Después" (Fondo) */}
      <div className="img-wrapper after-image">
        <img src={afterImage} alt="Después" />
        <span className="label label-after">Después</span>
      </div>

      {/* Imagen del "Antes" (Recortada) */}
      <div 
        className="img-wrapper before-image" 
        style={{ width: `${sliderPosition}%` }}
      >
        <img src={beforeImage} alt="Antes" />
        <span className="label label-before">Antes</span>
      </div>

      {/* Línea del Slider */}
      <div 
        className="slider-handle"
        style={{ left: `${sliderPosition}%` }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleMouseDown}
      >
        <div className="handle-line"></div>
        <div className="handle-circle">
          <MoveHorizontal size={20} color="#fff" />
        </div>
      </div>
    </div>
  );
};

export default ImageComparisonSlider;
