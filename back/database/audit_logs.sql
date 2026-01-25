-- =====================================================
-- SQL para tabla de auditoría en Supabase
-- =====================================================
-- Ejecutar en: Supabase Dashboard > SQL Editor > New query
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,          -- Ej: 'user_disabled', 'user_enabled', 'user_unlocked'
    admin_id INTEGER REFERENCES users(id),  -- ID del admin que realizó la acción
    admin_username VARCHAR(100),            -- Username del admin
    target_user_id INTEGER,                 -- ID del usuario afectado (si aplica)
    target_username VARCHAR(100),           -- Username del usuario afectado
    details TEXT,                           -- Detalles adicionales en JSON
    ip_address VARCHAR(45),                 -- IPv4 o IPv6
    user_agent TEXT,                        -- Navegador/dispositivo
    location_country VARCHAR(100),          -- País (de API de geolocalización)
    location_city VARCHAR(100),             -- Ciudad
    location_region VARCHAR(100),           -- Región/Estado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);

-- Verificar
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'audit_logs' 
ORDER BY ordinal_position;
