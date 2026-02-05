"""
Login Seguro - Rutas de Autenticación
Endpoints para registro y login con credenciales
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import logging

from ...application.dto.user_dto import (
    RegisterRequest, 
    LoginRequest, 
    TokenResponse, 
    MessageResponse
)
from ...application.use_cases import RegisterUserUseCase, LoginUserUseCase
from ...infrastructure.database import UserRepositoryImpl
from ..middleware.auth_middleware import jwt_bearer, get_current_user_id

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

# Rate limiting para prevenir fuerza bruta
limiter = Limiter(key_func=get_remote_address)


def get_user_repository():
    """Dependency injection para el repositorio"""
    return UserRepositoryImpl()


@router.post("/register", response_model=MessageResponse)
@limiter.limit("5/minute")  # Máximo 5 registros por minuto por IP
async def register(
    request: Request,
    data: RegisterRequest,
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Registra un nuevo usuario.
    
    - Valida username único
    - Hash de contraseña con bcrypt
    - Validación de formato de password seguro
    """
    use_case = RegisterUserUseCase(user_repo)
    success, message, user = use_case.execute(data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return MessageResponse(
        success=True,
        message=message,
        data={"user_id": user.id, "username": user.username}
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")  # Máximo 10 intentos por minuto por IP
async def login(
    request: Request,
    data: LoginRequest,
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Login con credenciales (usuario y contraseña).
    
    - Verifica credenciales
    - Bloquea cuenta después de 5 intentos fallidos
    - Indica si requiere registro o verificación facial
    """
    use_case = LoginUserUseCase(user_repo)
    success, message, token_response, additional_data = use_case.execute(data)
    
    if not success:
        # Retornar información adicional sobre intentos fallidos en JSON
        error_data = {
            "detail": message,
            "remaining_attempts": 3,
            "account_locked": False,
            "remaining_minutes": 0,
            "role": "user",
            "active_session_exists": False
        }
        
        if additional_data:
            if additional_data.get('remaining_attempts') is not None:
                error_data['remaining_attempts'] = additional_data['remaining_attempts']
            if additional_data.get('account_locked') is not None:
                error_data['account_locked'] = additional_data['account_locked']
            if additional_data.get('locked_until') is not None:
                error_data['locked_until'] = additional_data['locked_until']
                remaining_min = (additional_data['locked_until'] - datetime.now()).seconds // 60
                error_data['remaining_minutes'] = remaining_min
            if additional_data.get('role') is not None:
                error_data['role'] = additional_data['role']
            if additional_data.get('active_session_exists') is not None:
                error_data['active_session_exists'] = additional_data['active_session_exists']
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_data,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token_response


@router.get("/health")
async def health_check():
    """Endpoint de salud para verificar que el servicio está activo"""
    return {"status": "healthy", "service": "auth"}


@router.post("/logout")
async def logout(
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Cierra la sesión del usuario.
    """
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    logger.info(f"Usuario {user.username} cerró sesión")
    
    return {
        "success": True,
        "message": "Sesión cerrada exitosamente"
    }


# ===== ENDPOINTS DE PERFIL PARA CLIENTE =====

from pydantic import BaseModel
from typing import Optional


class ProfileResponse(BaseModel):
    """Respuesta con perfil del usuario"""
    success: bool
    user: dict


class PreferencesRequest(BaseModel):
    """Request para actualizar preferencias"""
    theme: Optional[str] = None  # "light" o "dark"
    notifications_enabled: Optional[bool] = None


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Obtiene el perfil del usuario autenticado.
    Incluye nombre, correo, fecha de registro y estado del rostro.
    """
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return ProfileResponse(
        success=True,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "face_registered": user.face_registered,
            "has_backup_code": user.has_backup_code(),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    )


@router.patch("/preferences")
async def update_preferences(
    data: PreferencesRequest,
    payload: dict = Depends(jwt_bearer)
):
    """
    Actualiza las preferencias del usuario.
    Las preferencias se almacenan en el frontend (localStorage).
    Este endpoint sirve para validar y confirmar la actualización.
    """
    user_id = get_current_user_id(payload)
    
    return {
        "success": True,
        "message": "Preferencias actualizadas",
        "user_id": user_id,
        "preferences": {
            "theme": data.theme,
            "notifications_enabled": data.notifications_enabled
        }
    }


# ===== CAMBIO DE CONTRASEÑA OBLIGATORIO =====

import bcrypt


class ChangePasswordRequest(BaseModel):
    """Request para cambiar contraseña"""
    current_password: str
    new_password: str = Field(..., min_length=8)


@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Cambia la contraseña del usuario.
    Requerido en el primer login cuando requires_password_reset=True.
    """
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar contraseña actual
    try:
        is_valid = bcrypt.checkpw(
            data.current_password.encode('utf-8')[:72],
            user.password_hash.encode('utf-8')
        )
    except Exception:
        is_valid = False
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )
    
    # Verificar que la nueva contraseña sea diferente
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la actual"
        )
    
    # Hash de la nueva contraseña
    password_bytes = data.new_password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    new_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Actualizar usuario
    user.password_hash = new_hash
    user.requires_password_reset = False  # Ya no requiere cambio
    user_repo.update(user)
    
    logger.info(f"Usuario {user.username} cambió su contraseña exitosamente")
    
    return {
        "success": True,
        "message": "Contraseña actualizada exitosamente",
        "requires_face_registration": not user.face_registered
    }

