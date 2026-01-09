import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';

export const useWallet = () => {
  const [account, setAccount] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [provider, setProvider] = useState(null);

  // Verificar si MetaMask está instalado
  const checkIfWalletIsConnected = useCallback(async () => {
    if (!window.ethereum) return;

    try {
      const provider = new ethers.providers.Web3Provider(window.ethereum);
      setProvider(provider);

      const accounts = await provider.listAccounts();
      const network = await provider.getNetwork();

      setChainId(network.chainId);

      if (accounts.length > 0) {
        setAccount(accounts[0]);
      }
    } catch (error) {
      console.error("Error verificando wallet:", error);
    }
  }, []);

  // Escuchar cambios en la cuenta o red
  useEffect(() => {
    checkIfWalletIsConnected();

    if (window.ethereum) {
      window.ethereum.on('accountsChanged', (accounts) => {
        setAccount(accounts[0] || null);
      });

      window.ethereum.on('chainChanged', () => {
        window.location.reload();
      });
    }

    return () => {
      if (window.ethereum) {
        window.ethereum.removeAllListeners();
      }
    };
  }, [checkIfWalletIsConnected]);

  // Función para conectar la wallet
  const connectWallet = async () => {
    if (!window.ethereum) {
      setError("MetaMask no está instalado. Por favor instálalo para continuar.");
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const provider = new ethers.providers.Web3Provider(window.ethereum);
      // Solicitar acceso a cuentas
      await provider.send("eth_requestAccounts", []);
      
      const signer = provider.getSigner();
      const address = await signer.getAddress();
      const network = await provider.getNetwork();

      setAccount(address);
      setChainId(network.chainId);
      setProvider(provider);
    } catch (err) {
      console.error(err);
      setError("Error al conectar la wallet. " + (err.message || ""));
    } finally {
      setIsConnecting(false);
    }
  };

  // Función para desconectar (solo visualmente, ya que MetaMask maneja la conexión real)
  const disconnectWallet = () => {
    setAccount(null);
    setChainId(null);
  };

  return {
    account,
    chainId,
    isConnecting,
    error,
    connectWallet,
    disconnectWallet,
    provider
  };
};
