-- Agregar columna para rastrear sesiones activas
-- Solo puede haber una sesión activa por usuario a la vez

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS active_session_token VARCHAR(500);

-- Crear índice para búsquedas rápidas por sesión
CREATE INDEX IF NOT EXISTS idx_users_active_session ON users(active_session_token);

-- Comentarios
COMMENT ON COLUMN users.active_session_token IS 'Token de sesión activa - solo una sesión permitida por usuario';
