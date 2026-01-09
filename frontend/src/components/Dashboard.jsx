// frontend/src/components/Dashboard.jsx
import React from 'react';
import { 
  Users, 
  Sparkles, 
  Activity, 
  AlertTriangle, 
  Target,
  ArrowUpRight,
  Plus
} from 'lucide-react';
import './Dashboard.css';

const Dashboard = ({ setActiveTab }) => {
  const stats = {
    totalPatients: 12,
    sessionsThisMonth: 48,
    activeAlerts: 1
  };

  const recentActivity = [
    { id: 1, type: 'Análisis', description: 'Paciente Juan Pérez: Tristeza alta detectada.', status: 'Completado', time: 'Hace 10 min' },
    { id: 2, type: 'Registro', description: 'Nuevo paciente: did:psych:002', status: 'Éxito', time: 'Hace 1 hora' },
    { id: 3, type: 'Seguridad', description: 'Alerta de riesgo detectada en sesión ID: 822', status: 'Revisado', time: 'Hace 3 horas' },
  ];

  return (
    <div className="dashboard-wrapper">
      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-header">
            <div className="stat-icon-wrapper users">
              <Users size={20} />
            </div>
            <span className="stat-change positive"><ArrowUpRight size={14} /> +12%</span>
          </div>
          <div className="stat-value">{stats.totalPatients}</div>
          <div className="stat-label">Total Pacientes</div>
        </div>

        <div className="card stat-card">
          <div className="stat-header">
            <div className="stat-icon-wrapper sessions">
              <Activity size={20} />
            </div>
            <span className="stat-change positive"><ArrowUpRight size={14} /> +5%</span>
          </div>
          <div className="stat-value">{stats.sessionsThisMonth}</div>
          <div className="stat-label">Consultas Mensuales</div>
        </div>

        <div className="card stat-card">
          <div className="stat-header">
            <div className="stat-icon-wrapper alerts">
              <AlertTriangle size={20} />
            </div>
            <span className="stat-label-alert">Crítico</span>
          </div>
          <div className="stat-value warning">{stats.activeAlerts}</div>
          <div className="stat-label">Alertas de Riesgo</div>
        </div>
      </div>

      <div className="dashboard-main-grid">
        <div className="card active-card">
          <div className="card-header-flex">
            <h3><Target size={18} /> Acciones Prioritarias</h3>
            <button className="primary-btn mini-btn" onClick={() => setActiveTab('analyze')}>
              <Plus size={16} /> Nueva Consulta
            </button>
          </div>
          
          <div className="quick-action-list">
            <div className="action-item" onClick={() => setActiveTab('analyze')}>
              <div className="action-icon brain"><Sparkles size={18} /></div>
              <div className="action-info">
                <h4>Iniciar Análisis Cognitivo</h4>
                <p>Procesa notas de sesión con el motor NLP.</p>
              </div>
              <ChevronRight size={18} className="chevron" />
            </div>

            <div className="action-item" onClick={() => setActiveTab('gallery')}>
              <div className="action-icon patients"><Users size={18} /></div>
              <div className="action-info">
                <h4>Gestionar Directorio</h4>
                <p>Ver y editar fichas de pacientes activos.</p>
              </div>
              <ChevronRight size={18} className="chevron" />
            </div>
          </div>
        </div>

        <div className="card activity-card">
          <h3><Activity size={18} /> Actividad Reciente</h3>
          <div className="activity-feed">
            {recentActivity.map((item) => (
              <div key={item.id} className="feed-item">
                <div className={`feed-indicator ${item.type.toLowerCase()}`}></div>
                <div className="feed-content">
                  <div className="feed-header">
                    <span className="feed-type">{item.type}</span>
                    <span className="feed-time">{item.time}</span>
                  </div>
                  <p className="feed-desc">{item.description}</p>
                  <span className={`feed-status ${item.status.toLowerCase()}`}>{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Internal minimal Chevron icon for actions
const ChevronRight = ({ size, className }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <path d="m9 18 6-6-6-6"/>
  </svg>
);

export default Dashboard;
