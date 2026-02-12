"""
Tests unitarios para UserRepositoryImpl
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from app.infrastructure.database.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.connection import DatabaseConnection
from app.domain.entities.user import User


@pytest.fixture
def mock_db():
    """Fixture que crea un mock de DatabaseConnection con cursor"""
    db = MagicMock(spec=DatabaseConnection)
    cursor = MagicMock()
    db.get_cursor.return_value.__enter__.return_value = cursor
    db.get_cursor.return_value.__exit__.return_value = None
    return db, cursor


class TestUserRepositoryCreate:
    """Tests para creación de usuarios"""
    
    def test_create_user_successfully(self, mock_db):
        """Debe crear usuario y retornar User con ID asignado"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # Simular que la BD retorna el ID 1
        cursor.fetchone.return_value = (1, datetime.now(), datetime.now())
        
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        result = repo.create(user)
        
        assert result.id == 1
        assert result.username == "testuser"
        cursor.execute.assert_called_once()


class TestUserRepositoryFindById:
    """Tests para búsqueda por ID"""
    
    def test_find_by_id_found(self, mock_db):
        """Debe retornar usuario cuando existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # Simular row completa (15 columnas)
        cursor.fetchone.return_value = (
            1, "testuser", "test@example.com", "hash", None, False,
            0, None, "user", False, None, None, None,
            datetime.now(), datetime.now()
        )
        
        result = repo.find_by_id(1)
        
        assert result is not None
        assert result.id == 1
        assert result.username == "testuser"
        
    def test_find_by_id_not_found(self, mock_db):
        """Debe retornar None si no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchone.return_value = None
        
        result = repo.find_by_id(999)
        
        assert result is None


class TestUserRepositoryFindByUsername:
    """Tests para búsqueda por username"""
    
    def test_find_by_username_found(self, mock_db):
        """Debe retornar usuario cuando existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchone.return_value = (
            1, "testuser", "test@example.com", "hash", None, False,
            0, None, "user", False, None, None, None,
            datetime.now(), datetime.now()
        )
        
        result = repo.find_by_username("testuser")
        
        assert result is not None
        assert result.username == "testuser"
        
    def test_find_by_username_not_found(self, mock_db):
        """Debe retornar None si no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchone.return_value = None
        
        result = repo.find_by_username("ghost")
        
        assert result is None


class TestUserRepositoryFindByEmail:
    """Tests para búsqueda por email"""
    
    def test_find_by_email_found(self, mock_db):
        """Debe retornar usuario cuando existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchone.return_value = (
            1, "testuser", "test@example.com", "hash", None, False,
            0, None, "user", False, None, None, None,
            datetime.now(), datetime.now()
        )
        
        result = repo.find_by_email("test@example.com")
        
        assert result is not None
        assert result.email == "test@example.com"
        
    def test_find_by_email_not_found(self, mock_db):
        """Debe retornar None si no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchone.return_value = None
        
        result = repo.find_by_email("ghost@example.com")
        
        assert result is None


class TestUserRepositoryUpdate:
    """Tests para actualización de usuarios"""
    
    def test_update_user_successfully(self, mock_db):
        """Debe actualizar un usuario y retornar User con updated_at"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # update() retorna el updated_at timestamp
        updated_at = datetime.now()
        cursor.fetchone.return_value = (updated_at,)
        
        user = User(
            id=1,
            username="testuser",
            email="new@example.com",
            password_hash="newhash"
        )
        
        result = repo.update(user)
        
        # update() retorna User, no bool
        assert isinstance(result, User)
        assert result.username == "testuser"
        assert result.updated_at == updated_at
        cursor.execute.assert_called_once()
        
    def test_update_failed_attempts(self, mock_db):
        """Debe actualizar intentos fallidos"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 1
        
        result = repo.update_failed_attempts(1, 3, None)
        
        assert result is True
        cursor.execute.assert_called_once()
        
    def test_update_failed_attempts_with_lock(self, mock_db):
        """Debe actualizar intentos fallidos y bloquear temporalmente"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 1
        lock_until = datetime.now() + timedelta(minutes=15)
        
        result = repo.update_failed_attempts(1, 5, lock_until)
        
        assert result is True
        cursor.execute.assert_called_once()
        
    def test_unlock_user(self, mock_db):
        """Debe desbloquear cuenta, resetear intentos y requerir password reset"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 1
        
        result = repo.unlock_user(1)
        
        assert result is True
        cursor.execute.assert_called_once()
        
    def test_update_password(self, mock_db):
        """Debe actualizar contraseña del usuario"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 1
        
        result = repo.update_password(1, "newhash")
        
        assert result is True
        cursor.execute.assert_called_once()
        
    def test_update_password_user_not_found(self, mock_db):
        """Debe retornar False si usuario no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 0
        
        result = repo.update_password(999, "newhash")
        
        assert result is False


