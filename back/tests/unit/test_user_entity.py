"""
Login Seguro - Tests Unitarios: Entidad User
Tests para la entidad de dominio User
"""
import pytest
from datetime import datetime, timedelta
import json

from app.domain.entities.user import User, UserRole


class TestUserEntity:
    """Tests para la entidad User"""
    
    def test_user_creation_default_values(self):
        """Test que un usuario se crea con valores por defecto correctos"""
        user = User()
        
        assert user.id is None
        assert user.username == ""
        assert user.email is None
        assert user.password_hash == ""
        assert user.face_encoding is None
        assert user.face_registered is False
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.role == UserRole.USER
        assert user.requires_password_reset is False
        assert user.backup_code_hash is None
        assert user.backup_code_encrypted is None
        assert user.active_session_token is None
    
    def test_user_creation_with_values(self, sample_user):
        """Test que un usuario se crea con valores específicos"""
        assert sample_user.id == 1
        assert sample_user.username == "testuser"
        assert sample_user.email == "test@example.com"
        assert sample_user.role == UserRole.USER
    
    def test_user_is_locked_when_locked_until_is_future(self):
        """Test que is_locked retorna True cuando locked_until está en el futuro"""
        user = User(
            username="test",
            locked_until=datetime.now() + timedelta(minutes=15)
        )
        
        assert user.is_locked() is True
    
    def test_user_is_not_locked_when_locked_until_is_past(self):
        """Test que is_locked retorna False cuando locked_until está en el pasado"""
        user = User(
            username="test",
            locked_until=datetime.now() - timedelta(minutes=15)
        )
        
        assert user.is_locked() is False
    
    def test_user_is_not_locked_when_locked_until_is_none(self):
        """Test que is_locked retorna False cuando locked_until es None"""
        user = User(username="test", locked_until=None)
        
        assert user.is_locked() is False
    
    def test_user_is_permanently_locked(self):
        """Test que is_permanently_locked detecta bloqueos permanentes"""
        user = User(
            username="test",
            locked_until=datetime.now() + timedelta(days=400)  # Más de 1 año
        )
        
        assert user.is_permanently_locked() is True
    
    def test_user_is_not_permanently_locked_short_lockout(self):
        """Test que bloqueos cortos no son permanentes"""
        user = User(
            username="test",
            locked_until=datetime.now() + timedelta(minutes=15)
        )
        
        assert user.is_permanently_locked() is False
    
    def test_user_is_admin_returns_true_for_admin(self, admin_user):
        """Test que is_admin retorna True para usuarios admin"""
        assert admin_user.is_admin() is True
    
    def test_user_is_admin_returns_false_for_regular_user(self, sample_user):
        """Test que is_admin retorna False para usuarios normales"""
        assert sample_user.is_admin() is False
    
    def test_user_is_auditor(self):
        """Test que is_auditor funciona correctamente"""
        auditor = User(username="auditor", role=UserRole.AUDITOR)
        regular_user = User(username="regular", role=UserRole.USER)
        
        assert auditor.is_auditor() is True
        assert regular_user.is_auditor() is False
    
    def test_has_backup_code_returns_true_when_hash_exists(self):
        """Test que has_backup_code retorna True cuando hay hash"""
        user = User(
            username="test",
            backup_code_hash="$2b$12$somehashvalue"
        )
        
        assert user.has_backup_code() is True
    
    def test_has_backup_code_returns_false_when_hash_is_none(self):
        """Test que has_backup_code retorna False cuando hash es None"""
        user = User(username="test", backup_code_hash=None)
        
        assert user.has_backup_code() is False
    
    def test_has_backup_code_returns_false_when_hash_is_empty(self):
        """Test que has_backup_code retorna False cuando hash está vacío"""
        user = User(username="test", backup_code_hash="")
        
        assert user.has_backup_code() is False
    
    def test_get_face_encoding_list_valid_json(self):
        """Test que get_face_encoding_list parsea JSON correctamente"""
        encoding = [0.1, 0.2, 0.3, 0.4, 0.5]
        user = User(
            username="test",
            face_encoding=json.dumps(encoding)
        )
        
        result = user.get_face_encoding_list()
        
        assert result == encoding
    
    def test_get_face_encoding_list_returns_none_when_no_encoding(self):
        """Test que get_face_encoding_list retorna None sin encoding"""
        user = User(username="test", face_encoding=None)
        
        assert user.get_face_encoding_list() is None
    
    def test_get_face_encoding_list_returns_none_on_invalid_json(self):
        """Test que get_face_encoding_list retorna None con JSON inválido"""
        user = User(username="test", face_encoding="invalid json")
        
        assert user.get_face_encoding_list() is None
    
    def test_set_face_encoding_from_list(self):
        """Test que set_face_encoding_from_list guarda correctamente"""
        user = User(username="test")
        encoding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        user.set_face_encoding_from_list(encoding)
        
        assert user.face_encoding == json.dumps(encoding)
        assert user.face_registered is True
    
    def test_increment_failed_attempts(self):
        """Test que increment_failed_attempts incrementa correctamente"""
        user = User(username="test", failed_login_attempts=2)
        
        user.increment_failed_attempts()
        
        assert user.failed_login_attempts == 3
    
    def test_reset_failed_attempts(self):
        """Test que reset_failed_attempts resetea correctamente"""
        user = User(
            username="test",
            failed_login_attempts=5,
            locked_until=datetime.now() + timedelta(minutes=15)
        )
        
        user.reset_failed_attempts()
        
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestUserRole:
    """Tests para el enum UserRole"""
    
    def test_user_role_values(self):
        """Test que los roles tienen los valores correctos"""
        assert UserRole.USER.value == "user"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.AUDITOR.value == "auditor"
    
    def test_user_role_is_string_enum(self):
        """Test que UserRole es un string enum"""
        assert isinstance(UserRole.USER, str)
        assert UserRole.USER == "user"
