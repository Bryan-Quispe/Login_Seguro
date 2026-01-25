"""
Login Seguro - Data Transfer Objects (DTOs)
Validación de entrada con Pydantic para prevenir inyección de código
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
import re
import bleach


class RegisterRequest(BaseModel):
    """DTO para registro de usuario con validación estricta"""
    
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Nombre de usuario (3-50 caracteres, solo alfanuméricos)"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Contraseña segura (mínimo 8 caracteres)"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email opcional"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Valida username para prevenir inyección.
        Solo permite caracteres alfanuméricos y guiones bajos.
        """
        # Sanitizar HTML/scripts
        v = bleach.clean(v, tags=[], strip=True)
        
        # Solo alfanuméricos y underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username solo puede contener letras, números y guiones bajos')
        
        # Prevenir palabras reservadas SQL
        forbidden = ['select', 'insert', 'update', 'delete', 'drop', 'union', 
                    'exec', 'execute', 'script', 'admin', 'root']
        if v.lower() in forbidden:
            raise ValueError('Username no permitido')
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Valida que la contraseña sea segura.
        Requiere mayúscula, minúscula, número y carácter especial.
        """
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial')
        
        return v


class LoginRequest(BaseModel):
    """DTO para login con validación"""
    
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    
    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Sanitiza el username para prevenir XSS"""
        return bleach.clean(v, tags=[], strip=True)


class FaceRegisterRequest(BaseModel):
    """DTO para registro de rostro"""
    
    image_data: str = Field(
        ...,
        description="Imagen en base64"
    )
    
    @field_validator('image_data')
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Valida que sea una imagen base64 válida"""
        # Remover prefijo data:image si existe
        if v.startswith('data:image'):
            # Validar formato MIME
            if not re.match(r'^data:image/(jpeg|png|jpg|webp);base64,', v):
                raise ValueError('Formato de imagen no soportado')
        
        # Verificar tamaño máximo (5MB en base64)
        if len(v) > 7_000_000:
            raise ValueError('Imagen demasiado grande (máximo 5MB)')
        
        return v


class FaceVerifyRequest(BaseModel):
    """DTO para verificación facial"""
    
    image_data: str = Field(..., description="Imagen en base64")
    
    @field_validator('image_data')
    @classmethod  
    def validate_image(cls, v: str) -> str:
        """Valida imagen base64"""
        if v.startswith('data:image'):
            if not re.match(r'^data:image/(jpeg|png|jpg|webp);base64,', v):
                raise ValueError('Formato de imagen no soportado')
        
        if len(v) > 7_000_000:
            raise ValueError('Imagen demasiado grande')
        
        return v


class UserResponse(BaseModel):
    """DTO de respuesta con datos del usuario (sin datos sensibles)"""
    
    id: int
    username: str
    email: Optional[str] = None
    role: str = "user"
    face_registered: bool
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """DTO de respuesta con token JWT"""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    requires_face_registration: bool = False
    requires_face_verification: bool = False


class MessageResponse(BaseModel):
    """DTO de respuesta genérica"""
    
    success: bool
    message: str
    data: Optional[dict] = None
