// frontend/src/components/Market.jsx
import React, { useEffect, useState } from "react";
import { ethers } from "ethers";
import { useWallet } from "../hooks/useWallet";
import { ORTHO_DATA_ADDRESS, ORTHO_DATA_ABI, ORTHO_MARKET_ADDRESS, ORTHO_MARKET_ABI } from "../config/contractConfig";
import { ShoppingCart, CheckCircle2, AlertCircle } from "lucide-react";
import "./Market.css";

const Market = () => {
  const { account, provider } = useWallet();
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [purchasing, setPurchasing] = useState(null);

  // Cargar listings al montar
  useEffect(() => {
    if (provider) loadListings();
  }, [provider]);

  const loadListings = async () => {
    setLoading(true);
    try {
      const market = new ethers.Contract(ORTHO_MARKET_ADDRESS, ORTHO_MARKET_ABI, provider);
      const dataContract = new ethers.Contract(ORTHO_DATA_ADDRESS, ORTHO_DATA_ABI, provider);
      const ids = await market.getActiveListings();
      const items = [];
      for (let tokenId of ids) {
        // Obtener precio (asumimos que el contrato expone price vía evento, pero para demo usamos 0)
        // En una implementación real habría una función getListing(tokenId) que devuelva price.
        const tokenURI = await dataContract.tokenURI(tokenId);
        // tokenURI está en base64 JSON, extraemos image URL (IPFS hash)
        let imageUrl = "";
        try {
          const base64 = tokenURI.split(",")[1];
          const json = JSON.parse(atob(base64));
          if (json.image) imageUrl = json.image.replace("ipfs://", "https://ipfs.io/ipfs/");
        } catch (e) {
          // ignore
        }
        items.push({ tokenId: tokenId.toString(), imageUrl, price: "0.01 ETH" }); // precio está hardcodeado para demo
      }
      setListings(items);
    } catch (e) {
      console.error(e);
      setError("Error cargando el mercado");
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async (tokenId) => {
    if (!account) {
      alert("Conecta tu wallet primero");
      return;
    }
    setPurchasing(tokenId);
    try {
      const signer = provider.getSigner();
      const market = new ethers.Contract(ORTHO_MARKET_ADDRESS, ORTHO_MARKET_ABI, signer);
      // En la demo usamos 0.01 ETH como precio fijo
      const tx = await market.purchaseData(tokenId, { value: ethers.utils.parseEther("0.01") });
      await tx.wait();
      alert(`Compra completada: token ${tokenId}`);
      loadListings();
    } catch (e) {
      console.error(e);
      alert("Error al comprar: " + (e.reason || e.message));
    } finally {
      setPurchasing(null);
    }
  };

  if (!account) return (
    <div className="market-warning">
      <AlertCircle /> Conecta tu wallet para ver el mercado
    </div>
  );

  return (
    <div className="market-container">
      <h3>🛒 Mercado de Datos Médicos</h3>
      {loading ? (
        <p>Cargando listings...</p>
      ) : error ? (
        <p className="error-message">{error}</p>
      ) : listings.length === 0 ? (
        <p>No hay datos a la venta en este momento.</p>
      ) : (
        <div className="listings-grid">
          {listings.map((item) => (
            <div key={item.tokenId} className="listing-card">
              {item.imageUrl && <img src={item.imageUrl} alt={`Token ${item.tokenId}`} className="listing-image" />}
              <p>Token ID: {item.tokenId}</p>
              <p>Precio: {item.price}</p>
              <button
                className="buy-btn"
                onClick={() => handlePurchase(item.tokenId)}
                disabled={purchasing === item.tokenId}
              >
                <ShoppingCart size={16} />
                {purchasing === item.tokenId ? "Comprando..." : "Comprar"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Market;
