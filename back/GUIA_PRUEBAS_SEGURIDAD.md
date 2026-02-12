# 🛡️ Guía Completa de Pruebas de Seguridad - Login Seguro

## 📋 Tabla de Contenido
1. [Requisitos Previos](#requisitos-previos)
2. [Configuración del Entorno](#configuración-del-entorno)
3. [Pruebas Estáticas (Modelo de IA)](#pruebas-estáticas-modelo-de-ia)
4. [Pruebas Dinámicas (XSS, CSRF)](#pruebas-dinámicas-xss-csrf)
5. [Análisis de Cobertura](#análisis-de-cobertura)
6. [Ejecución Completa](#ejecución-completa)
7. [Interpretar Resultados](#interpretar-resultados)

---

## 📦 Requisitos Previos

### Dependencias del Sistema
- Python 3.11+
- Entorno virtual Python activado

### Paquetes Python Necesarios

```bash
# Activar entorno virtual (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Instalar dependencias básicas del proyecto
pip install -r requirements.txt

# Instalar dependencias adicionales para análisis de seguridad
pip install pandas scikit-learn numpy pytest-json-report pytest-cov
```

---

## ⚙️ Configuración del Entorno

### Paso 1: Activar Entorno Virtual

**Windows PowerShell:**
```powershell
cd D:\Login_Seguro
.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
cd D:\Login_Seguro
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
cd /path/to/Login_Seguro
source .venv/bin/activate
```

### Paso 2: Verificar Instalación

```bash
python --version  # Debe ser 3.11+
pip list | grep pytest
pip list | grep pandas
```

---

## 🔍 Pruebas Estáticas (Modelo de IA)

### ¿Qué son las Pruebas Estáticas?

Las pruebas estáticas analizan el **código fuente** sin ejecutarlo. Nuestro modelo de IA (Random Forest) fue entrenado con datasets de CVE/CWE para detectar:

- 🚨 Inyecciones SQL
- 🚨 XSS (Cross-Site Scripting)
- 🚨 Uso de funciones peligrosas (`eval`, `exec`)
- 🚨 Secrets hardcodeados
- 🚨 Criptografía débil
- 🚨 Deserialización insegura
- 🚨 Manejo inadecuado de excepciones

### Ejecutar Solo Análisis Estático

```bash
cd back
python run_security_analysis.py --skip-dynamic --skip-coverage
```

### Cómo Funciona

1. **Extracción de Características**: El `CodeAnalyzer` parsea cada archivo `.py` usando AST (Abstract Syntax Tree)
2. **Análisis de Patrones**: Detecta patrones de riesgo (regex, imports, llamadas a funciones)
3. **Predicción con IA**: El modelo Random Forest predice probabilidad de vulnerabilidad
4. **Clasificación de Riesgo**:
   - 🔴 **Alto**: Probabilidad ≥ 70%
   - 🟡 **Medio**: Probabilidad 40-70%
   - 🟢 **Bajo**: Probabilidad < 40%

### Ejemplo de Salida

```
📊 ANÁLISIS ESTÁTICO CON MODELO DE IA
======================================================================
Analizando 45 archivos Python...
🔴 app/infrastructure/database/connection.py: VULNERABLE (85.3%)
  - Posible SQL Injection (concatenación)
  - Secrets hardcodeados detectados
🟢 app/domain/entities/user.py: SEGURO (12.4%)
🟢 app/presentation/routes/auth_routes.py: SEGURO (8.9%)
...
```

---

## 🎯 Pruebas Dinámicas (XSS, CSRF)

### ¿Qué son las Pruebas Dinámicas?

Las pruebas dinámicas **ejecutan** la aplicación y simulan ataques reales. Incluyen:

#### 1. XSS (Cross-Site Scripting)

**XSS Reflejado:**
```python
# Envía payload malicioso
payload = '<script>alert("xss")</script>'
response = client.post("/api/auth/register", json={
    "username": payload,
    "password": "Test@12345"
})

# Verifica que NO se refleje sin escapar
assert payload not in response.text
```

**XSS Persistente:**
```python
# Almacena payload en BD
payload = '<img src=x onerror=alert(1) />'
client.post("/api/admin/users", json={"bio": payload})

# Verifica que al leer NO ejecute el script
response = client.get("/api/admin/users/1")
assert payload not in response.text
```

#### 2. CSRF (Cross-Site Request Forgery)

```python
# Simula login para obtener sesión
client.post("/api/auth/login", json={...})

# Intenta acción sensible SIN token CSRF
response = client.post("/api/admin/disable/1")

# Debe rechazar (403 Forbidden)
assert response.status_code == 403
```

### Ejecutar Solo Pruebas Dinámicas

```bash
cd back
pytest tests/integration/test_dynamic_security.py -v
```

### Con Reporte Detallado

```bash
pytest tests/integration/test_dynamic_security.py -v --tb=long --json-report --json-report-file=dynamic_tests.json
```

### Archivo de Pruebas Dinámicas

**Ubicación:** `back/tests/integration/test_dynamic_security.py`

**Estructura:**
```python
class TestDynamicXSS:
    """Simulaciones de ataques XSS"""
    
    async def test_reflected_xss_payload_is_escaped(self, client):
        # Prueba XSS reflejado
        ...
    
    async def test_persistent_xss_check(self, client):
        # Prueba XSS almacenado
        ...

class TestDynamicCSRF:
    """Simulaciones de ataques CSRF"""
    
    async def test_csrf_missing_token_rejected_template(self, client):
        # Verifica protección CSRF
        ...
```

---

## 📈 Análisis de Cobertura

### ¿Qué es la Cobertura de Código?

Mide qué porcentaje del código fue ejecutado por las pruebas.

### Ejecutar Cobertura

```bash
cd back
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Ver Reporte HTML

```bash
# Abre en navegador
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

### Métricas Importantes

- **Statements**: Líneas de código ejecutadas
- **Missing**: Líneas nunca ejecutadas
- **Branch Coverage**: Cobertura de condicionales (if/else)

### Objetivo

- ✅ **>80%**: Excelente
- ⚠️ **60-80%**: Aceptable
- ❌ **<60%**: Insuficiente

---

## 🚀 Ejecución Completa

### Comando Principal

```bash
cd D:\Login_Seguro\back
python run_security_analysis.py
```

Este comando ejecuta:
1. ✅ Análisis estático con modelo de IA
2. ✅ Pruebas dinámicas (XSS, CSRF)
3. ✅ Análisis de cobertura
4. ✅ Generación de informe `INFORME_SEGURIDAD.md`

### Opciones Disponibles

```bash
# Omitir análisis estático
python run_security_analysis.py --skip-static

# Omitir pruebas dinámicas
python run_security_analysis.py --skip-dynamic

# Omitir cobertura
python run_security_analysis.py --skip-coverage

# Cambiar ruta del informe
python run_security_analysis.py --output mi_informe.md
```

### Ejemplo Completo (Paso a Paso)

```powershell
# 1. Abrir PowerShell en carpeta del proyecto
cd D:\Login_Seguro

# 2. Activar entorno virtual
.venv\Scripts\Activate.ps1

# 3. Asegurar dependencias
pip install pytest-json-report pytest-cov pandas scikit-learn

# 4. Ir a carpeta back
cd back

# 5. Ejecutar análisis completo
python run_security_analysis.py

# 6. Revisar informe generado
notepad INFORME_SEGURIDAD.md
```

---

## 📊 Interpretar Resultados

### Informe Generado: `INFORME_SEGURIDAD.md`

#### Sección 1: Resumen Ejecutivo

```markdown
## 📊 Resumen Ejecutivo

### Análisis Estático (Modelo de IA)
- **Archivos analizados:** 45
- **Vulnerabilidades detectadas:** 3
- **Archivos seguros:** 42
```

**Interpretación:**
- Si hay vulnerabilidades detectadas, revisar la sección de "Archivos de Alto Riesgo"
- Cada archivo vulnerable tiene una lista de issues específicos

#### Sección 2: Pruebas Dinámicas

```markdown
### Pruebas Dinámicas (XSS, CSRF)
- **Tests ejecutados:** 6
- **Pasados:** 6
- **Fallidos:** 0
```

**Interpretación:**
- ✅ **0 fallidos**: Todas las protecciones funcionan
- ❌ **> 0 fallidos**: Revisar logs, hay vulnerabilidades explotables

#### Sección 3: Cobertura

```markdown
### Cobertura de Código
- **Cobertura total:** 78.45%
```

**Acción:**
- Si < 80%, añadir más pruebas unitarias/integración
- Revisar `htmlcov/index.html` para ver archivos sin cobertura

#### Sección 4: Archivos de Alto Riesgo

```markdown
#### 🔴 Archivos de Alto Riesgo

- **app/infrastructure/database/connection.py** - Probabilidad: 85.3%
  - Posible SQL Injection (concatenación)
  - Secrets hardcodeados detectados
```

**Acción Inmediata:**
1. Abrir archivo mencionado
2. Buscar concatenación SQL (ej: `f"SELECT * FROM users WHERE id={user_id}"`)
3. Reemplazar con consultas parametrizadas
4. Buscar variables con `password` o `api_key` hardcodeadas
5. Moverlas a variables de entorno

---

## 🛠️ Correcciones Comunes

### 1. SQL Injection Detectada

**Problema:**
```python
# ❌ MAL - Concatenación directa
query = f"SELECT * FROM users WHERE username='{username}'"
cursor.execute(query)
```

**Solución:**
```python
# ✅ BIEN - Consulta parametrizada
query = "SELECT * FROM users WHERE username=%s"
cursor.execute(query, (username,))
```

### 2. XSS Test Fallido

**Problema:**
```python
# ❌ API devuelve input sin sanitizar
return {"message": f"Hola {username}"}
```

**Solución:**
```python
# ✅ Pydantic valida automáticamente
from pydantic import BaseModel, validator

class UserInput(BaseModel):
    username: str
    
    @validator('username')
    def sanitize_username(cls, v):
        # Remover caracteres peligrosos
        return re.sub(r'[<>]', '', v)
```

### 3. Secrets Hardcodeados

**Problema:**
```python
# ❌ Secret en código
DB_PASSWORD = "myP@ssw0rd123"
```

**Solución:**
```python
# ✅ Variable de entorno
import os
DB_PASSWORD = os.getenv("DB_PASSWORD")
```

---

## 📚 Herramientas Adicionales (Opcionales)

### OWASP ZAP (Escaneo Web Dinámico)

```bash
# Iniciar ZAP en modo daemon
docker run -u zap -p 8080:8080 owasp/zap2docker-stable zap.sh -daemon

# Ejecutar escaneo baseline
docker run --rm -v $(pwd):/zap/wrk owasp/zap2docker-stable zap-baseline.py -t http://localhost:3000 -r zap_report.html
```

### SQLMap (Detección SQL Injection)

```bash
sqlmap -u "http://localhost:3000/api/auth/login" \
       --data="username=test&password=test" \
       --batch --level=5 --risk=3
```

### Bandit (Análisis Estático Python)

```bash
pip install bandit
bandit -r app/ -f json -o bandit_report.json
```

---

## ✅ Checklist Final

Antes de entregar el proyecto, verificar:

- [ ] Ejecuté `python run_security_analysis.py` exitosamente
- [ ] Revisé `INFORME_SEGURIDAD.md` completo
- [ ] No hay archivos de "Alto Riesgo" sin revisar
- [ ] Todas las pruebas dinámicas pasan (0 fallidos)
- [ ] Cobertura de código > 70%
- [ ] No hay secrets hardcodeados en el código
- [ ] Consultas SQL usan parámetros (no concatenación)
- [ ] Endpoints validan entrada con Pydantic
- [ ] HTTPS está configurado para producción
- [ ] Rate limiting está activo

---

## 📞 Soporte

Para más información sobre interpretación de resultados o corrección de vulnerabilidades:

- **Documentación OWASP**: https://owasp.org/www-project-top-ten/
- **CWE Database**: https://cwe.mitre.org/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/

---

**Generado por:** `run_security_analysis.py`  
**Versión:** 1.0  
**Fecha:** 2026-02-11
