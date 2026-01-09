// frontend/src/components/IPFSUploader.jsx

import { useState, useEffect } from "react";
import { UploadCloud, CheckCircle2, AlertCircle, FileText, ExternalLink, Hexagon } from "lucide-react";
import ipfsService from "../services/ipfsService";
import { useWallet } from "../hooks/useWallet";
import { ethers } from "ethers";
import { ORTHO_DATA_ADDRESS, ORTHO_DATA_ABI } from "../config/contractConfig";
import "./IPFSUploader.css";

function IPFSUploader({ onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [uploading, setUploading] = useState(false);
  const [ipfsResult, setIpfsResult] = useState(null);
  const [error, setError] = useState("");
  const [ipfsStatus, setIpfsStatus] = useState({ connected: false });
  
  // Estados para NFT
  const { account, provider } = useWallet();
  const [minting, setMinting] = useState(false);
  const [nftResult, setNftResult] = useState(null);

  // Verificar estado de IPFS al cargar
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    const status = await ipfsService.getStatus();
    setIpfsStatus(status);
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    if (!selectedFile.type.startsWith("image/")) {
      setError("Solo se permiten imágenes");
      return;
    }

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setError("");
    setIpfsResult(null);
    setNftResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError("");

    try {
      const result = await ipfsService.uploadFile(file);
      setIpfsResult(result);
      if (onUploadComplete) {
        onUploadComplete(result);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleMintNFT = async () => {
    if (!ipfsResult || !account || !provider) return;

    setMinting(true);
    setError("");

    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_DATA_ADDRESS, ORTHO_DATA_ABI, signer);

      // Datos simulados del diagnóstico (en una app real vendrían del análisis de IA)
      const diagnosis = "Análisis Pendiente";
      const severity = 500; // Escala 0-1000
      const recommendations = "Consultar especialista";

      const tx = await contract.mintDiagnosis(
        account,
        diagnosis,
        severity,
        ipfsResult.hash,
        recommendations
      );

      await tx.wait(); // Esperar confirmación

      setNftResult({
        success: true,
        hash: tx.hash
      });

    } catch (err) {
      console.error(err);
      setError("Error al crear NFT: " + (err.reason || err.message));
    } finally {
      setMinting(false);
    }
  };

  return (
    <div className="ipfs-uploader">
      <div className="ipfs-header">
        <h3>Almacenamiento Descentralizado (IPFS + NFT)</h3>
        <div className={`status-badge ${ipfsStatus.connected ? "connected" : "disconnected"}`}>
          {ipfsStatus.connected ? "🟢 Nodo Conectado" : "🔴 Nodo Desconectado"}
        </div>
      </div>

      {!file ? (
        <div 
          className="upload-zone"
          onClick={() => document.getElementById("ipfsInput").click()}
        >
          <input
            type="file"
            id="ipfsInput"
            accept="image/*"
            style={{ display: "none" }}
            onChange={handleFileSelect}
          />
          <UploadCloud size={48} className="upload-icon" />
          <p>Click para seleccionar imagen</p>
          <span>Se subirá a la red IPFS global</span>
        </div>
      ) : (
        <div className="preview-zone">
          <img src={previewUrl} alt="Preview" className="preview-image" />
          
          {!ipfsResult && (
            <div className="actions">
              <button 
                className="upload-btn" 
                onClick={handleUpload}
                disabled={uploading || !ipfsStatus.connected}
              >
                {uploading ? "Subiendo a IPFS..." : "Subir a IPFS"}
              </button>
              <button 
                className="cancel-btn"
                onClick={() => {
                  setFile(null);
                  setPreviewUrl("");
                }}
                disabled={uploading}
              >
                Cancelar
              </button>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="error-message">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {ipfsResult && (
        <div className="success-result">
          <div className="result-header">
            <CheckCircle2 size={24} color="#16a34a" />
            <h4>¡Archivo Inmutable Creado!</h4>
          </div>
          
          <div className="hash-box">
            <span className="label">IPFS Hash (CID):</span>
            <code className="hash">{ipfsResult.hash}</code>
          </div>

          <div className="links">
            <a 
              href={ipfsResult.url_public} 
              target="_blank" 
              rel="noopener noreferrer"
              className="ipfs-link"
            >
              <ExternalLink size={16} />
              Ver en Gateway Público
            </a>
          </div>

          {/* Sección de NFT */}
          <div className="nft-section">
            {!nftResult ? (
              <div className="mint-action">
                <p>¿Quieres registrar la propiedad de este diagnóstico en la Blockchain?</p>
                {!account ? (
                  <div className="connect-warning">
                    <AlertCircle size={16} />
                    Conecta tu Wallet arriba para crear el NFT
                  </div>
                ) : (
                  <button 
                    className="mint-btn"
                    onClick={handleMintNFT}
                    disabled={minting}
                  >
                    <Hexagon size={18} />
                    {minting ? "Creando NFT..." : "Convertir en NFT (Mint)"}
                  </button>
                )}
              </div>
            ) : (
              <div className="nft-success">
                <div className="result-header">
                  <Hexagon size={24} color="#8b5cf6" />
                  <h4>¡NFT Creado Exitosamente!</h4>
                </div>
                <p>Tu diagnóstico ahora es un activo digital único en tu wallet.</p>
                <div className="hash-box">
                  <span className="label">Transaction Hash:</span>
                  <code className="hash">{nftResult.hash}</code>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default IPFSUploader;
