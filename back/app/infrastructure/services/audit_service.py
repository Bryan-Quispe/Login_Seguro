"""
Login Seguro - Servicio de Auditoría
Registra todas las acciones del administrador con IP y ubicación
"""
import logging
import httpx
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from fastapi import Request

from ..database.connection import get_db

logger = logging.getLogger(__name__)


@dataclass
class AuditLog:
    """Registro de auditoría"""
    id: Optional[int] = None
    action: str = ""
    admin_id: Optional[int] = None
    admin_username: str = ""
    target_user_id: Optional[int] = None
    target_username: str = ""
    details: str = ""
    ip_address: str = ""
    user_agent: str = ""
    location_country: str = ""
    location_city: str = ""
    location_region: str = ""
    created_at: Optional[datetime] = None


class AuditService:
    """Servicio para registrar y consultar auditoría"""
    
    def __init__(self):
        self._db = get_db()
    
    def get_real_ip(self, request: Request) -> str:
        """
        Obtiene la IP real del cliente.
        Revisa headers de proxy en orden de prioridad.
        """
        # Headers en orden de prioridad
        headers_to_check = [
            "X-Forwarded-For",
            "X-Real-IP", 
            "CF-Connecting-IP",  # Cloudflare
            "True-Client-IP",
            "X-Client-IP"
        ]
        
        for header in headers_to_check:
            ip = request.headers.get(header)
            if ip:
                # X-Forwarded-For puede tener múltiples IPs, tomar la primera
                return ip.split(",")[0].strip()
        
        # Fallback al cliente directo
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def get_location_from_ip(self, ip: str, is_local_dev: bool = False) -> dict:
        """
        Obtiene ubicación geográfica a partir de la IP.
        Usa API gratuita ip-api.com
        
        Args:
            ip: Dirección IP
            is_local_dev: Si True, significa que es desarrollo local y se usará ubicación configurada
        """
        # Para desarrollo local, usar ubicación configurada (Quito, Ecuador)
        # ya que la geolocalización por IP del ISP no es precisa
        if is_local_dev:
            return {
                "country": "Ecuador",
                "city": "Sangolquí",
                "region": "Pichincha"
            }
        
        # IPs locales/privadas no tienen ubicación pública
        if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
            return {
                "country": "Ecuador",
                "city": "Sangolquí", 
                "region": "Pichincha"
            }
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Request Spanish results with lang=es
                response = await client.get(f"http://ip-api.com/json/{ip}?lang=es")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        return {
                            "country": data.get("country", ""),
                            "city": data.get("city", ""),
                            "region": data.get("regionName", "")
                        }
        except Exception as e:
            logger.warning(f"Error obteniendo ubicación para IP {ip}: {e}")
        
        # Fallback a Ecuador si no se puede obtener ubicación
        return {"country": "Ecuador", "city": "Sangolquí", "region": "Pichincha"}
    
    async def get_public_ip(self) -> str:
        """Obtiene la IP pública del servidor (útil para desarrollo local)"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get('https://api.ipify.org')
                if resp.status_code == 200:
                    return resp.text
        except:
            pass
        return ""

    async def log_action(
        self,
        request: Request,
        action: str,
        admin_id: int,
        admin_username: str,
        target_user_id: Optional[int] = None,
        target_username: str = "",
        details: str = ""
    ) -> bool:
        """Registra una acción de auditoría"""
        try:
            ip = self.get_real_ip(request)
            is_local_dev = False
            
            # Si es localhost, intentar obtener IP pública real
            if ip in ["127.0.0.1", "::1", "localhost"]:
                public_ip = await self.get_public_ip()
                if public_ip:
                    ip = public_ip
                    is_local_dev = True  # Marcar como desarrollo local para usar ubicación configurada
            
            user_agent = request.headers.get("User-Agent", "")[:500]
            # Usar ubicación configurada si es desarrollo local
            location = await self.get_location_from_ip(ip, is_local_dev)
            
            # Get Ecuador time (UTC-5)
            # Remove tzinfo to store as naive timestamp in DB (which reflects the local face value)
            from zoneinfo import ZoneInfo
            ec_time = datetime.now(ZoneInfo("America/Guayaquil")).replace(tzinfo=None)
            
            query = """
                INSERT INTO audit_logs 
                (action, admin_id, admin_username, target_user_id, target_username, 
                 details, ip_address, user_agent, location_country, location_city, location_region, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            with self._db.get_cursor() as cursor:
                cursor.execute(query, (
                    action,
                    admin_id,
                    admin_username,
                    target_user_id,
                    target_username,
                    details,
                    ip,
                    user_agent,
                    location.get("country", ""),
                    location.get("city", ""),
                    location.get("region", ""),
                    ec_time
                ))
                result = cursor.fetchone()
                
                logger.info(f"Audit log: {action} by {admin_username} from {ip} ({location.get('city', 'unknown')})")
                return result[0] if result else False
                
        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")
            return False
    
    async def log_failed_attempt(
        self,
        request: Request,
        username: str,
        reason: str,
        details: str = ""
    ) -> bool:
        """Registra un intento fallido (login, verificación facial, etc)"""
        try:
            # Obtener IP y ubicación pero continuar si falla
            is_local_dev = False
            try:
                ip = self.get_real_ip(request)
                
                # Intentar obtener IP pública si es local
                if ip in ["127.0.0.1", "::1", "localhost"]:
                    public_ip = await self.get_public_ip()
                    if public_ip:
                        ip = public_ip
                        is_local_dev = True  # Marcar como desarrollo local
            except:
                ip = "unknown"
                
            try:
                user_agent = request.headers.get("User-Agent", "")[:500]
            except:
                user_agent = "unknown"
                
            try:
                # Usar ubicación configurada si es desarrollo local
                location = await self.get_location_from_ip(ip, is_local_dev) if ip != "unknown" else {"country": "Ecuador", "city": "Sangolquí", "region": "Pichincha"}
            except:
                location = {"country": "Ecuador", "city": "Sangolquí", "region": "Pichincha"}
            
            # Get Ecuador time (UTC-5)
            from zoneinfo import ZoneInfo
            ec_time = datetime.now(ZoneInfo("America/Guayaquil")).replace(tzinfo=None)
            
            query = """
                INSERT INTO audit_logs 
                (action, admin_username, target_username, details, ip_address, user_agent, 
                 location_country, location_city, location_region, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            with self._db.get_cursor() as cursor:
                cursor.execute(query, (
                    "failed_attempt",
                    "SYSTEM",  # Registrado por el sistema
                    username,
                    f"{reason} - {details}",
                    ip,
                    user_agent,
                    location.get("country", ""),
                    location.get("city", ""),
                    location.get("region", ""),
                    ec_time
                ))
                return True
                
        except Exception as e:
            logger.error(f"Error registrando intento fallido: {e}")
            return False

    def get_logs(self, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Obtiene los logs de auditoría"""
        query = """
            SELECT id, action, admin_id, admin_username, target_user_id, target_username,
                   details, ip_address, user_agent, location_country, location_city, 
                   location_region, created_at
            FROM audit_logs
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        try:
            with self._db.get_cursor(commit=False) as cursor:
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                
                logs = []
                for row in rows:
                    logs.append(AuditLog(
                        id=row[0],
                        action=row[1],
                        admin_id=row[2],
                        admin_username=row[3] or "",
                        target_user_id=row[4],
                        target_username=row[5] or "",
                        details=row[6] or "",
                        ip_address=row[7] or "",
                        user_agent=row[8] or "",
                        location_country=row[9] or "",
                        location_city=row[10] or "",
                        location_region=row[11] or "",
                        created_at=row[12]
                    ))
                return logs
        except Exception as e:
            logger.error(f"Error obteniendo logs: {e}")
            return []
    
    def get_logs_count(self) -> int:
        """Cuenta total de logs"""
        query = "SELECT COUNT(*) FROM audit_logs"
        try:
            with self._db.get_cursor(commit=False) as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
        except:
            return 0


# Singleton
_audit_service: Optional[AuditService] = None

def get_audit_service() -> AuditService:
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
