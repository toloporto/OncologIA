"""
Worker en Segundo Plano para Procesar Transacciones Blockchain
Ejecutar este script en paralelo al servidor API
"""

import time
import logging
import sys
import os

# Añadir path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.blockchain_queue_service import blockchain_queue_service
from backend.blockchain_service import blockchain_service
from backend.database import SessionLocal

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_pending_transactions():
    """Procesar transacciones pendientes en la cola"""
    logger.info("🔍 Buscando transacciones pendientes...")
    
    # Obtener transacciones pendientes
    pending_txs = blockchain_queue_service.get_pending_transactions(limit=5)
    
    if not pending_txs:
        logger.info("✅ No hay transacciones pendientes")
        return
    
    logger.info(f"📝 Procesando {len(pending_txs)} transacciones...")
    
    for tx in pending_txs:
        try:
            # Marcar como en procesamiento
            blockchain_queue_service.mark_as_processing(tx.id)
            logger.info(f"⚙️ Procesando transacción {tx.id} para paciente {tx.patient_did}")
            
            # Intentar escribir en blockchain
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                blockchain_service.record_evolution_hash(
                    patient_did=tx.patient_did,
                    content_hash=tx.content_hash,
                    severity=int(tx.severity),
                    diagnosis=tx.diagnosis,
                    is_anomaly=tx.is_anomaly
                )
            )
            
            loop.close()
            
            # Verificar resultado
            if result and result.get('success'):
                blockchain_queue_service.mark_as_completed(
                    tx.id,
                    result['tx_hash'],
                    result.get('block_number')
                )
                logger.info(f"✅ Transacción completada: {result['tx_hash']}")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No response'
                blockchain_queue_service.mark_as_failed(tx.id, error_msg)
                logger.error(f"❌ Transacción fallida: {error_msg}")
                
        except Exception as e:
            logger.error(f"❌ Error procesando transacción {tx.id}: {e}")
            blockchain_queue_service.mark_as_failed(tx.id, str(e))


def main():
    """Bucle principal del worker"""
    logger.info("🚀 Iniciando Blockchain Worker...")
    
    # Inicializar blockchain service
    if not blockchain_service.is_initialized:
        logger.info("🔧 Inicializando conexión blockchain...")
        success = blockchain_service.initialize()
        if not success:
            logger.warning("⚠️ Blockchain no inicializado. Worker funcionará en modo simulado.")
    
    logger.info("✅ Worker listo. Procesando cada 10 segundos...")
    logger.info("Presiona Ctrl+C para detener")
    
    try:
        while True:
            process_pending_transactions()
            time.sleep(10)  # Esperar 10 segundos entre ciclos
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Worker detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal en worker: {e}")
        raise


if __name__ == "__main__":
    main()