class TestUserRepositoryFaceOperations:
    """Tests para operaciones de rostro"""
    
    def test_update_face_encoding(self, mock_db):
        """Debe actualizar encoding facial correctamente"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 1
        
        result = repo.update_face_encoding(1, "encoded_face_data")
        
        assert result is True
        cursor.execute.assert_called_once()
        
    def test_update_face_encoding_user_not_found(self, mock_db):
        """Debe retornar False si usuario no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 0
        
        result = repo.update_face_encoding(999, "encoded_face_data")
        
        assert result is False


class TestUserRepositoryListOperations:
    """Tests para operaciones de listado"""
    
    def test_find_all_blocked(self, mock_db):
        """Debe retornar usuarios bloqueados"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # Simular 2 usuarios bloqueados
        cursor.fetchall.return_value = [
            (1, "user1", "user1@example.com", "hash", None, False,
             5, datetime.now(), "user", False, None, None, None,
             datetime.now(), datetime.now()),
            (2, "user2", "user2@example.com", "hash", None, False,
             5, datetime.now(), "user", False, None, None, None,
             datetime.now(), datetime.now()),
        ]
        
        result = repo.find_all_blocked()
        
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        
    def test_find_all_users(self, mock_db):
        """Debe retornar todos los usuarios"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchall.return_value = [
            (1, "user1", "user1@example.com", "hash", None, False,
             0, None, "user", False, None, None, None,
             datetime.now(), datetime.now()),
        ]
        
        result = repo.find_all_users()
        
        assert len(result) == 1
        assert result[0].username == "user1"
        
    def test_find_all_empty(self, mock_db):
        """Debe retornar lista vacía si no hay usuarios"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.fetchall.return_value = []
        
        result = repo.find_all_users()
        
        assert len(result) == 0


class TestUserRepositoryDelete:
    """Tests para eliminación de usuarios"""
    
    def test_delete_user_successfully(self, mock_db):
        """Debe eliminar usuario correctamente"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 1
        
        result = repo.delete(1)
        
        assert result is True
        cursor.execute.assert_called_once()
        
    def test_delete_user_not_found(self, mock_db):
        """Debe retornar False si usuario no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        cursor.rowcount = 0
        
        result = repo.delete(999)
        
        assert result is False


class TestUserRepositoryAdminCreation:
    """Tests para creación de usuarios especiales (admin, auditor)"""
    
    def test_create_admin_if_not_exists_creates_new(self, mock_db):
        """Debe crear administrador si no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # find_by_email retorna None (no existe)
        cursor.fetchone.side_effect = [
            None,  # find_by_email
            (1, datetime.now(), datetime.now())  # create
        ]
        
        result = repo.create_admin_if_not_exists("admin@test.com", "Admin@123")
        
        assert result is not None
        assert result.id == 1
        
    def test_create_admin_if_not_exists_returns_existing(self, mock_db):
        """Debe retornar admin existente si ya existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # find_by_email retorna admin existente
        cursor.fetchone.return_value = (
            1, "admin", "admin@test.com", "hash", None, False,
            0, None, "admin", False, None, None, None,
            datetime.now(), datetime.now()
        )
        
        result = repo.create_admin_if_not_exists("admin@test.com", "Admin@123")
        
        assert result is not None
        assert result.id == 1
        assert result.role == "admin"
        
    def test_create_auditor_if_not_exists_creates_new(self, mock_db):
        """Debe crear auditor si no existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # find_by_username retorna None, luego create retorna ID
        cursor.fetchone.side_effect = [
            None,  # find_by_username
            (2, datetime.now(), datetime.now())  # create
        ]
        
        result = repo.create_auditor_if_not_exists("auditor", "Auditor@123")
        
        assert result is not None
        assert result.id == 2
        
    def test_create_auditor_if_not_exists_returns_existing(self, mock_db):
        """Debe retornar auditor existente si ya existe"""
        db, cursor = mock_db
        repo = UserRepositoryImpl(db)
        
        # find_by_username retorna auditor existente
        cursor.fetchone.return_value = (
            2, "auditor", "auditor@test.com", "hash", None, False,
            0, None, "auditor", False, None, None, None,
            datetime.now(), datetime.now()
        )
        
        result = repo.create_auditor_if_not_exists("auditor", "Auditor@123")
        
        assert result is not None
        assert result.id == 2
        assert result.role == "auditor"
