import os
import logging
from typing import List, Dict
from datetime import datetime

# Intentamos importar librerías RAG, fallback si no están instaladas
try:
    import chromadb
    from chromadb.utils import embedding_functions
    from pypdf import PdfReader
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"DEBUG: Error importando librerías RAG. Detalles: {e}")
    RAG_AVAILABLE = False
except Exception as e:
    print(f"DEBUG: Error inesperado al importar RAG: {e}")
    RAG_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RagService:
    """
    Servicio de 'Cerebro Clínico' que gestiona una base de conocimientos local.
    """
    
    def __init__(self, knowledge_path: str = "knowledge_base", db_path: str = "./chroma_db"):
        self.knowledge_path = knowledge_path
        self.db_path = db_path
        self.client = None
        self.collection = None
        
        if RAG_AVAILABLE:
            try:
                # Usamos almacenamiento persistente en disco
                self.client = chromadb.PersistentClient(path=self.db_path)
                
                # Función de embedding por defecto (Sentence Transformers - all-MiniLM-L6-v2)
                # Es ligera, rápida y corre en CPU.
                self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
                
                self.collection = self.client.get_or_create_collection(
                    name="clinical_knowledge",
                    embedding_function=self.ef
                )
                
                # Active Learning Collection
                self.feedback_collection = self.client.get_or_create_collection(
                    name="feedback_learning",
                    embedding_function=self.ef
                )
                
                logger.info(f"🧠 RagService: Conectado a ChromaDB en '{db_path}'")
            except Exception as e:
                logger.error(f"❌ Error inicializando ChromaDB: {e}")
                # No modificamos la variable global para evitar UnboundLocalError
                self.client = None
                self.collection = None
                self.feedback_collection = None

    def store_feedback(self, text: str, correction: dict, session_id: str) -> bool:
        """
        Almacena una corrección médica como vector.
        Vector: Texto del paciente.
        Payload: La corrección (JSON).
        """
        if not RAG_AVAILABLE or not self.feedback_collection:
            return False
            
        try:
            import json
            # Convertimos el dict de corrección a string para almacenarlo
            correction_str = json.dumps(correction)
            
            self.feedback_collection.upsert(
                documents=[text],
                metadatas=[{"session_id": session_id, "correction": correction_str}],
                ids=[f"feedback_{session_id}"]
            )
            logger.info(f"🧠 Feedback aprendido y vectorizado para sesión {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error guardando vector de feedback: {e}")
            return False

    def find_similar_feedback(self, text: str, threshold: float = 0.5) -> List[Dict]:
        """
        Busca si existen correcciones previas para textos similares.
        """
        if not RAG_AVAILABLE or not self.feedback_collection:
            return []
            
        try:
            results = self.feedback_collection.query(
                query_texts=[text],
                n_results=3
            )
            
            # Formatear resultados
            found_cases = []
            if results['documents']:
                for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
                    # Distancia en Chroma (l2) -> menor es mejor. 
                    # Aproximación: si distance < 1.0 es algo similar. 
                    # Ajustar según métrica (si es cosine, distance es 1-sim).
                    # Asumimos que distance es "disimilitud".
                    if dist < 1.0: 
                        found_cases.append({
                            "text": doc,
                            "correction": meta["correction"], # String JSON
                            "distance": dist
                        })
            
            return found_cases
        except Exception as e:
            logger.error(f"Error buscando feedback similar: {e}")
            return []

    def ingest_documents(self) -> dict:
        """
        Lee todos los PDFs de la carpeta knowledge_base y los indexa.
        """
        if not RAG_AVAILABLE:
            return {"error": "Librerías RAG no instaladas (chromadb, pypdf)."}
            
        if not os.path.exists(self.knowledge_path):
            os.makedirs(self.knowledge_path)
            return {"message": f"Carpeta '{self.knowledge_path}' creada. Añade PDFs ahí."}

        files = []
        for root, dirs, filenames in os.walk(self.knowledge_path):
            for filename in filenames:
                if filename.lower().endswith(".pdf"):
                    # Guardamos ruta completa
                    files.append(os.path.join(root, filename))

        if not files:
            return {"message": "No hay PDFs en la carpeta de conocimiento (ni subcarpetas)."}
            
        total_chunks = 0
        
        for path in files:
            filename = os.path.basename(path)
            try:
                reader = PdfReader(path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Troceado básico (Chunking) cada 1000 caracteres
                chunk_size = 1000
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                
                # Generar IDs únicos y metadatos
                ids = [f"{filename}_{i}" for i in range(len(chunks))]
                metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
                
                # Upsert (Insertar o Actualizar)
                self.collection.upsert(
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )
                total_chunks += len(chunks)
                logger.info(f"📄 Procesado: {filename} ({len(chunks)} fragmentos)")
                
            except Exception as e:
                logger.error(f"⚠️ Error procesando {filename}: {e}")

        return {"success": True, "files_processed": len(files), "chunks_added": total_chunks}

    def query_expert(self, query: str, n_results: int = 3) -> Dict:
        """
        Busca contexto relevante para una pregunta clínica.
        """
        if not RAG_AVAILABLE or not self.collection:
            return {"error": "RAG no disponible"}
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Verificar si hay resultados
            if not results['documents'] or not results['documents'][0]:
                return {"query": query, "context": "No se encontró información relevante.", "sources": []}

            # Extracción segura de documentos y metadatos
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            
            context_text = "\n\n".join([f"[Fuente: {m['source']}]\n{d}" for d, m in zip(documents, metadatas)])
            
            return {
                "query": query,
                "context": context_text,
                "sources": [m['source'] for m in metadatas]
            }
        except Exception as e:
            logger.error(f"Error consultando ChromaDB: {e}")
            return {"error": str(e)}

# Instancia Global
rag_service = RagService()
