# 🔐 Login Seguro - Sistema de Autenticación Biométrica Facial

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

Sistema de autenticación de dos factores con credenciales + verificación biométrica facial con anti-spoofing.

## 🚀 Ejecución Rápida

### Requisitos
- **Python 3.10+**
- **Node.js 18+**
- **Base de datos:** Supabase (nube) o Docker (local)

### Pasos

```powershell
# 1. Backend
cd back
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload

# 2. Frontend (en otra terminal)
cd front
npm install
npx next dev -p 3001
```

### URLs
| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3001 |
| Backend API | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:3000/docs |
| **Panel Admin** | http://localhost:3001/admin |

---

## 🧠 Sistema de Reconocimiento Facial

### Librería Utilizada
**OpenCV (cv2)** con clasificadores Haar Cascade para detección de rostros.

### ¿Cómo funciona?

1. **Detección:** Se usa `haarcascade_frontalface_default.xml` para localizar el rostro
2. **Extracción de características:** Se generan 128 valores numéricos basados en:
   - Histograma de intensidades (escala de grises)
   - Histogramas de color (H y S del espacio HSV)
3. **Almacenamiento:** El encoding se serializa a JSON y se guarda en la columna `face_encoding` de PostgreSQL
4. **Comparación:** Al verificar, se calcula la correlación de histogramas entre el encoding guardado y el actual

### Anti-Spoofing
- **Técnica:** Análisis de varianza Laplaciana
- **Cómo funciona:** Las fotos de fotos/pantallas tienen menos textura y variación que un rostro real
- **Umbral:** Si la varianza es < 30, se rechaza como posible spoofing

### Almacenamiento en Base de Datos

```sql
-- Columna en tabla users
face_encoding TEXT        -- JSON con array de 128 valores float
face_registered BOOLEAN   -- true si ya registró su rostro
```

---

## 🔒 Sistema de Seguridad

### Bloqueo de Cuenta

| Parámetro | Valor |
|-----------|-------|
| Intentos de login | 5 máximo |
| Intentos de verificación facial | 3 máximo |
| Tiempo de bloqueo | 15 minutos |
| Desbloqueo | Automático o por administrador |

### Roles de Usuario

| Rol | Permisos |
|-----|----------|
| `user` | Registro, login, verificación facial |
| `admin` | Todo lo anterior + gestionar usuarios |

### Credenciales de Administrador
- **Email:** admin@loginseguro.com
- **Contraseña:** S@bryromero123

---

## ⚠️ Requisitos para Registro Facial

> **IMPORTANTE:** Para un registro facial exitoso, el usuario debe:

- ✅ **Sin lentes** (de sol o recetados)
- ✅ **Sin mascarilla** o cualquier cobertura facial
- ✅ **Sin gorras o sombreros**
- ✅ **Buena iluminación** (luz frontal)
- ✅ **Mirar directamente a la cámara**
- ✅ **Rostro centrado** en el marco

---

## 🔒 Características de Seguridad

| Característica | Implementación |
|----------------|----------------|
| SQL Injection | Consultas parametrizadas (psycopg2) |
| Contraseñas | Hash bcrypt (12 rondas) |
| Sesiones | JWT con expiración 30 min |
| Fuerza bruta | Rate limiting + bloqueo cuenta |
| Anti-Spoofing | Análisis Laplaciano |
| Validación | Pydantic + sanitización |

## 📡 API Endpoints

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Login con credenciales

### Biometría Facial
- `POST /api/face/register` - Registrar rostro (requiere JWT)
- `POST /api/face/verify` - Verificar rostro (requiere JWT)
- `GET /api/face/status` - Estado del registro facial

### Administrador
- `GET /api/admin/users` - Listar usuarios bloqueados
- `POST /api/admin/unlock/{id}` - Desbloquear usuario

---

## 🛠️ Tecnologías

**Backend:** FastAPI, OpenCV, PostgreSQL/Supabase, Bcrypt, JWT  
**Frontend:** Next.js 15, TypeScript, Tailwind CSS, React Webcam

---
**Desarrollado para Software Seguro - 7mo Semestre**