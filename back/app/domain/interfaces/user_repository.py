"""
Login Seguro - Interface del Repositorio de Usuarios
Define el contrato para la persistencia de usuarios (Interface Segregation Principle)
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..entities.user import User


class IUserRepository(ABC):
    """
    Interface para el repositorio de usuarios.
    Sigue el principio de Inversión de Dependencias (DIP) - 
    los casos de uso dependen de esta abstracción, no de implementaciones concretas.
    """
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Crea un nuevo usuario en la base de datos"""
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca un usuario por su ID"""
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su nombre de usuario"""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """Busca un usuario por su email"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        pass
    
    @abstractmethod
    def update_face_encoding(self, user_id: int, face_encoding: str) -> bool:
        """Actualiza el encoding facial de un usuario"""
        pass
    
    @abstractmethod
    def update_failed_attempts(self, user_id: int, attempts: int, locked_until=None) -> bool:
        """Actualiza los intentos fallidos de login"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Elimina un usuario"""
        pass
