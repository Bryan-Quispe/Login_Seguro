"""
Tests comprehensivos para audit_service.py
Objetivo: Subir cobertura de 25% a >95%

Estrategia de mocking:
- Mock get_db() para evitar conexión real
- Mock httpx.AsyncClient para geolocalización
- Mock Request de FastAPI
- Probar todas las ramas if/else
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.infrastructure.services.audit_service import (
    AuditService, 
    AuditLog,
    get_audit_service
)


@pytest.fixture
def mock_db():
    """
    Mock de la conexión de base de datos.
    
    CRÍTICO: get_cursor() se usa como context manager (with statement),
    por lo que necesitamos MagicMock para soportar __enter__/__exit__.
    """
    db = MagicMock()
    
    # Cursor mockeado que se retorna por __enter__
    cursor = MagicMock()
    cursor.fetchone.return_value = (123,)  # ID del registro insertado
    cursor.fetchall.return_value = []
    
    # Configurar get_cursor() para retornar un context manager válido
    # MagicMock automáticamente maneja __enter__ y __exit__
    db.get_cursor.return_value.__enter__.return_value = cursor
    db.get_cursor.return_value.__exit__.return_value = None
    
    return db


@pytest.fixture
def mock_request():
    """Mock de FastAPI Request"""
    request = Mock()
    request.headers = {"User-Agent": "Test Browser"}
    request.client = Mock()
    request.client.host = "192.168.1.100"
    return request


class TestAuditServiceGetRealIP:
    """Tests para get_real_ip - extracción de IP con diferentes headers"""
    
    def test_get_real_ip_from_x_forwarded_for(self, mock_db):
        """Test: Extrae IP de X-Forwarded-For (prioridad más alta)"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        request = Mock()
        request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}
        request.client = Mock()
        request.client.host = "10.0.0.1"
        
        ip = service.get_real_ip(request)
        
        # Debe tomar la primera IP de X-Forwarded-For
        assert ip == "203.0.113.1"
    
    def test_get_real_ip_from_x_real_ip(self, mock_db):
        """Test: Extrae IP de X-Real-IP cuando X-Forwarded-For no existe"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        request = Mock()
        request.headers = {"X-Real-IP": "198.51.100.50"}
        request.client = Mock()
        request.client.host = "10.0.0.1"
        
        ip = service.get_real_ip(request)
        
        assert ip == "198.51.100.50"
    
    def test_get_real_ip_from_cloudflare(self, mock_db):
        """Test: Extrae IP de CF-Connecting-IP (Cloudflare)"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        request = Mock()
        request.headers = {"CF-Connecting-IP": "203.0.113.100"}
        request.client = Mock()
        request.client.host = "10.0.0.1"
        
        ip = service.get_real_ip(request)
        
        assert ip == "203.0.113.100"
    
    def test_get_real_ip_from_client_fallback(self, mock_db):
        """Test: Fallback a request.client.host cuando no hay headers"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.50"
        
        ip = service.get_real_ip(request)
        
        assert ip == "192.168.1.50"
    
    def test_get_real_ip_returns_unknown_when_no_client(self, mock_db):
        """Test: Retorna 'unknown' cuando no hay información de cliente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        request = Mock()
        request.headers = {}
        request.client = None
        
        ip = service.get_real_ip(request)
        
        assert ip == "unknown"


class TestAuditServiceGetLocationFromIP:
    """Tests para get_location_from_ip - geolocalización"""
    
    @pytest.mark.asyncio
    async def test_get_location_for_local_dev(self, mock_db):
        """Test: Retorna ubicación configurada para desarrollo local"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        location = await service.get_location_from_ip("200.1.2.3", is_local_dev=True)
        
        assert location["country"] == "Ecuador"
        assert location["city"] == "Sangolquí"
        assert location["region"] == "Pichincha"
    
    @pytest.mark.asyncio
    async def test_get_location_for_localhost(self, mock_db):
        """Test: Retorna ubicación configurada para localhost"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        for local_ip in ["127.0.0.1", "localhost", "::1"]:
            location = await service.get_location_from_ip(local_ip)
            assert location["country"] == "Ecuador"
    
    @pytest.mark.asyncio
    async def test_get_location_for_private_ips(self, mock_db):
        """Test: Retorna ubicación configurada para IPs privadas"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        private_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1"]
        
        for private_ip in private_ips:
            location = await service.get_location_from_ip(private_ip)
            assert location["country"] == "Ecuador"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_get_location_from_api_success(self, mock_httpx_client, mock_db):
        """Test: Obtiene ubicación de API ip-api.com exitosamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock respuesta exitosa de API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "country": "United States",
            "city": "New York",
            "regionName": "New York"
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        location = await service.get_location_from_ip("8.8.8.8")
        
        assert location["country"] == "United States"
        assert location["city"] == "New York"
        assert location["region"] == "New York"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_get_location_api_failure(self, mock_httpx_client, mock_db):
        """Test: Fallback a Ecuador cuando API falla"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock respuesta con error
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "fail"}
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        location = await service.get_location_from_ip("8.8.8.8")
        
        # Debe usar fallback
        assert location["country"] == "Ecuador"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_get_location_api_exception(self, mock_httpx_client, mock_db):
        """Test: Maneja excepción de API correctamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock excepción de red
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        location = await service.get_location_from_ip("8.8.8.8")
        
        # Debe usar fallback sin lanzar excepción
        assert location["country"] == "Ecuador"


