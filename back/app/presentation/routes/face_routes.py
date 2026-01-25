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
from ...infrastructure.database import UserRepositoryImpl
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
    """
    user_id = get_current_user_id(payload)
    user = user_repo.find_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {
        "user_id": user_id,
        "face_registered": user.face_registered,
        "requires_registration": not user.face_registered
    }
