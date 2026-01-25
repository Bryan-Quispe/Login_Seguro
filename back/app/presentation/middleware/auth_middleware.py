"""
Login Seguro - Middleware de Autenticación JWT
Valida tokens JWT y extrae información del usuario
"""
from typing import Optional
from datetime import datetime
import logging

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):
    """
    Middleware de autenticación JWT.
    Valida el token en cada request protegida.
    """
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self._settings = get_settings()
    
    async def __call__(self, request: Request) -> Optional[dict]:
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
            
            if credentials:
                if credentials.scheme.lower() != "bearer":
                    logger.warning(f"Esquema inválido: {credentials.scheme}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Esquema de autenticación inválido"
                    )
                
                payload = self.verify_jwt(credentials.credentials)
                if not payload:
                    logger.warning("Token no pudo ser verificado")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Token inválido o expirado"
                    )
                
                logger.debug(f"Token verificado para usuario: {payload.get('username')}")
                return payload
            else:
                logger.warning("No se proporcionó token")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token de autorización requerido"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error en autenticación: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Error de autenticación: {str(e)}"
            )
    
    def verify_jwt(self, token: str) -> Optional[dict]:
        """Verifica y decodifica el token JWT"""
        try:
            payload = jwt.decode(
                token,
                self._settings.JWT_SECRET_KEY,
                algorithms=[self._settings.JWT_ALGORITHM]
            )
            
            # Verificar que tenga los campos necesarios
            if not payload.get("sub"):
                logger.warning("Token sin 'sub' claim")
                return None
            
            logger.info(f"Token decodificado exitosamente para user_id: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"Error verificando JWT: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado verificando JWT: {e}")
            return None


# Instancia global
jwt_bearer = JWTBearer()


def get_current_user_id(payload: dict) -> int:
    """Extrae el user_id del payload JWT"""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token inválido: falta user_id"
        )
    return int(user_id)
