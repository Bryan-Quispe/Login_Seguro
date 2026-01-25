"""
Login Seguro - Caso de Uso: Login de Usuario
Implementa la lógica de autenticación con credenciales
"""
from typing import Tuple, Optional
from datetime import datetime, timedelta
import logging
import bcrypt

from jose import jwt

from ...domain.entities.user import User
from ...domain.interfaces.user_repository import IUserRepository
from ...config.settings import get_settings
from ..dto.user_dto import LoginRequest, TokenResponse, UserResponse

logger = logging.getLogger(__name__)


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash using bcrypt directly"""
    password_bytes = password.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


class LoginUserUseCase:
    """
    Caso de uso para login con credenciales.
    Incluye protección contra fuerza bruta con bloqueo de cuenta.
    """
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
        self._settings = get_settings()
    
    def execute(self, request: LoginRequest) -> Tuple[bool, str, Optional[TokenResponse]]:
        """
        Ejecuta el login con credenciales.
        
        Returns:
            Tuple[success, message, token_response]
        """
        try:
            # Buscar usuario
            user = self._user_repository.find_by_username(request.username)
            
            if not user:
                # No revelar si el usuario existe o no (seguridad)
                logger.warning(f"Intento de login con usuario inexistente: {request.username}")
                return False, "Credenciales inválidas", None
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked():
                remaining = (user.locked_until - datetime.now()).seconds // 60
                logger.warning(f"Intento de login en cuenta bloqueada: {user.username}")
                return False, f"Cuenta bloqueada. Intente en {remaining} minutos", None
            
            # Verificar contraseña
            if not verify_password(request.password, user.password_hash):
                # Incrementar intentos fallidos
                self._handle_failed_attempt(user)
                logger.warning(f"Contraseña incorrecta para: {user.username}")
                return False, "Credenciales inválidas", None
            
            # Login exitoso - resetear intentos fallidos
            if user.failed_login_attempts > 0:
                self._user_repository.update_failed_attempts(user.id, 0, None)
            
            # Generar token JWT
            token = self._generate_token(user)
            
            # Determinar siguiente paso
            requires_face_registration = not user.face_registered
            requires_face_verification = user.face_registered
            
            logger.info(f"Login exitoso (credenciales): {user.username}")
            
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                face_registered=user.face_registered
            )
            
            return True, "Credenciales verificadas", TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user_response,
                requires_face_registration=requires_face_registration,
                requires_face_verification=requires_face_verification
            )
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return False, "Error interno al procesar login", None
    
    def _handle_failed_attempt(self, user: User) -> None:
        """Maneja un intento fallido de login"""
        new_attempts = user.failed_login_attempts + 1
        locked_until = None
        
        # Bloquear cuenta si excede el límite
        if new_attempts >= self._settings.MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.now() + timedelta(
                minutes=self._settings.LOCKOUT_DURATION_MINUTES
            )
            logger.warning(f"Cuenta bloqueada por múltiples intentos fallidos: {user.username}")
        
        self._user_repository.update_failed_attempts(user.id, new_attempts, locked_until)
    
    def _generate_token(self, user: User) -> str:
        """Genera un token JWT"""
        expire = datetime.utcnow() + timedelta(
            minutes=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "face_registered": user.face_registered,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            self._settings.JWT_SECRET_KEY,
            algorithm=self._settings.JWT_ALGORITHM
        )
