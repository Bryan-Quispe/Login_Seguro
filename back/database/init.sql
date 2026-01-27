-- Inicialización de la base de datos para Login Seguro
-- Sistema de autenticación biométrica facial

-- Crear extensión para UUID (opcional pero recomendado)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,  -- 'user', 'auditor', 'admin'
    face_encoding TEXT,  -- JSON con el encoding facial (128 dimensiones)
    face_registered BOOLEAN DEFAULT FALSE,
    backup_code_hash VARCHAR(255),  -- Hash bcrypt del código de respaldo
    backup_code_encrypted VARCHAR(255),  -- Código cifrado para visualización
    backup_code_used BOOLEAN DEFAULT FALSE,
    backup_code_generated_at TIMESTAMP,
    requires_password_reset BOOLEAN DEFAULT FALSE,  -- Requiere cambio de contraseña
    failed_login_attempts INTEGER DEFAULT 0,
    failed_face_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Tabla de logs de auditoría para seguridad (acciones administrativas)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,  -- user_disabled, user_enabled, user_unlocked, admin_login, etc.
    admin_id INTEGER REFERENCES users(id),  -- ID del admin que realizó la acción
    admin_username VARCHAR(50),  -- Username del admin
    target_user_id INTEGER REFERENCES users(id),  -- ID del usuario afectado
    target_username VARCHAR(50),  -- Username del usuario afectado
    details TEXT,  -- Detalles adicionales en JSON
    ip_address VARCHAR(45),  -- IP desde donde se realizó la acción
    user_agent TEXT,  -- User agent del navegador
    location_country VARCHAR(100),  -- País detectado
    location_city VARCHAR(100),  -- Ciudad detectada
    location_region VARCHAR(100),  -- Región/Estado detectado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_id ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Nota: La tabla sessions es para almacenar tokens de sesión (opcional, para invalidación manual)
-- Actualmente el sistema usa JWT stateless, pero esta tabla permite:
-- 1. Invalidar sesiones específicas
-- 2. Ver sesiones activas de un usuario
-- 3. Cerrar todas las sesiones al cambiar contraseña
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
