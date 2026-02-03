"""
Login Seguro - Tests Unitarios: Backup Code Service
Tests para el servicio de códigos de respaldo
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import bcrypt

from app.application.use_cases.backup_code_service import BackupCodeService, get_encryption_key
from app.domain.entities.user import User


class TestGetEncryptionKey:
    """Tests para get_encryption_key"""
    
    @patch('app.application.use_cases.backup_code_service.get_settings')
    def test_returns_bytes(self, mock_settings):
        """Test que retorna bytes"""
        settings_instance = MagicMock()
        settings_instance.JWT_SECRET_KEY = "test-secret-key"
        mock_settings.return_value = settings_instance
        
        key = get_encryption_key()
        
        assert isinstance(key, bytes)
    
    @patch('app.application.use_cases.backup_code_service.get_settings')
    def test_key_is_32_bytes_base64_encoded(self, mock_settings):
        """Test que la clave tiene el formato correcto para Fernet"""
        settings_instance = MagicMock()
        settings_instance.JWT_SECRET_KEY = "test-secret-key"
        mock_settings.return_value = settings_instance
        
        key = get_encryption_key()
        
        # Fernet requiere 32 bytes codificados en base64 (44 caracteres)
        assert len(key) == 44
    
    @patch('app.application.use_cases.backup_code_service.get_settings')
    def test_same_secret_produces_same_key(self, mock_settings):
        """Test que el mismo secret produce la misma clave"""
        settings_instance = MagicMock()
        settings_instance.JWT_SECRET_KEY = "consistent-secret"
        mock_settings.return_value = settings_instance
        
        key1 = get_encryption_key()
        key2 = get_encryption_key()
        
        assert key1 == key2


class TestBackupCodeService:
    """Tests para BackupCodeService"""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Mock del repositorio de usuarios"""
        return Mock()
    
    @pytest.fixture
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def backup_service(self, mock_encryption_key, mock_user_repo):
        """Fixture para crear instancia del servicio"""
        # Generar una clave Fernet válida para testing
        import base64
        test_key = base64.urlsafe_b64encode(b'0' * 32)
        mock_encryption_key.return_value = test_key
        
        return BackupCodeService(mock_user_repo)
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_generate_backup_code_user_not_found(self, mock_encryption_key, mock_user_repo):
        """Test que retorna None si usuario no existe"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        mock_user_repo.find_by_id.return_value = None
        service = BackupCodeService(mock_user_repo)
        
        result = service.generate_backup_code(999)
        
        assert result is None
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_generate_backup_code_returns_8_chars(self, mock_encryption_key, mock_user_repo):
        """Test que genera código de 8 caracteres"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        user = User(id=1, username="testuser")
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.update.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        code = service.generate_backup_code(1)
        
        assert code is not None
        assert len(code) == 8
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_generate_backup_code_is_uppercase_hex(self, mock_encryption_key, mock_user_repo):
        """Test que el código es hexadecimal en mayúsculas"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        user = User(id=1, username="testuser")
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.update.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        code = service.generate_backup_code(1)
        
        assert code.isupper()
        # Debe ser hexadecimal válido
        int(code, 16)  # No debe lanzar excepción
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_generate_backup_code_updates_user(self, mock_encryption_key, mock_user_repo):
        """Test que actualiza el usuario con el hash"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        user = User(id=1, username="testuser")
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.update.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        service.generate_backup_code(1)
        
        mock_user_repo.update.assert_called_once()
        updated_user = mock_user_repo.update.call_args[0][0]
        assert updated_user.backup_code_hash is not None
        assert updated_user.backup_code_hash.startswith("$2b$")
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_generate_backup_code_stores_encrypted_code(self, mock_encryption_key, mock_user_repo):
        """Test que guarda el código cifrado"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        user = User(id=1, username="testuser")
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.update.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        service.generate_backup_code(1)
        
        updated_user = mock_user_repo.update.call_args[0][0]
        assert updated_user.backup_code_encrypted is not None
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_get_existing_code_user_not_found(self, mock_encryption_key, mock_user_repo):
        """Test que retorna None si usuario no existe"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        mock_user_repo.find_by_id.return_value = None
        service = BackupCodeService(mock_user_repo)
        
        result = service.get_existing_code(999)
        
        assert result is None
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_get_existing_code_no_encrypted_code(self, mock_encryption_key, mock_user_repo):
        """Test que retorna None si no hay código cifrado"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        user = User(id=1, username="testuser", backup_code_encrypted=None)
        mock_user_repo.find_by_id.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        result = service.get_existing_code(1)
        
        assert result is None
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_get_existing_code_decrypts_correctly(self, mock_encryption_key, mock_user_repo):
        """Test que descifra correctamente el código existente"""
        import base64
        test_key = base64.urlsafe_b64encode(b'0' * 32)
        mock_encryption_key.return_value = test_key
        
        user = User(id=1, username="testuser")
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.update.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        
        # Generar código
        original_code = service.generate_backup_code(1)
        
        # Actualizar el mock para retornar el usuario con código cifrado
        updated_user = mock_user_repo.update.call_args[0][0]
        mock_user_repo.find_by_id.return_value = updated_user
        
        # Obtener código existente
        retrieved_code = service.get_existing_code(1)
        
        assert retrieved_code == original_code
    
    @patch('app.application.use_cases.backup_code_service.get_encryption_key')
    def test_generate_unique_codes(self, mock_encryption_key, mock_user_repo):
        """Test que genera códigos únicos"""
        import base64
        mock_encryption_key.return_value = base64.urlsafe_b64encode(b'0' * 32)
        
        user = User(id=1, username="testuser")
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo.update.return_value = user
        
        service = BackupCodeService(mock_user_repo)
        
        codes = set()
        for _ in range(10):
            code = service.generate_backup_code(1)
            codes.add(code)
        
        # Todos deberían ser únicos
        assert len(codes) == 10
