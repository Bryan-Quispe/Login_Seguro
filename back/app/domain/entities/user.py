"""
Login Seguro - Entidad Usuario
Definición de la entidad de dominio User siguiendo DDD
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum
import json


class UserRole(str, Enum):
    """Roles de usuario en el sistema"""
    USER = "user"
    ADMIN = "admin"
    AUDITOR = "auditor"  # Rol separado para auditoría


@dataclass
class User:
    """Entidad de dominio que representa un usuario del sistema"""
    
    id: Optional[int] = None
    username: str = ""
    email: Optional[str] = None
    password_hash: str = ""
    face_encoding: Optional[str] = None  # JSON string con los 128 valores
    face_registered: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    role: str = UserRole.USER  # Rol del usuario (user/admin/auditor)
    requires_password_reset: bool = False  # Si debe cambiar contraseña
    backup_code_hash: Optional[str] = None  # Hash del código de respaldo para fallback biométrico
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def has_backup_code(self) -> bool:
        """Verifica si el usuario tiene un código de respaldo configurado"""
        return self.backup_code_hash is not None
    
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada"""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until
    
    def is_permanently_locked(self) -> bool:
        """Verifica si está bloqueado permanentemente (hasta que admin desbloquee)"""
        if self.locked_until is None:
            return False
        # Si locked_until es más de 1 año en el futuro, es bloqueo permanente
        return (self.locked_until - datetime.now()).days > 365
    
    def is_admin(self) -> bool:
        """Verifica si es administrador"""
        return self.role == UserRole.ADMIN
    
    def is_auditor(self) -> bool:
        """Verifica si es auditor"""
        return self.role == UserRole.AUDITOR
    
    def get_face_encoding_list(self) -> Optional[list]:
        """Convierte el encoding facial de JSON a lista"""
        if self.face_encoding is None:
            return None
        try:
            return json.loads(self.face_encoding)
        except json.JSONDecodeError:
            return None
    
    def set_face_encoding_from_list(self, encoding_list: list) -> None:
        """Convierte la lista de encoding a JSON para almacenar"""
        self.face_encoding = json.dumps(encoding_list)
        self.face_registered = True
    
    def increment_failed_attempts(self) -> None:
        """Incrementa el contador de intentos fallidos"""
        self.failed_login_attempts += 1
    
    def reset_failed_attempts(self) -> None:
        """Reinicia el contador de intentos fallidos"""
        self.failed_login_attempts = 0
        self.locked_until = None
