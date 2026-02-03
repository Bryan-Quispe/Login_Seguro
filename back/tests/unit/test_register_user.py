"""
Login Seguro - Tests Unitarios: Caso de Uso Register User
Tests para el caso de uso de registro de usuarios
"""
import pytest
from unittest.mock import Mock, patch

from app.application.use_cases.register_user import (
    RegisterUserUseCase, 
    hash_password, 
    verify_password
)
from app.application.dto.user_dto import RegisterRequest
from app.domain.entities.user import User


class TestHashPassword:
    """Tests para la función hash_password"""
    
    def test_hash_password_returns_different_from_plain(self):
        """Test que el hash es diferente al texto plano"""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        assert hashed != password
    
    def test_hash_password_starts_with_bcrypt_prefix(self):
        """Test que el hash tiene formato bcrypt"""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        assert hashed.startswith("$2b$")
    
    def test_hash_password_different_hashes_for_same_password(self):
        """Test que cada hash es único (por el salt)"""
        password = "MySecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
    
    def test_hash_password_truncates_to_72_bytes(self):
        """Test que contraseñas largas son truncadas a 72 bytes"""
        long_password = "A" * 100  # Más de 72 bytes
        hashed = hash_password(long_password)
        
        # No debe fallar y debe generar un hash válido
        assert hashed.startswith("$2b$")


class TestVerifyPassword:
    """Tests para la función verify_password"""
    
    def test_verify_password_correct(self):
        """Test que verificación correcta retorna True"""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test que contraseña incorrecta retorna False"""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test que la verificación es case-sensitive"""
        password = "MySecurePassword123!"
        hashed = hash_password(password)
        
        assert verify_password("mysecurepassword123!", hashed) is False


class TestRegisterUserUseCase:
    """Tests para RegisterUserUseCase"""
    
    def test_successful_registration(self, mock_user_repository, valid_register_request):
        """Test registro exitoso de usuario"""
        # Arrange
        mock_user_repository.find_by_username.return_value = None
        mock_user_repository.find_by_email.return_value = None
        
        created_user = User(
            id=1,
            username=valid_register_request.username,
            email=valid_register_request.email,
            face_registered=False
        )
        mock_user_repository.create.return_value = created_user
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        success, message, user_response = use_case.execute(valid_register_request)
        
        # Assert
        assert success is True
        assert "exitosamente" in message.lower()
        assert user_response is not None
        assert user_response.username == valid_register_request.username
        mock_user_repository.create.assert_called_once()
    
    def test_registration_fails_username_exists(self, mock_user_repository, valid_register_request):
        """Test que registro falla si username ya existe"""
        # Arrange
        existing_user = User(
            id=1,
            username=valid_register_request.username,
            email="other@example.com"
        )
        mock_user_repository.find_by_username.return_value = existing_user
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        success, message, user_response = use_case.execute(valid_register_request)
        
        # Assert
        assert success is False
        assert "ya está registrado" in message
        assert user_response is None
        mock_user_repository.create.assert_not_called()
    
    def test_registration_fails_email_exists(self, mock_user_repository, valid_register_request):
        """Test que registro falla si email ya existe"""
        # Arrange
        mock_user_repository.find_by_username.return_value = None
        
        existing_user = User(
            id=2,
            username="otheruser",
            email=valid_register_request.email
        )
        mock_user_repository.find_by_email.return_value = existing_user
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        success, message, user_response = use_case.execute(valid_register_request)
        
        # Assert
        assert success is False
        assert "email ya está registrado" in message.lower()
        assert user_response is None
    
    def test_registration_without_email(self, mock_user_repository):
        """Test registro sin email (es opcional)"""
        # Arrange
        request = RegisterRequest(
            username="newuser",
            password="Secure@Password123"
            # Sin email
        )
        
        mock_user_repository.find_by_username.return_value = None
        
        created_user = User(
            id=1,
            username=request.username,
            email=None,
            face_registered=False
        )
        mock_user_repository.create.return_value = created_user
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        success, message, user_response = use_case.execute(request)
        
        # Assert
        assert success is True
        mock_user_repository.find_by_email.assert_not_called()
    
    def test_registration_handles_repository_exception(self, mock_user_repository, valid_register_request):
        """Test que maneja excepciones del repositorio"""
        # Arrange
        mock_user_repository.find_by_username.return_value = None
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.create.side_effect = Exception("Database error")
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        success, message, user_response = use_case.execute(valid_register_request)
        
        # Assert
        assert success is False
        assert "error" in message.lower()
        assert user_response is None
    
    def test_password_is_hashed_before_storage(self, mock_user_repository, valid_register_request):
        """Test que la contraseña se hashea antes de guardar"""
        # Arrange
        mock_user_repository.find_by_username.return_value = None
        mock_user_repository.find_by_email.return_value = None
        
        captured_user = None
        def capture_user(user):
            nonlocal captured_user
            captured_user = user
            user.id = 1
            return user
        
        mock_user_repository.create.side_effect = capture_user
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        use_case.execute(valid_register_request)
        
        # Assert
        assert captured_user is not None
        assert captured_user.password_hash != valid_register_request.password
        assert captured_user.password_hash.startswith("$2b$")
    
    def test_user_created_with_correct_defaults(self, mock_user_repository, valid_register_request):
        """Test que el usuario se crea con valores por defecto correctos"""
        # Arrange
        mock_user_repository.find_by_username.return_value = None
        mock_user_repository.find_by_email.return_value = None
        
        captured_user = None
        def capture_user(user):
            nonlocal captured_user
            captured_user = user
            user.id = 1
            return user
        
        mock_user_repository.create.side_effect = capture_user
        
        use_case = RegisterUserUseCase(mock_user_repository)
        
        # Act
        use_case.execute(valid_register_request)
        
        # Assert
        assert captured_user.face_registered is False
        assert captured_user.username == valid_register_request.username
        assert captured_user.email == valid_register_request.email
