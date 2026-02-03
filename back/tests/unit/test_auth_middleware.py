"""
Login Seguro - Tests Unitarios: Auth Middleware
Tests para el middleware de autenticación JWT
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from jose import jwt

from app.presentation.middleware.auth_middleware import JWTBearer, get_current_user_id
from fastapi import HTTPException


class TestJWTBearer:
    """Tests para JWTBearer middleware"""
    
    @pytest.fixture
    def jwt_bearer(self):
        """Fixture para crear instancia de JWTBearer"""
        return JWTBearer(auto_error=True)
    
    @pytest.fixture
    def valid_token(self):
        """Fixture para generar token válido"""
        from app.config.settings import get_settings
        settings = get_settings()
        
        payload = {
            "sub": "1",
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    @pytest.fixture
    def expired_token(self):
        """Fixture para generar token expirado"""
        from app.config.settings import get_settings
        settings = get_settings()
        
        payload = {
            "sub": "1",
            "username": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expirado
        }
        
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    def test_verify_jwt_valid_token(self, jwt_bearer, valid_token):
        """Test verificación de token válido"""
        payload = jwt_bearer.verify_jwt(valid_token)
        
        assert payload is not None
        assert payload.get("sub") == "1"
        assert payload.get("username") == "testuser"
    
    def test_verify_jwt_expired_token(self, jwt_bearer, expired_token):
        """Test que token expirado retorna None"""
        payload = jwt_bearer.verify_jwt(expired_token)
        
        assert payload is None
    
    def test_verify_jwt_invalid_token(self, jwt_bearer):
        """Test que token inválido retorna None"""
        payload = jwt_bearer.verify_jwt("invalid.token.here")
        
        assert payload is None
    
    def test_verify_jwt_wrong_secret(self, jwt_bearer):
        """Test que token con secret incorrecto retorna None"""
        payload = {
            "sub": "1",
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Token firmado con secret incorrecto
        wrong_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        
        result = jwt_bearer.verify_jwt(wrong_token)
        
        assert result is None
    
    def test_verify_jwt_missing_sub_claim(self, jwt_bearer):
        """Test que token sin 'sub' claim retorna None"""
        from app.config.settings import get_settings
        settings = get_settings()
        
        payload = {
            "username": "testuser",  # Sin 'sub'
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        result = jwt_bearer.verify_jwt(token)
        
        assert result is None
    
    def test_verify_jwt_empty_sub_claim(self, jwt_bearer):
        """Test que token con 'sub' vacío retorna None"""
        from app.config.settings import get_settings
        settings = get_settings()
        
        payload = {
            "sub": "",  # Sub vacío
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        result = jwt_bearer.verify_jwt(token)
        
        assert result is None


class TestGetCurrentUserId:
    """Tests para get_current_user_id"""
    
    def test_extracts_user_id_from_payload(self):
        """Test que extrae user_id correctamente"""
        payload = {
            "sub": 123,
            "username": "testuser"
        }
        
        user_id = get_current_user_id(payload)
        
        assert user_id == 123
    
    def test_raises_exception_when_sub_missing(self):
        """Test que lanza excepción cuando falta 'sub'"""
        payload = {
            "username": "testuser"  # Sin 'sub'
        }
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(payload)
        
        assert exc_info.value.status_code == 403
    
    def test_raises_exception_when_sub_empty(self):
        """Test que lanza excepción cuando 'sub' está vacío"""
        payload = {
            "sub": "",
            "username": "testuser"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(payload)
        
        assert exc_info.value.status_code == 403


class TestJWTBearerIntegration:
    """Tests de integración para JWTBearer"""
    
    @pytest.mark.asyncio
    async def test_bearer_with_valid_credentials(self):
        """Test JWTBearer con credenciales válidas"""
        from app.config.settings import get_settings
        settings = get_settings()
        
        # Crear token válido
        payload = {
            "sub": "1",
            "username": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        # Mock del request
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": f"Bearer {token}"}
        
        bearer = JWTBearer(auto_error=True)
        
        # El test verifica que el método verify_jwt funciona correctamente
        result = bearer.verify_jwt(token)
        
        assert result is not None
        assert result.get("sub") == "1"
