# 🔐 Login Seguro - Sistema de Autenticación Biométrica Facial

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)

Sistema de autenticación de dos factores con credenciales + verificación biométrica facial con anti-spoofing.

## � Ejecución Rápida

### Requisitos
- **Docker Desktop** (para PostgreSQL)
- **Python 3.10+**
- **Node.js 18+**

### Pasos

```powershell
# 1. Iniciar PostgreSQL con Docker
docker compose up -d

# 2. Backend (en una terminal nueva)
cd back
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload

# 3. Frontend (en otra terminal nueva)
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

## 📁 Estructura

```
Login_Seguro/
├── docker-compose.yml      # PostgreSQL 16
├── back/                   # Backend Python (FastAPI)
│   ├── app/
│   │   ├── main.py        # Entry point
│   │   ├── config/        # Configuración
│   │   ├── domain/        # Entidades e interfaces
│   │   ├── infrastructure/# BD y reconocimiento facial
│   │   ├── application/   # Casos de uso
│   │   └── presentation/  # Rutas API
│   └── requirements.txt
└── front/                  # Frontend Next.js
    └── src/
        ├── app/           # Páginas
        ├── components/    # Componentes React
        └── hooks/         # Custom hooks
```

## 🔒 Características de Seguridad

| Característica | Implementación |
|----------------|----------------|
| SQL Injection | Consultas parametrizadas |
| Contraseñas | Hash bcrypt (12 rondas) |
| Sesiones | JWT con expiración |
| Fuerza bruta | Rate limiting + bloqueo cuenta |
| Anti-Spoofing | MediaPipe (detecta fotos/videos) |
| Validación | Pydantic + bleach |

## 📡 API Endpoints

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Login con credenciales

### Biometría Facial
- `POST /api/face/register` - Registrar rostro (requiere JWT)
- `POST /api/face/verify` - Verificar rostro (requiere JWT)
- `GET /api/face/status` - Estado del registro facial

## 🛠️ Tecnologías

**Backend:** FastAPI, MediaPipe, PostgreSQL, Bcrypt, JWT  
**Frontend:** Next.js 15, TypeScript, Tailwind CSS, React Webcam

---
**Desarrollado para Software Seguro - 7mo Semestre**