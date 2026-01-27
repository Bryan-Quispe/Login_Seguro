# 🔐 Login Seguro - Sistema de Autenticación Biométrica Facial

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

Sistema de autenticación de dos factores con credenciales + verificación biométrica facial con anti-spoofing y código de respaldo.

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
**OpenCV (cv2)** con clasificadores Haar Cascade para detección de rostros y **LBP (Local Binary Patterns)** para extracción de características.

### ¿Cómo funciona?

1. **Detección:** Se usa `haarcascade_frontalface_default.xml` para localizar el rostro
2. **Preprocesamiento:** Ecualización de histograma para normalizar iluminación
3. **Extracción de características (LBP):**
   - Se calcula el patrón binario local de cada píxel comparando con sus 8 vecinos
   - Se divide el rostro en una grilla de 8x8 celdas
   - Se genera un histograma de 16 bins por cada celda
   - Resultado: Vector de 1024 características (64 celdas × 16 bins)
4. **Almacenamiento:** El encoding se serializa a JSON y se guarda en la columna `face_encoding` de PostgreSQL
5. **Comparación:** Al verificar, se usan múltiples métricas:
   - Intersección de histogramas (40%)
   - Chi-Square (30%)
   - Correlación (30%)

### Ventajas de LBP
- **Invariante a cambios de iluminación** - funciona mejor con diferentes condiciones de luz
- **Robusto a cambios de fondo** - se enfoca en patrones de textura facial
- **Eficiente computacionalmente** - no requiere GPU

### Anti-Spoofing
- **Técnica:** Análisis de varianza Laplaciana
- **Cómo funciona:** Las fotos de fotos/pantallas tienen menos textura y variación que un rostro real
- **Umbral:** Si la varianza es < 30, se rechaza como posible spoofing

### Código de Respaldo
- **Fallback seguro** cuando la verificación facial falla
- Código alfanumérico de 8 caracteres (**un solo uso**)
- Hash bcrypt almacenado en base de datos
- Código cifrado con Fernet (AES-128) para visualización
- **Importante:** Después de usar el código, se invalida automáticamente
- Rate limit: 3 generaciones por hora por usuario

---

## 🔒 Sistema de Seguridad

### Rate Limiting (Protección Fuerza Bruta)

| Endpoint | Límite | Propósito |
|----------|--------|-----------|
| `/api/auth/register` | 5/min | Prevenir spam de registros |
| `/api/auth/login` | 10/min | Bloquear ataques de fuerza bruta |
| `/api/face/register` | 30/min | Permitir múltiples intentos de registro |
| `/api/face/verify` | 5/min | Limitar verificaciones fallidas |
| `/api/face/backup-code/generate` | 3/hora | Seguridad de códigos de respaldo |
| `/api/face/backup-code/verify` | 5/min | Bloquear intentos de adivinación |

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
| `user` | Registro, login, verificación facial, perfil |
| `auditor` | Todo lo anterior + ver logs de auditoría |
| `admin` | Todo lo anterior + gestionar usuarios |



---

## 🏗️ Arquitectura y Patrones de Diseño

### Clean Architecture (Separación de Capas)

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│           Next.js 15 + TypeScript + React Webcam            │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (HTTPS)
┌─────────────────────────▼───────────────────────────────────┐
│                 Presentation Layer                           │
│     Controllers/Routes (FastAPI + JWT + Rate Limiting)       │
├─────────────────────────────────────────────────────────────┤
│                 Application Layer                            │
│            Use Cases + DTOs + Validación Pydantic            │
├─────────────────────────────────────────────────────────────┤
│                   Domain Layer                               │
│          Entidades + Reglas de Negocio + Interfaces          │
├─────────────────────────────────────────────────────────────┤
│               Infrastructure Layer                           │
│     Repositorios + Servicios Externos + Base de Datos       │
└─────────────────────────────────────────────────────────────┘
```

### Patrones de Diseño Implementados

| Patrón | Uso en el Sistema |
|--------|-------------------|
| **Repository** | `UserRepositoryImpl` abstrae acceso a datos |
| **Dependency Injection** | FastAPI `Depends()` inyecta repositorios y servicios |
| **Strategy** | Anti-spoofing configurable (Laplacian variance) |
| **Factory** | Creación de tokens JWT con configuración |
| **Singleton** | Conexión a base de datos (`db_connection.py`) |
| **DTO** | `LoginRequest`, `RegisterRequest` para transferencia de datos |

### Principios SOLID

| Principio | Implementación |
|-----------|----------------|
| **S**ingle Responsibility | Cada use case tiene una sola responsabilidad |
| **O**pen/Closed | Nuevos validadores sin modificar existentes |
| **L**iskov Substitution | Repositorios implementan interfaces base |
| **I**nterface Segregation | Interfaces específicas por dominio |
| **D**ependency Inversion | Use cases dependen de abstracciones |

---

## ⚙️ Análisis de Seguridad

### Ejecución de Análisis Estático

```powershell
# Backend (Python con Bandit)
cd back
pip install bandit
python run_security_analysis.py

# Frontend (TypeScript/React)
cd front
node run_security_analysis.js
```

Los reportes se generan en:
- `back/security_report_bandit.json`
- `front/security_report_frontend.json`

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
| HTTPS | Requerido en producción |
| Cookies Seguras | `secure=true, sameSite=strict` |
| Logout Seguro | Limpieza completa de sesión |
| Código de Respaldo | Fallback cifrado para biometría (un solo uso) |
| Cifrado de Códigos | Fernet (AES-128) derivado de JWT_SECRET |

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

## 📡 API Endpoints

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Login con credenciales
- `GET /api/auth/profile` - Obtener perfil de usuario
- `PATCH /api/auth/preferences` - Actualizar preferencias

### Biometría Facial
- `POST /api/face/register` - Registrar rostro (requiere JWT)
- `POST /api/face/verify` - Verificar rostro (requiere JWT)
- `GET /api/face/status` - Estado del registro facial
- `GET /api/face/backup-code` - Obtener estado del código de respaldo
- `POST /api/face/backup-code/generate` - Generar código de respaldo
- `POST /api/face/backup-code/verify` - Verificar código de respaldo (lo invalida)

### Administrador
- `GET /api/admin/users` - Listar todos los usuarios
- `GET /api/admin/users/search?q=` - Buscar usuarios
- `GET /api/admin/users/blocked` - Listar bloqueados
- `GET /api/admin/stats` - Estadísticas del sistema
- `POST /api/admin/users` - Crear nuevo usuario
- `PUT /api/admin/users/{id}` - Actualizar usuario
- `POST /api/admin/unlock/{id}` - Desbloquear usuario
- `POST /api/admin/disable/{id}` - Deshabilitar usuario
- `POST /api/admin/enable/{id}` - Habilitar usuario

### Auditoría
- `GET /api/audit/logs` - Ver logs de auditoría (solo auditor/admin)

---

## 🛠️ Tecnologías

**Backend:** FastAPI, OpenCV (LBP), PostgreSQL/Docker, Bcrypt, JWT, SlowAPI, Cryptography (Fernet)  
**Frontend:** Next.js 15, TypeScript, Tailwind CSS, React Webcam  
**Seguridad:** Bandit (Python), ESLint Security (TypeScript)

---

## ♿ Accesibilidad

- Labels ARIA en todos los componentes interactivos
- Roles semánticos en modales y formularios
- Navegación por teclado soportada
- Contraste de colores WCAG 2.1 AA

---

**Desarrollado para Software Seguro - 7mo Semestre**
