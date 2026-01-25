"""
Login Seguro - Aplicación Principal FastAPI
Entry point de la API REST con autenticación biométrica facial
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import sys

from .presentation import auth_router, face_router, setup_cors
from .presentation.routes.admin_routes import router as admin_router
from .config.settings import get_settings
from .infrastructure.database import UserRepositoryImpl

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Login Seguro API",
    description="""
    API de autenticación segura con verificación biométrica facial.
    
    ## Características de Seguridad
    
    - ✅ Protección contra SQL Injection (consultas parametrizadas)
    - ✅ Protección contra XSS (sanitización de entrada)
    - ✅ Hash de contraseñas con bcrypt
    - ✅ JWT para sesiones
    - ✅ Rate limiting para prevenir fuerza bruta
    - ✅ Bloqueo de cuenta por intentos fallidos
    - ✅ Anti-spoofing facial (detecta fotos/videos)
    - ✅ CORS configurado
    - ✅ Sistema de roles (admin/user)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar rate limiting global
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
setup_cors(app)

# Registrar routers
app.include_router(auth_router)
app.include_router(face_router)
app.include_router(admin_router)

# Importar y registrar rutas de auditoría
from .presentation.routes.audit_routes import router as audit_router
app.include_router(audit_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de entrada"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    
    logger.warning(f"Error de validación: {errors}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Error de validación en los datos de entrada",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Maneja excepciones no capturadas"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Error interno del servidor"
        }
    )


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": "Login Seguro API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Evento de inicio
@app.on_event("startup")
async def startup_event():
    """Inicialización de la aplicación"""
    settings = get_settings()
    logger.info("=" * 50)
    logger.info("Login Seguro API iniciando...")
    logger.info(f"Documentación disponible en: http://localhost:3000/docs")
    
    # Crear usuario admin si no existe
    try:
        user_repo = UserRepositoryImpl()
        
        # Admin
        admin = user_repo.create_admin_if_not_exists(
            email="admin@loginseguro.com",
            password="S@bryromero123"
        )
        if admin:
            logger.info(f"Usuario admin verificado: {admin.email}")
            
        # Auditor
        auditor = user_repo.create_auditor_if_not_exists(
            username="audit",
            password="S@bryromero123"
        )
        if auditor:
            logger.info(f"Usuario auditor verificado: {auditor.username}")
            
    except Exception as e:
        logger.warning(f"No se pudo crear/verificar usuarios de sistema: {e}")
    
    logger.info("=" * 50)


# Evento de cierre
@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la aplicación"""
    logger.info("Login Seguro API cerrando...")
