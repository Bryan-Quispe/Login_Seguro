"""
Login Seguro - Entidad Usuario
Definición de la entidad de dominio User siguiendo DDD
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json


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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada"""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until
    
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
