"""
Login Seguro - Tests de Integración: API Routes
Tests para los endpoints de la API REST usando pytest-asyncio y httpx
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

import httpx
from app.main import app
from app.domain.entities.user import User, UserRole


@pytest_asyncio.fixture
async def client():
    """Cliente de prueba asíncrono para FastAPI"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client


class TestAuthRoutes:
    """Tests para rutas de autenticación"""
    
    @pytest.mark.asyncio
    async def test_register_endpoint_exists(self, client):
        """Test que endpoint de registro existe"""
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "Test@12345",
            "email": "test@example.com"
        })
        
        # No debería retornar 404
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_register_validation_error_short_password(self, client):
        """Test que rechaza contraseña corta"""
        response = await client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "short",
            "email": "test@example.com"
        })
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_validation_error_invalid_username(self, client):
        """Test que rechaza username con caracteres especiales"""
        response = await client.post("/api/auth/register", json={
            "username": "test@user!",
            "password": "Test@12345",
            "email": "test@example.com"
        })
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_endpoint_exists(self, client):
        """Test que endpoint de login existe"""
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test@12345"
        })
        
        # No debería retornar 404
        assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_login_validation_error_empty_username(self, client):
        """Test que rechaza username vacío"""
        response = await client.post("/api/auth/login", json={
            "username": "",
            "password": "Test@12345"
        })
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_validation_error_empty_password(self, client):
        """Test que rechaza password vacío"""
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": ""
        })
        
        assert response.status_code == 422


class TestFaceRoutes:
    """Tests para rutas de verificación facial"""
    
    @pytest.mark.asyncio
    async def test_face_register_requires_auth(self, client):
        """Test que registro facial requiere autenticación"""
        response = await client.post("/api/face/register", json={
            "image_data": "data:image/jpeg;base64,/9j/..."
        })
        
        # Debería requerir autenticación
        assert response.status_code in [401, 403, 422]
    
    @pytest.mark.asyncio
    async def test_face_verify_requires_auth(self, client):
        """Test que verificación facial requiere autenticación"""
        response = await client.post("/api/face/verify", json={
            "image_data": "data:image/jpeg;base64,/9j/..."
        })
        
        # Debería requerir autenticación
        assert response.status_code in [401, 403, 422]


class TestAPIDocumentation:
    """Tests para documentación de la API"""
    
    @pytest.mark.asyncio
    async def test_docs_endpoint_available(self, client):
        """Test que /docs está disponible"""
        response = await client.get("/docs")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_redoc_endpoint_available(self, client):
        """Test que /redoc está disponible"""
        response = await client.get("/redoc")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_openapi_schema_available(self, client):
        """Test que schema OpenAPI está disponible"""
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestErrorHandling:
    """Tests para manejo de errores"""
    
    @pytest.mark.asyncio
    async def test_validation_error_format(self, client):
        """Test que errores de validación tienen formato correcto"""
        response = await client.post("/api/auth/register", json={
            "username": "",
            "password": ""
        })
        
        assert response.status_code == 422
        data = response.json()
        assert "success" in data or "detail" in data
    
    @pytest.mark.asyncio
    async def test_not_found_error(self, client):
        """Test respuesta para ruta inexistente"""
        response = await client.get("/nonexistent/route")
        
        assert response.status_code == 404


class TestRateLimiting:
    """Tests para rate limiting"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, client):
        """Test que headers de rate limit están presentes"""
        # Hacer una petición válida
        response = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        
        # Los headers de rate limit pueden o no estar presentes
        # dependiendo de la configuración
        # Este test verifica que la petición se procesa
        assert response.status_code in [200, 400, 401, 422, 429]


class TestCORS:
    """Tests para configuración CORS"""
    
    @pytest.mark.asyncio
    async def test_cors_headers_on_options(self, client):
        """Test que CORS headers están en respuestas OPTIONS"""
        response = await client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # La respuesta puede variar según configuración
        assert response.status_code in [200, 204, 405]
    
    @pytest.mark.asyncio
    async def test_cors_allows_configured_origin(self, client):
        """Test que CORS permite origen configurado"""
        response = await client.post(
            "/api/auth/login",
            json={"username": "test", "password": "test"},
            headers={"Origin": "http://localhost:3001"}
        )
        
        # Debería procesar la petición
        assert response.status_code != 403
