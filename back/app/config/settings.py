"""
Login Seguro - Configuración de la aplicación
Módulo de configuración centralizada con variables de entorno
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic para validación"""
    
    # Database
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "login_seguro"
    DATABASE_USER: str = "admin"
    DATABASE_PASSWORD: str = "SecureP@ssw0rd2024!"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "super-secure-jwt-secret-key-change-in-production-2024!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security
    BCRYPT_ROUNDS: int = 12
    MAX_LOGIN_ATTEMPTS: int = 3
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3001", "http://127.0.0.1:3001"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # Face Recognition
    FACE_RECOGNITION_MODEL: str = "VGG-Face"
    FACE_DISTANCE_THRESHOLD: float = 0.6
    
    @property
    def database_url(self) -> str:
        """Construye la URL de conexión a PostgreSQL"""
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración cacheada (singleton)"""
    return Settings()
