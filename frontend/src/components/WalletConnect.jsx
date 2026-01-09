import React from 'react';
import { Wallet, AlertCircle, CheckCircle2, LogOut } from 'lucide-react';
import { useWallet } from '../hooks/useWallet';
import './WalletConnect.css';

const WalletConnect = () => {
  const { account, isConnecting, error, connectWallet, disconnectWallet } = useWallet();

  // Función para acortar la dirección (ej: 0x1234...5678)
  const formatAddress = (address) => {
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <div className="wallet-connect-container">
      {error && (
        <div className="wallet-error">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {!account ? (
        <button 
          className="connect-wallet-btn"
          onClick={connectWallet}
          disabled={isConnecting}
        >
          <Wallet size={18} />
          {isConnecting ? 'Conectando...' : 'Conectar Wallet'}
        </button>
      ) : (
        <div className="wallet-connected">
          <div className="wallet-info">
            <div className="status-indicator"></div>
            <span className="address">{formatAddress(account)}</span>
          </div>
          <button 
            className="disconnect-btn"
            onClick={disconnectWallet}
            title="Desconectar"
          >
            <LogOut size={16} />
          </button>
        </div>
      )}
    </div>
  );
};

export default WalletConnect;
