"""
Login Seguro - Conexión a Base de Datos PostgreSQL
Implementa connection pooling seguro con inicialización lazy
"""
import logging
from typing import Optional
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Gestiona la conexión a PostgreSQL con connection pooling.
    Usa inicialización lazy para evitar errores al arrancar.
    """
    
    _instance: Optional['DatabaseConnection'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._settings = get_settings()
    
    def _initialize_pool(self) -> bool:
        """Inicializa el pool de conexiones (lazy initialization)"""
        if self._pool is not None:
            return True
            
        try:
            settings = self._settings
            self._pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                dbname=settings.DATABASE_NAME,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD
            )
            logger.info("Pool de conexiones inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"Error al inicializar pool de conexiones: {e}")
            self._pool = None
            return False
    
    def get_connection(self):
        """Obtiene una conexión del pool"""
        if not self._initialize_pool():
            raise ConnectionError("No se pudo conectar a la base de datos. Asegúrese de que PostgreSQL esté corriendo.")
        return self._pool.getconn()
    
    def release_connection(self, conn):
        """Devuelve una conexión al pool"""
        if self._pool is not None:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """
        Context manager para obtener un cursor.
        Maneja automáticamente la conexión y el commit/rollback.
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error en operación de base de datos: {e}")
            raise
        finally:
            if conn:
                self.release_connection(conn)
    
    def close_all(self):
        """Cierra todas las conexiones del pool"""
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None
            logger.info("Pool de conexiones cerrado")


# Funciones de utilidad (no se inicializan al importar)
_db_instance: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """Obtiene la instancia de conexión a base de datos"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance
