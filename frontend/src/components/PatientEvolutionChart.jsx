import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { getPatientEvolution } from '../services/api';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';

/**
 * Componente gráfico para visualizar la evolución del tratamiento.
 * @param {string} patientDid - DID del paciente a analizar.
 */
const PatientEvolutionChart = ({ patientDid }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            if (!patientDid) return;
            try {
                setLoading(true);
                const result = await getPatientEvolution(patientDid);
                setData(result.data);
                setError(null);
            } catch (err) {
                console.error("Error fetching evolution:", err);
                setError("No se pudo cargar el historial evolutivo.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [patientDid]);

    if (!patientDid) return <div className="text-gray-500">Seleccione un paciente para ver su evolución.</div>;
    if (loading) return <div className="text-blue-500 animate-pulse">Cargando evolución... ⏳</div>;
    if (error) return <div className="text-red-500 bg-red-50 p-4 rounded-lg border border-red-200">{error}</div>;
    if (!data || !data.timeline || data.timeline.length === 0) return <div className="text-gray-500">No hay historial suficiente para generar gráficas.</div>;

    // Formatear datos para el gráfico
    const chartData = data.timeline.map(item => ({
        date: new Date(item.date).toLocaleDateString(),
        severity: item.severity,
        diagnosis: item.diagnosis.replace('class_', '').replace('_', ' ').toUpperCase(),
        fullDate: item.date
    }));

    // Determinar icono de tendencia
    let TrendIcon = Minus;
    let trendColor = "text-gray-500";
    if (data.trend?.status === "improving") {
        TrendIcon = TrendingDown; // Bajada en severidad es bueno
        trendColor = "text-green-500";
    } else if (data.trend?.status === "worsening") {
        TrendIcon = TrendingUp; // Subida en severidad es malo
        trendColor = "text-red-500";
    }

    // Detectar métrica de IA
    const isNeural = data.trend?.prediction_method === "lstm_neural_network";
    const methodLabel = isNeural ? "Neural AI 🧠" : "Linear Trend 📉";
    const methodColor = isNeural ? "text-purple-600 bg-purple-100 border-purple-200" : "text-gray-500 bg-gray-100";

    return (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-100">
            {/* Header Section */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-gray-800">Evolución del Tratamiento 📈</h2>
                    <p className="text-gray-500 text-sm">Índice de severidad (0 = Meta)</p>
                </div>
                
                <div className="flex gap-2">
                    {/* Trend Status Badge */}
                    {data.trend && (
                        <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${trendColor} bg-opacity-10 font-medium`}>
                            <TrendIcon size={20} />
                            <span>{data.trend.status.toUpperCase()}</span>
                        </div>
                    )}
                    
                    {/* AI Method Badge */}
                    {data.trend && (
                        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold border ${methodColor}`}>
                            <span>{methodLabel}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Anomaly Warning Banner */}
            {data.trend?.anomaly_detected && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-3 text-amber-800">
                    <span className="text-2xl">⚠️</span>
                    <div>
                        <span className="font-bold">Anomalía Detectada:</span> Patrón de recuperación inusual. Se recomienda revisión clínica manual.
                    </div>
                </div>
            )}

            <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                        <XAxis 
                            dataKey="date" 
                            stroke="#888888" 
                            tick={{fontSize: 12}}
                        />
                        <YAxis 
                            domain={[0, 10]} 
                            label={{ value: 'Severidad', angle: -90, position: 'insideLeft' }} 
                            stroke="#888888"
                        />
                        <Tooltip 
                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                        />
                        <Legend />
                        <ReferenceLine y={0} label="Meta (Normal)" stroke="green" strokeDasharray="3 3" />
                        <Line 
                            type="monotone" 
                            dataKey="severity" 
                            name="Índice de Severidad"
                            stroke={isNeural ? "#8b5cf6" : "#3b82f6"} // Turn purple if AI
                            strokeWidth={3}
                            activeDot={{ r: 8 }}
                            dot={{ r: 4 }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                 <div className="p-4 bg-blue-50 rounded-lg">
                    <span className="block text-sm text-gray-500">Diagnóstico Actual</span>
                    <span className="font-bold text-lg text-blue-700">{chartData[chartData.length-1].diagnosis}</span>
                 </div>
                 <div className="p-4 bg-purple-50 rounded-lg">
                    <span className="block text-sm text-gray-500">Severidad Actual</span>
                    <span className="font-bold text-lg text-purple-700">{data.trend?.current_severity ?? 'N/A'} / 10</span>
                 </div>
                 <div className="p-4 bg-green-50 rounded-lg relative overflow-hidden">
                    <span className="block text-sm text-gray-500">Proyección 30 días</span>
                    <span className="font-bold text-lg text-green-700">~{data.trend?.predicted_severity_next_month?.toFixed(1) ?? '?'}</span>
                    {isNeural && (
                        <div className="absolute top-0 right-0 p-1 bg-purple-500 text-white text-[10px] rounded-bl-lg font-bold">AI</div>
                    )}
                 </div>
            </div>
        </div>
    );
};

export default PatientEvolutionChart;
