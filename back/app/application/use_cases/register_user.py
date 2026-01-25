"""
Login Seguro - Caso de Uso: Registrar Usuario
Implementa la lógica de negocio para registro de usuarios
"""
from typing import Tuple
import logging
import bcrypt

from ...domain.entities.user import User
from ...domain.interfaces.user_repository import IUserRepository
from ..dto.user_dto import RegisterRequest, UserResponse

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly (compatible with bcrypt 5.0)"""
    # Encode password to bytes, truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    password_bytes = password.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


class RegisterUserUseCase:
    """
    Caso de uso para registro de usuarios.
    Sigue el principio de Single Responsibility.
    """
    
    def __init__(self, user_repository: IUserRepository):
        """
        Inyección de dependencias - Dependency Inversion Principle.
        El caso de uso depende de la abstracción, no de la implementación.
        """
        self._user_repository = user_repository
    
    def execute(self, request: RegisterRequest) -> Tuple[bool, str, UserResponse | None]:
        """
        Ejecuta el registro de usuario.
        
        Args:
            request: DTO con datos de registro validados
            
        Returns:
            Tuple[success, message, user_response]
        """
        try:
            # Verificar si el usuario ya existe
            existing_user = self._user_repository.find_by_username(request.username)
            if existing_user:
                logger.warning(f"Intento de registro con username existente: {request.username}")
                return False, "El nombre de usuario ya está registrado", None
            
            # Verificar email si fue proporcionado
            if request.email:
                existing_email = self._user_repository.find_by_email(request.email)
                if existing_email:
                    logger.warning(f"Intento de registro con email existente: {request.email}")
                    return False, "El email ya está registrado", None
            
            # Hash de la contraseña con bcrypt
            password_hash = hash_password(request.password)
            
            # Crear entidad de usuario
            user = User(
                username=request.username,
                email=request.email,
                password_hash=password_hash,
                face_registered=False
            )
            
            # Persistir en base de datos
            created_user = self._user_repository.create(user)
            
            logger.info(f"Usuario registrado exitosamente: {created_user.username}")
            
            # Crear respuesta
            user_response = UserResponse(
                id=created_user.id,
                username=created_user.username,
                email=created_user.email,
                face_registered=created_user.face_registered
            )
            
            return True, "Usuario registrado exitosamente", user_response
            
        except Exception as e:
            logger.error(f"Error en registro de usuario: {e}")
            return False, "Error interno al registrar usuario", None
