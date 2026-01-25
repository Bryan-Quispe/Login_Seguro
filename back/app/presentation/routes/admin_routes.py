"""
Login Seguro - Rutas de Administrador
Endpoints para gestión de usuarios por el administrador
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
import logging

from ..middleware.auth_middleware import jwt_bearer, get_current_user_id
from ...application.dto.user_dto import MessageResponse
from ...infrastructure.database import UserRepositoryImpl
from ...infrastructure.services.audit_service import get_audit_service, AuditService
from ...domain.entities.user import UserRole
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Administrador"])


class UserListItem(BaseModel):
    """DTO para lista de usuarios"""
    id: int
    username: str
    email: str | None
    role: str
    face_registered: bool
    is_locked: bool
    locked_until: str | None
    failed_attempts: int
    requires_password_reset: bool


class UserListResponse(BaseModel):
    """Respuesta con lista de usuarios"""
    success: bool
    users: List[UserListItem]
    total: int


def get_user_repository():
    return UserRepositoryImpl()


def require_admin(
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """Middleware que verifica que el usuario sea administrador"""
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador."
        )
    
    return user


@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin = Depends(require_admin),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Lista todos los usuarios del sistema (excepto admin).
    Solo accesible por administradores.
    """
    users = user_repo.find_all_users()
    
    user_list = []
    for u in users:
        user_list.append(UserListItem(
            id=u.id,
            username=u.username,
            email=u.email or "",
            role=u.role,
            face_registered=u.face_registered,
            is_locked=u.is_locked(),
            locked_until=u.locked_until.isoformat() if u.locked_until else None,
            failed_attempts=u.failed_login_attempts,
            requires_password_reset=u.requires_password_reset
        ))
    
    return UserListResponse(
        success=True,
        users=user_list,
        total=len(user_list)
    )


@router.get("/users/blocked", response_model=UserListResponse)
async def list_blocked_users(
    admin = Depends(require_admin),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Lista solo los usuarios bloqueados.
    Solo accesible por administradores.
    """
    users = user_repo.find_all_blocked()
    
    user_list = []
    for u in users:
        user_list.append(UserListItem(
            id=u.id,
            username=u.username,
            email=u.email or "",
            role=u.role,
            face_registered=u.face_registered,
            is_locked=True,
            locked_until=u.locked_until.isoformat() if u.locked_until else None,
            failed_attempts=u.failed_login_attempts,
            requires_password_reset=u.requires_password_reset
        ))
    
    return UserListResponse(
        success=True,
        users=user_list,
        total=len(user_list)
    )


@router.post("/unlock/{user_id}", response_model=MessageResponse)
async def unlock_user(
    request: Request,
    user_id: int,
    admin = Depends(require_admin),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Desbloquea un usuario.
    - Elimina el bloqueo temporal
    - Resetea los intentos fallidos
    - ELIMINA el registro facial (debe registrar de nuevo)
    - Marca que debe cambiar contraseña
    """
    # Verificar que el usuario existe
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No se puede desbloquear a un admin
    if user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar al administrador"
        )
    
    # Desbloquear usuario
    success = user_repo.unlock_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desbloquear usuario"
        )
    
    # Registrar en auditoría
    await audit_service.log_action(
        request=request,
        action="user_unlocked",
        admin_id=admin.id,
        admin_username=admin.username,
        target_user_id=user_id,
        target_username=user.username,
        details="Usuario desbloqueado con reset de contraseña y rostro"
    )
    
    logger.info(f"Admin {admin.username} desbloqueó al usuario {user.username} (ID: {user_id})")
    
    return MessageResponse(
        success=True,
        message=f"Usuario '{user.username}' desbloqueado. Debe crear nueva contraseña y registrar su rostro nuevamente.",
        data={
            "user_id": user_id,
            "username": user.username,
            "requires_password_reset": True,
            "requires_face_registration": True
        }
    )


@router.get("/stats")
async def admin_stats(
    admin = Depends(require_admin),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Estadísticas del sistema para el dashboard de admin.
    """
    all_users = user_repo.find_all_users()
    blocked_users = user_repo.find_all_blocked()
    
    total_users = len(all_users)
    total_blocked = len(blocked_users)
    users_with_face = sum(1 for u in all_users if u.face_registered)
    users_pending_reset = sum(1 for u in all_users if u.requires_password_reset)
    
    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "blocked_users": total_blocked,
            "users_with_face_registered": users_with_face,
            "users_pending_password_reset": users_pending_reset
        }
    }


@router.post("/disable/{user_id}", response_model=MessageResponse)
async def disable_user(
    request: Request,
    user_id: int,
    admin = Depends(require_admin),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Deshabilita un usuario (lo bloquea permanentemente hasta que admin lo habilite).
    """
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede deshabilitar al administrador"
        )
    
    # Bloquear permanentemente (1 año en el futuro)
    from datetime import datetime, timedelta
    user.locked_until = datetime.now() + timedelta(days=365)
    user.failed_login_attempts = 999  # Marcar como deshabilitado
    user_repo.update(user)
    
    # Registrar en auditoría
    await audit_service.log_action(
        request=request,
        action="user_disabled",
        admin_id=admin.id,
        admin_username=admin.username,
        target_user_id=user_id,
        target_username=user.username,
        details="Usuario deshabilitado manualmente"
    )
    
    logger.info(f"Admin {admin.username} deshabilitó al usuario {user.username} (ID: {user_id})")
    
    return MessageResponse(
        success=True,
        message=f"Usuario '{user.username}' deshabilitado.",
        data={"user_id": user_id, "disabled": True}
    )


@router.post("/enable/{user_id}", response_model=MessageResponse)
async def enable_user(
    request: Request,
    user_id: int,
    admin = Depends(require_admin),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Habilita un usuario deshabilitado.
    - Desbloquea la cuenta
    - Resetea intentos fallidos  
    - Mantiene el registro facial si existe
    """
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar al administrador"
        )
    
    # Habilitar usuario
    user.locked_until = None
    user.failed_login_attempts = 0
    user_repo.update(user)
    
    # Registrar en auditoría
    await audit_service.log_action(
        request=request,
        action="user_enabled",
        admin_id=admin.id,
        admin_username=admin.username,
        target_user_id=user_id,
        target_username=user.username,
        details="Usuario habilitado"
    )
    
    logger.info(f"Admin {admin.username} habilitó al usuario {user.username} (ID: {user_id})")
    
    return MessageResponse(
        success=True,
        message=f"Usuario '{user.username}' habilitado.",
        data={"user_id": user_id, "enabled": True}
    )
