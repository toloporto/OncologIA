import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Activity, 
  Send, 
  Brain, 
  ShieldAlert, 
  CheckCircle2,
  FileText,
  Sparkles,
  Download,
  Mail,
  User,
  Plus,
  RefreshCw,
  Clock,

  ChevronRight,
  Edit2,
  Save,
  X,
  Database
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';
import * as api from '../services/api';
import AudioRecorder from './AudioRecorder';

const SessionAnalysis = () => {
    const [text, setText] = useState("");
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState("");
    const [soapReport, setSoapReport] = useState(null);
    const [isGeneratingSOAP, setIsGeneratingSOAP] = useState(false);
    const [psychoDraft, setPsychoDraft] = useState(null);
    const [isGeneratingPsycho, setIsGeneratingPsycho] = useState(false);
    const [isSafeMode, setIsSafeMode] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [correctedData, setCorrectedData] = useState({});
    const [feedbackStatus, setFeedbackStatus] = useState("");

    const SafeModeBadge = () => (
        <div className="safe-mode-badge animate-pulse">
            <ShieldAlert size={14} />
            <span>PROTECCIÓN ACTIVA: MODO SEGURO</span>
        </div>
    );

    const handleAnalyze = async () => {
        if (!text.trim()) return;
        setIsAnalyzing(true);
        setError("");
        setResults(null);
        setSoapReport(null);
        setPsychoDraft(null);
        
        try {
            const patientDid = localStorage.getItem("patientDID") || "anonymous";
            const data = await api.analyzeSession(text, patientDid);
            setResults(data);
            setCorrectedData(data.emotion_analysis || {});
            // El cambio de vista ocurre automáticamente al poblar 'results'
        } catch (err) {
            console.error(err);
            if (err.response?.status === 429) {
                setError("La IA está saturada por exceso de peticiones. Por favor, espera 30-60 segundos e inténtalo de nuevo.");
            } else {
                setError("Error al analizar sesión: " + (err.response?.data?.detail || err.message));
            }
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleGenerateSOAP = async () => {
        if (!results?.session_id) return;
        setIsGeneratingSOAP(true);
        try {
            const data = await api.generateSOAPReport(results.session_id);
            setSoapReport(data.soap_report);
        } catch (err) {
            console.error(err);
            if (err.response?.status === 429) {
                setError("El servidor de IA está saturado (Límite de cuota). Por favor, espera 10 segundos e inténtalo de nuevo.");
            } else {
                setError("Error al generar nota SOAP: " + err.message);
            }
        } finally {
            setIsGeneratingSOAP(false);
        }
    };

    const handleGeneratePsycho = async () => {
        if (!results?.session_id) return;
        setIsGeneratingPsycho(true);
        try {
            const data = await api.generatePsychoeducationReport(results.session_id);
            setPsychoDraft(data.psychoeducation_draft);
        } catch (err) {
            console.error(err);
            if (err.response?.status === 429) {
                setError("El servidor de IA está saturado (Límite de cuota). Por favor, espera 10 segundos e inténtalo de nuevo.");
            } else {
                setError("Error al generar psicoeducación: " + err.message);
            }
        } finally {
            setIsGeneratingPsycho(false);
        }
    };

    const handleExportPDF = () => {
        window.print();
    };

    const handleSendEmail = () => {
        const topEmotion = chartData.sort((a,b) => b.A - a.A)[0]?.subject || "N/A";
        const subject = `Resumen de Sesión y Tareas - PsychoWebAI - ${new Date().toLocaleDateString()}`;
        
        let body = `INFORME CLÍNICO - PsychoWebAI\n\n`;
        
        if (psychoDraft) {
            body += `MATERIAL PARA EL PACIENTE:\n${psychoDraft}\n\n`;
        } else {
            body += `CONTENIDO DE LA SESIÓN:\n"${results.raw_text}"\n\n`;
            if (soapReport) {
                body += `INFORME SOAP:\n${soapReport}\n\n`;
            }
        }
        
        body += `Generado automáticamente por PsychoWebAI Expert Model (Gemini AI).`;
        
        window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    };

    const handleReset = () => {
        setResults(null);
        setText("");
        setSoapReport(null);
        setPsychoDraft(null);
        setError("");
        setIsEditing(false);
        setFeedbackStatus("");
    };

    const handleSaveCorrection = async () => {
        try {
            await api.submitFeedback(
                results.session_id,
                results.emotion_analysis,
                correctedData,
                "Corrección manual del especialista (Active Learning Loop)"
            );
            setFeedbackStatus("✅ Aprendizaje guardado.");
            setIsEditing(false);
            // Actualizar visualmente los resultados con la corrección
            setResults(prev => ({
                ...prev,
                emotion_analysis: correctedData
            }));
            setTimeout(() => setFeedbackStatus(""), 3000);
        } catch (err) {
            console.error("Error saving feedback:", err);
            setError("No se pudo guardar la corrección.");
        }
    };

    // Helper para parsear la nota SOAP
    const parseSOAP = (text) => {
        if (!text) return null;
        const sections = { S: "", O: "", A: "", P: "" };
        const lines = text.split('\n');
        let currentKey = null;

        const sectionRegex = /^[#*\s]*([SOAP])(?:\s?\(.*?\))?[:\s-\*]*/i;

        lines.forEach(line => {
            const match = line.match(sectionRegex);
            if (match) {
                currentKey = match[1].toUpperCase();
                const content = line.replace(sectionRegex, '').trim();
                if (content) sections[currentKey] = content + '\n';
            } else if (currentKey) {
                sections[currentKey] += line + '\n';
            }
        });

        Object.keys(sections).forEach(k => {
            sections[k] = sections[k].trim();
        });

        return sections;
    };

    const soapSections = parseSOAP(soapReport);
    const hasDemoMarker = (text) => text?.includes("(MODO SEGURO") || text?.includes("(MODO DEMO");
    const isActuallySafeMode = hasDemoMarker(soapReport) || hasDemoMarker(psychoDraft);

    // Mapeo de traducciones ESAS (Symptom Assessment)
    const emotionTranslations = {
        "pain": "Dolor",
        "anxiety": "Ansiedad",
        "fatigue": "Fatiga / Cansancio",
        "nausea": "Náuseas",
        "depression": "Depresión / Ánimo",
        "insomnia": "Insomnio",
        "appetite": "Falta de Apetito",
        "shortness_of_breath": "Falta de Aire"
    };

    // Preparar datos para el gráfico
    const chartData = results?.emotion_analysis 
        ? Object.entries(results.emotion_analysis).map(([key, value]) => ({
            subject: emotionTranslations[key] || key.charAt(0).toUpperCase() + key.slice(1),
            A: value * 100, // Escala 0-100
            fullMark: 100
        })) 
        : [];

    const selectedPatientName = localStorage.getItem("patientName");
    const selectedPatientDID = localStorage.getItem("patientDID");

    return (
        <div className="analysis-wrapper">
            {/* PATIENT INFO BANNER */}
            <div className={`card patient-status-banner ${!selectedPatientDID ? 'warning-bg' : 'info-bg'}`}>
                <div className="banner-left">
                    <div className="avatar-circle">
                      <User size={20} color={selectedPatientDID ? "#0d9488" : "#f59e0b"} />
                    </div>
                    <div className="banner-text">
                        <span className="label">Paciente en Sesión</span>
                        <h4 className="value">{selectedPatientName || "Sin Seleccionar"}</h4>
                        <span className="did-tag">DID: {selectedPatientDID || "Anónimo / Temporal"}</span>
                    </div>
                </div>
                {!selectedPatientDID && (
                    <div className="banner-warning">
                        <AlertTriangle size={18} />
                        <span>Recomendado: selecciona un paciente antes de iniciar.</span>
                    </div>
                )}
            </div>

            {isActuallySafeMode && <SafeModeBadge />}
            {error && <div className="card error-alert-full">{error}</div>}

            {/* INPUT SECTION */}
            {!results && (
                <div className="card session-input-card">
                    <div className="card-header-flex">
                        <div className="header-text">
                            <h3><FileText size={18} color="#0d9488" /> Notas de Consulta</h3>
                            <p>Escribe los pensamientos o diálogos relevantes de la sesión.</p>
                        </div>
                        <div className="status-chip-compact primary">
                            <Sparkles size={14} /> <span>IA Activa</span>
                        </div>
                    </div>
                    
                    <div style={{ position: 'relative' }}>
                        <textarea 
                            className="clinical-textarea"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Paciente expresa síntomas de..."
                            /* ... */
                        />
                        <div style={{ position: 'absolute', bottom: '20px', right: '20px' }}>
                             <AudioRecorder onTranscriptionComplete={(newText) => setText(prev => prev + (prev ? " " : "") + newText)} />
                        </div>
                    </div>
                    
                    <div className="action-toolbar">
                      <p className="char-count">{text.length} caracteres</p>
                      <button 
                          className="primary-btn wide-btn"
                          onClick={handleAnalyze} 
                          disabled={isAnalyzing || !text.trim()}
                      >
                          {isAnalyzing ? (
                              <><RefreshCw className="spin" size={20} /> Analizando...</>
                          ) : (
                              <><Activity size={20} /> Ejecutar Evaluación de Síntomas</>
                          )}
                      </button>
                    </div>
                </div>
            )}

            {/* RESULTS SECTION */}
            {results && (
                <div className="results-view animate-fade-in">
                    
                    {/* RISK ALERT */}
                    {results.risk_flag ? (
                        <div className="card risk-alert-card">
                            <ShieldAlert size={48} className="risk-icon" />
                            <div className="risk-content">
                                <h3 className="risk-title">⚠️ ALERTA DE RIESGO CRÍTICA</h3>
                                <p className="risk-desc">{results.alert}</p>
                                <div className="risk-protocol">
                                    <strong>Protocolo de Emergencia:</strong>
                                    <ul>
                                        <li>Evaluación inmediata de seguridad del paciente.</li>
                                        <li>Notificación a contactos de confianza o servicios médicos.</li>
                                        <li>Documentación exhaustiva del plan de seguridad.</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="card safety-confirmation">
                             <CheckCircle2 size={24} color="#10b981" />
                             <span>Análisis completado: No se identificaron marcadores de riesgo eminente.</span>
                        </div>
                    )}

                    {/* XAI EXPLAINABILITY SECTION */}
                    {results.explanation && results.explanation.length > 0 && (
                        <div className="card xai-card animate-fade-in" style={{marginBottom: '2.5rem', borderLeft: '4px solid #8b5cf6'}}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem'}}>
                                <Sparkles size={20} color="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
                                <h3 style={{margin: 0, color: '#4c1d95'}}>Interpretación del Modelo (XAI)</h3>
                            </div>
                            <p style={{fontSize: '0.9rem', color: '#64748b', marginBottom: '1rem'}}>
                                El sistema detectó las siguientes palabras clave como factores determinantes para el análisis emocional:
                            </p>
                            <div className="xai-chips" style={{display: 'flex', flexWrap: 'wrap', gap: '8px'}}>
                                {results.explanation.map((item, idx) => (
                                    <div key={idx} className="xai-chip" title={`Impacto: ${item.impact.toFixed(3)}`}>
                                        <span style={{fontWeight: '600'}}>{item.word}</span>
                                    </div>
                                ))}
                            </div>
                            <style>{`
                                .xai-chip {
                                    background: #f3e8ff;
                                    color: #6b21a8;
                                    padding: 6px 14px;
                                    border-radius: 99px;
                                    font-size: 0.9rem;
                                    border: 1px solid #d8b4fe;
                                    transition: all 0.2s;
                                    cursor: help;
                                }
                                .xai-chip:hover {
                                    transform: translateY(-2px);
                                    box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.2);
                                    background: #faf5ff;
                                }
                            `}</style>
                        </div>
                    )}

                    <div className="analysis-grid">
                        {/* CHART CARD */}
                        <div className="card visual-analysis">
                            <div className="card-header-flex" style={{marginBottom: '1rem', justifyContent: 'space-between', display: 'flex'}}>
                                <h3><Activity size={18} color="#0d9488" /> Perfil de Síntomas (ESAS)</h3>
                                {results && !isEditing && (
                                    <button onClick={() => setIsEditing(true)} className="icon-btn-secondary" title="Corregir IA">
                                        <Edit2 size={16} /> <span>Corregir</span>
                                    </button>
                                )}
                            </div>

                            <div className="radar-container" style={{ minHeight: '320px', width: '100%' }}>
                                {chartData.length > 0 && (
                                    <ResponsiveContainer width="100%" height={320}>
                                      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                                          <PolarGrid stroke="#e2e8f0" />
                                          <PolarAngleAxis dataKey="subject" tick={{fontSize: 12, fontWeight: 600, fill: '#64748b'}} />
                                          <PolarRadiusAxis angle={30} domain={[0, 100]} axisLine={false} tick={false} />
                                          <Radar
                                              name="Intensidad %"
                                              dataKey="A"
                                              stroke={isEditing ? "#f59e0b" : "#0ea5e9"}
                                              strokeWidth={4}
                                              fill="url(#colorEmotions)"
                                              fillOpacity={0.6}
                                          />
                                          <defs>
                                              <linearGradient id="colorEmotions" x1="0" y1="0" x2="0" y2="1">
                                                  <stop offset="5%" stopColor={isEditing ? "#fbbf24" : "#0ea5e9"} stopOpacity={0.8}/>
                                                  <stop offset="95%" stopColor={isEditing ? "#d97706" : "#2dd4bf"} stopOpacity={0.2}/>
                                              </linearGradient>
                                          </defs>
                                          <Tooltip />
                                      </RadarChart>
                                  </ResponsiveContainer>
                                )}
                            </div>
                        </div>

                        {/* LIST ANALYSIS / EDITING */}
                        <div className="card list-analysis">
                            <div className="card-header-flex" style={{marginBottom: '1rem', justifyContent: 'space-between', display: 'flex'}}>
                                {isEditing ? (
                                    <>
                                        <h3><Database size={18} color="#f59e0b" /> Modo Aprendizaje</h3>
                                        <div style={{display: 'flex', gap: '8px'}}>
                                            <button onClick={() => setIsEditing(false)} className="icon-btn-secondary"><X size={16}/></button>
                                            <button onClick={handleSaveCorrection} className="primary-btn sm" style={{padding: '0 12px', height: '32px'}}>
                                                <Save size={14} /> Guardar
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <h3><FileText size={18} color="#0d9488" /> Desglose de Probabilidades</h3>
                                )}
                            </div>
                            
                            {feedbackStatus && <div style={{color: '#059669', fontSize: '0.9rem', marginBottom: '1rem', fontWeight: '600'}}>{feedbackStatus}</div>}

                            <div className="metrics-list-labels">
                                {!isEditing ? (
                                    chartData.sort((a,b) => b.A - a.A).map((item, idx) => (
                                        <div key={idx} className="metric-row">
                                            <div className="metric-info">
                                                <span className="m-name">{item.subject}</span>
                                                <span className="m-value">{Math.round(item.A)}%</span>
                                            </div>
                                            <div className="m-bar-bg">
                                                <div 
                                                    className={`m-bar-fill ${item.A > 70 ? 'high' : (item.A > 40 ? 'mid' : 'low')}`}
                                                    style={{ width: `${item.A}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="editing-list">
                                        <p style={{fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem'}}>
                                            Ajusta los valores reales. El sistema aprenderá de tus correcciones.
                                        </p>
                                        {Object.entries(correctedData).map(([key, val]) => (
                                            <div key={key} className="edit-row" style={{marginBottom: '1rem'}}>
                                                <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '4px'}}>
                                                    <label style={{fontSize: '0.9rem', fontWeight: '600', color: '#334155'}}>
                                                        {emotionTranslations[key] || key}
                                                    </label>
                                                    <span style={{fontWeight: '700', color: '#0d9488'}}>{Math.round(val * 100)}%</span>
                                                </div>
                                                <input 
                                                    type="range" 
                                                    min="0" 
                                                    max="1" 
                                                    step="0.05"
                                                    value={val}
                                                    onChange={(e) => setCorrectedData({...correctedData, [key]: parseFloat(e.target.value)})}
                                                    style={{width: '100%', accentColor: '#0d9488'}}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* SOAP SECTION */}
                    <div className="soap-action-area">
                      {!soapReport ? (
                          <div className="soap-cta-card card">
                              <Sparkles size={32} color="#0d9488" />
                              <h3>Generar Nota Clínica SOAP</h3>
                              <p>Utiliza nuestra IA de grado médico para estructurar un reporte profesional basado en este análisis.</p>
                              <button 
                                  className="primary-btn lg"
                                  onClick={handleGenerateSOAP}
                                  disabled={isGeneratingSOAP}
                                >
                                  {isGeneratingSOAP ? (
                                      <><RefreshCw className="spin" size={20} /> Estructurando Informe...</>
                                  ) : (
                                      <><Brain size={20} /> Generar Reporte Experto</>
                                  )}
                              </button>
                          </div>
                      ) : (
                          <div className="soap-results card animate-fade-in">
                              <div className="report-header no-print">
                                  <div className="report-title-group">
                                      <FileText color="#0d9488" size={22} />
                                      <h3>Informe Clínico SOAP (IA)</h3>
                                  </div>
                                  <div className="report-actions">
                                      <button onClick={handleExportPDF} className="icon-btn-secondary"><Download size={16} /> <span>PDF</span></button>
                                      <button onClick={handleSendEmail} className="icon-btn-secondary"><Mail size={16} /> <span>Email</span></button>
                                  </div>
                              </div>

                              <div className="soap-grid-matrix">
                                  {['S', 'O', 'A', 'P'].map((key) => (
                                      <div key={key} className="soap-item-card">
                                          <div className="soap-item-header">
                                              <div className="soap-circle">{key}</div>
                                              <h4>
                                                  {key === 'S' && "Subjetivo"}
                                                  {key === 'O' && "Objetivo"}
                                                  {key === 'A' && "Análisis"}
                                                  {key === 'P' && "Plan"}
                                              </h4>
                                          </div>
                                          <div className="soap-item-body">
                                              {soapSections ? soapSections[key] : "Cargando..."}
                                          </div>
                                      </div>
                                  ))}
                              </div>

                              <div className="confirmation-pill no-print">
                                  <CheckCircle2 size={16} /> <span>Reporte vinculado al historial del paciente exitosamente.</span>
                              </div>
                          </div>
                      )}
                    </div>

                    {/* PSYCHOEDUCATION SECTION */}
                    {soapReport && (
                        <div className="psycho-action-area animate-fade-in" style={{ marginTop: '2rem' }}>
                            {!psychoDraft ? (
                                <div className="soap-cta-card card psycho-cta">
                                    <Mail size={32} color="#0d9488" />
                                    <h3>Material de Apoyo al Paciente</h3>
                                    <p>Genera ejercicios de TCC y una metáfora explicativa basada en esta sesión para enviar al paciente.</p>
                                    <button 
                                        className="primary-btn lg"
                                        onClick={handleGeneratePsycho}
                                        disabled={isGeneratingPsycho}
                                        style={{ background: 'linear-gradient(135deg, #0d9488 0%, #065f46 100%)' }}
                                    >
                                        {isGeneratingPsycho ? (
                                            <><RefreshCw className="spin" size={20} /> Preparando Material...</>
                                        ) : (
                                            <><Sparkles size={20} /> Generar Guía TCC y Tareas</>
                                        )}
                                    </button>
                                </div>
                            ) : (
                                <div className="psycho-results card">
                                    <div className="report-header">
                                        <div className="report-title-group">
                                            <Mail color="#0d9488" size={22} />
                                            <h3>Borrador Terapéutico (Email)</h3>
                                        </div>
                                        <div className="status-chip-compact success" style={{ background: '#ecfdf5', color: '#059669', border: '1px solid #d1fae5' }}>
                                            <CheckCircle2 size={14} /> <span>Material Listo</span>
                                        </div>
                                    </div>
                                    <div className="psycho-content-body" style={{ padding: '1.5rem', background: '#f8fafc', borderRadius: '0 0 16px 16px', borderTop: '1px solid #e2e8f0' }}>
                                        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.95rem', color: '#334155', lineHeight: '1.6' }}>
                                            {psychoDraft}
                                        </pre>
                                        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                                            <button onClick={handleSendEmail} className="primary-btn">
                                                <Send size={18} /> Enviar por Email
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* FINAL ACTIONS */}
                    <div className="final-actions no-print">
                        <button onClick={handleReset} className="secondary-btn">
                            <Plus size={18} /> Iniciar Nueva Consulta
                        </button>
                    </div>

                    {/* PRINT VIEW */}
                    <div className="print-only">
                        <div className="p-header">
                          <h1>REPORTE DE SESIÓN CLÍNICA</h1>
                          <p>PsychoWebAI Expert Analysis</p>
                        </div>
                        <div className="p-meta">
                          <div><strong>Paciente:</strong> {selectedPatientName} ({selectedPatientDID})</div>
                          <div><strong>Fecha:</strong> {new Date().toLocaleString()}</div>
                        </div>
                        <div className="p-section">
                          <h3>NOTAS ORIGINALES</h3>
                          <p>{text}</p>
                        </div>
                        {soapReport && (
                          <div className="p-section">
                            <h3>ESTRUCTURA SOAP</h3>
                            {Object.entries(soapSections).map(([k, c]) => (
                              <div key={k} className="p-soap-block">
                                <strong>{k} - {k==='S'?'Subjetivo':k==='O'?'Objetivo':k==='A'?'Análisis':'Plan'}:</strong>
                                <p>{c}</p>
                              </div>
                            ))}
                          </div>
                        )}
                        <p className="p-footer">Análisis generado por PsychoWebAI. Requiere supervisión clínica.</p>
                    </div>
                </div>
            )}

            <style>{`
              .safe-mode-badge {
                display: flex; align-items: center; gap: 8px;
                background: var(--safe-mode-bg);
                border: 1px solid var(--safe-mode-border);
                color: var(--safe-mode-text);
                padding: 6px 14px; border-radius: 99px;
                font-size: 0.75rem; font-weight: 800;
                box-shadow: var(--shadow-safe-mode);
                margin-bottom: 1rem;
              }

              @keyframes pulse-soft {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(0.98); }
              }
              .animate-pulse { animation: pulse-soft 2s infinite ease-in-out; }

              .analysis-wrapper { 
                animation: fadeInSlide 0.6s cubic-bezier(0.16, 1, 0.3, 1);
                max-width: 1100px; margin: 0 auto; 
              }
              
              .card {
                background: rgba(255, 255, 255, 0.7) !important;
                -webkit-backdrop-filter: blur(12px);
                backdrop-filter: blur(12px);
              }

              .radar-container { 
                background: white; border-radius: var(--radius-lg); 
                padding: 1rem; border: 1px solid var(--border-soft);
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
              }
              
              .patient-status-banner { 
                display: flex; justify-content: space-between; align-items: center; 
                padding: 1.25rem 1.5rem !important; margin-bottom: 2rem; border: 1px solid var(--border-soft);
              }
              .patient-status-banner.info-bg { border-left: 4px solid var(--primary); }
              .patient-status-banner.warning-bg { border-left: 4px solid #f59e0b; background: #fffbeb; }
              
              .banner-left { display: flex; align-items: center; gap: 1rem; }
              .avatar-circle { width: 40px; height: 40px; border-radius: 50%; background: white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
              .banner-text .label { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
              .banner-text h4 { margin: 0; font-size: 1.1rem; color: var(--text-main); }
              .did-tag { font-size: 0.75rem; color: var(--text-muted); font-family: monospace; }
              
              .banner-warning { display: flex; align-items: center; gap: 8px; color: #b45309; font-size: 0.85rem; font-weight: 600; }

              .session-input-card { padding: 1.5rem !important; }
              .clinical-textarea { 
                width: 100%; min-height: 250px; padding: 1.25rem; border: 1px solid var(--border-soft); 
                border-radius: 12px; font-size: 1rem; line-height: 1.6; background: #fcfcfd; 
                color: #1e293b; resize: none; margin: 1.25rem 0; box-sizing: border-box; transition: all 0.2s;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              }
              .clinical-textarea::placeholder { color: #94a3b8; }
              .clinical-textarea:focus { outline: none; border-color: var(--primary); background: white; box-shadow: 0 0 0 4px rgba(13, 148, 136, 0.05); }
              
              .action-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 2rem; }
              .char-count { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
              .wide-btn { flex: 1; height: 52px; font-size: 1.05rem !important; box-shadow: 0 10px 15px -3px rgba(13, 148, 136, 0.2); }

              .safety-confirmation { 
                background: #ecfdf5; border-color: #10b981 !important; color: #065f46; 
                padding: 1rem 1.5rem !important; display: flex; align-items: center; gap: 12px; 
                margin-bottom: 2rem; font-weight: 600; font-size: 0.95rem;
              }
              
              .risk-alert-card { 
                background: #fef2f2; border: 2px solid #ef4444 !important; display: flex; gap: 1.5rem; 
                padding: 2rem !important; margin-bottom: 2.5rem; animation: soft-pulse 2s infinite;
              }
              @keyframes soft-pulse { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
              .risk-icon { flex-shrink: 0; margin-top: 4px; }
              .risk-title { margin: 0 0 0.5rem 0; color: #991b1b; letter-spacing: 0.02em; }
              .risk-desc { font-weight: 700; color: #b91c1c; font-size: 1.1rem; line-height: 1.4; }
              .risk-protocol { margin-top: 1.25rem; background: rgba(255,255,255,0.5); padding: 1rem; border-radius: 8px; }
              .risk-protocol strong { color: #7f1d1d; display: block; margin-bottom: 0.5rem; font-size: 0.9rem; }
              .risk-protocol ul { margin: 0; padding-left: 1.25rem; color: #991b1b; font-size: 0.9rem; }

              .analysis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2.5rem; }
              .radar-container { height: 320px; margin-top: 1rem; }
              
              .metric-row { margin-bottom: 1rem; }
              .metric-info { display: flex; justify-content: space-between; margin-bottom: 6px; }
              .m-name { font-weight: 600; color: var(--text-main); font-size: 0.9rem; }
              .m-value { font-size: 0.85rem; font-weight: 700; color: var(--text-muted); }
              .m-bar-bg { height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
              .m-bar-fill { height: 100%; border-radius: 4px; transition: width 1s ease-out; }
              .m-bar-fill.high { background: #ef4444; }
              .m-bar-fill.mid { background: var(--primary); }
              .m-bar-fill.low { background: #94a3b8; }

              .soap-cta-card { text-align: center; padding: 3rem !important; background: #fcfcfd; border: 2px dashed #cbd5e1 !important; }
              .soap-cta-card h3 { margin: 1.25rem 0 0.5rem 0; }
              .soap-cta-card p { color: var(--text-muted); margin-bottom: 2rem; }
              .lg { height: 56px; padding: 0 2.5rem !important; }

              .soap-results { padding: 0 !important; }
              .report-header { padding: 1.5rem; border-bottom: 1px solid var(--border-soft); display: flex; justify-content: space-between; align-items: center; }
              .report-title-group { display: flex; align-items: center; gap: 12px; }
              .report-title-group h3 { margin: 0; color: var(--text-main); }
              .report-actions { display: flex; gap: 10px; }
              
              .soap-grid-matrix { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; padding: 1.5rem; background: #fcfcfd; }
              .soap-item-card { background: white; border: 1px solid var(--border-soft); border-radius: 12px; padding: 1.25rem; }
              .soap-item-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
              .soap-circle { width: 28px; height: 28px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.8rem; }
              .soap-item-header h4 { margin: 0; font-size: 0.95rem; color: var(--text-main); }
              .soap-item-body { font-size: 0.95rem; line-height: 1.6; color: #475569; }

              .confirmation-pill { display: flex; align-items: center; gap: 8px; margin: 0 1.5rem 1.5rem 1.5rem; background: #ecfdf5; color: #065f46; padding: 8px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; border: 1px solid #d1fae5; }

              .final-actions { display: flex; justify-content: center; margin-top: 3rem; }
              .secondary-btn { background: white; border: 1px solid var(--border-soft); color: var(--text-main); padding: 0.8rem 2rem; border-radius: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: all 0.2s; }
              .secondary-btn:hover { border-color: var(--primary); color: var(--primary); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }

              @media (max-width: 800px) {
                .analysis-grid, .soap-grid-matrix { grid-template-columns: 1fr; }
                .action-toolbar { flex-direction: column; gap: 1rem; align-items: stretch; text-align: center; }
              }
            `}</style>
        </div>
    );
};

export default SessionAnalysis;
