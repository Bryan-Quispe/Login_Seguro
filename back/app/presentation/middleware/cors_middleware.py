"""
Login Seguro - Configuración CORS
Permite requests desde el frontend Next.js
"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from ...config.settings import get_settings


def setup_cors(app: FastAPI) -> None:
    """Configura CORS para la aplicación"""
    settings = get_settings()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600  # Cache preflight por 10 minutos
    )
