// frontend/src/components/Consult.jsx
import React, { useState, useEffect } from "react";
import { ethers } from "ethers";
import { useWallet } from "../hooks/useWallet";
import { ORTHO_CONSULT_ADDRESS, ORTHO_CONSULT_ABI } from "../config/contractConfig";
import { Shield, UserCheck, UserX, AlertCircle, FileSignature, Coins } from "lucide-react";
import "./Consult.css";

const Consult = () => {
  const { account, provider } = useWallet();
  const [role, setRole] = useState(null); // "patient" | "orthodontist" | null
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form fields for patient (create case)
  const [caseDescHash, setCaseDescHash] = useState("");
  const [caseReward, setCaseReward] = useState("0.01"); // ETH
  const [requiredOpinions, setRequiredOpinions] = useState(1);
  const [createdCaseId, setCreatedCaseId] = useState(null);

  // Form fields for orthodontist (submit opinion)
  const [opinionCaseId, setOpinionCaseId] = useState("");
  const [opinionHash, setOpinionHash] = useState("");
  const [opinionTx, setOpinionTx] = useState(null);

  // Claim reward
  const [claimCaseId, setClaimCaseId] = useState("");
  const [claimTx, setClaimTx] = useState(null);

  // Detect role (simple heuristic: if address is registered orthodontist in contract)
  const checkRole = async () => {
    if (!provider) return;
    try {
      const contract = new ethers.Contract(ORTHO_CONSULT_ADDRESS, ORTHO_CONSULT_ABI, provider);
      const isRegistered = await contract.isRegisteredOrthodontist(account);
      setRole(isRegistered ? "orthodontist" : "patient");
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (account && provider) checkRole();
  }, [account, provider]);

  const handleCreateCase = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_CONSULT_ADDRESS, ORTHO_CONSULT_ABI, signer);
      const tx = await contract.createCase(
        caseDescHash,
        ethers.utils.parseEther(caseReward),
        requiredOpinions,
        { value: ethers.utils.parseEther(caseReward) } // send reward as ETH for demo
      );
      const receipt = await tx.wait();
      // Event CaseCreated emits caseId as first argument
      const event = receipt.events?.find((e) => e.event === "CaseCreated");
      const caseId = event?.args?.caseId?.toString();
      setCreatedCaseId(caseId);
    } catch (err) {
      console.error(err);
      setError(err.reason || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitOpinion = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_CONSULT_ADDRESS, ORTHO_CONSULT_ABI, signer);
      const tx = await contract.submitOpinion(opinionCaseId, opinionHash);
      await tx.wait();
      setOpinionTx(tx.hash);
    } catch (err) {
      console.error(err);
      setError(err.reason || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClaimReward = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_CONSULT_ADDRESS, ORTHO_CONSULT_ABI, signer);
      const tx = await contract.claimReward(claimCaseId);
      await tx.wait();
      setClaimTx(tx.hash);
    } catch (err) {
      console.error(err);
      setError(err.reason || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterOrthodontist = async () => {
    setLoading(true);
    setError("");
    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_CONSULT_ADDRESS, ORTHO_CONSULT_ABI, signer);
      const tx = await contract.registerOrthodontist(account);
      await tx.wait();
      alert("✅ Registrado como ortodoncista!");
      checkRole(); // Refresh role
    } catch (err) {
      console.error(err);
      setError(err.reason || err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!account) {
    return (
      <div className="consult-warning">
        <AlertCircle /> Conecta tu wallet para usar consultas
      </div>
    );
  }

  return (
    <div className="consult-container">
      <h3><Shield className="icon" /> Consultas de Segunda Opinión</h3>
      
      {/* Role Badge */}
      {role && (
        <div className={`role-badge ${role}`}>
          {role === "orthodontist" ? <UserCheck size={14} /> : <UserX size={14} />}
          {role === "orthodontist" ? "Ortodoncista Verificado" : "Paciente / Dentista General"}
        </div>
      )}

      {error && <div className="error-message"><AlertCircle size={16} /> {error}</div>}

      {/* Grid Layout */}
      <div className="consult-grid">
        {/* Paciente: registro y crear caso */}
        {role === "patient" && (
          <>
            <div className="section">
              <h4>¿Eres Ortodoncista?</h4>
              <p>Regístrate para poder dar opiniones y ganar recompensas</p>
              <button 
                onClick={handleRegisterOrthodontist} 
                className={`action-btn ${loading ? 'loading' : ''}`} 
                disabled={loading}
              >
                <UserCheck size={16} />
                {loading ? "Registrando..." : "Registrarse como Ortodoncista"}
              </button>
            </div>

            <div className="section">
              <h4>Crear Caso (Solicitar Opinión)</h4>
              <form onSubmit={handleCreateCase} className="form">
                <div className="form-group">
                  <label>Hash del caso (IPFS CID)</label>
                  <input type="text" value={caseDescHash} onChange={(e) => setCaseDescHash(e.target.value)} required placeholder="Qm..." />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Recompensa (ETH)</label>
                    <input type="number" step="0.01" value={caseReward} onChange={(e) => setCaseReward(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Opiniones requeridas</label>
                    <input type="number" min="1" value={requiredOpinions} onChange={(e) => setRequiredOpinions(e.target.value)} required />
                  </div>
                </div>
                <button type="submit" className={`action-btn ${loading ? 'loading' : ''}`} disabled={loading}>
                  <FileSignature size={16} />
                  {loading ? "Creando..." : "Crear Caso"}
                </button>
              </form>
              {createdCaseId && (
                <div className="success-box">
                  Caso creado con ID: <strong>{createdCaseId}</strong>
                </div>
              )}
            </div>
          </>
        )}

        {/* Ortodoncista: enviar opinión y reclamar */}
        {role === "orthodontist" && (
          <>
            <div className="section">
              <h4>Enviar Opinión</h4>
              <form onSubmit={handleSubmitOpinion} className="form">
                <div className="form-group">
                  <label>ID del Caso</label>
                  <input type="number" value={opinionCaseId} onChange={(e) => setOpinionCaseId(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Hash de la opinión (IPFS CID)</label>
                  <input type="text" value={opinionHash} onChange={(e) => setOpinionHash(e.target.value)} required placeholder="Qm..." />
                </div>
                <button type="submit" className={`action-btn ${loading ? 'loading' : ''}`} disabled={loading}>
                  <UserCheck size={16} />
                  {loading ? "Enviando..." : "Enviar Opinión"}
                </button>
              </form>
              {opinionTx && (
                <div className="success-box">
                  Opinión enviada. Tx: <a href={`https://sepolia.etherscan.io/tx/${opinionTx}`} target="_blank" rel="noopener noreferrer">{opinionTx.slice(0, 12)}...</a>
                </div>
              )}
            </div>

            <div className="section">
              <h4>Reclamar Recompensa</h4>
              <form onSubmit={handleClaimReward} className="form">
                <div className="form-group">
                  <label>ID del Caso</label>
                  <input type="number" value={claimCaseId} onChange={(e) => setClaimCaseId(e.target.value)} required />
                </div>
                <button type="submit" className={`action-btn ${loading ? 'loading' : ''}`} disabled={loading}>
                  <Coins size={16} />
                  {loading ? "Reclamando..." : "Reclamar"}
                </button>
              </form>
              {claimTx && (
                <div className="success-box">
                  Recompensa reclamada. Tx: <a href={`https://sepolia.etherscan.io/tx/${claimTx}`} target="_blank" rel="noopener noreferrer">{claimTx.slice(0, 12)}...</a>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Consult;
