// frontend/src/services/api.js
import axios from 'axios';
import authService from './authService';

// Interceptar requests para agregar token de autenticación
const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";
// Ensure protocol is present (Render 'host' property might return just domain)
const finalBaseURL = baseURL.startsWith('http') ? baseURL : `https://${baseURL}`;

const apiClient = axios.create({
    baseURL: finalBaseURL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Agregar interceptor para incluir el token JWT automáticamente
apiClient.interceptors.request.use(
    (config) => {
        const token = authService.getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Agregar interceptor para manejar errores de autenticación
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token inválido o expirado
            authService.logout();
            // Recargar la página para ir al login
            window.location.href = '/';
        }
        return Promise.reject(error);
    }
);

/**
 * Verifica el estado del sistema (backend y modelo de IA).
 * @returns {Promise<object>} Datos del estado del sistema.
 */
export const checkSystemStatus = async () => {
    const { data } = await apiClient.get('/health');
    return data;
};

/**
 * Obtiene información detallada sobre el modelo de IA.
 * @returns {Promise<object>} Métricas y clases del modelo.
 */
export const getModelInfo = async () => {
    const { data } = await apiClient.get('/model-info');
    return data;
};

/**
 * Analiza una sesión de texto (NLP) para obtener emociones y riesgos.
 * @param {string} text - El texto de la sesión o diario.
 * @param {string} patientId - El ID del paciente.
 * @returns {Promise<object>} Resultados de emociones y riesgo.
 */
export const analyzeSession = async (text, patientId) => {
    const { data } = await apiClient.post('/session/analyze', {
        text,
        patient_id: patientId
    });
    return data;
};

/**
 * Envía una imagen para ser analizada por la IA.
 * @param {File} file - El archivo de imagen a analizar.
 * @param {string} patientDid - El DID del paciente.
 * @param {boolean} useEnsemble - Si se debe usar el ensemble de modelos.
 * @returns {Promise<object>} Los resultados del análisis.
 */
export const analyzeImage = async (file, patientDid, useEnsemble = false) => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await apiClient.post(
        `/analyze?patient_did=${encodeURIComponent(patientDid)}&use_ensemble=${useEnsemble}`, 
        formData, 
        {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        }
    );

    if (!data.success) {
        throw new Error(data.error || "Error desconocido en el análisis.");
    }

    return data;
};

/**
 * Contribuye con los datos de un análisis para investigación (DeSci).
 * @param {string} analysisId - El ID del análisis a contribuir.
 * @param {string} patientDid - El DID del paciente que autoriza.
 * @returns {Promise<object>} El resultado de la contribución.
 */
export const contributeToDeSci = async (analysisId, patientDid) => {
    const { data } = await apiClient.post(`/contribute-data?analysis_id=${analysisId}&patient_did=${encodeURIComponent(patientDid)}`);
    if (!data.success) {
        throw new Error(data.error || "Error al contribuir a DeSci.");
    }
    return data;
};

/**
 * Obtiene el historial de análisis realizados.
 * @returns {Promise<Array>} Lista de análisis previos.
 */
export const getHistory = async () => {
    const { data } = await apiClient.get('/history');
    return data;
};

/**
 * Crea un nuevo paciente en el sistema.
 * @param {object} patientData - Datos del paciente (full_name, did).
 * @returns {Promise<object>} El resultado del registro.
 */
export const createPatient = async (patientData) => {
    const { data } = await apiClient.post('/patients', patientData);
    return data;
};

/**
 * Obtiene las imágenes de la galería/pacientes.
 * @returns {Promise<Array>} Lista de imágenes o pacientes.
 */
export const getGalleryImages = async () => {
    const { data } = await apiClient.get('/gallery/images');
    return data;
};

/**
 * Simula el resultado de un tratamiento.
 * @param {File} file - Imagen original.
 * @param {string} type - Tipo de tratamiento (aligner, brackets, whitening).
 * @returns {Promise<object>} Resultado con imagen simulada.
 */
