"""
Servicio de integración con Blockchain para OrthoWeb3
Maneja la escritura de hashes de evolución en smart contracts
"""

import os
import json
import asyncio
from typing import Optional, Dict
from web3 import Web3
from web3.middleware import geth_poa_middleware
import logging

logger = logging.getLogger(__name__)

class BlockchainService:
    """Servicio para interactuar con smart contracts en Ethereum/Polygon"""
    
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.account = None
        self.contract_address = None
        self.rpc_url = None
        self.contract_abi_path = None
        self.private_key = None
        self.is_initialized = False
        
    def initialize(
        self,
        rpc_url: str = None,
        contract_address: str = None,
        private_key: str = None,
        contract_abi_path: str = None
    ) -> bool:
        """
        Inicializar configuración de blockchain
        """
        try:
            # Cargar configuración desde variables de entorno
            self.rpc_url = rpc_url or os.getenv('BLOCKCHAIN_RPC_URL')
            self.contract_address = contract_address or os.getenv('EVOLUTION_CONTRACT_ADDRESS')
            self.private_key = private_key or os.getenv('BLOCKCHAIN_PRIVATE_KEY')
            self.contract_abi_path = contract_abi_path or os.getenv('BLOCKCHAIN_ABI_PATH', 'smart-contracts/artifacts/contracts/PatientEvolution.sol/PatientEvolution.json')
            
            if not self.rpc_url:
                logger.error("❌ BLOCKCHAIN_RPC_URL no configurado")
                return False

            return self._ensure_connection()
            
        except Exception as e:
            logger.error(f"❌ Error inicializando configuración blockchain: {e}")
            return False

    def _ensure_connection(self) -> bool:
        """Verifica y restablece la conexión Web3 si es necesario"""
        try:
            if self.w3 and self.w3.is_connected():
                return True

            logger.info(f"🔄 Conectando a blockchain: {self.rpc_url}")
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not self.w3.is_connected():
                logger.error("❌ No se pudo establecer conexión con el nodo RPC")
                return False

            # Recargar contrato y cuenta
            if os.path.exists(self.contract_abi_path):
                with open(self.contract_abi_path, 'r') as f:
                    contract_json = json.load(f)
                    contract_abi = contract_json['abi']
                
                if self.contract_address:
                    addr = Web3.to_checksum_address(self.contract_address)
                    self.contract = self.w3.eth.contract(address=addr, abi=contract_abi)
                
                if self.private_key:
                    self.account = self.w3.eth.account.from_key(self.private_key)
                
                self.is_initialized = True
                logger.info("✅ Conexión Web3 y Contrato inicializados")
                return True
            else:
                logger.error(f"❌ ABI no encontrado en {self.contract_abi_path}")
                return False

        except Exception as e:
            logger.error(f"❌ Fallo en _ensure_connection: {e}")
            return False
    
    async def record_evolution_hash(
        self,
        patient_did: str,
        content_hash: str,
        severity: int,
        diagnosis: str,
        is_anomaly: bool = False
    ) -> Optional[Dict]:
        """Registrar un hash de evolución en blockchain con estimación dinámica de gas"""
        if not self._ensure_connection() or not self.account:
            return {'success': False, 'error': 'Blockchain connection or account not available'}
        
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Construir función
            func = self.contract.functions.recordEvolution(
                patient_did, content_hash, severity, diagnosis, is_anomaly
            )
            
            # Estimar gas dinámicamente
            try:
                gas_estimate = func.estimate_gas({'from': self.account.address})
                gas_limit = int(gas_estimate * 1.2) # 20% de margen
            except Exception as ge:
                logger.warning(f"⚠️ Error estimando gas, usando fallback: {ge}")
                gas_limit = 500000

            transaction = func.build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'block_number': receipt['blockNumber']
                }
            return {'success': False, 'error': 'Transaction reverted'}
                
        except Exception as e:
            logger.error(f"❌ Error en transacción blockchain: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_patient_evolution(self, patient_did: str) -> Optional[list]:
        """Obtener historial con validación de conexión previa"""
        if not self._ensure_connection():
            return None
        
        try:
            return self.contract.functions.getPatientEvolution(patient_did).call()
        except Exception as e:
            logger.error(f"❌ Error en call blockchain: {e}")
            return None
    
    def get_snapshot_count(self, patient_did: str) -> int:
        if not self._ensure_connection(): return 0
        try:
            return self.contract.functions.getSnapshotCount(patient_did).call()
        except: return 0
    
    def has_anomalies(self, patient_did: str) -> bool:
        if not self._ensure_connection(): return False
        try:
            return self.contract.functions.hasAnomalies(patient_did).call()
        except: return False
    
    def get_trend(self, patient_did: str) -> Optional[bool]:
        if not self._ensure_connection(): return None
        try:
            return self.contract.functions.getTrend(patient_did).call()
        except: return None

# Instancia global del servicio
blockchain_service = BlockchainService()

