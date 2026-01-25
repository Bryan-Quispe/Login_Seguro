-- =====================================================
-- SQL para agregar sistema de roles en Supabase
-- =====================================================
-- Ejecutar en: Supabase Dashboard > SQL Editor > New query
-- =====================================================

-- 1. Agregar columna de rol (si no existe)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='role') THEN
        ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
    END IF;
END $$;

-- 2. Agregar columna para reseteo de contraseña
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='users' AND column_name='requires_password_reset') THEN
        ALTER TABLE users ADD COLUMN requires_password_reset BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- 3. Crear índice en rol
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 4. Verificar estructura
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;
