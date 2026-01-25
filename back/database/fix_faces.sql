-- =====================================================
-- SQL para corregir estado de rostro de Admin y Auditor
-- =====================================================
-- Problema: Se crearon con face_registered = TRUE por error
-- Solución: Ponerlos en FALSE para que deban registrar rostro
-- =====================================================

UPDATE users 
SET face_registered = FALSE, 
    face_encoding = NULL 
WHERE username IN ('admin', 'audit');

-- Verificar el cambio
SELECT id, username, role, face_registered 
FROM users 
WHERE username IN ('admin', 'audit');
