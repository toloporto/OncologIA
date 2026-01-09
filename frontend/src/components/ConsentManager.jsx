import { useState, useEffect } from 'react';
import { 
  Shield, 
  UserCheck, 
  UserX, 
  Clock, 
  FileSignature, 
  AlertCircle,
  Hash,
  Activity,
  Calendar,
  Wallet,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { ethers } from 'ethers';
import { useWallet } from '../hooks/useWallet';
import { ORTHO_CONSENT_ADDRESS, ORTHO_CONSENT_ABI } from '../config/contractConfig';
import './ConsentManager.css';

const PURPOSES = {
  0: "Diagnóstico",
  1: "Segunda Opinión",
  2: "Investigación",
  3: "Entrenamiento IA",
  4: "Comercial"
};

const ConsentManager = () => {
  const { account, provider } = useWallet();
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [granting, setGranting] = useState(false);
  
  const [recipient, setRecipient] = useState("");
  const [tokenId, setTokenId] = useState("1");
  const [purpose, setPurpose] = useState("1");
  const [duration, setDuration] = useState("2592000");

  useEffect(() => {
    // MODO SIMULACIÓN
    setLoading(true);
    const fakeConsents = [
      {
        id: 1,
        tokenId: "101",
        patient: "0x...",
        recipient: "0x1234567890123456789012345678901234567890",
        purpose: 0,
        expirationTime: Math.floor(Date.now() / 1000) + 86400,
        isValid: true,
      },
      {
        id: 2,
        tokenId: "102",
        patient: "0x...",
        recipient: "0x0987654321098765432109876543210987654321",
        purpose: 2,
        expirationTime: Math.floor(Date.now() / 1000) - 86400,
        isValid: false,
      },
    ];
    setConsents(fakeConsents);
    setLoading(false);
  }, []);

  const handleGrant = async (e) => {
    e.preventDefault();
    if (!ethers.utils.isAddress(recipient)) {
      alert("Dirección de Bio-Bóveda o Médico inválida.");
      return;
    }

    setGranting(true);
    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_CONSENT_ADDRESS, ORTHO_CONSENT_ABI, signer);
      
      const tx = await contract.grantConsent(
        tokenId,
        recipient,
        purpose,
        duration,
        "QmHashDeTerminosLegales"
      );
      
      await tx.wait();
      setRecipient("");
    } catch (error) {
      console.error("Error otorgando consentimiento:", error);
      alert("Error en Blockchain: " + (error.reason || error.message));
    } finally {
      setGranting(false);
    }
  };

  const handleRevoke = async (consentId) => {
    if (!confirm("¿Desea revocar inmediatamente el acceso a estos datos médicos?")) return;
    
    try {
      const signer = provider.getSigner();
      const contract = new ethers.Contract(ORTHO_CONSENT_ADDRESS, ORTHO_CONSENT_ABI, signer);
      
      const tx = await contract.revokeConsent(consentId, "Revocado por el usuario");
      await tx.wait();
    } catch (error) {
      console.error("Error revocando:", error);
    }
  };

  const formatDate = (timestamp) => {
    if (timestamp.toString() === "0") return "Indefinido";
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  if (!account) return (
    <div className="card wallet-warning-card">
      <Wallet size={48} color="#f59e0b" />
      <h3>Billetera No Sincronizada</h3>
      <p>Es necesario conectar su Bio-Billetera (Web3) para gestionar los permisos de privacidad y consentimiento sobre sus registros clínicos en la red descentralizada.</p>
    </div>
  );

  return (
    <div className="consent-wrapper animate-fade-in">
      <div className="consent-view-header">
        <div className="header-info">
          <h2><Shield className="icon-emerald" /> Centro de Privacidad Soberana</h2>
          <p>Gestione el acceso de terceros a sus registros médicos con validación criptográfica.</p>
        </div>
        <div className="simulation-tag">
          <Activity size={14} /> MODO BLOCKCHAIN SIMULADO
        </div>
      </div>

      <div className="consent-main-grid">
        <div className="card grant-access-section">
          <h3><FileSignature size={18} color="#10b981" /> Autorizar Nuevo Acceso</h3>
          <p className="card-desc">Asigne permisos de lectura específicos a médicos o investigadores externos.</p>
          
          <form onSubmit={handleGrant} className="clinical-form">
            <div className="form-group-full">
              <label>Dirección Bio-Digital del Receptor</label>
              <div className="input-with-icon">
                <Wallet size={16} />
                <input 
                  type="text" 
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                  placeholder="0x..."
                  required
                />
              </div>
            </div>
            
            <div className="form-grid-3">
              <div className="form-group-cl">
                <label>Registro (NFT ID)</label>
                <div className="input-with-icon">
                  <Hash size={14} />
                  <input type="number" value={tokenId} onChange={(e) => setTokenId(e.target.value)} min="1" />
                </div>
              </div>
              
              <div className="form-group-cl">
                <label>Propósito Clínico</label>
                <select value={purpose} onChange={(e) => setPurpose(e.target.value)}>
                  {Object.entries(PURPOSES).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group-cl">
                <label>Periodo de Vigencia</label>
                <select value={duration} onChange={(e) => setDuration(e.target.value)}>
                  <option value="86400">24 Horas</option>
                  <option value="604800">7 Días</option>
                  <option value="2592000">30 Días</option>
                  <option value="31536000">1 Año</option>
                  <option value="0">Indefinido</option>
                </select>
              </div>
            </div>

            <button type="submit" className="primary-btn btn-lg full-width" disabled={granting}>
              {granting ? <RefreshCw className="spin" size={18} /> : <FileSignature size={18} />}
              <span>{granting ? "Procesando en Blockchain..." : "Emitir Consentimiento Digital"}</span>
            </button>
          </form>
        </div>

        <div className="consents-history-section">
          <div className="section-title-flex">
            <h3><Clock size={18} color="#64748b" /> Historial de Consentimientos</h3>
            <span className="count-badge">{consents.length} registros</span>
          </div>
          
          {loading ? (
            <div className="loading-consents"><RefreshCw className="spin" size={24} /></div>
          ) : consents.length === 0 ? (
            <div className="card empty-consents">
              <Shield size={40} color="#e2e8f0" />
              <p>No se han emitido consentimientos activos.</p>
            </div>
          ) : (
            <div className="consents-vertical-list">
              {consents.map((c) => (
                <div key={c.id} className={`card consent-item-card ${!c.isValid ? 'revoked-style' : ''}`}>
                  <div className="item-main-info">
                    <div className={`status-dot ${c.isValid ? 'active' : 'inactive'}`}></div>
                    <div className="item-text">
                      <div className="item-purpose">{PURPOSES[c.purpose]}</div>
                      <div className="item-address">A: <span>{c.recipient.substring(0, 8)}...{c.recipient.substring(34)}</span></div>
                    </div>
                  </div>
                  
                  <div className="item-meta">
                    <div className="meta-bit"><Hash size={12} /> ID #{c.tokenId}</div>
                    <div className="meta-bit"><Calendar size={12} /> {formatDate(c.expirationTime)}</div>
                  </div>

                  <div className="item-actions">
                    {c.isValid ? (
                      <button onClick={() => handleRevoke(c.id)} className="revoke-link-btn">
                        <UserX size={14} /> Revocar
                      </button>
                    ) : (
                      <span className="revoked-badge">EXPIRADO / REVOCADO</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div className="privacy-info-footer">
        <AlertTriangle size={16} />
        <span>Todos los consentimientos son inmutables y quedan registrados permanentemente en el libro mayor de la red PsychoWeb3. Revocar un acceso invalida la clave de descifrado asociada.</span>
      </div>
    </div>
  );
};

const RefreshCw = ({ size, className }) => (
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
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
    <path d="M21 3v5h-5"/>
    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
    <path d="M8 16H3v5"/>
  </svg>
);

export default ConsentManager;
