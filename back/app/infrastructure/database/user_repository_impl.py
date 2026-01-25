"""
Login Seguro - Implementación del Repositorio de Usuarios
Implementa IUserRepository usando PostgreSQL con protección contra SQL Injection
"""
from typing import Optional
from datetime import datetime
import logging

from ...domain.entities.user import User
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
            INSERT INTO users (username, email, password_hash, face_encoding, face_registered)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """
        
        with self._db.get_cursor() as cursor:
            # Parámetros pasados como tupla - NUNCA concatenar strings
            cursor.execute(query, (
                user.username,
                user.email,
                user.password_hash,
                user.face_encoding,
                user.face_registered
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
                   created_at, updated_at
            FROM users 
            WHERE id = %s
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            cursor.execute(query, (user_id,))  # Parámetro como tupla
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
                   created_at, updated_at
            FROM users 
            WHERE username = %s
        """
        
        with self._db.get_cursor(commit=False) as cursor:
            # El username se pasa como parámetro, NUNCA se concatena al query
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
    
    def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        query = """
            UPDATE users 
            SET username = %s, email = %s, password_hash = %s,
                face_encoding = %s, face_registered = %s,
                failed_login_attempts = %s, locked_until = %s
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
            SET face_encoding = %s, face_registered = TRUE
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
    
    def delete(self, user_id: int) -> bool:
        """Elimina un usuario"""
        query = "DELETE FROM users WHERE id = %s"
        
        with self._db.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            success = cursor.rowcount > 0
            
            if success:
                logger.info(f"Usuario eliminado ID: {user_id}")
            
            return success
    
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
            created_at=row[8],
            updated_at=row[9]
        )
