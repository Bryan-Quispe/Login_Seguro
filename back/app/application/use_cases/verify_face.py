"""
Login Seguro - Caso de Uso: Verificar Rostro
Implementa la verificación biométrica facial para login
Con límite de 3 intentos y bloqueo de cuenta
"""
from typing import Tuple
from datetime import datetime, timedelta
import logging
import json

from ...domain.interfaces.user_repository import IUserRepository
from ...domain.interfaces.face_service import IFaceService
from ...config.settings import get_settings
from ..dto.user_dto import FaceVerifyRequest

logger = logging.getLogger(__name__)

# Configuración de intentos
MAX_FACE_ATTEMPTS = 3
FACE_LOCKOUT_MINUTES = 15


class VerifyFaceUseCase:
    """
    Caso de uso para verificación facial.
    Usa anti-spoofing + reconocimiento facial para máxima seguridad.
    NUEVO: Límite de 3 intentos con bloqueo de cuenta.
    """
    
    def __init__(self,
                 user_repository: IUserRepository,
                 face_service: IFaceService):
        self._user_repository = user_repository
        self._face_service = face_service
        self._settings = get_settings()
    
    def execute(self, user_id: int, request: FaceVerifyRequest) -> Tuple[bool, str, dict]:
        """
        Verifica el rostro del usuario contra el almacenado.
        
        Args:
            user_id: ID del usuario autenticado
            request: DTO con imagen en base64
            
        Returns:
            Tuple[success, message, details]
        """
        try:
            # Obtener usuario
            user = self._user_repository.find_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", {}
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked():
                remaining = (user.locked_until - datetime.now()).seconds // 60
                logger.warning(f"Intento de verificación facial en cuenta bloqueada: {user.username}")
                return False, "Cuenta bloqueada por seguridad. Contacte con el administrador.", {
                    "account_locked": True,
                    "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                    "remaining_minutes": remaining
                }
            
            # Verificar que tenga rostro registrado
            if not user.face_registered or not user.face_encoding:
                return False, "No tiene rostro registrado", {
                    "requires_face_registration": True
                }
            
            # Obtener encoding almacenado
            stored_encoding = json.loads(user.face_encoding)
            
            # Verificación completa con anti-spoofing
            success, details, message = self._face_service.verify_face_with_antispoofing(
                image_data=request.image_data,
                stored_encoding=stored_encoding
            )
            
            if success:
                # Resetear intentos fallidos en verificación exitosa
                if user.failed_login_attempts > 0:
                    self._user_repository.update_failed_attempts(user_id, 0, None)
                
                logger.info(f"Verificación facial exitosa para user {user_id}")
                # Convertir valores numpy a float nativo para evitar error de serialización
                confidence_val = details.get('spoof_confidence', 1.0)
                distance_val = details.get('distance', 0.0)
                
                return True, "Verificación facial exitosa. Acceso concedido.", {
                    "verified": True,
                    "is_real": details.get('is_real', True),
                    "confidence": float(confidence_val) if hasattr(confidence_val, 'item') else float(confidence_val),
                    "match_distance": float(distance_val) if hasattr(distance_val, 'item') else float(distance_val),
                    "role": user.role  # Incluir rol para redirección
                }
            else:
                # Manejar intento fallido
                remaining_attempts = self._handle_failed_attempt(user)
                
                logger.warning(f"Verificación facial fallida para user {user_id}: {message}")
                
                if remaining_attempts == 0:
                    return False, "Cuenta bloqueada por múltiples intentos fallidos de verificación facial", {
                        "verified": False,
                        "account_locked": True,
                        "reason": "max_attempts_exceeded"
                    }
                
                return False, f"{message}. Intentos restantes: {remaining_attempts}", {
                    "verified": False,
                    "is_real": details.get('is_real', False),
                    "reason": "spoofing" if not details.get('is_real') else "no_match",
                    "remaining_attempts": remaining_attempts
                }
            
        except json.JSONDecodeError:
            logger.error(f"Encoding facial corrupto para user {user_id}")
            return False, "Error en datos faciales almacenados", {}
        except Exception as e:
            logger.error(f"Error en verificación facial: {e}")
            return False, "Error interno al verificar rostro", {}
    
    def _handle_failed_attempt(self, user) -> int:
        """
        Maneja un intento fallido de verificación facial.
        Retorna el número de intentos restantes.
        """
        new_attempts = user.failed_login_attempts + 1
        locked_until = None
        
        # Bloquear cuenta si excede el límite
        if new_attempts >= MAX_FACE_ATTEMPTS:
            locked_until = datetime.now() + timedelta(minutes=FACE_LOCKOUT_MINUTES)
            logger.warning(f"Cuenta bloqueada por verificación facial fallida: {user.username}")
        
        self._user_repository.update_failed_attempts(user.id, new_attempts, locked_until)
        
        remaining = max(0, MAX_FACE_ATTEMPTS - new_attempts)
        return remaining
