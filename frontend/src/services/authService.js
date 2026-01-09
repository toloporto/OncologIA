// frontend/src/services/authService.js

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Servicio de autenticación para comunicarse con el backend
 */

export const authService = {
  /**
   * Login de usuario
   * @param {string} email - Email del usuario
   * @param {string} password - Contraseña del usuario
   * @returns {Promise<{access_token: string, token_type: string}>}
   */
  async login(email, password) {
    const formData = new FormData();
    formData.append("username", email); // OAuth2 usa 'username' para el email
    formData.append("password", password);

    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Error en el login");
    }

    const data = await response.json();
    
    // Guardar token en localStorage
    localStorage.setItem("token", data.access_token);
    
    return data;
  },

  /**
   * Registro de nuevo usuario
   * @param {string} email - Email del usuario
   * @param {string} password - Contraseña del usuario
   * @param {string} fullName - Nombre completo del usuario
   * @returns {Promise<Object>}
   */
  async register(email, password, fullName) {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Error en el registro");
    }

    return await response.json();
  },

  /**
   * Obtener información del usuario actual
   * @returns {Promise<Object>}
   */
  async getCurrentUser() {
    const token = localStorage.getItem("token");
    
    if (!token) {
      throw new Error("No hay token");
    }

    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      // Si el token es inválido, eliminarlo
      if (response.status === 401) {
        localStorage.removeItem("token");
      }
      throw new Error("Error al obtener usuario");
    }

    return await response.json();
  },

  /**
   * Verificar si el token es válido
   * @returns {Promise<boolean>}
   */
  async verifyToken() {
    const token = localStorage.getItem("token");
    
    if (!token) {
      return false;
    }

    try {
      const response = await fetch(`${API_URL}/auth/verify`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      return response.ok;
    } catch (error) {
      return false;
    }
  },

  /**
   * Logout del usuario
   */
  logout() {
    localStorage.removeItem("token");
  },

  /**
   * Obtener el token actual
   * @returns {string|null}
   */
  getToken() {
    return localStorage.getItem("token");
  },

  /**
   * Verificar si el usuario está autenticado
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!localStorage.getItem("token");
  },
};

export default authService;
