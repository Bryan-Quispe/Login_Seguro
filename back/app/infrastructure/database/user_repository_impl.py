"""
Login Seguro - Implementación del Repositorio de Usuarios
Implementa IUserRepository usando PostgreSQL con protección contra SQL Injection
"""
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import bcrypt

from ...domain.entities.user import User, UserRole
from ...domain.interfaces.user_repository import IUserRepository
from .connection import DatabaseConnection, get_db

logger = logging.getLogger(__name__)


class UserRepositoryImpl(IUserRepository):
    """
    Implementación concreta del repositorio de usuarios.
    USA CONSULTAS PARAMETRIZADAS para prevenir SQL Injection.
    """
    
    def __init__(self, db: DatabaseConnection = None):
        self._db = db or get_db()
    
    def create(self, user: User) -> User:
        """
        Crea un nuevo usuario.
        Usa consultas parametrizadas para prevenir SQL Injection.
        """
        query = """
            INSERT INTO users (username, email, password_hash, face_encoding, face_registered, role, requires_password_reset, active_session_token)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (
                user.username,
                user.email,
                user.password_hash,
                user.face_encoding,
                user.face_registered,
                user.role if hasattr(user, 'role') else 'user',
                user.requires_password_reset if hasattr(user, 'requires_password_reset') else False,
                user.active_session_token if hasattr(user, 'active_session_token') else None
            ))
            
            result = cursor.fetchone()
            user.id = result[0]
            user.created_at = result[1]
            user.updated_at = result[2]
            
            logger.info(f"Usuario creado: {user.username} (ID: {user.id})")
            return user
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuario por ID usando consulta parametrizada"""
        query = """
            SELECT id, username, email, password_hash, face_encoding, 
                   face_registered, failed_login_attempts, locked_until,
                   COALESCE(role, 'user') as role, 
                   COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                   backup_code_hash, backup_code_encrypted,
                   active_session_token,
                   created_at, updated_at
            FROM users 
            WHERE id = %s
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_user(row)
    
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Busca usuario por username.
        IMPORTANTE: Usa consulta parametrizada para prevenir SQL Injection.
        """
        query = """
            SELECT id, username, email, password_hash, face_encoding, 
                   face_registered, failed_login_attempts, locked_until,
                   COALESCE(role, 'user') as role,
                   COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                   backup_code_hash, backup_code_encrypted,
                   active_session_token,
                   created_at, updated_at
            FROM users 
            WHERE username = %s
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_user(row)
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Busca usuario por email usando consulta parametrizada"""
        query = """
            SELECT id, username, email, password_hash, face_encoding, 
                   face_registered, failed_login_attempts, locked_until,
                   COALESCE(role, 'user') as role,
                   COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                   backup_code_hash, backup_code_encrypted,
                   active_session_token,
                   created_at, updated_at
            FROM users 
            WHERE email = %s
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_user(row)
    
    def find_all_blocked(self) -> List[User]:
        """Obtiene todos los usuarios bloqueados"""
        query = """
            SELECT id, username, email, password_hash, face_encoding, 
                   face_registered, failed_login_attempts, locked_until,
                   COALESCE(role, 'user') as role,
                   COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                   backup_code_hash, backup_code_encrypted,
                   active_session_token,
                   created_at, updated_at
            FROM users 
            WHERE locked_until IS NOT NULL AND locked_until > NOW()
            ORDER BY locked_until DESC
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]
    
    def find_all_users(self) -> List[User]:
        """Obtiene todos los usuarios (excepto admin)"""
        query = """
            SELECT id, username, email, password_hash, face_encoding, 
                   face_registered, failed_login_attempts, locked_until,
                   COALESCE(role, 'user') as role,
                   COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                   backup_code_hash, backup_code_encrypted,
                   active_session_token,
                   created_at, updated_at
            FROM users 
            WHERE COALESCE(role, 'user') != 'admin'
            ORDER BY created_at DESC
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]
    
    def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        query = """
            UPDATE users 
            SET username = %s, email = %s, password_hash = %s,
                face_encoding = %s, face_registered = %s,
                failed_login_attempts = %s, locked_until = %s,
                role = %s, requires_password_reset = %s,
                backup_code_hash = %s, backup_code_encrypted = %s,
                active_session_token = %s
            WHERE id = %s
            RETURNING updated_at
        """
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (
                user.username,
                user.email,
                user.password_hash,
                user.face_encoding,
                user.face_registered,
                user.failed_login_attempts,
                user.locked_until,
                user.role if hasattr(user, 'role') else 'user',
                user.requires_password_reset if hasattr(user, 'requires_password_reset') else False,
                user.backup_code_hash if hasattr(user, 'backup_code_hash') else None,
                user.backup_code_encrypted if hasattr(user, 'backup_code_encrypted') else None,
                user.active_session_token if hasattr(user, 'active_session_token') else None,
                user.id
            ))
            
            result = cursor.fetchone()
            if result:
                user.updated_at = result[0]
            
            logger.info(f"Usuario actualizado: {user.username} (ID: {user.id})")
            return user
    
    def update_face_encoding(self, user_id: int, face_encoding: str) -> bool:
        """Actualiza solo el encoding facial de un usuario"""
        query = """
            UPDATE users 
            SET face_encoding = %s, face_registered = TRUE, requires_password_reset = FALSE
            WHERE id = %s
        """
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (face_encoding, user_id))
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"Encoding facial registrado para usuario ID: {user_id}")
            
            return success
    
    def update_failed_attempts(self, user_id: int, attempts: int, locked_until=None) -> bool:
        """Actualiza los intentos fallidos de login"""
        query = """
            UPDATE users 
            SET failed_login_attempts = %s, locked_until = %s
            WHERE id = %s
        """
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (attempts, locked_until, user_id))
            return cursor.rowcount > 0
    
    def unlock_user(self, user_id: int) -> bool:
        """
        Desbloquea un usuario y requiere que resetee su contraseña y rostro.
        """
        query = """
            UPDATE users 
            SET locked_until = NULL, 
                failed_login_attempts = 0,
                face_encoding = NULL,
                face_registered = FALSE,
                requires_password_reset = TRUE
            WHERE id = %s
        """
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"Usuario desbloqueado ID: {user_id} - requiere resetear contraseña y rostro")
            
            return success
    
    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """Actualiza la contraseña de un usuario"""
        query = """
            UPDATE users 
            SET password_hash = %s, requires_password_reset = FALSE
            WHERE id = %s
        """
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (new_password_hash, user_id))
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"Contraseña actualizada para usuario ID: {user_id}")
            
            return success
    
    def delete(self, user_id: int) -> bool:
        """Elimina un usuario"""
        query = "DELETE FROM users WHERE id = %s"
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"Usuario eliminado ID: {user_id}")
            
            return success
    
    def get_users_with_face_encoding(self, exclude_user_id: int = None) -> List[User]:
        """
        Obtiene todos los usuarios que tienen rostro registrado.
        Excluye opcionalmente un usuario específico.
        """
        if exclude_user_id:
            query = """
                SELECT id, username, email, password_hash, face_encoding, 
                       face_registered, failed_login_attempts, locked_until,
                       COALESCE(role, 'user') as role,
                       COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                       backup_code_hash, backup_code_encrypted,
                       active_session_token,
                       created_at, updated_at
                FROM users 
                WHERE face_registered = TRUE 
                AND face_encoding IS NOT NULL
                AND id != %s
            """
            params = (exclude_user_id,)
        else:
            query = """
                SELECT id, username, email, password_hash, face_encoding, 
                       face_registered, failed_login_attempts, locked_until,
                       COALESCE(role, 'user') as role,
                       COALESCE(requires_password_reset, FALSE) as requires_password_reset,
                       backup_code_hash, backup_code_encrypted,
                       active_session_token,
                       created_at, updated_at
                FROM users 
                WHERE face_registered = TRUE 
                AND face_encoding IS NOT NULL
            """
            params = ()
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_user(row) for row in rows]
    
    def _row_to_user(self, row: tuple) -> User:
        """Convierte una fila de BD a entidad User"""
        return User(
            id=row[0],
            username=row[1],
            email=row[2],
            password_hash=row[3],
            face_encoding=row[4],
            face_registered=row[5],
            failed_login_attempts=row[6],
            locked_until=row[7],
            role=row[8] if len(row) > 8 else 'user',
            requires_password_reset=row[9] if len(row) > 9 else False,
            backup_code_hash=row[10] if len(row) > 10 else None,
            backup_code_encrypted=row[11] if len(row) > 11 else None,
            active_session_token=row[12] if len(row) > 12 else None,
            created_at=row[13] if len(row) > 13 else None,
            updated_at=row[14] if len(row) > 14 else None
        )
    
    def create_admin_if_not_exists(self, email: str, password: str) -> Optional[User]:
        """Crea el usuario administrador si no existe"""
        existing = self.find_by_email(email)
        if existing:
            return existing
        
        # Hash password
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        admin = User(
            username="admin",
            email=email,
            password_hash=password_hash,
            role=UserRole.ADMIN,
            face_registered=False,  # Debe registrar su rostro la primera vez
            requires_password_reset=False
        )
        
        return self.create(admin)
    
    def create_auditor_if_not_exists(self, username: str, password: str) -> Optional[User]:
        """Crea el usuario auditor si no existe"""
        existing = self.find_by_username(username)
        if existing:
            return existing
        
        # Hash password
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        auditor = User(
            username=username,
            email="auditor@loginseguro.com",
            password_hash=password_hash,
            role=UserRole.AUDITOR,
            face_registered=False,  # Debe registrar su rostro la primera vez
            requires_password_reset=False
        )
        
        return self.create(auditor)


def get_user_repository() -> UserRepositoryImpl:
    """Dependency injection para UserRepository"""
    return UserRepositoryImpl(get_db())
