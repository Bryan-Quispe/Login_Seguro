"""
Login Seguro - Rutas de Auditoría
Endpoints para consultar logs de auditoría
"""
from fastapi import APIRouter, Depends, Query
from typing import List
import logging

from ..middleware.auth_middleware import jwt_bearer, get_current_user_id
from ...infrastructure.database import UserRepositoryImpl
from ...infrastructure.services.audit_service import get_audit_service, AuditService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Auditoría"])


class AuditLogItem(BaseModel):
    """DTO para log de auditoría"""
    id: int
    action: str
    admin_id: int | None
    admin_username: str
    target_user_id: int | None
    target_username: str
    details: str
    ip_address: str
    user_agent: str
    location_country: str
    location_city: str
    location_region: str
    created_at: str


class AuditLogsResponse(BaseModel):
    """Respuesta con logs de auditoría"""
    success: bool
    logs: List[AuditLogItem]
    total: int
    page: int
    limit: int


def get_user_repository():
    return UserRepositoryImpl()


def require_auditor(
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """Middleware que verifica que el usuario sea AUDITOR (rol separado de admin)"""
    from fastapi import HTTPException, status
    
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Solo auditor puede acceder (NO admin)
    if not user.is_auditor():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de AUDITOR."
        )
    
    return user


@router.get("/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    auditor = Depends(require_auditor),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Obtiene los logs de auditoría.
    Solo accesible por auditores/administradores.
    """
    offset = (page - 1) * limit
    logs = audit_service.get_logs(limit=limit, offset=offset)
    total = audit_service.get_logs_count()
    
    log_items = []
    for log in logs:
        log_items.append(AuditLogItem(
            id=log.id or 0,
            action=log.action,
            admin_id=log.admin_id,
            admin_username=log.admin_username,
            target_user_id=log.target_user_id,
            target_username=log.target_username,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent[:100] + "..." if len(log.user_agent) > 100 else log.user_agent,
            location_country=log.location_country,
            location_city=log.location_city,
            location_region=log.location_region,
            created_at=log.created_at.isoformat() if log.created_at else ""
        ))
    
    return AuditLogsResponse(
        success=True,
        logs=log_items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/stats")
async def audit_stats(
    auditor = Depends(require_auditor),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Estadísticas de auditoría.
    """
    total_logs = audit_service.get_logs_count()
    recent_logs = audit_service.get_logs(limit=10)
    
    # Contar acciones por tipo
    actions_count = {}
    for log in recent_logs:
        actions_count[log.action] = actions_count.get(log.action, 0) + 1
    
    return {
        "success": True,
        "stats": {
            "total_logs": total_logs,
            "recent_actions": actions_count
        }
    }
