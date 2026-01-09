import React, { useState } from 'react';
import { UploadCloud, ArrowRight, Sparkles, RefreshCw } from 'lucide-react';
import * as api from '../services/api';
import ImageComparisonSlider from './ImageComparisonSlider';
import './TreatmentSimulator.css';

const TreatmentSimulator = () => {
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [resultUrl, setResultUrl] = useState(null);
    const [loading, setLoading] = useState(false);
    const [treatmentType, setTreatmentType] = useState('aligner');

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile) {
            setFile(selectedFile);
            setPreviewUrl(URL.createObjectURL(selectedFile));
            setResultUrl(null);
        }
    };

    const handleSimulate = async () => {
        if (!file) return;
        setLoading(true);
        try {
            const result = await api.simulateTreatment(file, treatmentType);
            if (result.success && result.after_image_base64) {
                setResultUrl(`data:image/jpeg;base64,${result.after_image_base64}`);
            }
        } catch (error) {
            console.error("Error simulating treatment:", error);
            alert("Error al generar la simulación.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="simulator-container">
            <div className="simulator-header">
                <h2><Sparkles className="icon-sparkle" /> Simulación de Tratamiento Generativo</h2>
                <p>Visualiza el futuro de tu sonrisa con nuestra IA generativa.</p>
            </div>

            <div className="controls-section">
                <div className="file-upload">
                    <input 
                        type="file" 
                        id="sim-upload" 
                        accept="image/*" 
                        onChange={handleFileChange} 
                        hidden 
                    />
                    <label htmlFor="sim-upload" className="upload-btn">
                        <UploadCloud size={20} />
                        {file ? "Cambiar Imagen" : "Subir Foto"}
                    </label>
                </div>

                <div className="treatment-select">
                    <label>Tipo de Tratamiento:</label>
                    <select value={treatmentType} onChange={(e) => setTreatmentType(e.target.value)}>
                        <option value="aligner">Alineadores Invisibles</option>
                        <option value="whitening">Blanqueamiento</option>
                        <option value="brackets">Brackets Estéticos</option>
                    </select>
                </div>

                <button 
                    className="simulate-btn" 
                    onClick={handleSimulate} 
                    disabled={!file || loading}
                >
                    {loading ? <RefreshCw className="spin" /> : <Sparkles />}
                    {loading ? "Generando..." : "Simular Resultado"}
                </button>
            </div>

            <div className="visualization-area">
                {resultUrl && previewUrl ? (
                    // Si tenemos ambas imágenes, mostramos el slider
                    <div className="comparison-wrapper">
                        <h3>Desliza para comparar</h3>
                        <ImageComparisonSlider 
                            beforeImage={previewUrl} 
                            afterImage={resultUrl} 
                        />
                    </div>
                ) : (
                    // Si no, mostramos la vista clásica o placeholder
                    <div className="single-view">
                        <div className="image-card before">
                            <h3>Vista Previa</h3>
                            {previewUrl ? (
                                <img src={previewUrl} alt="Original" />
                            ) : (
                                <div className="placeholder">
                                    <p>Sube una foto para comenzar</p>
                                </div>
                            )}
                        </div>
                        {!previewUrl && (
                            <div className="placeholder-info">
                                <p>El resultado aparecerá aquí después de la simulación.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TreatmentSimulator;