class TestAuditServiceGetPublicIP:
    """Tests para get_public_ip"""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_get_public_ip_success(self, mock_httpx_client, mock_db):
        """Test: Obtiene IP pública exitosamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "203.0.113.50"
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        public_ip = await service.get_public_ip()
        
        assert public_ip == "203.0.113.50"
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_get_public_ip_failure(self, mock_httpx_client, mock_db):
        """Test: Retorna string vacío cuando falla"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Timeout")
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        public_ip = await service.get_public_ip()
        
        assert public_ip == ""


class TestAuditServiceLogAction:
    """Tests para log_action - registro de acciones de auditoría"""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.datetime')
    @patch('zoneinfo.ZoneInfo')  # Parchear ZoneInfo para evitar error en Windows
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_log_action_success(self, mock_httpx_client, mock_zoneinfo, mock_datetime, mock_db):
        """Test: Registra acción exitosamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock datetime.now() para retornar objeto con método replace
        fixed_time = datetime(2026, 2, 5, 10, 30, 0)
        mock_now_result = Mock()
        mock_now_result.replace.return_value = fixed_time
        mock_datetime.now.return_value = mock_now_result
        
        # Mock API de geolocalización
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "country": "Ecuador",
            "city": "Quito",
            "regionName": "Pichincha"
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        request = Mock()
        request.headers = {"User-Agent": "Mozilla/5.0", "X-Real-IP": "190.1.2.3"}
        request.client = Mock()
        request.client.host = "190.1.2.3"
        
        result = await service.log_action(
            request=request,
            action="unlock_user",
            admin_id=1,
            admin_username="admin",
            target_user_id=5,
            target_username="johndoe",
            details="Cuenta desbloqueada manualmente"
        )
        
        assert result == 123  # ID retornado por mock_db
        # Verificar que se ejecutó el query
        mock_db.get_cursor.return_value.__enter__.return_value.execute.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.datetime')
    @patch('zoneinfo.ZoneInfo')  # Parchear ZoneInfo para evitar error en Windows
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_log_action_with_localhost_gets_public_ip(self, mock_httpx_client, mock_zoneinfo, mock_datetime, mock_db):
        """Test: Cuando IP es localhost, intenta obtener IP pública"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock datetime.now() para retornar objeto con método replace
        fixed_time = datetime(2026, 2, 5, 10, 30, 0)
        mock_now_result = Mock()
        mock_now_result.replace.return_value = fixed_time
        mock_datetime.now.return_value = mock_now_result
        
        # Mock ipify.org para obtener IP pública
        mock_ipify = Mock()
        mock_ipify.status_code = 200
        mock_ipify.text = "200.50.100.150"
        
        # Mock ip-api.com
        mock_ipapi = Mock()
        mock_ipapi.status_code = 200
        mock_ipapi.json.return_value = {
            "status": "success",
            "country": "Ecuador",
            "city": "Quito",
            "regionName": "Pichincha"
        }
        
        mock_client = AsyncMock()
        mock_client.get.side_effect = [mock_ipify, mock_ipapi]
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        request = Mock()
        request.headers = {"User-Agent": "Test"}
        request.client = Mock()
        request.client.host = "127.0.0.1"  # Localhost
        
        result = await service.log_action(
            request=request,
            action="test_action",
            admin_id=1,
            admin_username="admin"
        )
        
        assert result == 123
    
    @pytest.mark.asyncio
    async def test_log_action_handles_exception(self, mock_db):
        """Test: Maneja excepciones y retorna False"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Forzar excepción en cursor.execute
        mock_db.get_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("DB Error")
        
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        result = await service.log_action(
            request=request,
            action="test",
            admin_id=1,
            admin_username="admin"
        )
        
        assert result is False


class TestAuditServiceLogFailedAttempt:
    """Tests para log_failed_attempt"""
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.datetime')
    @patch('zoneinfo.ZoneInfo')  # Parchear ZoneInfo para evitar error en Windows
    @patch('app.infrastructure.services.audit_service.httpx.AsyncClient')
    async def test_log_failed_attempt_success(self, mock_httpx_client, mock_zoneinfo, mock_datetime, mock_db):
        """Test: Registra intento fallido exitosamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock datetime.now() para retornar objeto con método replace
        fixed_time = datetime(2026, 2, 5, 10, 30, 0)
        mock_now_result = Mock()
        mock_now_result.replace.return_value = fixed_time
        mock_datetime.now.return_value = mock_now_result
        
        # Mock geolocalización
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "country": "Ecuador",
            "city": "Guayaquil",
            "regionName": "Guayas"
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        request = Mock()
        request.headers = {"User-Agent": "Hacker Tool"}
        request.client = Mock()
        request.client.host = "203.0.113.99"
        
        result = await service.log_failed_attempt(
            request=request,
            username="attacker",
            reason="invalid_password",
            details="3 intentos consecutivos"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.services.audit_service.datetime')
    @patch('zoneinfo.ZoneInfo')  # Parchear ZoneInfo para evitar error en Windows
    async def test_log_failed_attempt_handles_all_errors(self, mock_zoneinfo, mock_datetime, mock_db):
        """Test: Maneja errores en IP, User-Agent y ubicación"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock datetime.now() para retornar objeto con método replace
        fixed_time = datetime(2026, 2, 5, 10, 30, 0)
        mock_now_result = Mock()
        mock_now_result.replace.return_value = fixed_time
        mock_datetime.now.return_value = mock_now_result
        
        # Request que lanza excepciones
        request = Mock()
        request.headers.get.side_effect = Exception("Header error")
        request.client = None
        
        result = await service.log_failed_attempt(
            request=request,
            username="test",
            reason="test",
            details="test"
        )
        
        # Debe continuar y registrar con valores por defecto
        assert result is True


class TestAuditServiceGetLogs:
    """Tests para get_logs - consulta de registros"""
    
    def test_get_logs_success(self, mock_db):
        """Test: Obtiene logs exitosamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        # Mock datos de retorno
        mock_db.get_cursor.return_value.__enter__.return_value.fetchall.return_value = [
            (1, "unlock_user", 1, "admin", 5, "john", "Test details", 
             "192.168.1.1", "Mozilla", "Ecuador", "Quito", "Pichincha", datetime.now()),
            (2, "delete_user", 1, "admin", 6, "jane", "Deleted inactive",
             "192.168.1.2", "Chrome", "Ecuador", "Guayaquil", "Guayas", datetime.now())
        ]
        
        logs = service.get_logs(limit=50, offset=0)
        
        assert len(logs) == 2
        assert logs[0].action == "unlock_user"
        assert logs[1].action == "delete_user"
    
    def test_get_logs_handles_exception(self, mock_db):
        """Test: Retorna lista vacía cuando hay error"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        mock_db.get_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("Query error")
        
        logs = service.get_logs()
        
        assert logs == []


class TestAuditServiceGetLogsCount:
    """Tests para get_logs_count"""
    
    def test_get_logs_count_success(self, mock_db):
        """Test: Obtiene conteo exitosamente"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        mock_db.get_cursor.return_value.__enter__.return_value.fetchone.return_value = (42,)
        
        count = service.get_logs_count()
        
        assert count == 42
    
    def test_get_logs_count_handles_exception(self, mock_db):
        """Test: Retorna 0 cuando hay error"""
        service = AuditService.__new__(AuditService)
        service._db = mock_db
        
        mock_db.get_cursor.return_value.__enter__.return_value.execute.side_effect = Exception("Error")
        
        count = service.get_logs_count()
        
        assert count == 0


class TestAuditServiceSingleton:
    """Tests para patrón singleton get_audit_service"""
    
    @patch('app.infrastructure.services.audit_service.get_db')
    def test_get_audit_service_returns_singleton(self, mock_get_db):
        """Test: get_audit_service retorna la misma instancia"""
        mock_get_db.return_value = Mock()
        
        service1 = get_audit_service()
        service2 = get_audit_service()
        
        assert service1 is service2
