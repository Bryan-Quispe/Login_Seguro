# 🔐 Login Seguro - Sistema de Autenticación Biométrica Facial

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-DNN-green.svg)](https://opencv.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)

Sistema de autenticación de dos factores con credenciales + verificación biométrica facial con anti-spoofing y código de respaldo.

---

## 🛠️ Stack Tecnológico Completo

### Backend
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.10+ | Lenguaje principal |
| **FastAPI** | 0.109.0 | Framework web asíncrono |
| **Uvicorn** | 0.27.0 | Servidor ASGI |
| **OpenCV** | 4.x | Procesamiento de imágenes y reconocimiento facial |
| **MediaPipe** | Latest | Detección facial alternativa |
| **NumPy** | Latest | Operaciones matemáticas con embeddings |
| **Pydantic** | 2.5.3 | Validación de datos y DTOs |
| **psycopg2** | Latest | Driver PostgreSQL |
| **SQLAlchemy** | 2.0.25 | ORM (opcional) |
| **python-jose** | 3.3.0 | Tokens JWT |
| **passlib** | 1.7.4 | Hash bcrypt para contraseñas |
| **cryptography** | 41.0+ | Cifrado Fernet (AES-128) |
| **SlowAPI** | 0.1.9 | Rate limiting |
| **Bleach** | 6.1.0 | Sanitización de inputs |

### Frontend
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Next.js** | 16.1.4 | Framework React con SSR |
| **React** | 19.2.3 | Librería UI |
| **TypeScript** | 5.x | Tipado estático |
| **Tailwind CSS** | 4.x | Estilos utilitarios |
| **Axios** | 1.13.2 | Cliente HTTP |
| **React Webcam** | 7.2.0 | Captura de video |
| **js-cookie** | 3.0.5 | Manejo de cookies |

### Base de Datos e Infraestructura
| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **PostgreSQL** | 16 | Base de datos relacional |
| **Docker** | 20+ | Contenedorización |
| **Docker Compose** | 3.8 | Orquestación de contenedores |

---

## 🚀 Guía de Instalación y Ejecución

### 📋 Requisitos Previos

| Requisito | Versión Mínima | Descripción |
|-----------|----------------|-------------|
| **Python** | 3.10+ | Lenguaje backend |
| **Node.js** | 18+ | Runtime para Next.js |
| **npm** | 9+ | Gestor de paquetes |
| **Docker** | 20+ | Para base de datos local (opcional) |
| **PostgreSQL** | 16 | Base de datos (Docker o Supabase) |

### 🗄️ Paso 1: Configurar Base de Datos

#### Opción A: Docker (Recomendado para desarrollo local)

```powershell
# En la raíz del proyecto, levantar PostgreSQL con Docker
docker-compose up -d

# Verificar que el contenedor esté corriendo
docker ps
```

> ⚠️ **Nota:** El archivo `docker-compose.yml` configura automáticamente:
> - Base de datos: `login_seguro`
> - Usuario: `admin`
> - Puerto: `5432`
> - Ejecuta `init.sql` para crear las tablas

#### Opción B: Supabase (Nube)

1. Crear proyecto en [Supabase](https://supabase.com)
2. Ejecutar el script `back/database/init.sql` en el SQL Editor
3. Configurar variables de entorno en `back/.env`:

```env
DATABASE_HOST=tu-proyecto.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=tu-password-supabase
```

#### 🔐 Variables de Entorno Backend (back/.env)

> **Recomendado:** definir todas las variables en `back/.env` para un entorno reproducible.

```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=login_seguro
DATABASE_USER=admin
DATABASE_PASSWORD=SecureP@ssw0rd2024!

# JWT
JWT_SECRET_KEY=super-secure-jwt-secret-key-change-in-production-2024!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Security
BCRYPT_ROUNDS=12
MAX_LOGIN_ATTEMPTS=3
LOCKOUT_DURATION_MINUTES=15

# CORS
CORS_ORIGINS=["http://localhost:3001","http://127.0.0.1:3001"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# Face Recognition (compat)
FACE_RECOGNITION_MODEL=VGG-Face
FACE_DISTANCE_THRESHOLD=0.6
```

### ⚙️ Paso 2: Backend (FastAPI + Python)

```powershell
# Navegar al directorio del backend
cd back

# Crear entorno virtual (recomendado)
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate   # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

### 🎨 Paso 3: Frontend (Next.js + React)

```powershell
# En otra terminal, navegar al frontend
cd front

# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npx next dev -p 3001
```

### 🌐 URLs del Sistema

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Frontend** | http://localhost:3001 | Interfaz de usuario |
| **Backend API** | http://localhost:3000 | API REST |
| **Swagger Docs** | http://localhost:3000/docs | Documentación interactiva |
| **ReDoc** | http://localhost:3000/redoc | Documentación alternativa |
| **Panel Admin** | http://localhost:3001/admin | Gestión de usuarios |
| **Auditoría** | http://localhost:3001/audit | Logs del sistema |

### 👤 Usuarios del Sistema (Solo desarrollo)

En el arranque, el backend crea/verifica estos usuarios:

- **Admin**: `admin@loginseguro.com` / `S@bryromero123`
- **Auditor**: `audit` / `S@bryromero123`

> ⚠️ **Importante:** Cambiar credenciales y `JWT_SECRET_KEY` en producción.

### 🔧 Script de Inicio Rápido (Windows)

```powershell
# Ejecutar desde la raíz del proyecto
.\start.ps1
```

---

## 🧠 Sistema de Reconocimiento Facial

### 🛠️ Tecnologías de Reconocimiento Facial

| Componente | Tecnología | Modelo/Archivo |
|------------|------------|----------------|
| **Detección Facial** | OpenCV DNN | `face_detection_yunet.onnx` |
| **Reconocimiento** | OpenCV DNN | `face_recognition_sface.onnx` |
| **Anti-Spoofing** | OpenCV | Análisis Laplaciano |
| **Fallback Detección** | OpenCV | Haar Cascade |
| **Fallback Reconocimiento** | OpenCV | LBP (Local Binary Patterns) |

### 📁 Modelos de Deep Learning

Los modelos ONNX se encuentran en `back/models/`:

| Archivo | Propósito | Especificaciones |
|---------|-----------|------------------|
| `face_detection_yunet.onnx` | Detector facial de alta precisión | Input: 320x320, Score: 0.9 |
| `face_recognition_sface.onnx` | Extractor de embeddings faciales | Output: Vector 128D |

### 🔄 Pipeline de Reconocimiento Facial

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FLUJO DE VERIFICACIÓN FACIAL                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CAPTURA            2. ANTI-SPOOFING        3. DETECCIÓN             │
│  ┌──────────┐          ┌──────────────┐        ┌─────────────┐          │
│  │  Webcam  │ ──────▶  │  Laplaciano  │ ─────▶ │   YuNet     │          │
│  │  Base64  │          │  Varianza>30 │        │   DNN       │          │
│  └──────────┘          └──────────────┘        └─────────────┘          │
│                               │                       │                 │
│                               ▼                       ▼                 │
│                        ¿Rostro Real?          ¿Rostro Detectado?        │
│                          │    │                  │       │              │
│                         Sí   No                 Sí      No              │
│                          │    │                  │       │              │
│                          │    └───────────▶ RECHAZAR ◀───┘              │
│                          │                                              │
│                          ▼                                              │
│  4. EXTRACCIÓN         5. COMPARACIÓN          6. RESULTADO            │
│  ┌─────────────┐       ┌──────────────┐        ┌─────────────┐          │
│  │   SFace     │ ────▶ │   Coseno     │ ─────▶ │  Match >    │          │
│  │  128-dim    │       │   70% + L2   │        │   35% ?     │          │
│  └─────────────┘       │   30%        │        └─────────────┘          │
│                        └──────────────┘               │                 │
│                                                   Sí     No             │
│                                                   │       │             │
│                                              ACCESO   DENEGADO          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 📊 Algoritmos de Reconocimiento

#### 1. YuNet - Detección Facial (DNN)
| Característica | Valor |
|----------------|-------|
| **Tipo** | Red Neuronal Convolucional |
| **Formato** | ONNX |
| **Input** | Imagen 320x320 px |
| **Score Threshold** | 0.9 |
| **NMS Threshold** | 0.3 |
| **Output** | Coordenadas (x, y, w, h) + 5 landmarks |

#### 2. SFace - Reconocimiento Facial (DNN)
| Característica | Valor |
|----------------|-------|
| **Tipo** | Embedding Facial Deep Learning |
| **Formato** | ONNX |
| **Dimensiones** | Vector de **128 características** (float32) |
| **Métricas** | Similitud Coseno + Distancia L2 |

#### 3. Métricas de Comparación
| Métrica | Peso | Descripción |
|---------|------|-------------|
| **Similitud Coseno** | 70% | Mide el ángulo entre vectores de embedding |
| **Distancia L2 Normalizada** | 30% | Distancia euclidiana normalizada |

### 🎯 Umbrales de Verificación

| Método | Umbral | Descripción |
|--------|--------|-------------|
| **SFace Coseno** | ≥ 0.35 (35%) | Similitud mínima requerida |
| **Distancia Combinada** | < 0.30 | Umbral de aceptación |
| **LBP Fallback** | ≥ 0.90 (90%) | Más estricto por menor precisión |

### 🛡️ Sistema Anti-Spoofing

| Técnica | Descripción | Umbral |
|---------|-------------|--------|
| **Varianza Laplaciana** | Detecta falta de textura en fotos/pantallas | > 30 |
| **Contraste (STD)** | Analiza desviación estándar de grises | > 20 |
| **Score Combinado** | Textura (70%) + Contraste (30%) | 0-1 |

**¿Cómo funciona el anti-spoofing?**
- Las fotos de fotos/pantallas tienen menos variación de textura
- El operador Laplaciano detecta bordes y detalles finos
- Un rostro real tiene mayor varianza que una imagen plana o impresa
- Se analiza también el contraste para detectar imágenes de baja calidad

### 🔄 Sistema de Fallback

Si los modelos DNN no están disponibles, el sistema usa automáticamente:

| Componente | Fallback | Descripción |
|------------|----------|-------------|
| **Detección** | Haar Cascade | `haarcascade_frontalface_default.xml` |
| **Reconocimiento** | LBP | Local Binary Patterns con CLAHE |
| **Preprocesamiento** | CLAHE | Ecualización adaptativa de histograma |

### 🔑 Código de Respaldo

| Característica | Valor |
|----------------|-------|
| **Longitud** | 8 caracteres alfanuméricos |
| **Uso** | Un solo uso (se invalida después) |
| **Almacenamiento** | Hash bcrypt en base de datos |
| **Visualización** | Cifrado Fernet (AES-128) |
| **Rate Limit** | 3 generaciones/hora/usuario |
| **Propósito** | Fallback cuando la verificación facial falla |

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
| Intentos de verificación facial | 3 máximo |
| Tiempo de bloqueo | 15 minutos |
| Desbloqueo | Automático o por administrador |

### Roles de Usuario

| Rol | Permisos |
|-----|----------|
| `user` | Registro, login, verificación facial, perfil |
| `auditor` | Todo lo anterior + ver logs de auditoría |
| `admin` | Todo lo anterior + gestionar usuarios |

### Características de Seguridad Implementadas

| Característica | Implementación |
|----------------|----------------|
| **SQL Injection** | Consultas parametrizadas (psycopg2) |
| **Contraseñas** | Hash bcrypt (12 rondas) |
| **Sesiones** | JWT con expiración 30 min |
| **Fuerza Bruta** | Rate limiting + bloqueo cuenta |
| **Anti-Spoofing** | Análisis Laplaciano + Contraste |
| **Validación** | Pydantic + sanitización Bleach |
| **HTTPS** | Requerido en producción |
| **Cookies Seguras** | `secure=true, sameSite=strict` |
| **Logout Seguro** | Limpieza completa de sesión |
| **Código de Respaldo** | Fallback cifrado para biometría |
| **Cifrado de Códigos** | Fernet (AES-128) derivado de JWT_SECRET |

---

## 🏗️ Arquitectura y Patrones de Diseño

### Clean Architecture (Separación de Capas)

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│           Next.js 16 + TypeScript + React Webcam            │
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

### Estructura del Proyecto

```
Login_Seguro/
├── docker-compose.yml          # Configuración de PostgreSQL
├── start.ps1                   # Script de inicio rápido
├── README.md
│
├── back/                       # Backend Python/FastAPI
│   ├── requirements.txt        # Dependencias Python
│   ├── models/                 # Modelos ONNX para reconocimiento facial
│   │   ├── face_detection_yunet.onnx
│   │   └── face_recognition_sface.onnx
│   ├── database/               # Scripts SQL
│   │   ├── init.sql
│   │   ├── add_roles.sql
│   │   └── audit_logs.sql
│   └── app/
│       ├── main.py             # Entry point FastAPI
│       ├── config/             # Configuración y settings
│       ├── domain/             # Entidades e interfaces
│       ├── application/        # Use cases y DTOs
│       ├── infrastructure/     # Repositorios y servicios
│       └── presentation/       # Routes y middleware
│
└── front/                      # Frontend Next.js/React
    ├── package.json
    ├── src/
    │   ├── app/                # Pages (App Router)
    │   ├── components/         # Componentes React
    │   ├── hooks/              # Custom hooks
    │   ├── services/           # API client
    │   └── types/              # TypeScript types
    └── public/
```

### Patrones de Diseño Implementados

| Patrón | Uso en el Sistema |
|--------|-------------------|
| **Repository** | `UserRepositoryImpl` abstrae acceso a datos |
| **Dependency Injection** | FastAPI `Depends()` inyecta repositorios y servicios |
| **Strategy** | Anti-spoofing configurable (Laplacian variance) |
| **Factory** | Creación de tokens JWT con configuración |
| **Singleton** | Conexión a base de datos (`connection.py`) |
| **DTO** | `LoginRequest`, `RegisterRequest` para transferencia de datos |
| **Facade** | `OpenCVDNNFaceService` unifica detección y reconocimiento |

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
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Registrar usuario |
| `POST` | `/api/auth/login` | Login con credenciales |
| `POST` | `/api/auth/logout` | Cerrar sesión |
| `GET` | `/api/auth/profile` | Obtener perfil de usuario |
| `PATCH` | `/api/auth/preferences` | Actualizar preferencias |
| `POST` | `/api/auth/change-password` | Cambiar contraseña (obligatorio si aplica) |
| `GET` | `/api/auth/health` | Health check de autenticación |

### Biometría Facial
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/face/register` | Registrar rostro (requiere JWT) |
| `POST` | `/api/face/verify` | Verificar rostro (requiere JWT) |
| `GET` | `/api/face/status` | Estado del registro facial |
| `GET` | `/api/face/backup-code` | Estado del código de respaldo |
| `POST` | `/api/face/backup-code/generate` | Generar código de respaldo |
| `POST` | `/api/face/backup-code/verify` | Verificar código (lo invalida) |

### Administrador
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/admin/users` | Listar todos los usuarios |
| `GET` | `/api/admin/users/search?q=` | Buscar usuarios |
| `GET` | `/api/admin/users/blocked` | Listar bloqueados |
| `GET` | `/api/admin/stats` | Estadísticas del sistema |
| `POST` | `/api/admin/users` | Crear nuevo usuario |
| `PUT` | `/api/admin/users/{id}` | Actualizar usuario |
| `POST` | `/api/admin/unlock/{id}` | Desbloquear usuario |
| `POST` | `/api/admin/disable/{id}` | Deshabilitar usuario |
| `POST` | `/api/admin/enable/{id}` | Habilitar usuario |

### Auditoría
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/audit/logs` | Ver logs de auditoría (solo auditor) |
| `GET` | `/api/audit/stats` | Estadísticas de auditoría (solo auditor) |

---

## ♿ Accesibilidad

- Labels ARIA en todos los componentes interactivos
- Roles semánticos en modales y formularios
- Navegación por teclado soportada
- Contraste de colores WCAG 2.1 AA

---

## 📚 Referencias y Documentación

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenCV Face Detection](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html)
- [YuNet Paper](https://arxiv.org/abs/2108.03312)
- [SFace: Sigmoid-Constrained Hypersphere Loss](https://arxiv.org/abs/2205.12010)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Webcam](https://github.com/mozmorris/react-webcam)

---

**Desarrollado para Software Seguro - 7mo Semestre**
