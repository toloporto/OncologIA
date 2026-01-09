import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  FileText, 
  Activity, 
  ChevronDown, 
  ChevronUp, 
  Download, 
  Mail, 
  Brain,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  User,
  Search,
  Filter
} from 'lucide-react';
import * as api from '../services/api';

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.getHistory();
        setHistory(data);
      } catch (err) {
        setError("No se pudo cargar el historial.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  // Mapeo de traducciones
  const emotionTranslations = {
      "others": "Otros",
      "joy": "Alegría",
      "sadness": "Tristeza",
      "anger": "Ira / Enojo",
      "surprise": "Sorpresa",
      "disgust": "Asco",
      "fear": "Miedo"
  };

  const getTopEmotion = (emotions) => {
    if (!emotions) return "N/A";
    const top = Object.entries(emotions).sort((a,b) => b[1] - a[1])[0];
    return emotionTranslations[top[0]] || top[0];
  };

  const handleExportPDF = () => {
    window.print();
  };

  const handleSendEmail = (item) => {
    const subject = `Informe Clínico PsychoWebAI - Sesión ${new Date(item.timestamp).toLocaleDateString()}`;
    const body = `INFORME CLÍNICO - PsychoWebAI\n
Fecha: ${new Date(item.timestamp).toLocaleString()}
Paciente: ${item.patient_id}
Emoción Dominante: ${getTopEmotion(item.emotion_analysis)}\n
CONTENIDO DE LA SESIÓN:
"${item.raw_text}"\n
INFORME SOAP:
${item.soap_report || "Informe no generado"}\n
Generado automáticamente por PsychoWebAI Expert Model.`;
    
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  const parseSOAP = (text) => {
    if (!text) return null;
    const sections = { S: "", O: "", A: "" , P: "" };
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

  if (loading) {
    return (
      <div className="history-status-view">
        <Loader2 className="spin" size={48} color="#0d9488" />
        <p>Cargando registros históricos...</p>
      </div>
    );
  }

  return (
    <div className="history-wrapper">
      <div className="history-filters">
        <div className="search-bar">
          <Search size={18} color="#94a3b8" />
          <input type="text" placeholder="Filtrar por paciente, fecha o emoción..." disabled />
        </div>
        <button className="icon-btn-secondary"><Filter size={18} /><span>Filtros</span></button>
      </div>

      {history.length === 0 ? (
        <div className="empty-history card">
          <Clock size={64} color="#e2e8f0" />
          <p>No hay registros en el historial.</p>
          <span>Las sesiones analizadas aparecerán aquí cronológicamente.</span>
        </div>
      ) : (
        <div className="history-feed">
          {history.map((item) => {
            const isExpanded = expandedId === item.id;
            const topEmotion = getTopEmotion(item.emotion_analysis);
            
            return (
              <div key={item.id} className={`card history-record ${isExpanded ? 'expanded' : ''} no-print`}>
                <div className="record-header" onClick={() => toggleExpand(item.id)}>
                  <div className="record-meta-main">
                    <div className="record-date-badge">
                      <span className="day">{new Date(item.timestamp).getDate()}</span>
                      <span className="month">{new Date(item.timestamp).toLocaleString('default', { month: 'short' }).toUpperCase()}</span>
                    </div>
                    <div className="record-info-summary">
                      <div className="record-patient-id"><User size={14} /> {item.patient_id}</div>
                      <div className="record-time-detail">{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {topEmotion}</div>
                    </div>
                  </div>

                  <div className="record-status-tags">
                    <div className={`status-chip-compact ${item.risk_flag ? 'danger' : 'success'}`}>
                      {item.risk_flag ? <AlertTriangle size={14} /> : <CheckCircle2 size={14} />}
                      <span>{item.risk_flag ? 'Riesgo' : 'Seguro'}</span>
                    </div>
                    {item.soap_report && <div className="status-chip-compact primary"><Brain size={14} /><span>IA</span></div>}
                    <div className="expand-icon">{isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</div>
                  </div>
                </div>
                
                <div className={`record-content-collapsible ${isExpanded ? 'show' : ''}`}>
                  <div className="content-inner">
                    <div className="preview-section">
                      <h5><FileText size={14} /> Transcripción / Notas</h5>
                      <p className="raw-text-quotation">"{item.raw_text}"</p>
                    </div>

                    {item.soap_report ? (
                      <div className="soap-report-container">
                        <div className="report-header-flex">
                          <h5><Brain size={14} /> Evaluación Clínica Especializada (IA)</h5>
                          <div className="report-actions">
                            <button onClick={handleExportPDF} className="action-btn-pill" title="Imprimir PDF">
                                <Download size={14} /> <span>PDF</span>
                            </button>
                            <button onClick={() => handleSendEmail(item)} className="action-btn-pill" title="Enviar Email">
                                <Mail size={14} /> <span>Email</span>
                            </button>
                          </div>
                        </div>
                        
                        <div className="soap-matrix">
                          {Object.entries(parseSOAP(item.soap_report) || {}).map(([key, content]) => (
                            <div key={key} className="soap-tile">
                              <div className="soap-tile-header">
                                <span className="soap-letter">{key}</span>
                                <span className="soap-title">
                                    {key === 'S' && "Subjetivo"}
                                    {key === 'O' && "Objetivo"}
                                    {key === 'A' && "Análisis"}
                                    {key === 'P' && "Plan"}
                                </span>
                              </div>
                              <div className="soap-tile-body">{content || "Sin datos clínicos registrados."}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="no-report-note">
                        <Brain size={24} color="#cbd5e1" />
                        <p>No se generó un reporte clínico SOAP para esta consulta.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* HIDDEN PRINT VIEW */}
                <div className="print-only">
                  <div className="print-report-header">
                    <h2>INFORME CLÍNICO PSICOLÓGICO</h2>
                    <p className="psychoweb-brand">PsychoWebAI Clinical Platform</p>
                  </div>
                  <div className="print-meta-grid">
                    <div className="print-meta-item"><strong>Paciente:</strong> {item.patient_id}</div>
                    <div className="print-meta-item"><strong>Fecha/Hora:</strong> {new Date(item.timestamp).toLocaleString()}</div>
                    <div className="print-meta-item"><strong>Emoción:</strong> {topEmotion}</div>
                    <div className="print-meta-item"><strong>Estado:</strong> {item.risk_flag ? 'ALERTA DE RIESGO' : 'NORMAL'}</div>
                  </div>
                  <div className="print-section">
                    <h3>NOTAS DE LA CONSULTA</h3>
                    <p>{item.raw_text}</p>
                  </div>
                  {item.soap_report && (
                    <div className="print-section">
                      <h3>EVALUACIÓN SOAP (IA EXPERT)</h3>
                      {Object.entries(parseSOAP(item.soap_report) || {}).map(([key, content]) => (
                        <div key={key} className="print-soap-block">
                          <h4 className="print-soap-title">{key} - {key === 'S' && "Subjetivo"} {key === 'O' && "Objetivo"} {key === 'A' && "Análisis"} {key === 'P' && "Plan"}</h4>
                          <p>{content}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="print-footer">
                    Este documento ha sido generado por PsychoWebAI. Requiere la revisión y firma de un profesional colegiado.
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      <style>{`
        .history-wrapper { animation: fadeInSlide 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
        
        .history-filters { display: flex; gap: 1.5rem; margin-bottom: 2.5rem; }
        .search-bar { 
          flex: 1; 
          background: white; 
          border: 1px solid var(--border-soft); 
          border-radius: 16px; 
          display: flex; 
          align-items: center; 
          padding: 0 1.25rem;
          height: 52px;
          box-shadow: var(--shadow-sm);
        }
        .search-bar input { border: none; outline: none; background: transparent; width: 100%; padding-left: 10px; font-size: 1rem; color: var(--text-main); }
        
        .icon-btn-secondary {
          background: white; border: 1px solid var(--border-soft); border-radius: 16px; padding: 0 1.5rem;
          display: flex; align-items: center; gap: 10px; font-weight: 700; color: var(--text-muted); cursor: pointer; transition: all 0.3s;
          box-shadow: var(--shadow-sm);
        }
        .icon-btn-secondary:hover { 
            border-color: var(--primary); 
            color: var(--primary); 
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .history-feed { display: flex; flex-direction: column; gap: 1.5rem; }
        
        .history-record { padding: 0 !important; cursor: default; overflow: hidden; }
        .record-header { padding: 1.5rem 2rem; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.2s; }
        .record-header:hover { background: #f8fafc; }
        
        .record-meta-main { display: flex; align-items: center; gap: 1.5rem; }
        .record-date-badge { 
          display: flex; flex-direction: column; align-items: center; 
          background: #fff; border: 1px solid var(--border-soft); border-radius: 14px; padding: 8px 14px; min-width: 50px;
          box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        }
        .record-date-badge .day { font-size: 1.4rem; font-weight: 800; color: var(--text-main); line-height: 1; font-family: 'Plus Jakarta Sans', sans-serif; }
        .record-date-badge .month { font-size: 0.75rem; font-weight: 800; color: var(--primary); margin-top: 2px; }

        .record-patient-id { 
            font-weight: 800; 
            color: var(--text-main); 
            font-size: 1.1rem; 
            display: flex; 
            align-items: center; 
            gap: 8px;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        .record-time-detail { font-size: 0.9rem; color: var(--text-muted); margin-top: 4px; font-weight: 500; }

        .record-status-tags { display: flex; align-items: center; gap: 12px; }
        .status-chip-compact { 
          display: flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 99px; 
          font-size: 0.8rem; font-weight: 800; text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .status-chip-compact.success { background: #ecfdf5; color: #059669; border: 1px solid #d1fae5; }
        .status-chip-compact.danger { background: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
        .status-chip-compact.primary { background: #f5f3ff; color: #7c3aed; border: 1px solid #ede9fe; }
        
        .expand-icon { color: #cbd5e1; margin-left: 15px; transition: all 0.3s; }
        .record-header:hover .expand-icon { color: var(--primary); transform: scale(1.1); }

        .record-content-collapsible { 
          max-height: 0; overflow: hidden; transition: max-height 0.5s cubic-bezier(0.16, 1, 0.3, 1); 
          background: #fbfbfc; border-top: 1px solid var(--border-soft);
        }
        .record-content-collapsible.show { max-height: 2500px; }
        .content-inner { padding: 2.5rem; }

        .preview-section h5, .report-header-flex h5 { 
          margin: 0 0 1rem 0; font-size: 0.85rem; font-weight: 800; color: var(--text-muted); 
          text-transform: uppercase; letter-spacing: 0.1em; display: flex; align-items: center; gap: 10px;
        }
        .raw-text-quotation { 
          font-size: 1.05rem; line-height: 1.7; color: var(--text-main); font-style: italic; 
          background: white; padding: 1.5rem; border-radius: 16px; border: 1px solid var(--border-soft);
          border-left: 6px solid #e2e8f0; margin-bottom: 3rem;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }

        .soap-report-container { border-top: 1px dashed #e2e8f0; padding-top: 2.5rem; }
        .report-header-flex { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        .report-actions { display: flex; gap: 12px; }
        
        .action-btn-pill { 
          display: flex; align-items: center; gap: 8px; padding: 8px 18px; border-radius: 100px; 
          background: white; border: 1px solid var(--border-soft); font-size: 0.85rem; font-weight: 700; 
          color: var(--text-muted); cursor: pointer; transition: all 0.3s;
          box-shadow: var(--shadow-sm);
        }
        .action-btn-pill:hover { 
            border-color: var(--primary); 
            color: var(--primary); 
            background: #f5f3ff;
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .soap-matrix { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; }
        .soap-tile { background: white; border-radius: 20px; border: 1px solid var(--border-soft); padding: 2rem; transition: all 0.3s; }
        .soap-tile:hover { border-color: var(--primary-light); box-shadow: var(--shadow-premium); transform: translateY(-4px); }
        .soap-tile-header { display: flex; align-items: center; gap: 14px; margin-bottom: 1.25rem; }
        .soap-letter { 
          width: 32px; height: 32px; background: linear-gradient(135deg, var(--primary) 0%, var(--accent-violet) 100%); 
          color: white; border-radius: 10px; 
          display: flex; align-items: center; justify-content: center; font-size: 1rem; font-weight: 800;
          box-shadow: 0 4px 10px rgba(99, 102, 241, 0.2);
        }
        .soap-title { font-weight: 800; font-size: 1.1rem; color: var(--text-main); font-family: 'Plus Jakarta Sans', sans-serif; }
        .soap-tile-body { font-size: 1rem; line-height: 1.6; color: #475569; white-space: pre-wrap; }

        .no-report-note { text-align: center; padding: 3.5rem; background: #f8fafc; border-radius: 20px; color: var(--text-muted); font-size: 1rem; }
        
        .history-status-view { min-height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1.5rem; color: var(--text-muted); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        .print-only { display: none; }
        @media print {
          .no-print { display: none !important; }
          .print-only { display: block !important; padding: 2cm; font-family: 'Inter', sans-serif; color: black; background: white; }
          .print-report-header { text-align: center; margin-bottom: 2rem; border-bottom: 2px solid #000; padding-bottom: 1rem; }
          .psychoweb-brand { font-size: 0.8rem; color: #666; font-weight: 700; margin-top: 4px; }
          .print-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem; background: #f8fafc; padding: 1rem; }
          .print-section { margin-bottom: 2rem; }
          .print-section h3 { border-bottom: 1px solid #ddd; padding-bottom: 0.5rem; font-size: 1.1rem; }
          .print-soap-block { margin-top: 1rem; }
          .print-soap-title { margin: 0 0 0.5rem 0; font-weight: 800; font-size: 0.95rem; }
          .print-footer { margin-top: 4rem; text-align: center; font-size: 0.75rem; color: #777; border-top: 1px solid #eee; padding-top: 1rem; }
        }
      `}</style>
    </div>
  );
};

const Loader2 = ({ size, className, color }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke={color || "currentColor"} 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
);

export default History;
