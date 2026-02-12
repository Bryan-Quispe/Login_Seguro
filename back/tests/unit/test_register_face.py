"""
Login Seguro - Tests Unitarios: RegisterFaceUseCase
Tests para el caso de uso de registro de rostro
"""
import pytest
from unittest.mock import Mock
import json

from app.application.use_cases.register_face import RegisterFaceUseCase
from app.application.dto.user_dto import FaceRegisterRequest
from app.domain.entities.user import User, UserRole


@pytest.fixture
def mock_user_repository():
    """Mock del repositorio de usuarios"""
    return Mock()


@pytest.fixture
def mock_face_service():
    """Mock del servicio de reconocimiento facial"""
    return Mock()


@pytest.fixture
def register_face_use_case(mock_user_repository, mock_face_service):
    """Instancia del caso de uso con mocks"""
    return RegisterFaceUseCase(mock_user_repository, mock_face_service)


@pytest.fixture
def sample_user():
    """Usuario de ejemplo sin rostro registrado"""
    return User(
        id=1,
        username="testuser",
        password_hash="hashed_password",
        face_registered=False,
        role=UserRole.USER
    )


@pytest.fixture
def sample_user_with_face():
    """Usuario de ejemplo con rostro ya registrado"""
    return User(
        id=2,
        username="faceuser",
        password_hash="hashed_password",
        face_registered=True,
        face_encoding="[1,2,3]",
        role=UserRole.USER
    )


@pytest.fixture
def valid_face_request():
    """Request válido con imagen en base64"""
    return FaceRegisterRequest(
        image_data="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
    )


class TestRegisterFaceSuccess:
    """Tests para registro exitoso de rostro"""
    
    def test_register_face_successfully(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe registrar el rostro exitosamente"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_face_service.extract_face_encoding.return_value = (
            True,
            [0.1, 0.2, 0.3, 0.4, 0.5],
            "Encoding extraído"
        )
        mock_user_repository.update_face_encoding.return_value = True
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is True
        assert "exitosamente" in message.lower()
        assert data["face_registered"] is True
        assert data["encoding_dimensions"] == 5
        assert data["role"] == UserRole.USER
        
        mock_face_service.extract_face_encoding.assert_called_once_with(
            valid_face_request.image_data
        )
        mock_user_repository.update_face_encoding.assert_called_once()
        
    def test_register_face_saves_encoding_as_json(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe guardar el encoding como JSON"""
        # Arrange
        encoding = [0.1, 0.2, 0.3]
        mock_user_repository.find_by_id.return_value = sample_user
        mock_face_service.extract_face_encoding.return_value = (
            True, encoding, "OK"
        )
        mock_user_repository.update_face_encoding.return_value = True
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is True
        call_args = mock_user_repository.update_face_encoding.call_args[0]
        saved_encoding = call_args[1]
        
        # Verificar que se guardó como JSON válido
        parsed = json.loads(saved_encoding)
        assert parsed == encoding


class TestRegisterFaceValidation:
    """Tests para validaciones del registro de rostro"""
    
    def test_register_face_user_not_found(
        self,
        register_face_use_case,
        mock_user_repository,
        valid_face_request
    ):
        """Debe fallar si el usuario no existe"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None
        
        # Act
        success, message, data = register_face_use_case.execute(999, valid_face_request)
        
        # Assert
        assert success is False
        assert "no encontrado" in message.lower()
        assert data == {}
        
    def test_register_face_already_registered(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user_with_face,
        valid_face_request
    ):
        """Debe fallar si el usuario ya tiene rostro registrado"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user_with_face
        
        # Act
        success, message, data = register_face_use_case.execute(
            2, valid_face_request
        )
        
        # Assert
        assert success is False
        assert "ya tiene" in message.lower()
        assert data == {}
        
        # No debe llamar al servicio facial
        mock_face_service.extract_face_encoding.assert_not_called()


class TestRegisterFaceFaceService:
    """Tests para interacción con el servicio de reconocimiento facial"""
    
    def test_register_face_extraction_fails(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe fallar si la extracción del encoding falla"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_face_service.extract_face_encoding.return_value = (
            False,
            None,
            "No se detectó rostro"
        )
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is False
        assert "no se detectó" in message.lower()
        assert data == {}
        
        # No debe intentar guardar
        mock_user_repository.update_face_encoding.assert_not_called()
        
    def test_register_face_spoofing_detected(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe fallar si se detecta spoofing"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_face_service.extract_face_encoding.return_value = (
            False,
            None,
            "Posible intento de spoofing"
        )
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is False
        assert "spoofing" in message.lower()
        assert data == {}


class TestRegisterFaceDatabaseOperations:
    """Tests para operaciones de base de datos"""
    
    def test_register_face_database_save_fails(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe fallar si no se puede guardar en la base de datos"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        mock_face_service.extract_face_encoding.return_value = (
            True, [0.1, 0.2], "OK"
        )
        mock_user_repository.update_face_encoding.return_value = False
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is False
        assert "error al guardar" in message.lower()
        assert data == {}


class TestRegisterFaceErrorHandling:
    """Tests para manejo de errores"""
    
    def test_register_face_handles_exception(
        self,
        register_face_use_case,
        mock_user_repository,
        valid_face_request
    ):
        """Debe manejar excepciones gracefully"""
        # Arrange
        mock_user_repository.find_by_id.side_effect = Exception("Database error")
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is False
        assert "error interno" in message.lower()
        assert data == {}
        
    def test_register_face_handles_json_encoding_error(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe manejar errores al convertir encoding a JSON"""
        # Arrange
        mock_user_repository.find_by_id.return_value = sample_user
        
        # Objeto que no se puede serializar a JSON
        class NotSerializable:
            pass
        
        mock_face_service.extract_face_encoding.return_value = (
            True, NotSerializable(), "OK"
        )
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is False
        assert "error interno" in message.lower()


class TestRegisterFaceResponseData:
    """Tests para los datos de respuesta"""
    
    def test_register_face_returns_user_role(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        valid_face_request
    ):
        """Debe incluir el rol del usuario en la respuesta"""
        # Arrange
        admin_user = User(
            id=1,
            username="admin",
            password_hash="hash",
            face_registered=False,
            role=UserRole.ADMIN
        )
        mock_user_repository.find_by_id.return_value = admin_user
        mock_face_service.extract_face_encoding.return_value = (
            True, [0.1], "OK"
        )
        mock_user_repository.update_face_encoding.return_value = True
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is True
        assert data["role"] == UserRole.ADMIN
        
    def test_register_face_returns_encoding_dimensions(
        self,
        register_face_use_case,
        mock_user_repository,
        mock_face_service,
        sample_user,
        valid_face_request
    ):
        """Debe retornar las dimensiones del encoding"""
        # Arrange
        encoding_128 = [0.0] * 128
        mock_user_repository.find_by_id.return_value = sample_user
        mock_face_service.extract_face_encoding.return_value = (
            True, encoding_128, "OK"
        )
        mock_user_repository.update_face_encoding.return_value = True
        
        # Act
        success, message, data = register_face_use_case.execute(1, valid_face_request)
        
        # Assert
        assert success is True
        assert data["encoding_dimensions"] == 128
