import React, { useState, useEffect } from 'react';
import { Eye, CheckCircle, XCircle, AlertTriangle, ChevronRight, MessageSquare } from 'lucide-react';

const ReviewQueue = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedReview, setSelectedReview] = useState(null);
  const [correction, setCorrection] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [explanationMap, setExplanationMap] = useState(null);
  const [explaining, setExplaining] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/reviews/pending`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) throw new Error('No se pudo cargar la cola de revisión');
      const data = await response.json();
      setReviews(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!correction) return;

    try {
      setSubmitting(true);
      const response = await fetch(`${API_URL}/reviews/${selectedReview.id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          correct_label: correction,
          notes: notes
        })
      });

      if (!response.ok) throw new Error('Error al enviar la revisión');
      
      // Limpiar y recargar
      setReviews(reviews.filter(r => r.id !== selectedReview.id));
      setSelectedReview(null);
      setCorrection('');
      setNotes('');
      alert('Feedback enviado con éxito. El modelo aprenderá de esta corrección.');
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const fetchExplanation = async () => {
    if (!selectedReview) return;
    try {
      setExplaining(true);
      const response = await fetch(`${API_URL}/reviews/${selectedReview.id}/explain`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) throw new Error('Error al obtener la explicación');
      const data = await response.json();
      setExplanationMap(data.explanation_image);
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setExplaining(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando cola de revisión...</div>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* ... (anterior) */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
            <AlertTriangle className="text-amber-500" />
            Cola de Revisión (Active Learning)
          </h1>
          <p className="text-slate-500 mt-2">
            Casos con baja confianza que requieren validación experta para mejorar la IA.
          </p>
        </div>
        <div className="bg-slate-100 px-4 py-2 rounded-full text-slate-600 font-medium">
          {reviews.length} Casos pendientes
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Lista de Casos */}
        <div className="lg:col-span-1 space-y-4">
          {reviews.length === 0 ? (
            <div className="p-8 bg-green-50 rounded-2xl text-green-700 text-center border border-green-100">
              <CheckCircle className="mx-auto mb-2" size={32} />
              <p className="font-medium">¡Todo al día!</p>
              <p className="text-sm">No hay casos pendientes de revisión.</p>
            </div>
          ) : (
            reviews.map((review) => (
              <div
                key={review.id}
                onClick={() => {
                  setSelectedReview(review);
                  setExplanationMap(null); // Limpiar explicación al cambiar de caso
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  selectedReview?.id === review.id
                    ? 'border-indigo-500 bg-indigo-50 shadow-md ring-2 ring-indigo-200'
                    : 'border-slate-200 bg-white hover:border-indigo-300 hover:shadow-sm'
                }`}
              >
                <div className="flex gap-4">
                  <img
                    src={`${API_URL}${review.image_url}`}
                    alt="Dental"
                    className="w-16 h-16 rounded-lg object-cover bg-slate-100"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">
                      ID: {review.analysis_id.split('-')[0]}...
                    </p>
                    <p className="text-xs text-slate-500">
                      Predicho: <span className="text-indigo-600">{review.predicted_class}</span>
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-500"
                          style={{ width: `${review.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-[10px] font-bold text-amber-600">
                        {Math.round(review.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                  <ChevronRight size={18} className="text-slate-400 self-center" />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Detalle y Formulario */}
        <div className="lg:col-span-2">
          {selectedReview ? (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                <h2 className="text-xl font-bold text-slate-800">Detalle del Análisis</h2>
                <div className="flex gap-2">
                  <button
                    onClick={fetchExplanation}
                    disabled={explaining}
                    className={`px-4 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${
                      explanationMap 
                        ? 'bg-amber-100 text-amber-700 border border-amber-200'
                        : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
                    }`}
                  >
                    <Sparkles size={16} />
                    {explaining ? 'Generando...' : explanationMap ? 'Explicación Cargada' : 'Ver Explicación IA'}
                  </button>
                </div>
              </div>

              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="relative">
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-3">
                    {explanationMap ? 'Visualización Grad-CAM' : 'Imagen Original'}
                  </label>
                  <div className="relative rounded-xl overflow-hidden shadow-inner border border-slate-100">
                    <img
                      src={explanationMap || `${API_URL}${selectedReview.image_url}`}
                      alt="Dental Visual"
                      className="w-full h-auto transition-opacity duration-500"
                    />
                    {explanationMap && (
                      <div className="absolute bottom-3 left-3 right-3 bg-black/60 backdrop-blur-sm text-white text-[10px] p-2 rounded-lg">
                        Las zonas <b>rojas/amarillas</b> indican dónde se enfocó el modelo para clasificar como <i>{selectedReview.predicted_class}</i>.
                      </div>
                    )}
                  </div>
                  {explanationMap && (
                    <button 
                      onClick={() => setExplanationMap(null)}
                      className="mt-2 text-xs text-slate-400 hover:text-indigo-600 underline"
                    >
                      Restaurar imagen original
                    </button>
                  )}
                </div>

                <div>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase mb-3">
                        Diagnóstico Experto (Corrección)
                      </label>
                      <select
                        required
                        value={correction}
                        onChange={(e) => setCorrection(e.target.value)}
                        className="w-full p-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                      >
                        <option value="">Seleccione la clase correcta...</option>
                        <option value="class_i_normal">Clase I (Normal)</option>
                        <option value="class_ii_division1">Clase II Div 1</option>
                        <option value="class_ii_division2">Clase II Div 2</option>
                        <option value="class_iii">Clase III</option>
                        <option value="cross_bite">Mala oclusión (Cruzada)</option>
                        <option value="open_bite">Mala oclusión (Abierta)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-400 uppercase mb-3">
                        Notas Médicas / Justificación
                      </label>
                      <textarea
                        rows="4"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Explique por qué es corrección o qué observó..."
                        className="w-full p-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
                      ></textarea>
                    </div>

                    <div className="bg-amber-50 border border-amber-100 p-4 rounded-xl flex gap-3 text-amber-800 text-sm">
                      <MessageSquare className="shrink-0" size={18} />
                      <p>
                        Tu corrección se guardará en el dataset de entrenamiento para mejorar
                        la precisión del modelo en futuras actualizaciones.
                      </p>
                    </div>

                    <button
                      type="submit"
                      disabled={submitting || !correction}
                      className={`w-full py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2 ${
                        submitting || !correction
                          ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                          : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-100'
                      }`}
                    >
                      {submitting ? 'Enviando...' : 'Confirmar Revisión Experta'}
                    </button>
                  </form>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[400px] border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center text-slate-400 p-8 text-center">
              <Eye size={48} className="mb-4 opacity-20" />
              <p className="text-lg font-medium">Seleccione un caso de la lista</p>
              <p className="text-sm max-w-xs">
                Haga clic en uno de los análisis pendientes de la izquierda para ver los detalles y proporcionar su feedback experto.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReviewQueue;
