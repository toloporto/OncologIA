import { useState, useEffect } from "react";
import {
  Brain,
  LayoutDashboard,
  Users,
  ClipboardCheck,
  ShieldCheck,
  LogOut,
  User,
  Cpu,
  Server,
  HeartPulse,
  ChevronRight
} from "lucide-react";

import * as api from "./services/api";
import Dashboard from "./components/Dashboard";
import SessionAnalysis from "./components/SessionAnalysis";
import Gallery from "./components/Gallery";
import History from "./components/History";
import Login from "./components/Login";
import Register from "./components/Register";
import WalletConnect from "./components/WalletConnect";
import ConsentManager from "./components/ConsentManager";
import { useAuth } from "./contexts/AuthContext";
import ClinicalAssistant from "./components/ClinicalAssistant";
import "./App.css";

function App() {
  const { user, loading: authLoading, isAuthenticated, logout } = useAuth();
  const [showRegister, setShowRegister] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [systemStatus, setSystemStatus] = useState(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const status = await api.checkSystemStatus();
        setSystemStatus(status);
      } catch (err) {
        setSystemStatus({ model_loaded: false, status: "Desconectado" });
      }
    };
    fetchInitialData();
  }, []);

  if (authLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <h2>Cargando PsychoWebAI...</h2>
      </div>
    );
  }

  if (!isAuthenticated) {
    return showRegister ? (
      <Register onSwitchToLogin={() => setShowRegister(false)} />
    ) : (
      <Login onSwitchToRegister={() => setShowRegister(true)} />
    );
  }

  const getPageTitle = () => {
    switch(activeTab) {
      case "dashboard": return "Panel de Control";
      case "analyze": return "Análisis de Sesión";
      case "gallery": return "Directorio de Pacientes";
      case "history": return "Historial Clínico";
      case "privacy": return "Gestión de Privacidad";
      default: return "OncologIA";
    }
  };

  const getPageSubtitle = () => {
    switch(activeTab) {
      case "dashboard": return "Resumen general de actividad y métricas.";
      case "analyze": return "Asistente clínico inteligente para oncología.";
      case "gallery": return "Gestiona perfiles y registros de tus pacientes.";
      case "history": return "Cronología completa de consultas pasadas.";
      default: return "Plataforma de asistente clínico.";
    }
  };

  return (
    <div className="app-layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Brain size={32} color="#0ea5e9" strokeWidth={2.5} />
          <h1>OncologIA</h1>
        </div>

        <nav className="nav-links">
          <button 
            className={`nav-item ${activeTab === "dashboard" && "active"}`} 
            onClick={() => setActiveTab("dashboard")}
          >
            <LayoutDashboard size={20} />
            <span>Inicio</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === "analyze" && "active"}`} 
            onClick={() => setActiveTab("analyze")}
          >
            <HeartPulse size={20} />
            <span>Nueva Sesión</span>
          </button>

          <button 
            className={`nav-item ${activeTab === "gallery" && "active"}`} 
            onClick={() => setActiveTab("gallery")}
          >
            <Users size={20} />
            <span>Pacientes</span>
          </button>

          <button 
            className={`nav-item ${activeTab === "history" && "active"}`} 
            onClick={() => setActiveTab("history")}
          >
            <ClipboardCheck size={20} />
            <span>Historial</span>
          </button>

          <button 
            className={`nav-item ${activeTab === "privacy" && "active"}`} 
            onClick={() => setActiveTab("privacy")}
          >
            <ShieldCheck size={20} />
            <span>Privacidad</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">
              <User size={18} />
            </div>
            <div className="user-name">{user?.full_name || user?.email}</div>
          </div>
          <button onClick={logout} className="logout-btn">
            <LogOut size={16} />
            Cerrar Sesión
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="main-content">
        <header className="top-bar">
          <div>
            <h1 className="page-title">{getPageTitle()}</h1>
            <p className="page-subtitle">{getPageSubtitle()}</p>
          </div>

          <div className="status-chips">
            <div className="status-chip">
              <Cpu size={14} color="#64748b" />
              <span>Modelo:</span>
              <div className={`status-indicator ${systemStatus?.model_loaded ? "on" : "off"}`}></div>
              <span style={{color: systemStatus?.model_loaded ? "#14b8a6" : "#ef4444"}}>
                {systemStatus?.model_loaded ? "Expert O-1" : "Off"}
              </span>
            </div>
            <div className="status-chip">
              <Server size={14} color="#64748b" />
              <span>API:</span>
              <span style={{color: systemStatus?.status === "online" ? "#14b8a6" : "#ef4444"}}>
                {systemStatus?.status || "Check"}
              </span>
            </div>
          </div>
        </header>

        <section className="content-area">
          {activeTab === "dashboard" && <Dashboard setActiveTab={setActiveTab} />}
          {activeTab === "analyze" && <SessionAnalysis />}
          {activeTab === "gallery" && <Gallery />}
          {activeTab === "history" && <History />}
          {activeTab === "privacy" && <ConsentManager />}
        </section>

      </main>
      
      {/* FLOATING CLINICAL ASSISTANT */}
      <ClinicalAssistant />
    </div>
  );
}

export default App;
