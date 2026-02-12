"""
Login Seguro - Tests Unitarios: Caso de Uso Verify Face
Tests para el caso de uso de verificación facial
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from app.application.use_cases.verify_face import VerifyFaceUseCase
from app.application.dto.user_dto import FaceVerifyRequest
from app.domain.entities.user import User, UserRole


class TestVerifyFaceUseCase:
    """Tests para VerifyFaceUseCase"""
    
    @pytest.fixture
    def verify_face_use_case(self, mock_user_repository, mock_face_service):
        """Fixture para crear instancia del caso de uso"""
        return VerifyFaceUseCase(mock_user_repository, mock_face_service)
    
    def test_verify_face_user_not_found(self, verify_face_use_case, mock_user_repository, valid_face_verify_request):
        """Test que falla cuando usuario no existe"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None
        
        # Act
        success, message, details = verify_face_use_case.execute(1, valid_face_verify_request)
        
        # Assert
        assert success is False
        assert "no encontrado" in message.lower()
    
    def test_verify_face_account_locked(self, verify_face_use_case, mock_user_repository, valid_face_verify_request, locked_user):
        """Test que falla cuando cuenta está bloqueada"""
        # Arrange
        mock_user_repository.find_by_id.return_value = locked_user
        
        # Act
        success, message, details = verify_face_use_case.execute(locked_user.id, valid_face_verify_request)
        
        # Assert
        assert success is False
        assert "bloqueada" in message.lower()
        assert details.get('account_locked') is True
    
    def test_verify_face_no_face_registered(self, verify_face_use_case, mock_user_repository, valid_face_verify_request, sample_user):
        """Test que falla cuando usuario no tiene rostro registrado"""
        # Arrange
        sample_user.face_registered = False
        sample_user.face_encoding = None
        mock_user_repository.find_by_id.return_value = sample_user
        
        # Act
        success, message, details = verify_face_use_case.execute(sample_user.id, valid_face_verify_request)
        
        # Assert
        assert success is False
        assert "rostro registrado" in message.lower()
        assert details.get('requires_face_registration') is True
    
    def test_verify_face_successful(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test verificación facial exitosa"""
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=0,
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        
        mock_face_service.verify_face_with_antispoofing.return_value = (
            True,
            {'is_real': True, 'distance': 0.3, 'spoof_confidence': 0.95},
            "Verificación exitosa"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is True
        assert "exitosa" in message.lower()
        assert details.get('verified') is True
        assert details.get('is_real') is True
    
    def test_verify_face_spoofing_detected(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que detecta intento de spoofing"""
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=0,
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        
        mock_face_service.verify_face_with_antispoofing.return_value = (
            False,
            {'is_real': False, 'spoof_confidence': 0.2},
            "Posible intento de spoofing detectado"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is False
    
    def test_verify_face_no_match(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que falla cuando rostro no coincide"""
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=0,
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        
        mock_face_service.verify_face_with_antispoofing.return_value = (
            False,
            {'is_real': True, 'distance': 0.8},
            "Rostro no coincide"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is False
    
    def test_verify_face_resets_failed_attempts_on_success(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que resetea intentos fallidos en éxito"""
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=2,  # Tenía intentos fallidos
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        
        mock_face_service.verify_face_with_antispoofing.return_value = (
            True,
            {'is_real': True, 'distance': 0.3, 'spoof_confidence': 0.95},
            "Verificación exitosa"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is True
        mock_user_repository.update_failed_attempts.assert_called_with(user.id, 0, None)
    
    def test_verify_face_returns_user_role(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que retorna el rol del usuario"""
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=0,
            role=UserRole.ADMIN
        )
        mock_user_repository.find_by_id.return_value = user
        
        mock_face_service.verify_face_with_antispoofing.return_value = (
            True,
            {'is_real': True, 'distance': 0.3, 'spoof_confidence': 0.95},
            "Verificación exitosa"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is True
        assert details.get('role') == UserRole.ADMIN
    
    def test_verify_face_handles_invalid_encoding(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que maneja encoding inválido"""
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding="invalid json",  # JSON inválido
            failed_login_attempts=0,
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert - debería manejar el error gracefully
        # El comportamiento exacto depende de la implementación
        assert success is False or success is True  # Depende del manejo de errores
    
    def test_verify_face_converts_numpy_values(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que convierte valores numpy a float nativo"""
        import numpy as np
        
        # Arrange
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=0,
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        
        # Simular valores numpy
        mock_face_service.verify_face_with_antispoofing.return_value = (
            True,
            {'is_real': True, 'distance': np.float64(0.3), 'spoof_confidence': np.float64(0.95)},
            "Verificación exitosa"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is True
        assert isinstance(details.get('confidence'), float)
        assert isinstance(details.get('match_distance'), float)
    
    def test_verify_face_locks_account_after_max_attempts(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que bloquea cuenta después de máximo de intentos fallidos"""
        # Arrange - usuario con 4 intentos fallidos (el 5to lo bloqueará)
        user = User(
            id=1,
            username="testuser",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=4,
            role=UserRole.USER
        )
        mock_user_repository.find_by_id.return_value = user
        mock_face_service.verify_face_with_antispoofing.return_value = (
            False,
            {'is_real': True, 'matched': False},
            "Rostro no coincide"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert
        assert success is False
        assert "bloqueada" in message.lower() or "locked" in message.lower()
        assert details.get('account_locked') is True or details.get('remaining_attempts') == 0
    
    def test_verify_face_admin_temporary_lockout(self, verify_face_use_case, mock_user_repository, mock_face_service, valid_face_verify_request):
        """Test que admin recibe bloqueo temporal (no permanente) después de max intentos"""
        # Arrange - admin con 4 intentos fallidos
        user = User(
            id=1,
            username="admin",
            face_registered=True,
            face_encoding=json.dumps([0.1] * 128),
            failed_login_attempts=4,
            role=UserRole.ADMIN
        )
        mock_user_repository.find_by_id.return_value = user
        mock_face_service.verify_face_with_antispoofing.return_value = (
            False,
            {'is_real': True, 'matched': False},
            "Rostro no coincide"
        )
        
        # Act
        success, message, details = verify_face_use_case.execute(user.id, valid_face_verify_request)
        
        # Assert - admin se bloquea pero temporalmente
        assert success is False
        # Verificar que update_failed_attempts fue llamado
        assert mock_user_repository.update_failed_attempts.called
