// frontend/src/services/ipfsService.js

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const ipfsService = {
  /**
   * Verificar estado de IPFS
   * @returns {Promise<{connected: boolean, node_id: string}>}
   */
  async getStatus() {
    try {
      const response = await fetch(`${API_URL}/ipfs/status`);
      return await response.json();
    } catch (error) {
      console.error("Error verificando estado IPFS:", error);
      return { connected: false };
    }
  },

  /**
   * Subir archivo a IPFS
   * @param {File} file - Archivo a subir
   * @returns {Promise<{success: boolean, hash: string, url_public: string}>}
   */
  async uploadFile(file) {
    const token = localStorage.getItem("token");
    if (!token) throw new Error("No autenticado");

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/ipfs/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Error subiendo a IPFS");
    }

    return await response.json();
  },

  /**
   * Obtener URL pública de IPFS
   * @param {string} hash - Hash IPFS
   * @returns {string}
   */
  getPublicUrl(hash) {
    return `https://ipfs.io/ipfs/${hash}`;
  }
};

export default ipfsService;
