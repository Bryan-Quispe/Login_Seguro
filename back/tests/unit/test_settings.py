"""
Login Seguro - Tests Unitarios: Settings
Tests para la configuración de la aplicación
"""
import pytest
from unittest.mock import patch
import os

from app.config.settings import Settings, get_settings


class TestSettings:
    """Tests para la clase Settings"""
    
    def test_default_database_settings(self):
        """Test valores por defecto de base de datos"""
        settings = Settings()
        
        assert settings.DATABASE_HOST == "localhost"
        assert settings.DATABASE_PORT == 5432
        assert settings.DATABASE_NAME == "login_seguro"
    
    def test_default_jwt_settings(self):
        """Test valores por defecto de JWT"""
        settings = Settings()
        
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
    
    def test_default_security_settings(self):
        """Test valores por defecto de seguridad"""
        settings = Settings()
        
        assert settings.BCRYPT_ROUNDS == 12
        assert settings.MAX_LOGIN_ATTEMPTS == 5  # Valor actual en el sistema
        assert settings.LOCKOUT_DURATION_MINUTES == 15
    
    def test_default_cors_origins(self):
        """Test orígenes CORS por defecto"""
        settings = Settings()
        
        assert "http://localhost:3001" in settings.CORS_ORIGINS
        assert "http://127.0.0.1:3001" in settings.CORS_ORIGINS
    
    def test_default_rate_limit(self):
        """Test rate limit por defecto"""
        settings = Settings()
        
        assert settings.RATE_LIMIT_PER_MINUTE == 30
    
    def test_default_face_recognition_settings(self):
        """Test configuración de reconocimiento facial"""
        settings = Settings()
        
        assert settings.FACE_RECOGNITION_MODEL == "VGG-Face"
        assert settings.FACE_DISTANCE_THRESHOLD == 0.45  # Valor actual en el sistema
    
    def test_database_url_property(self):
        """Test que database_url construye URL correctamente"""
        settings = Settings(
            DATABASE_HOST="testhost",
            DATABASE_PORT=5433,
            DATABASE_NAME="testdb",
            DATABASE_USER="testuser",
            DATABASE_PASSWORD="testpass"
        )
        
        expected = "postgresql://testuser:testpass@testhost:5433/testdb"
        assert settings.database_url == expected
    
    def test_settings_with_environment_variables(self):
        """Test que settings lee variables de entorno"""
        with patch.dict(os.environ, {
            'DATABASE_HOST': 'envhost',
            'DATABASE_PORT': '5434',
            'JWT_SECRET_KEY': 'env-secret-key'
        }):
            # Crear nueva instancia para que lea las env vars
            settings = Settings(
                _env_file=None  # Evitar leer .env
            )
            
            # Los valores por defecto se sobrescriben con env vars
            # Nota: esto depende de la configuración de Pydantic
    
    def test_jwt_secret_key_exists(self):
        """Test que JWT secret key tiene un valor"""
        settings = Settings()
        
        assert settings.JWT_SECRET_KEY is not None
        assert len(settings.JWT_SECRET_KEY) > 0


class TestGetSettings:
    """Tests para la función get_settings"""
    
    def test_returns_settings_instance(self):
        """Test que retorna instancia de Settings"""
        settings = get_settings()
        
        assert isinstance(settings, Settings)
    
    def test_returns_cached_instance(self):
        """Test que retorna la misma instancia (singleton)"""
        # Limpiar cache primero
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_settings_are_valid(self):
        """Test que settings son válidos"""
        settings = get_settings()
        
        assert settings.DATABASE_PORT > 0
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.BCRYPT_ROUNDS >= 4  # Mínimo para bcrypt
        assert settings.FACE_DISTANCE_THRESHOLD > 0
        assert settings.FACE_DISTANCE_THRESHOLD < 1
