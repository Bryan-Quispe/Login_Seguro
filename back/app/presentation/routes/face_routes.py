"""
Login Seguro - Rutas de Biometría Facial
Endpoints para registro y verificación facial
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from ...application.dto.user_dto import (
    FaceRegisterRequest,
    FaceVerifyRequest,
    MessageResponse
)
from ...application.use_cases import RegisterFaceUseCase, VerifyFaceUseCase
from ...infrastructure.database import UserRepositoryImpl, get_user_repository
from fastapi.responses import JSONResponse
from ...infrastructure.services import DeepFaceService
from ..middleware.auth_middleware import jwt_bearer, get_current_user_id

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/face", tags=["Biometría Facial"])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


def get_user_repository():
    return UserRepositoryImpl()


def get_face_service():
    return DeepFaceService()


@router.post("/register", response_model=MessageResponse)
@limiter.limit("30/minute")  # Aumentado para debugging
async def register_face(
    request: Request,
    data: FaceRegisterRequest,
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    face_service: DeepFaceService = Depends(get_face_service)
):
    """
    Registra el rostro del usuario autenticado.
    
    - Requiere token JWT válido
    - Verifica anti-spoofing antes de registrar
    - Solo permite un registro por usuario
    """
    user_id = get_current_user_id(payload)
    
    use_case = RegisterFaceUseCase(user_repo, face_service)
    success, message, details = use_case.execute(user_id, data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return MessageResponse(
        success=True,
        message=message,
        data=details
    )


@router.post("/verify", response_model=MessageResponse)
@limiter.limit("5/minute")  # Máximo 5 verificaciones por minuto
async def verify_face(
    request: Request,
    data: FaceVerifyRequest,
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
    face_service: DeepFaceService = Depends(get_face_service)
):
    """
    Verifica el rostro del usuario para completar el login.
    
    - Requiere token JWT válido
    - Verifica anti-spoofing (detecta fotos/videos)
    - Compara con el encoding facial almacenado
    - SIEMPRE retorna 200 para evitar redirecciones en el frontend
    """
    user_id = get_current_user_id(payload)
    
    use_case = VerifyFaceUseCase(user_repo, face_service)
    success, message, details = use_case.execute(user_id, data)
    
    # SIEMPRE retornar 200 con success=true/false
    # Esto evita que el interceptor del frontend redirija a login
    return MessageResponse(
        success=success,
        message=message,
        data=details
    )


@router.get("/status")
async def face_status(
    payload: dict = Depends(jwt_bearer),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Obtiene el estado del registro facial del usuario.
    Incluye intentos restantes para sincronizar frontend con backend.
    """
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Calcular intentos restantes (máximo 3)
    max_attempts = 3
    remaining_attempts = max(0, max_attempts - user.failed_login_attempts)
    
    return {
        "user_id": user_id,
        "face_registered": user.face_registered,
        "requires_registration": not user.face_registered,
        "has_backup_code": user.has_backup_code(),
        "remaining_attempts": remaining_attempts,
        "is_locked": user.is_locked(),
        "failed_attempts": user.failed_login_attempts
    }


# ===== ENDPOINTS DE CÓDIGO DE RESPALDO (FALLBACK BIOMÉTRICO) =====

from ...application.use_cases.backup_code_service import get_backup_code_service, BackupCodeService
from pydantic import BaseModel


class BackupCodeRequest(BaseModel):
    """Request para verificar código de respaldo"""
    code: str


class BackupCodeResponse(BaseModel):
    """Response con código de respaldo generado"""
    success: bool
    message: str
    backup_code: str | None = None


def get_backup_service():
    return get_backup_code_service()


@router.post("/backup-code/generate", response_model=BackupCodeResponse)
@limiter.limit("3/hour")  # Máximo 3 generaciones por hora para seguridad
async def generate_backup_code(
    request: Request,
    payload: dict = Depends(jwt_bearer),
    backup_service: BackupCodeService = Depends(get_backup_service)
):
    """
    Genera un nuevo código de respaldo para el usuario.
    
    - El código es de un solo uso
    - Solo se muestra una vez, debe guardarse de forma segura
    - Invalida cualquier código anterior
    """
    user_id = get_current_user_id(payload)
    
    code = backup_service.generate_backup_code(user_id)
    
    if not code:
        return BackupCodeResponse(
            success=False,
            message="No se pudo generar el código de respaldo"
        )
    
    return BackupCodeResponse(
        success=True,
        message="Código de respaldo generado. Guárdelo en un lugar seguro, solo se muestra una vez.",
        backup_code=code
    )


@router.post("/backup-code/verify", response_model=MessageResponse)
@limiter.limit("5/minute")  # Mismo límite que verificación facial
async def verify_backup_code(
    request: Request,
    data: BackupCodeRequest,
    payload: dict = Depends(jwt_bearer),
    backup_service: BackupCodeService = Depends(get_backup_service),
    user_repo: UserRepositoryImpl = Depends(get_user_repository)
):
    """
    Verifica un código de respaldo como alternativa a la biometría facial.
    
    - Usar cuando falla la verificación facial
    - El código se invalida después de uso exitoso
    - Requiere generar un nuevo código después
    """
    user_id = get_current_user_id(payload)
    
    # Validar código
    is_valid = backup_service.verify_backup_code(user_id, data.code)
    
    if not is_valid:
        # Obtener estado actualizado del usuario para informar intentos
        user = user_repo.find_by_id(user_id)
        max_attempts = 3
        remaining = max(0, max_attempts - user.failed_login_attempts)
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False, 
                "message": "Código de respaldo inválido o ya utilizado",
                "remaining_attempts": remaining,
                "is_locked": user.is_locked(),
                "failed_attempts": user.failed_login_attempts
            }
        )
    
    return MessageResponse(
        success=True,
        message="Código verificado correctamente. Acceso concedido.",
        data={"verified": True, "method": "backup_code"}
    )

