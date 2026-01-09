import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import ssl

def create_production_app():
    """Crea la aplicación FastAPI optimizada para producción"""
    
    app = FastAPI(
        title="OrthoWeb3 Production API",
        description="Sistema de diagnóstico de ortodoncia con IA y Web3",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Middleware de seguridad
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["orthoweb3.com", "www.orthoweb3.com", "api.orthoweb3.com"]
    )
    
    # Middleware de compresión
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # CORS para producción
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://orthoweb3.com",
            "https://www.orthoweb3.com",
            "https://app.orthoweb3.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configuración de SSL
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
        '/etc/ssl/certs/orthoweb3.crt',
        '/etc/ssl/private/orthoweb3.key'
    )
    
    return app, ssl_context

# Configuración de logging para producción
def setup_production_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'production': {
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/orthoweb3/api.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'production',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': '/var/log/orthoweb3/error.log',
                'maxBytes': 10485760,
                'backupCount': 5,
                'formatter': 'production',
            },
        },
        'loggers': {
            '': {
                'handlers': ['file', 'error_file'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    })