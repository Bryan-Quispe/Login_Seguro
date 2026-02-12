# 🎨 Frontend - Login Seguro

Frontend del sistema **Login Seguro** construido con **Next.js 16** + **React 19** + **TypeScript**. Provee la interfaz para autenticación, registro facial y paneles de administración/auditoría.

---

## 🧩 Stack Tecnológico

- **Next.js** 16.1.4 (App Router)
- **React** 19.2.3
- **TypeScript** 5.x
- **Tailwind CSS** 4.x
- **Axios** para consumo de API
- **React Webcam** para captura de video

---

## 🚀 Instalación y Ejecución

```bash
# desde /front
npm install
npm run dev -- -p 3001
```

Abrir: http://localhost:3001

> El backend debe estar corriendo en http://localhost:3000

---

## 🔧 Scripts Disponibles

| Script | Descripción |
|--------|-------------|
| `npm run dev` | Levanta entorno de desarrollo |
| `npm run build` | Build de producción |
| `npm run start` | Servir build de producción |
| `npm run lint` | Ejecuta ESLint |

---

## 🔐 Funcionalidades Clave

- Login seguro con JWT
- Registro facial con webcam
- Verificación facial (anti-spoofing en backend)
- Código de respaldo (fallback biométrico)
- Panel de administración de usuarios
- Panel de auditoría
- Gestión de perfil y preferencias

---

## 🧭 Rutas Principales

| Ruta | Descripción |
|------|-------------|
| `/` | Home / Landing |
| `/login` | Login |
| `/register` | Registro de usuario |
| `/face-register` | Registro facial |
| `/face-verify` | Verificación facial |
| `/dashboard` | Panel del usuario |
| `/change-password` | Cambio de contraseña |
| `/admin` | Panel admin |
| `/audit` | Panel auditoría |

---

## ⚙️ Configuración

El frontend consume la API del backend. Si cambias el host/puerto, ajusta el cliente en:

- [src/services/api.ts](src/services/api.ts)

---

## 🧪 Análisis de Seguridad (Frontend)

```bash
node run_security_analysis.js
```

Genera el reporte en `front/security_report_frontend.json`.

---

## ✅ Accesibilidad

- ARIA labels en componentes interactivos
- Navegación por teclado en formularios
- Contraste WCAG 2.1 AA

---

**Desarrollado para Software Seguro - 7mo Semestre**
