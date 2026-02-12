"""
Login Seguro - Caso de Uso: Registrar Rostro
Implementa el registro del encoding facial del usuario
"""
from typing import Tuple
import logging
import json

from ...domain.interfaces.user_repository import IUserRepository
from ...domain.interfaces.face_service import IFaceService
from ..dto.user_dto import FaceRegisterRequest, MessageResponse

logger = logging.getLogger(__name__)


class RegisterFaceUseCase:
    """
    Caso de uso para registro de rostro.
    Valida anti-spoofing y unicidad del rostro antes de registrar.
    """
    
    def __init__(self, 
                 user_repository: IUserRepository,
                 face_service: IFaceService):
        self._user_repository = user_repository
        self._face_service = face_service
    
    def execute(self, user_id: int, request: FaceRegisterRequest) -> Tuple[bool, str, dict]:
        """
        Registra el rostro del usuario.
        
        Args:
            user_id: ID del usuario autenticado
            request: DTO con imagen en base64
            
        Returns:
            Tuple[success, message, data]
        """
        try:
            # Verificar que el usuario existe
            user = self._user_repository.find_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado", {}
            
            # Verificar que no tenga rostro registrado
            if user.face_registered:
                return False, "Ya tiene un rostro registrado", {}
            
            # Extraer encoding facial (incluye anti-spoofing)
            success, encoding, message = self._face_service.extract_face_encoding(
                request.image_data
            )
            
            if not success:
                logger.warning(f"Fallo en registro facial para user {user_id}: {message}")
                return False, message, {}
            
            # Verificar que el rostro no esté registrado en otra cuenta
            duplicate_check = self._check_face_duplicate(encoding, user_id)
            if duplicate_check:
                logger.warning(f"Intento de registrar rostro duplicado por user {user_id}")
                return False, "Este rostro ya fue registrado en otra cuenta. Solo puede tener una cuenta por rostro.", {}
            
            # Guardar encoding en base de datos
            encoding_json = json.dumps(encoding)
            updated = self._user_repository.update_face_encoding(user_id, encoding_json)
            
            if not updated:
                return False, "Error al guardar el registro facial", {}
            
            logger.info(f"Rostro registrado exitosamente para user {user_id}")
            
            return True, "Rostro registrado exitosamente", {
                "face_registered": True,
                "encoding_dimensions": len(encoding),
                "role": user.role  # Incluir rol para redirección
            }
            
        except Exception as e:
            logger.error(f"Error registrando rostro: {e}")
            return False, "Error interno al registrar rostro", {}
    
    def _check_face_duplicate(self, new_encoding: list, exclude_user_id: int) -> bool:
        """
        Verifica si el rostro ya está registrado en otra cuenta.
        
        Returns:
            True si el rostro ya existe en otra cuenta, False si es único.
        """
        try:
            # Obtener todos los usuarios con rostro registrado (excepto el actual)
            users_with_face = self._user_repository.get_users_with_face_encoding(exclude_user_id)
            
            if not users_with_face:
                return False  # No hay otros rostros registrados
            
            for existing_user in users_with_face:
                if not existing_user.face_encoding:
                    continue
                
                try:
                    stored_encoding = json.loads(existing_user.face_encoding)
                    
                    # Comparar rostros usando el servicio
                    is_match, similarity, _ = self._face_service.verify_face_encoding(
                        new_encoding, 
                        stored_encoding
                    )
                    
                    if is_match:
                        logger.warning(f"Rostro duplicado detectado: coincide con usuario {existing_user.username}")
                        return True
                        
                except (json.JSONDecodeError, Exception) as e:
                    logger.error(f"Error comparando con usuario {existing_user.id}: {e}")
                    continue
            
            return False  # Rostro único
            
        except Exception as e:
            logger.error(f"Error verificando duplicados de rostro: {e}")
            return False  # En caso de error, permitir registro
