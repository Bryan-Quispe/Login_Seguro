"""
Login Seguro - Configuración de Pytest (Fixtures compartidas)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from typing import Optional, List

from app.domain.entities.user import User, UserRole
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.interfaces.face_service import IFaceService
from app.application.dto.user_dto import (
    RegisterRequest, LoginRequest, 
    FaceRegisterRequest, FaceVerifyRequest,
    UserResponse, TokenResponse
)


# ============= USER FIXTURES =============

@pytest.fixture
def sample_user() -> User:
    """Usuario de ejemplo para tests"""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.NRZ8Z1v4W1G1WdS",  # hash de "Test@123"
        face_encoding=None,
        face_registered=False,
        failed_login_attempts=0,
        locked_until=None,
        role=UserRole.USER,
        requires_password_reset=False,
        backup_code_hash=None,
        backup_code_encrypted=None,
        active_session_token=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def admin_user() -> User:
    """Usuario admin de ejemplo"""
    return User(
        id=2,
        username="adminuser",
        email="admin@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.NRZ8Z1v4W1G1WdS",
        face_encoding='[0.1, 0.2, 0.3]',
        face_registered=True,
        failed_login_attempts=0,
        locked_until=None,
        role=UserRole.ADMIN,
        requires_password_reset=False,
        backup_code_hash="$2b$12$somehash",
        backup_code_encrypted="encrypted_code",
        active_session_token=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def locked_user() -> User:
    """Usuario bloqueado de ejemplo"""
    return User(
        id=3,
        username="lockeduser",
        email="locked@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.NRZ8Z1v4W1G1WdS",
        face_encoding=None,
        face_registered=False,
        failed_login_attempts=5,
        locked_until=datetime.now() + timedelta(minutes=15),
        role=UserRole.USER,
        requires_password_reset=False,
        backup_code_hash=None,
        backup_code_encrypted=None,
        active_session_token=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def user_with_active_session() -> User:
    """Usuario con sesión activa"""
    return User(
        id=4,
        username="activeuser",
        email="active@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.NRZ8Z1v4W1G1WdS",
        face_encoding='[0.1, 0.2, 0.3]',
        face_registered=True,
        failed_login_attempts=0,
        locked_until=None,
        role=UserRole.USER,
        requires_password_reset=False,
        backup_code_hash=None,
        backup_code_encrypted=None,
        active_session_token="existing_session_token_123",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def user_requiring_password_reset() -> User:
    """Usuario que requiere cambio de contraseña"""
    return User(
        id=5,
        username="resetuser",
        email="reset@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X.NRZ8Z1v4W1G1WdS",
        face_encoding=None,
        face_registered=False,
        failed_login_attempts=0,
        locked_until=None,
        role=UserRole.USER,
        requires_password_reset=True,
        backup_code_hash=None,
        backup_code_encrypted=None,
        active_session_token=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


# ============= MOCK REPOSITORIES =============

@pytest.fixture
def mock_user_repository() -> Mock:
    """Mock del repositorio de usuarios"""
    repo = Mock(spec=IUserRepository)
    repo.create = Mock(return_value=None)
    repo.find_by_id = Mock(return_value=None)
    repo.find_by_username = Mock(return_value=None)
    repo.find_by_email = Mock(return_value=None)
    repo.update = Mock(return_value=None)
    repo.update_face_encoding = Mock(return_value=True)
    repo.update_failed_attempts = Mock(return_value=True)
    repo.delete = Mock(return_value=True)
    return repo


@pytest.fixture
def mock_face_service() -> Mock:
    """Mock del servicio de reconocimiento facial"""
    service = Mock(spec=IFaceService)
    service.extract_face_encoding = Mock(return_value=(True, [0.1] * 128, "Encoding extraído"))
    service.verify_face = Mock(return_value=(True, 0.3, "Verificación exitosa"))
    service.detect_spoofing = Mock(return_value=(True, 0.95, "Rostro real"))
    service.verify_face_with_antispoofing = Mock(return_value=(
        True, 
        {'is_real': True, 'distance': 0.3, 'spoof_confidence': 0.95}, 
        "Verificación exitosa"
    ))
    return service


# ============= DTO FIXTURES =============

@pytest.fixture
def valid_register_request() -> RegisterRequest:
    """Request de registro válido"""
    return RegisterRequest(
        username="newuser",
        password="Secure@Password123",
        email="newuser@example.com"
    )


@pytest.fixture
def valid_login_request() -> LoginRequest:
    """Request de login válido"""
    return LoginRequest(
        username="testuser",
        password="Test@123"
    )


@pytest.fixture
def valid_face_verify_request() -> FaceVerifyRequest:
    """Request de verificación facial válido"""
    return FaceVerifyRequest(
        image_data="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQ..."
    )


@pytest.fixture
def valid_face_register_request() -> FaceRegisterRequest:
    """Request de registro facial válido"""
    return FaceRegisterRequest(
        image_data="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQ..."
    )


# ============= TEST CLIENT FIXTURES =============

@pytest.fixture
def test_settings():
    """Settings para tests"""
    from app.config.settings import Settings
    return Settings(
        DATABASE_HOST="localhost",
        DATABASE_PORT=5432,
        DATABASE_NAME="test_db",
        DATABASE_USER="test_user",
        DATABASE_PASSWORD="test_password",
        JWT_SECRET_KEY="test-jwt-secret-key-for-testing-only",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        MAX_LOGIN_ATTEMPTS=3,
        LOCKOUT_DURATION_MINUTES=15
    )
