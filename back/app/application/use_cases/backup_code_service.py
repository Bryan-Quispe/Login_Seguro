"""
Login Seguro - Caso de Uso: Verificar Código de Respaldo
Permite autenticación alternativa cuando falla la biometría facial
"""
from typing import Optional
import bcrypt
import secrets
import logging

from ...domain.entities.user import User
from ...infrastructure.database import UserRepositoryImpl

logger = logging.getLogger(__name__)


class BackupCodeService:
    """
    Servicio para gestión de códigos de respaldo.
    Implementa el patrón Service para operaciones de código de respaldo.
    """
    
    def __init__(self, user_repository: UserRepositoryImpl):
        self._user_repo = user_repository
    
    def generate_backup_code(self, user_id: int) -> Optional[str]:
        """
        Genera un nuevo código de respaldo para el usuario.
        Retorna el código en texto claro (solo se muestra una vez).
        El hash se almacena en la base de datos.
        
        Returns:
            str: Código de 8 caracteres alfanumérico
        """
        user = self._user_repo.find_by_id(user_id)
        if not user:
            logger.warning(f"Usuario no encontrado para generar código: {user_id}")
            return None
        
        # Generar código aleatorio de 8 caracteres
        code = secrets.token_hex(4).upper()  # 8 caracteres hex
        
        # Hash del código con bcrypt
        code_bytes = code.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        code_hash = bcrypt.hashpw(code_bytes, salt).decode('utf-8')
        
        # Guardar hash en usuario
        user.backup_code_hash = code_hash
        self._user_repo.update(user)
        
        logger.info(f"Código de respaldo generado para usuario: {user.username}")
        
        return code
    
    def verify_backup_code(self, user_id: int, code: str) -> bool:
        """
        Verifica un código de respaldo.
        El código es de un solo uso - se invalida después de verificación exitosa.
        Ahora comparte el contador de intentos con la verificación facial.
        
        Args:
            user_id: ID del usuario
            code: Código de respaldo proporcionado
            
        Returns:
            bool: True si el código es válido
        """
        user = self._user_repo.find_by_id(user_id)
        if not user:
            return False

        # 1. Verificar si la cuenta ya está bloqueada
        if user.is_locked():
            logger.warning(f"Intento de uso de código de respaldo en cuenta bloqueada: {user.username}")
            return False

        # 2. Verificar existencia de hash
        if not user.backup_code_hash:
            logger.warning(f"Verificación de código fallida - usuario sin código: {user.id}")
            # Incrementar intentos aunque no tenga código para evitar enumeración
            self._handle_failed_attempt(user)
            return False
        
        # 3. Verificar hash
        code_bytes = code.upper().encode('utf-8')
        try:
            is_valid = bcrypt.checkpw(code_bytes, user.backup_code_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verificando código: {e}")
            self._handle_failed_attempt(user)
            return False
        
        if is_valid:
            # Invalidar código después de uso exitoso
            user.backup_code_hash = None
            
            # Resetear intentos fallidos SOLO si es exitoso
            user.failed_login_attempts = 0
            user.locked_until = None
            self._user_repo.update(user)
            
            logger.info(f"Código de respaldo verificado exitosamente: {user.username}")
            return True
        else:
            # 4. Manejar intento fallido
            logger.warning(f"Código de respaldo incorrecto para usuario: {user.username}")
            self._handle_failed_attempt(user)
            return False

    def _handle_failed_attempt(self, user):
        """Maneja el incremento de intentos fallidos y bloqueo"""
        from datetime import datetime, timedelta
        # Configuración duplicated de verify_face (idealmente debería estar en config o user entity)
        MAX_ATTEMPTS = 3
        LOCKOUT_MINUTES = 15
        
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= MAX_ATTEMPTS:
            user.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
            logger.warning(f"Cuenta bloqueada por fallos en código de respaldo: {user.username}")
            
        self._user_repo.update(user)
    
    def invalidate_backup_code(self, user_id: int) -> bool:
        """
        Invalida el código de respaldo de un usuario.
        Útil cuando se resetea la cuenta o se genera un nuevo código.
        """
        user = self._user_repo.find_by_id(user_id)
        if not user:
            return False
        
        user.backup_code_hash = None
        self._user_repo.update(user)
        
        logger.info(f"Código de respaldo invalidado para: {user.username}")
        return True


# Singleton para inyección de dependencias
_backup_code_service: Optional[BackupCodeService] = None


def get_backup_code_service() -> BackupCodeService:
    """Factory method para obtener instancia del servicio"""
    global _backup_code_service
    if _backup_code_service is None:
        _backup_code_service = BackupCodeService(UserRepositoryImpl())
    return _backup_code_service
