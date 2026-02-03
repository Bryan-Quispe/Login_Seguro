"""
Login Seguro - Tests Unitarios: DTOs (Data Transfer Objects)
Tests para validación de DTOs con Pydantic
"""
import pytest
from pydantic import ValidationError

from app.application.dto.user_dto import (
    RegisterRequest, LoginRequest,
    FaceRegisterRequest, FaceVerifyRequest,
    UserResponse, TokenResponse, MessageResponse
)


class TestRegisterRequest:
    """Tests para RegisterRequest DTO"""
    
    def test_valid_register_request(self):
        """Test registro válido con todos los campos"""
        request = RegisterRequest(
            username="validuser",
            password="Secure@Password123",
            email="user@example.com"
        )
        
        assert request.username == "validuser"
        assert request.password == "Secure@Password123"
        assert request.email == "user@example.com"
    
    def test_valid_register_request_without_email(self):
        """Test registro válido sin email (es opcional)"""
        request = RegisterRequest(
            username="validuser",
            password="Secure@Password123"
        )
        
        assert request.username == "validuser"
        assert request.email is None
    
    def test_username_too_short(self):
        """Test que username muy corto falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="ab",  # Menos de 3 caracteres
                password="Secure@Password123"
            )
        
        errors = exc_info.value.errors()
        assert any("username" in str(e.get("loc", "")) for e in errors)
    
    def test_username_too_long(self):
        """Test que username muy largo falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="a" * 51,  # Más de 50 caracteres
                password="Secure@Password123"
            )
        
        errors = exc_info.value.errors()
        assert any("username" in str(e.get("loc", "")) for e in errors)
    
    def test_username_with_special_characters_fails(self):
        """Test que username con caracteres especiales falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="user@name!",  # Caracteres no permitidos
                password="Secure@Password123"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_username_with_sql_keyword_fails(self):
        """Test que username con palabra SQL reservada falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="select",
                password="Secure@Password123"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_username_sanitizes_html(self):
        """Test que username sanitiza HTML"""
        # El validador debe limpiar el HTML
        with pytest.raises(ValidationError):
            RegisterRequest(
                username="<script>alert('xss')</script>user",
                password="Secure@Password123"
            )
    
    def test_password_too_short(self):
        """Test que contraseña muy corta falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="validuser",
                password="Short1!"  # Menos de 8 caracteres
            )
        
        errors = exc_info.value.errors()
        assert any("password" in str(e.get("loc", "")) for e in errors)
    
    def test_password_without_uppercase_fails(self):
        """Test que contraseña sin mayúscula falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="validuser",
                password="password123!"  # Sin mayúscula
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_password_without_lowercase_fails(self):
        """Test que contraseña sin minúscula falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="validuser",
                password="PASSWORD123!"  # Sin minúscula
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_password_without_number_fails(self):
        """Test que contraseña sin número falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="validuser",
                password="Password!@#"  # Sin número
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_password_without_special_char_fails(self):
        """Test que contraseña sin carácter especial falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="validuser",
                password="Password123"  # Sin carácter especial
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_invalid_email_format(self):
        """Test que email con formato inválido falla"""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                username="validuser",
                password="Secure@Password123",
                email="invalid-email"  # Formato inválido
            )
        
        errors = exc_info.value.errors()
        assert any("email" in str(e.get("loc", "")) for e in errors)


class TestLoginRequest:
    """Tests para LoginRequest DTO"""
    
    def test_valid_login_request(self):
        """Test login válido"""
        request = LoginRequest(
            username="testuser",
            password="password123"
        )
        
        assert request.username == "testuser"
        assert request.password == "password123"
    
    def test_empty_username_fails(self):
        """Test que username vacío falla"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(
                username="",
                password="password123"
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_empty_password_fails(self):
        """Test que password vacío falla"""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(
                username="testuser",
                password=""
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_username_sanitized_from_html(self):
        """Test que username es sanitizado de HTML/XSS"""
        request = LoginRequest(
            username="<script>test</script>",
            password="password123"
        )
        
        # El sanitizador debe haber limpiado el HTML
        assert "<script>" not in request.username


class TestFaceRegisterRequest:
    """Tests para FaceRegisterRequest DTO"""
    
    def test_valid_jpeg_image(self):
        """Test imagen JPEG válida"""
        request = FaceRegisterRequest(
            image_data="data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        )
        
        assert request.image_data.startswith("data:image/jpeg")
    
    def test_valid_png_image(self):
        """Test imagen PNG válida"""
        request = FaceRegisterRequest(
            image_data="data:image/png;base64,iVBORw0KGgo..."
        )
        
        assert request.image_data.startswith("data:image/png")
    
    def test_invalid_image_format_fails(self):
        """Test que formato de imagen inválido falla"""
        with pytest.raises(ValidationError) as exc_info:
            FaceRegisterRequest(
                image_data="data:image/gif;base64,R0lGODlh..."  # GIF no soportado
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_image_too_large_fails(self):
        """Test que imagen muy grande falla"""
        large_data = "data:image/jpeg;base64," + "A" * 7_000_001  # > 7MB
        
        with pytest.raises(ValidationError) as exc_info:
            FaceRegisterRequest(image_data=large_data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_raw_base64_accepted(self):
        """Test que base64 sin prefijo MIME es aceptado"""
        request = FaceRegisterRequest(
            image_data="/9j/4AAQSkZJRgABAQAAAQABAAD..."
        )
        
        assert request.image_data.startswith("/9j/")


class TestFaceVerifyRequest:
    """Tests para FaceVerifyRequest DTO"""
    
    def test_valid_verify_request(self):
        """Test request de verificación válido"""
        request = FaceVerifyRequest(
            image_data="data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        )
        
        assert request.image_data is not None
    
    def test_invalid_format_fails(self):
        """Test que formato inválido falla"""
        with pytest.raises(ValidationError):
            FaceVerifyRequest(
                image_data="data:image/bmp;base64,Qk..."  # BMP no soportado
            )


class TestUserResponse:
    """Tests para UserResponse DTO"""
    
    def test_user_response_creation(self):
        """Test creación de UserResponse"""
        response = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            role="user",
            face_registered=True
        )
        
        assert response.id == 1
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.role == "user"
        assert response.face_registered is True
    
    def test_user_response_default_role(self):
        """Test que rol por defecto es 'user'"""
        response = UserResponse(
            id=1,
            username="testuser",
            face_registered=False
        )
        
        assert response.role == "user"
    
    def test_user_response_optional_email(self):
        """Test que email es opcional"""
        response = UserResponse(
            id=1,
            username="testuser",
            face_registered=False
        )
        
        assert response.email is None


class TestTokenResponse:
    """Tests para TokenResponse DTO"""
    
    def test_token_response_creation(self):
        """Test creación de TokenResponse"""
        user_response = UserResponse(
            id=1,
            username="testuser",
            face_registered=True
        )
        
        response = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIs...",
            expires_in=1800,
            user=user_response
        )
        
        assert response.access_token == "eyJhbGciOiJIUzI1NiIs..."
        assert response.token_type == "bearer"
        assert response.expires_in == 1800
        assert response.user.username == "testuser"
    
    def test_token_response_defaults(self):
        """Test valores por defecto de TokenResponse"""
        user_response = UserResponse(
            id=1,
            username="testuser",
            face_registered=False
        )
        
        response = TokenResponse(
            access_token="token",
            expires_in=1800,
            user=user_response
        )
        
        assert response.token_type == "bearer"
        assert response.requires_face_registration is False
        assert response.requires_face_verification is False
        assert response.requires_password_reset is False


class TestMessageResponse:
    """Tests para MessageResponse DTO"""
    
    def test_message_response_success(self):
        """Test respuesta de éxito"""
        response = MessageResponse(
            success=True,
            message="Operación exitosa",
            data={"key": "value"}
        )
        
        assert response.success is True
        assert response.message == "Operación exitosa"
        assert response.data == {"key": "value"}
    
    def test_message_response_failure(self):
        """Test respuesta de error"""
        response = MessageResponse(
            success=False,
            message="Error en la operación"
        )
        
        assert response.success is False
        assert response.message == "Error en la operación"
        assert response.data is None
