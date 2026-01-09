// frontend/src/components/Register.jsx

import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { UserPlus, Mail, Lock, User, AlertCircle, LogIn } from "lucide-react";
import "./Login.css"; // Reutilizamos los mismos estilos

function Register({ onSwitchToLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Validaciones
    if (!email || !password || !confirmPassword || !fullName) {
      setError("Por favor completa todos los campos");
      setLoading(false);
      return;
    }

    if (!email.includes("@")) {
      setError("Por favor ingresa un email válido");
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      setLoading(false);
      return;
    }

    try {
      const result = await register(email, password, fullName);
      
      if (!result.success) {
        setError(result.error || "Error al registrar usuario");
      }
      // Si es exitoso, el AuthContext manejará el login automático
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
          <UserPlus size={48} className="auth-icon" />
          <h2>Crear Cuenta</h2>
          <p>Regístrese en el ecosistema PsychoWebAI</p>
        </div>

        {error && (
          <div className="error-alert">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="fullName">
              <User size={18} />
              Nombre Completo
            </label>
            <input
              type="text"
              id="fullName"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Juan Pérez"
              disabled={loading}
              autoComplete="name"
            />
          </div>

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
              placeholder="tu@email.com"
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
              placeholder="Mínimo 6 caracteres"
              disabled={loading}
              autoComplete="new-password"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">
              <Lock size={18} />
              Confirmar Contraseña
            </label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repite tu contraseña"
              disabled={loading}
              autoComplete="new-password"
            />
          </div>

          <button
            type="submit"
            className="auth-button primary"
            disabled={loading}
          >
            {loading ? "Creando cuenta..." : "Crear Cuenta"}
          </button>
        </form>

        <div className="auth-footer">
          <p>¿Ya tienes una cuenta?</p>
          <button
            className="auth-button secondary"
            onClick={onSwitchToLogin}
            disabled={loading}
          >
            <LogIn size={18} />
            Iniciar Sesión
          </button>
        </div>
      </div>
    </div>
  );
}

export default Register;
