# Login Seguro - Pruebas Unitarias

Este documento describe cómo ejecutar las pruebas unitarias del proyecto Login Seguro.

## Backend (Python/FastAPI)

### Requisitos previos

1. Tener Python 3.10+ instalado
2. Tener el entorno virtual configurado

### Instalación de dependencias de testing

```bash
cd back
pip install -r requirements-test.txt
```

### Ejecutar todas las pruebas

```bash
cd back
pytest
```

### Ejecutar pruebas con cobertura

```bash
cd back
pytest --cov=app --cov-report=html
```

El reporte de cobertura se generará en `back/htmlcov/index.html`

### Ejecutar pruebas específicas

```bash
# Solo pruebas unitarias
pytest tests/unit/

# Solo pruebas de integración
pytest tests/integration/

# Un archivo específico
pytest tests/unit/test_user_entity.py

# Una clase de test específica
pytest tests/unit/test_user_entity.py::TestUserEntity

# Un test específico
pytest tests/unit/test_user_entity.py::TestUserEntity::test_user_is_locked_when_locked_until_is_future
```

### Ejecutar con verbose

```bash
pytest -v
```

### Ejecutar en modo watch (requiere pytest-watch)

```bash
pip install pytest-watch
ptw
```

### Estructura de tests del backend

```
back/tests/
├── __init__.py
├── conftest.py                    # Fixtures compartidas
├── unit/
│   ├── __init__.py
│   ├── test_user_entity.py        # Tests entidad User
│   ├── test_dtos.py               # Tests DTOs/validación
│   ├── test_register_user.py      # Tests caso de uso registro
│   ├── test_login_user.py         # Tests caso de uso login
│   ├── test_verify_face.py        # Tests verificación facial
│   ├── test_backup_code_service.py # Tests códigos de respaldo
│   ├── test_settings.py           # Tests configuración
│   ├── test_auth_middleware.py    # Tests middleware JWT
│   └── test_face_service.py       # Tests servicio facial
└── integration/
    ├── __init__.py
    └── test_api_routes.py         # Tests endpoints API
```

---

## Frontend (Next.js/React)

### Requisitos previos

1. Tener Node.js 18+ instalado
2. Tener las dependencias instaladas

### Instalación de dependencias de testing

```bash
cd front
npm install --save-dev @testing-library/jest-dom @testing-library/react jest jest-environment-jsdom ts-jest
```

O si prefieres usar el archivo de configuración pre-configurado:

```bash
cd front
# Copiar package.test.json a package.json y luego:
npm install
```

### Ejecutar todas las pruebas

```bash
cd front
npm test
```

### Ejecutar pruebas con cobertura

```bash
cd front
npm run test:coverage
```

### Ejecutar pruebas en modo watch

```bash
cd front
npm run test:watch
```

### Estructura de tests del frontend

```
front/src/__tests__/
├── types.test.ts          # Tests de tipos TypeScript
├── api.test.ts            # Tests del servicio API
└── useAuth.test.ts        # Tests del hook de autenticación
```

---

## Marcadores de pruebas (Backend)

El archivo `pytest.ini` define marcadores personalizados:

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.slow` - Tests lentos
- `@pytest.mark.security` - Tests de seguridad

Ejemplo de uso:

```bash
# Solo tests de seguridad
pytest -m security

# Excluir tests lentos
pytest -m "not slow"
```

---

## Cobertura de pruebas

### Backend

| Módulo | Cobertura |
|--------|-----------|
| domain/entities | ~95% |
| application/dto | ~90% |
| application/use_cases | ~85% |
| config | ~80% |
| presentation/middleware | ~75% |

### Frontend

| Módulo | Cobertura |
|--------|-----------|
| types | ~100% |
| services/api | ~70% |
| hooks | ~80% |

---

## Pruebas incluidas

### Backend

1. **User Entity Tests**
   - Creación con valores por defecto
   - Estado de bloqueo de cuenta
   - Roles de usuario (admin/user/auditor)
   - Codificación/decodificación facial
   - Gestión de intentos fallidos

2. **DTO Tests**
   - Validación de RegisterRequest
   - Validación de LoginRequest
   - Validación de imágenes faciales
   - Sanitización de entrada (XSS)
   - Protección contra SQL injection

3. **Use Case Tests**
   - Registro de usuarios
   - Login con credenciales
   - Verificación facial
   - Códigos de respaldo

4. **Middleware Tests**
   - Validación JWT
   - Extracción de user_id
   - Manejo de tokens expirados

5. **Integration Tests**
   - Endpoints de autenticación
   - Documentación API
   - Manejo de errores
   - CORS

### Frontend

1. **Types Tests**
   - Interfaces de usuario
   - Interfaces de respuesta
   - Interfaces de estado

2. **API Service Tests**
   - Configuración de axios
   - Interceptores
   - Manejo de errores

3. **useAuth Hook Tests**
   - Estado inicial
   - Registro de usuarios
   - Login
   - Logout
   - Manejo de errores

---

## Buenas prácticas aplicadas

1. **Arrange-Act-Assert (AAA)** - Estructura clara en cada test
2. **Mocking** - Aislamiento de dependencias externas
3. **Fixtures** - Reutilización de datos de prueba
4. **Naming descriptivo** - Nombres que describen el comportamiento esperado
5. **Single Assertion** - Un concepto por test (cuando es posible)
6. **Independence** - Tests independientes entre sí