export const simulateTreatment = async (file, type = 'aligner') => {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await apiClient.post(`/simulate-treatment?treatment_type=${type}`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return data;
};

/**
 * Analiza una imagen existente en la galería del servidor.
 * @param {string} filename - Nombre del archivo en la galería.
 * @param {string} patientDid - El DID del paciente.
 * @param {boolean} useEnsemble - Si se debe usar el ensemble de modelos.
 * @returns {Promise<object>} Los resultados del análisis.
 */
export const analyzeGalleryImage = async (filename, patientDid, useEnsemble = false) => {
    const { data } = await apiClient.post(
        `/analyze/gallery?patient_did=${encodeURIComponent(patientDid)}&filename=${encodeURIComponent(filename)}&use_ensemble=${useEnsemble}`
    );
    
    if (!data.success) {
        throw new Error(data.error || "Error desconocido en el análisis de galería.");
    }
    
    return data;
};

/**
 * Obtiene la evolución temporal de un paciente.
 * @param {string} patientDid - El DID del paciente.
 * @returns {Promise<object>} Datos de evolución (timeline, tendencia).
 */
export const getPatientEvolution = async (patientDid) => {
    const { data } = await apiClient.get(`/patient/${encodeURIComponent(patientDid)}/evolution`);
    
    if (!data.success) {
        throw new Error(data.error || "Error al obtener evolución del paciente.");
    }
    
    return data;
};

/**
 * Verifica si la evolución del paciente es adecuada.
 * @param {string} patientDid - El DID del paciente.
 * @returns {Promise<object>} Estado de evolución y métricas.
 */
export const getPatientEvolutionCheck = async (patientDid) => {
    const { data } = await apiClient.get(`/patients/${encodeURIComponent(patientDid)}/evolution-check`);
    return data;
};

/**
 * Obtiene una explicación visual (Grad-CAM) para una imagen.
 * @param {File} file - El archivo de imagen.
 * @returns {Promise<object>} Datos de la explicación (heatmap base64, regiones).
 */
export const explainAnalysis = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await apiClient.post('/analyze/explain', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    if (!data.success) {
        throw new Error(data.error || "Error al generar la explicación visual.");
    }

    return data;
};
/**
 * Genera un informe clínico SOAP utilizando Gemini AI.
 * @param {string} sessionId - El ID de la sesión.
 * @returns {Promise<object>} El informe generado.
 */
export const generateSOAPReport = async (sessionId) => {
    const { data } = await apiClient.post(`/api/reports/generate_soap/${sessionId}`);
    return data;
};

/**
 * Genera material psicoeducativo y tareas para el paciente usando LangChain.
 * @param {string} sessionId - El ID de la sesión.
 * @returns {Promise<object>} El material generado.
 */
export const generatePsychoeducationReport = async (sessionId) => {
    const { data } = await apiClient.post(`/api/reports/psychoeducation/${sessionId}`);
    return data;
};

/**
 * Envía feedback clínico para el aprendizaje activo del sistema.
 * @param {string} sessionId - ID de la sesión.
 * @param {object} originalOutput - Diccionario de emociones/síntomas original de la IA.
 * @param {object} correctedOutput - Diccionario corregido por el doctor.
 * @param {string} comments - Comentarios opcionales.
 * @returns {Promise<object>} Respuesta del servidor.
 */
export const submitFeedback = async (sessionId, originalOutput, correctedOutput, comments) => {
    const { data } = await apiClient.post('/learning/feedback', {
        session_id: sessionId,
        original_ai_output: originalOutput,
        doctor_corrected_output: correctedOutput,
        comments
    });
    return data;
};

/**
 * Envía una consulta al Asistente Clínico Inteligente (RAG).
 * @param {string} query - Pregunta del médico.
 * @param {string} patientId - (Opcional) Contexto del paciente.
 * @returns {Promise<object>} Respuesta del agente y fuentes.
 */
export const chatWithAssistant = async (query, patientId = null) => {
    const payload = { query, patient_id: patientId };
    const { data } = await apiClient.post('/api/chat', payload);
    return data;
};
