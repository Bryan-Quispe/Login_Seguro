"""
Login Seguro - Rutas de Autenticación
Endpoints para registro y login con credenciales
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from ...application.dto.user_dto import (
    RegisterRequest, 
    LoginRequest, 
    TokenResponse, 
    MessageResponse
)
from ...application.use_cases import RegisterUserUseCase, LoginUserUseCase
from ...infrastructure.database import UserRepositoryImpl

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
    success, message, token_response = use_case.execute(data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token_response


@router.get("/health")
async def health_check():
    """Endpoint de salud para verificar que el servicio está activo"""
    return {"status": "healthy", "service": "auth"}
