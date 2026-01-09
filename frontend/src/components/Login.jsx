// frontend/src/components/Login.jsx

import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { LogIn, Mail, Lock, AlertCircle, UserPlus } from "lucide-react";
import "./Login.css";

function Login({ onSwitchToRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Validaciones básicas
    if (!email || !password) {
      setError("Por favor completa todos los campos");
      setLoading(false);
      return;
    }

    if (!email.includes("@")) {
      setError("Por favor ingresa un email válido");
      setLoading(false);
      return;
    }

    try {
      const result = await login(email, password);
      
      if (!result.success) {
        setError(result.error || "Error al iniciar sesión");
      }
      // Si es exitoso, el AuthContext manejará la redirección
    } catch (err) {
      setError("Error de conexión. Verifica que el servidor esté corriendo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <LogIn size={48} className="auth-icon" />
          <h2>Iniciar Sesión</h2>
          <p>Acceda a su cuenta profesional OncologIA</p>
        </div>

        {error && (
          <div className="error-alert">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">
              <Mail size={18} />
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="doctor@oncologia.com"
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              <Lock size={18} />
              Contraseña
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="auth-button primary"
            disabled={loading}
          >
            {loading ? "Iniciando sesión..." : "Iniciar Sesión"}
          </button>
        </form>

        <div className="auth-footer">
          <p>¿No tienes una cuenta?</p>
          <button
            className="auth-button secondary"
            onClick={onSwitchToRegister}
            disabled={loading}
          >
            <UserPlus size={18} />
            Crear cuenta
          </button>
        </div>

        <div className="demo-credentials">
          <p><strong>🔑 Credenciales de Acceso:</strong></p>
          <p>Email: <strong>test@psych.com</strong></p>
          <p>Contraseña: <strong>Psycho2024!</strong></p>
        </div>
      </div>
    </div>
  );
}

export default Login;
