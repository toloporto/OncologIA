"""
Servicio de IPFS para OrthoWeb3
Maneja la subida y recuperación de archivos en IPFS
"""

import requests
import io
from typing import Optional, Dict
import mimetypes

class IPFSService:
    """Servicio para interactuar con IPFS"""
    
    def __init__(self, api_url: str = None):
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.api_url = api_url or os.getenv('IPFS_API_URL', 'http://127.0.0.1:5001/api/v0')
        self.gateway_url = os.getenv('IPFS_GATEWAY_URL', 'http://127.0.0.1:8080/ipfs')
        self.public_gateway = "https://ipfs.io/ipfs"
    
    def is_connected(self) -> bool:
        """Verificar si IPFS está disponible"""
        try:
            response = requests.post(f"{self.api_url}/id", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def upload_file(self, file_data: bytes, filename: str) -> Optional[Dict]:
        """
        Subir un archivo a IPFS
        
        Args:
            file_data: Datos del archivo en bytes
            filename: Nombre del archivo
            
        Returns:
            Dict con información del archivo subido o None si falla
        """
        try:
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Preparar archivo para subida
            files = {
                'file': (filename, io.BytesIO(file_data), mime_type)
            }
            
            # Subir a IPFS
            response = requests.post(
                f"{self.api_url}/add",
                files=files,
                params={'pin': 'true'}  # Pin para que no se elimine
            )
            
            if response.status_code == 200:
                result = response.json()
                ipfs_hash = result['Hash']
                
                return {
                    'success': True,
                    'hash': ipfs_hash,
                    'size': result['Size'],
                    'name': filename,
                    'url_local': f"{self.gateway_url}/{ipfs_hash}",
                    'url_public': f"{self.public_gateway}/{ipfs_hash}",
                    'mime_type': mime_type
                }
            else:
                return {
                    'success': False,
                    'error': f"Error HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_image(self, image_data: bytes, filename: str) -> Optional[Dict]:
        """
        Subir una imagen médica a IPFS
        
        Args:
            image_data: Datos de la imagen en bytes
            filename: Nombre del archivo
            
        Returns:
            Dict con información de la imagen subida
        """
        return self.upload_file(image_data, filename)
    
    def get_file(self, ipfs_hash: str) -> Optional[bytes]:
        """
        Recuperar un archivo desde IPFS
        
        Args:
            ipfs_hash: Hash IPFS del archivo
            
        Returns:
            Datos del archivo en bytes o None si falla
        """
        try:
            response = requests.post(
                f"{self.api_url}/cat",
                params={'arg': ipfs_hash},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.content
            else:
                return None
                
        except Exception as e:
            print(f"Error recuperando archivo de IPFS: {e}")
            return None
    
    def pin_file(self, ipfs_hash: str) -> bool:
        """
        Pin un archivo para que no se elimine
        
        Args:
            ipfs_hash: Hash IPFS del archivo
            
        Returns:
            True si se pineó correctamente
        """
        try:
            response = requests.post(
                f"{self.api_url}/pin/add",
                params={'arg': ipfs_hash}
            )
            return response.status_code == 200
        except:
            return False
    
    def get_stats(self) -> Optional[Dict]:
        """Obtener estadísticas del nodo IPFS"""
        try:
            response = requests.post(f"{self.api_url}/id")
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

# Instancia global del servicio
ipfs_service = IPFSService()
