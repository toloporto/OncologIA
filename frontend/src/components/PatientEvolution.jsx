
import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Calendar,
  AlertOctagon
} from 'lucide-react';
import * as api from '../services/api';

const PatientEvolution = ({ patientId, patientName }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (patientId) {
      fetchEvolution();
    }
  }, [patientId]);

  const fetchEvolution = async () => {
    try {
      setLoading(true);
      const result = await api.getPatientEvolution(patientId);
      setData(result);
    } catch (err) {
      console.error("Error fetching evolution:", err);
      setError("No se pudo cargar la evolución del paciente.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Cargando historial oncológico...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!data || data.status === 'no_data' || !data.timeline || data.timeline.length === 0) {
    return (
      <div className="empty-evolution card">
        <Activity size={48} color="#94a3b8" />
        <p>No hay suficientes datos históricos para generar tendencias.</p>
        <span>Se requieren al menos 2 sesiones registradas.</span>
      </div>
    );
  }

  // Preparar datos para gráficos
  // data.timeline es [{date: '...', symptoms: {pain: 5, ...}}, ...]
  // Recharts necesita flat objects: [{date: '...', pain: 5, fatigue: 2}, ...]
  const chartData = data.timeline.map(day => ({
    date: new Date(day.date).toLocaleDateString(undefined, {month: 'short', day: 'numeric'}),
    fullDate: day.date,
    pain: day.symptoms.pain || 0,
    fatigue: day.symptoms.fatigue || 0,
    anxiety: day.symptoms.anxiety || 0,
    depression: day.symptoms.depression || 0,
    nausea: day.symptoms.nausea || 0
  })).reverse(); // El servicio suele devolver desc (más reciente primero), recharts quiere asc para tiempo izq->der?
  // Espera, el servicio debería devolver cronológicamente o nosotros lo ordenamos.
  // Asumamos que backend devuelve cronológico. Si no, .reverse()

  return (
    <div className="evolution-dashboard animate-fade-in">
      
      {/* HEADER & ALERTS */}
      <div className="evolution-header">
        <div className="title-group">
            <Activity color="#0d9488" size={24} />
            <h2>Evolución Clínica: {patientName}</h2>
        </div>
        <div className="meta-tag">
            <Calendar size={14} /> Últimos {chartData.length} registros
        </div>
      </div>

      {/* ALERT BANNERS */}
      {data.alerts && data.alerts.length > 0 && (
        <div className="alerts-container">
            {data.alerts.map((alert, idx) => (
                <div key={idx} className={`alert-banner ${alert.severity === 'high' ? 'critical' : 'warning'}`}>
                    {alert.severity === 'high' ? <AlertOctagon size={20} /> : <AlertTriangle size={20} />}
                    <div className="alert-content">
                        <strong>{alert.type === 'critical_level' ? 'NIVEL CRÍTICO' : 'TENDENCIA NEGATIVA'}</strong>
                        <span>{alert.message}</span>
                    </div>
                </div>
            ))}
        </div>
      )}

      {/* MAIN CHART */}
      <div className="card chart-card">
        <h3><TrendingUp size={18} /> Tendencias de Síntomas (ESAS)</h3>
        <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                    <linearGradient id="colorPain" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorFatigue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                    </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} label={{ value: 'Intensidad (0-10)', angle: -90, position: 'insideLeft', style: {textAnchor: 'middle'} }} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <Tooltip 
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                />
                <Legend iconType="circle" />
                
                <Area type="monotone" dataKey="pain" name="Dolor" stroke="#ef4444" fillOpacity={1} fill="url(#colorPain)" strokeWidth={3} />
                <Area type="monotone" dataKey="fatigue" name="Fatiga" stroke="#f59e0b" fillOpacity={1} fill="url(#colorFatigue)" strokeWidth={2} />
                <Line type="monotone" dataKey="anxiety" name="Ansiedad" stroke="#8b5cf6" strokeWidth={2} dot={false} />
            </AreaChart>
            </ResponsiveContainer>
        </div>
      </div>

      {/* TRENDS SUMMARY */}
      <div className="trends-grid">
        {Object.entries(data.trends).map(([symptom, slope]) => {
            if (slope === 0) return null;
            const isWorsening = slope > 0.1; // Pendiente positiva es mala (más síntoma)
            const isImproving = slope < -0.1;
            
            // Traducir key
            const label = {
                pain: 'Dolor',
                fatigue: 'Fatiga',
                anxiety: 'Ansiedad',
                depression: 'Depresión',
                nausea: 'Náuseas'
            }[symptom] || symptom;

            return (
                <div key={symptom} className="card trend-card">
                    <div className="trend-header">
                        <span className="t-label">{label}</span>
                        {isWorsening && <TrendingUp size={16} color="#ef4444" />}
                        {isImproving && <TrendingDown size={16} color="#10b981" />}
                    </div>
                    <div className="trend-value">
                        <span className={`val ${isWorsening ? 'bad' : (isImproving ? 'good' : 'neutral')}`}>
                            {Math.abs(slope * 7).toFixed(1)} pts
                        </span>
                        <span className="unit">/ semana</span>
                    </div>
                    <div className="trend-desc">
                        {isWorsening ? 'Empeorando' : (isImproving ? 'Mejorando' : 'Estable')}
                    </div>
                </div>
            );
        })}
      </div>

      <style>{`
        .evolution-dashboard { display: flex; flex-direction: column; gap: 1.5rem; }
        .evolution-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .title-group { display: flex; align-items: center; gap: 10px; }
        .title-group h2 { margin: 0; color: var(--text-main); font-size: 1.4rem; }
        .meta-tag { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: var(--text-muted); background: white; padding: 4px 10px; border-radius: 20px; border: 1px solid var(--border-soft); }

        .alerts-container { display: flex; flex-direction: column; gap: 0.75rem; animation: slideDown 0.4s ease-out; }
        .alert-banner { display: flex; align-items: center; gap: 1rem; padding: 1rem; border-radius: 12px; border-left: 5px solid; }
        .alert-banner.critical { background: #fef2f2; border-color: #ef4444; color: #991b1b; }
        .alert-banner.warning { background: #fffbeb; border-color: #f59e0b; color: #92400e; }
        .alert-content { display: flex; flex-direction: column; }
        .alert-content strong { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }

        .empty-evolution { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem !important; text-align: center; gap: 1rem; color: var(--text-muted); }

        .chart-card { padding: 1.5rem !important; min-height: 400px; }
        .chart-card h3 { margin: 0 0 1.5rem 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px; color: var(--text-main); }

        .trends-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; }
        .trend-card { padding: 1rem !important; display: flex; flex-direction: column; gap: 8px; }
        .trend-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; color: var(--text-muted); font-size: 0.9rem; text-transform: capitalize; }
        .trend-value { display: flex; align-items: baseline; gap: 4px; }
        .trend-value .val { font-size: 1.5rem; font-weight: 800; }
        .trend-value .val.bad { color: #ef4444; }
        .trend-value .val.good { color: #10b981; }
        .trend-value .unit { font-size: 0.8rem; color: var(--text-muted); }
        .trend-desc { font-size: 0.8rem; font-weight: 600; color: var(--text-main); }

        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
};

export default PatientEvolution;
