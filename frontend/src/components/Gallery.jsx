import { useState, useEffect } from 'react';
import { User, Loader2, RefreshCw, Calendar, Fingerprint, Plus, Search, ArrowLeft } from 'lucide-react';
import * as api from '../services/api';
import PatientEvolution from './PatientEvolution';

const Gallery = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Vista de detalle
  const [selectedPatient, setSelectedPatient] = useState(null);

  const [registerForm, setRegisterForm] = useState({ fullName: '', did: '' });
  const [isRegistering, setIsRegistering] = useState(false);
  const [registerError, setRegisterError] = useState(null);
  const [registerSuccess, setRegisterSuccess] = useState(false);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getGalleryImages();
      setPatients(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error fetching patients:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!registerForm.fullName || !registerForm.did) return;

    setIsRegistering(true);
    setRegisterError(null);
    setRegisterSuccess(false);

    try {
      await api.createPatient({
        full_name: registerForm.fullName,
        did: registerForm.did
      });
      setRegisterSuccess(true);
      setRegisterForm({ fullName: '', did: '' });
      fetchPatients(); // Recargar lista
      setTimeout(() => setRegisterSuccess(false), 3000);
    } catch (err) {
      setRegisterError(err.response?.data?.detail || "Error al registrar paciente");
    } finally {
      setIsRegistering(false);
    }
  };

  const handlePatientClick = (patient) => {
    // Establecer como activo globalmente
    localStorage.setItem("patientDID", patient.filename);
    localStorage.setItem("patientName", patient.full_name);
    // Cambiar vista a detalle
    setSelectedPatient(patient);
  };

  const handleBackToList = () => {
    setSelectedPatient(null);
  };

  if (loading && !patients.length) {
    return (
      <div className="gallery-loading">
        <Loader2 className="spin" size={48} color="#0d9488" />
        <p>Cargando información de pacientes...</p>
      </div>
    );
  }

  // VISTA DE DETALLE (EVOLUCIÓN)
  if (selectedPatient) {
    return (
        <div className="patient-detail-view animate-fade-in">
            <button onClick={handleBackToList} className="back-btn">
                <ArrowLeft size={18} /> Volver al Directorio
            </button>
            
            <div className="detail-header card">
                <div className="patient-avatar-xl">
                    <User size={40} color="#0d9488" />
                </div>
                <div>
                    <h1 style={{margin: 0, fontSize: '1.8rem', color: 'var(--text-main)'}}>{selectedPatient.full_name}</h1>
                    <span className="did-chip-lg">{selectedPatient.filename}</span>
                </div>
            </div>

            <PatientEvolution 
                patientId={selectedPatient.id} 
                patientName={selectedPatient.full_name} 
            />

            <style>{`
                .patient-detail-view { max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem; }
                .back-btn { align-self: flex-start; background: none; border: none; display: flex; align-items: center; gap: 8px; font-weight: 600; color: var(--text-muted); cursor: pointer; padding: 8px 0; transition: color 0.2s; }
                .back-btn:hover { color: var(--primary); }
                
                .detail-header { display: flex; align-items: center; gap: 1.5rem; padding: 2rem !important; border-left: 6px solid var(--primary); }
                .patient-avatar-xl { width: 80px; height: 80px; background: #ccfbf1; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
                .did-chip-lg { background: #f1f5f9; padding: 4px 12px; border-radius: 6px; font-family: monospace; color: var(--text-muted); font-size: 0.9rem; margin-top: 8px; display: inline-block; }
            `}</style>
        </div>
    );
  }

  return (
    <div className="gallery-content-wrapper">
      <div className="gallery-grid-layout">
        {/* SIDEBAR FOR REGISTRATION */}
        <div className="card registration-sidebar">
          <div className="card-header-simple">
            <Plus size={18} color="#0d9488" />
            <h3>Nuevo Registro</h3>
          </div>
          <p className="helper-text">Añade un paciente al directorio para iniciar su seguimiento clínico.</p>
          
          <form onSubmit={handleRegister} className="register-form-vertical">
            <div className="input-group">
              <label>Nombre Completo</label>
              <input 
                type="text" 
                placeholder="Ej: Juan Pérez"
                value={registerForm.fullName}
                onChange={(e) => setRegisterForm({...registerForm, fullName: e.target.value})}
                required
              />
            </div>
            <div className="input-group">
              <label>Identificador (DID)</label>
              <input 
                type="text" 
                placeholder="Ej: JP-2025"
                value={registerForm.did}
                onChange={(e) => setRegisterForm({...registerForm, did: e.target.value})}
                required
              />
            </div>
            <button 
              type="submit" 
              className="primary-btn"
              disabled={isRegistering}
            >
              {isRegistering ? 'Procesando...' : 'Registrar Paciente'}
            </button>
          </form>

          {registerError && <div className="error-note">{registerError}</div>}
          {registerSuccess && <div className="success-note">¡Paciente registrado con éxito!</div>}
        </div>

        {/* MAIN PATIENT LIST */}
        <div className="patient-list-area">
          <div className="filter-bar">
            <div className="search-box">
              <Search size={18} color="#94a3b8" />
              <input type="text" placeholder="Buscar paciente por nombre o ID..." disabled />
            </div>
            <button onClick={fetchPatients} className="icon-btn" title="Refrescar lista">
              <RefreshCw size={18} className={loading ? "spin" : ""} />
            </button>
          </div>

          {patients.length === 0 ? (
            <div className="empty-gallery card">
              <User size={64} color="#e2e8f0" />
              <p>No hay pacientes registrados.</p>
              <span>Usa el panel lateral para añadir el primero.</span>
            </div>
          ) : (
            <div className="patients-grid">
              {patients.map((patient) => {
                const isActive = localStorage.getItem("patientDID") === patient.filename;
                return (
                  <div 
                    key={patient.id} 
                    className={`card patient-card ${isActive ? 'active-item' : ''}`}
                    onClick={() => handlePatientClick(patient)}
                  >
                    <div className="patient-avatar-large">
                      <User size={32} color={isActive ? '#0d9488' : '#94a3b8'} />
                    </div>
                    <div className="patient-card-body">
                      <h4 className="patient-card-name" title={patient.full_name}>{patient.full_name}</h4>
                      <div className="patient-card-meta">
                        <span className="did-chip"><Fingerprint size={12} /> {patient.filename}</span>
                        <div className="date-tag"><Calendar size={12} /> {new Date(patient.created_at).toLocaleDateString()}</div>
                      </div>
                    </div>
                    {isActive && <div className="active-badge">Seleccionado</div>}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
      
      <style>{`
        .gallery-content-wrapper {
          animation: fadeInSlide 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .gallery-grid-layout {
          display: grid;
          grid-template-columns: 340px 1fr;
          gap: 2.5rem;
          align-items: start;
        }

        /* Registration Sidebar */
        .registration-sidebar {
          position: sticky;
          top: 2rem;
          background: rgba(255, 255, 255, 0.8) !important;
          -webkit-backdrop-filter: blur(16px);
          backdrop-filter: blur(16px);
          border: 1px solid var(--border-glass) !important;
        }
        .card-header-simple {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 0.75rem;
        }
        .card-header-simple h3 { 
            margin: 0; 
            font-size: 1.3rem; 
            font-weight: 800;
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        .helper-text { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 2rem; line-height: 1.5; }

        .register-form-vertical {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        .input-group label {
          display: block;
          font-size: 0.8rem;
          font-weight: 700;
          color: var(--text-muted);
          margin-bottom: 0.6rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .input-group input {
          width: 100%;
          padding: 1rem;
          border-radius: 12px;
          border: 1px solid var(--border-soft);
          background: #fff;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          box-sizing: border-box;
          font-size: 1rem;
        }
        .input-group input:focus {
          border-color: var(--primary);
          outline: none;
          box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
          transform: translateY(-1px);
        }

        .error-note { 
            color: #ef4444; 
            font-size: 0.85rem; 
            margin-top: 1rem; 
            background: #fef2f2; 
            padding: 0.75rem; 
            border-radius: 10px;
            border: 1px solid #fee2e2;
        }
        .success-note { 
            color: #10b981; 
            font-size: 0.85rem; 
            margin-top: 1rem; 
            background: #f0fdf4; 
            padding: 0.75rem; 
            border-radius: 10px;
            border: 1px solid #dcfce7;
            font-weight: 600; 
        }

        /* Patient List Area */
        .patient-list-area {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        .filter-bar {
          display: flex;
          gap: 1rem;
          align-items: center;
        }
        .search-box {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 12px;
          background: white;
          padding: 0 1.25rem;
          border-radius: 16px;
          border: 1px solid var(--border-soft);
          height: 52px;
          box-shadow: var(--shadow-sm);
        }
        .search-box input {
          border: none;
          background: transparent;
          width: 100%;
          font-size: 1rem;
          outline: none;
          color: var(--text-main);
        }
        .icon-btn {
          width: 52px;
          height: 52px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border: 1px solid var(--border-soft);
          border-radius: 16px;
          color: var(--text-muted);
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
          box-shadow: var(--shadow-sm);
        }
        .icon-btn:hover { 
            color: var(--primary); 
            border-color: var(--primary-light); 
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        .patients-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 2rem;
        }
        .patient-card {
          padding: 1.5rem !important;
          cursor: pointer;
          position: relative;
          display: flex;
          align-items: center;
          gap: 1.25rem;
          background: white;
          border: 1px solid var(--border-soft);
          border-radius: var(--radius-xl);
        }
        .patient-card:hover {
            transform: translateY(-6px);
            border-color: var(--primary-light);
            box-shadow: var(--shadow-hover);
        }
        .patient-card.active-item {
          border-color: var(--primary);
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.03) 100%);
          box-shadow: 0 15px 30px rgba(99, 102, 241, 0.1);
        }
        .patient-avatar-large {
          width: 64px;
          height: 64px;
          background: #f8fafc;
          border: 1px solid #f1f5f9;
          border-radius: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: all 0.3s;
        }
        .patient-card.active-item .patient-avatar-large { 
            background: white; 
            color: var(--primary);
            box-shadow: 0 8px 16px rgba(99, 102, 241, 0.1);
        }

        .patient-card-body { overflow: hidden; }
        .patient-card-name { 
            margin: 0 0 8px 0; 
            font-size: 1.2rem; 
            font-weight: 700;
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            white-space: nowrap; 
            overflow: hidden; 
            text-overflow: ellipsis; 
        }
        .patient-card-meta { display: flex; flex-direction: column; gap: 6px; }
        .did-chip { 
            font-size: 0.8rem; 
            color: var(--text-muted); 
            display: flex; 
            align-items: center; 
            gap: 6px; 
            font-family: 'JetBrains Mono', monospace; 
            background: #f1f5f9;
            padding: 2px 8px;
            border-radius: 6px;
            width: fit-content;
        }
        .date-tag { font-size: 0.8rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; font-weight: 500; }
        
        .active-badge {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: linear-gradient(135deg, var(--primary) 0%, var(--accent-violet) 100%);
          color: white;
          font-size: 0.7rem;
          font-weight: 800;
          padding: 4px 12px;
          border-radius: 99px;
          text-transform: uppercase;
          box-shadow: 0 4px 10px rgba(99, 102, 241, 0.2);
        }

        .gallery-loading { min-height: 400px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1.5rem; color: var(--text-muted); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        @media (max-width: 1100px) {
          .gallery-grid-layout { grid-template-columns: 1fr; }
          .registration-sidebar { position: static; max-width: 100%; }
        }
      `}</style>
    </div>
  );
};

export default Gallery;
