import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Activity, Calendar } from 'lucide-react';
import * as api from '../services/api';

const ProgressChart = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [evolutionCheck, setEvolutionCheck] = useState(null);

  useEffect(() => {
    fetchEvolutionData();
  }, []);

  const fetchEvolutionData = async () => {
    try {
      setLoading(true);
      // Intentar obtener el DID del paciente del localStorage o generar uno demo
      const patientDid = localStorage.getItem("patientDID") || "did:ortho:test_patient_001";
      console.log("Fetching evolution for:", patientDid);

      const result = await api.getPatientEvolution(patientDid);
      setData(result.data);
      
      // Nueva llamada para verificar alertas de evolución
      try {
        const checkResult = await api.getPatientEvolutionCheck(patientDid);
        setEvolutionCheck(checkResult);
      } catch (checkErr) {
        console.warn("No se pudo verificar estado de evolución:", checkErr);
      }

    } catch (err) {
      console.error('Error cargando evolución:', err);
      setError("No se pudo cargar el historial evolutivo. Asegúrate de tener análisis previos.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center p-10 text-blue-400">Cargando inteligencia temporal... ⏳</div>;
  if (error) return (
    <div className="text-center p-10 text-gray-500">
      <Activity size={48} className="mx-auto mb-4 opacity-50" />
      <p>{error}</p>
    </div>
  );
  if (!data || !data.timeline || data.timeline.length === 0) return (
    <div className="text-center p-10 text-gray-500">
      <Activity size={48} className="mx-auto mb-4 opacity-50" />
      <p>No hay suficientes datos para calcular la evolución.</p>
    </div>
  );

  // Preparar datos para Recharts
  const chartData = data.timeline.map(item => ({
    date: new Date(item.date).toLocaleDateString(),
    severity: item.severity,
    diagnosis: item.diagnosis.replace('class_', '').replace('_', ' ').toUpperCase(),
    fullDate: item.date
  }));

  // Icono de tendencia
  let TrendIcon = Minus;
  let trendColor = "#888";
  let trendText = "Estable";

  if (data.trend?.status === "improving") {
    TrendIcon = TrendingDown; // Bajada es buena en severidad
    trendColor = "#4caf50";
    trendText = "Mejorando";
  } else if (data.trend?.status === "worsening") {
    TrendIcon = TrendingUp; // Subida es mala
    trendColor = "#f44336";
    trendText = "Empeorando";
  }

  return (
    <div className="progress-chart-container">
      {/* Cabecera */}
      <div className="chart-header">
        <div>
          <h2>📉 Evolución del Tratamiento (IA)</h2>
          <p style={{ color: '#888', marginTop: '0.5rem' }}>Índice de Severidad (0 = Meta Ideal)</p>
        </div>
        <div className="trend-badge" style={{ borderColor: trendColor, color: trendColor }}>
          <TrendIcon size={20} />
          <span>{trendText}</span>
        </div>
      </div>

      {/* Alerta de Evolución Estancada */}
      {evolutionCheck?.status === "ALERTA" && (
        <div style={{
          background: 'rgba(244, 67, 54, 0.1)',
          border: '1px solid #f44336',
          borderRadius: '12px',
          padding: '1rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          color: '#ff8a80'
        }}>
          <div style={{ background: 'rgba(244, 67, 54, 0.2)', padding:'0.5rem', borderRadius:'50%' }}>
            <TrendingUp size={24} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontWeight: 'bold' }}>Alerta de Evolución Lenta</h4>
            <p style={{ margin: 0, fontSize: '0.9rem', opacity: 0.9 }}>
              La mejora respecto al mes anterior es inferior al 5% ({evolutionCheck.improvement_percent}). 
              Se recomienda revisar el plan de tratamiento.
            </p>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="stats-grid">
         <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(255,255,255,0.1)' }}>
               <Calendar size={24} />
            </div>
            <div className="stat-content">
               <span className="stat-label">Inicio Tratamiento</span>
               <span className="stat-value" style={{ fontSize: '1.2rem' }}>{chartData[0].date}</span>
            </div>
         </div>
         <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(255,255,255,0.1)' }}>
               <Activity size={24} />
            </div>
            <div className="stat-content">
               <span className="stat-label">Severidad Actual</span>
               <span className="stat-value">{data.trend?.current_severity ?? 'N/A'} <span style={{fontSize:'0.8rem', color:'#888'}}>/ 10</span></span>
            </div>
         </div>
         <div className="stat-card">
            <div className="stat-icon" style={{ background: trendColor }}>
               <TrendIcon size={24} color="#fff" />
            </div>
            <div className="stat-content">
               <span className="stat-label">Proyección (30 días)</span>
               <span className="stat-value" style={{ color: trendColor }}>
                  {data.trend?.predicted_severity_next_month?.toFixed(1) ?? '?'}
               </span>
            </div>
         </div>
      </div>

      {/* Gráfico */}
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" tick={{fontSize: 12}} />
            <YAxis domain={[0, 10]} stroke="#888" label={{ value: 'Severidad', angle: -90, position: 'insideLeft', fill: '#888' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
              itemStyle={{ color: '#fff' }}
            />
            <ReferenceLine y={0} label="META" stroke="#4caf50" strokeDasharray="3 3" />
            <Line 
              type="monotone" 
              dataKey="severity" 
              name="Severidad"
              stroke="#00d4ff" 
              strokeWidth={3}
              activeDot={{ r: 8 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <style>{`
        .progress-chart-container {
          padding: 1.5rem;
          max-width: 1400px;
          margin: 0 auto;
          color: #fff;
        }
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 2rem;
        }
        .trend-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border: 1px solid;
            border-radius: 20px;
            font-weight: bold;
            background: rgba(0,0,0,0.2);
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin-bottom: 2rem;
        }
        .stat-card {
          background: rgba(255, 255, 255, 0.05);
          padding: 1rem;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        .stat-icon {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .stat-content {
            display: flex;
            flex-direction: column;
        }
        .stat-label { font-size: 0.8rem; color: #888; }
        .stat-value { font-size: 1.5rem; font-weight: bold; }
        .chart-wrapper {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 1.5rem;
        }
      `}</style>
    </div>
  );
};

export default ProgressChart;
