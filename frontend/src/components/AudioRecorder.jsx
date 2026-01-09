import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2, AlertCircle } from 'lucide-react';
import * as api from '../services/api';

const AudioRecorder = ({ onTranscriptionComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState("");
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);

    const startRecording = async () => {
        setError("");
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorderRef.current.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
                // Detener tracks del micrófono
                stream.getTracks().forEach(track => track.stop());
                
                await sendToBackend(audioBlob);
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
        } catch (err) {
            console.error(err);
            setError("No se pudo acceder al micrófono. Verifica los permisos.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            setIsProcessing(true);
        }
    };

    const sendToBackend = async (blob) => {
        try {
            // Se asume que api.transcribeAudio existe o llamamos fetch directo
            // Para mantener consistencia con api.js, lo ideal es agregarlo allí, 
            // pero aquí podemos hacer el fetch directo si es más rápido.
            const formData = new FormData();
            formData.append('file', blob, 'recording.webm');

            // Usamos fetch directo al endpoint que acabamos de crear
            const response = await fetch('http://localhost:8000/api/transcribe', {
                method: 'POST',
                body: formData,
                // No setear Content-Type, fetch lo pone con boundary automáticamente
            });
            
            if (!response.ok) throw new Error("Error en servidor de transcripción");

            const data = await response.json();
            if (data.success && data.text) {
                onTranscriptionComplete(data.text);
            }
        } catch (err) {
            console.error(err);
            setError("Error transcribiendo audio. ¿Está el backend corriendo?");
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="audio-recorder-wrapper" style={{ display: 'inline-block', marginLeft: '10px' }}>
            {error && (
                <div className="tooltip-error" style={{ position: 'absolute', background: '#fee2e2', color: '#b91c1c', padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', marginTop: '-30px' }}>
                    {error}
                </div>
            )}
            
            <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                className={`record-btn ${isRecording ? 'recording' : ''}`}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '0 16px',
                    height: '42px',
                    borderRadius: '21px',
                    border: 'none',
                    background: isRecording ? '#ef4444' : (isProcessing ? '#e2e8f0' : '#f1f5f9'),
                    color: isRecording ? 'white' : (isProcessing ? '#64748b' : '#334155'),
                    fontWeight: 600,
                    cursor: isProcessing ? 'wait' : 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: isRecording ? '0 0 0 4px rgba(239, 68, 68, 0.2)' : 'none'
                }}
            >
                {isProcessing ? (
                    <>
                        <Loader2 className="spin" size={18} /> Procesando...
                    </>
                ) : isRecording ? (
                    <>
                        <Square size={18} fill="currentColor" /> Detener
                    </>
                ) : (
                    <>
                        <Mic size={18} /> Grabar Voz
                    </>
                )}
            </button>
            <style>{`
                .spin { animation: spin 1s linear infinite; }
                @keyframes spin { 100% { transform: rotate(360deg); } }
                .recording { animation: pulse-red 2s infinite; }
                @keyframes pulse-red { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }
            `}</style>
        </div>
    );
};

export default AudioRecorder;
