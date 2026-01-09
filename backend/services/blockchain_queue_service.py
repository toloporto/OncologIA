"""
Servicio de Cola para Transacciones Blockchain
Gestiona la cola de escrituras blockchain pendientes
"""

import uuid
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from backend.models import PendingBlockchainTransaction
from backend.database import SessionLocal
import datetime

logger = logging.getLogger(__name__)


class BlockchainQueueService:
    """Servicio para gestionar cola de transacciones blockchain"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session
    
    def enqueue_blockchain_write(
        self,
        patient_did: str,
        content_hash: str,
        severity: int,
        diagnosis: str,
        is_anomaly: bool = False
    ) -> Optional[str]:
        """
        Encolar una transacción blockchain para procesamiento asíncrono
        
        Args:
            patient_did: DID del paciente
            content_hash: Hash del contenido (IPFS o SHA256)
            severity: Severidad (0-10)
            diagnosis: Diagnóstico
            is_anomaly: Si se detectó anomalía
            
        Returns:
            ID de la transacción encolada o None si falla
        """
        db = self.db or SessionLocal()
        try:
            transaction_id = str(uuid.uuid4())
            
            pending_tx = PendingBlockchainTransaction(
                id=transaction_id,
                patient_did=patient_did,
                content_hash=content_hash,
                severity=severity,
                diagnosis=diagnosis,
                is_anomaly=is_anomaly,
                status="pending",
                created_at=datetime.datetime.utcnow()
            )
            
            db.add(pending_tx)
            db.commit()
            
            logger.info(f"✅ Transacción encolada: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"❌ Error encolando transacción: {e}")
            db.rollback()
            return None
        finally:
            if not self.db:
                db.close()
    
    def get_pending_transactions(self, limit: int = 10) -> List[PendingBlockchainTransaction]:
        """
        Obtener transacciones pendientes más antiguas
        
        Args:
            limit: Número máximo de transacciones a obtener
            
        Returns:
            Lista de transacciones pendientes
        """
        db = self.db or SessionLocal()
        try:
            transactions = db.query(PendingBlockchainTransaction).filter(
                PendingBlockchainTransaction.status == "pending"
            ).order_by(
                PendingBlockchainTransaction.created_at
            ).limit(limit).all()
            
            return transactions
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo transacciones pendientes: {e}")
            return []
        finally:
            if not self.db:
                db.close()
    
    def mark_as_processing(self, transaction_id: str) -> bool:
        """Marcar transacción como en procesamiento"""
        db = self.db or SessionLocal()
        try:
            tx = db.query(PendingBlockchainTransaction).filter(
                PendingBlockchainTransaction.id == transaction_id
            ).first()
            
            if tx:
                tx.status = "processing"
                db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error marcando como processing: {e}")
            db.rollback()
            return False
        finally:
            if not self.db:
                db.close()
    
    def mark_as_completed(
        self,
        transaction_id: str,
        tx_hash: str,
        block_number: int = None
    ) -> bool:
        """Marcar transacción como completada"""
        db = self.db or SessionLocal()
        try:
            tx = db.query(PendingBlockchainTransaction).filter(
                PendingBlockchainTransaction.id == transaction_id
            ).first()
            
            if tx:
                tx.status = "completed"
                tx.tx_hash = tx_hash
                tx.processed_at = datetime.datetime.utcnow()
                db.commit()
                logger.info(f"✅ Transacción completada: {tx_hash}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error marcando como completed: {e}")
            db.rollback()
            return False
        finally:
            if not self.db:
                db.close()
    
    def mark_as_failed(
        self,
        transaction_id: str,
        error_message: str
    ) -> bool:
        """Marcar transacción como fallida"""
        db = self.db or SessionLocal()
        try:
            tx = db.query(PendingBlockchainTransaction).filter(
                PendingBlockchainTransaction.id == transaction_id
            ).first()
            
            if tx:
                tx.retry_count += 1
                
                # Si supera 3 reintentos, marcar como failed permanente
                if tx.retry_count >= 3:
                    tx.status = "failed"
                    tx.error_message = error_message
                    tx.processed_at = datetime.datetime.utcnow()
                    logger.error(f"❌ Transacción fallida permanentemente: {transaction_id}")
                else:
                    # Volver a pending para reintento
                    tx.status = "pending"
                    tx.error_message = error_message
                    logger.warning(f"⚠️ Transacción fallida, reintento {tx.retry_count}/3")
                
                db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error marcando como failed: {e}")
            db.rollback()
            return False
        finally:
            if not self.db:
                db.close()


# Instancia global
blockchain_queue_service = BlockchainQueueService()
