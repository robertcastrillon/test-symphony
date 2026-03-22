# ChronoTrack — Product Requirements Document

**Version:** 1.0
**Stack:** FastAPI · PostgreSQL · React · TypeScript · Docker Compose
**Objetivo:** Time tracking para freelancers con dashboard visual, facturación y bot de Telegram

---

## 1. Visión del Producto

ChronoTrack permite a freelancers registrar sesiones de trabajo, agruparlas por proyecto y cliente, generar facturas PDF y consultar métricas de productividad. La propuesta de valor es la **fricción mínima**: el freelancer puede loguear tiempo desde el navegador, desde Telegram, o desde la API directamente.

**Usuarios objetivo:**
- Freelancers individuales
- Equipos pequeños (1-5 personas)

---

## 2. Stack Técnico

| Capa | Tecnología |
|------|-----------|
| API | Python 3.12 · FastAPI · SQLAlchemy async · Alembic |
| Base de datos | PostgreSQL 16 |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS |
| Auth | JWT (access + refresh tokens) · passlib[bcrypt] · `bcrypt==4.0.1` |
| PDF | WeasyPrint o reportlab |
| Bot | python-telegram-bot v20 (async) |
| Infra | Docker Compose (api + web + db + bot) |
| Tests API | pytest · pytest-asyncio · httpx |
| Tests UI | Vitest · React Testing Library |
| E2E | Playwright (via MCP en Quality Check / Local Review) |

---

## 3. Arquitectura

```
docker-compose.yml
  ├── db          PostgreSQL 16 — puerto 5432
  ├── api         FastAPI — puerto 8000
  │               GET  /api/v1/health
  │               POST /api/v1/auth/register
  │               POST /api/v1/auth/login
  │               POST /api/v1/auth/refresh
  │               CRUD /api/v1/clients
  │               CRUD /api/v1/projects
  │               CRUD /api/v1/sessions
  │               POST /api/v1/sessions/start   ← timer start
  │               POST /api/v1/sessions/stop    ← timer stop
  │               GET  /api/v1/reports/summary  ← horas por proyecto/cliente
  │               POST /api/v1/invoices         ← genera PDF
  │               GET  /api/v1/invoices/{id}/pdf
  │               POST /api/v1/telegram/webhook ← webhook del bot
  ├── web         React — puerto 5173
  │               /login · /register
  │               /dashboard         ← resumen horas semana/mes + timer activo
  │               /projects          ← CRUD proyectos
  │               /clients           ← CRUD clientes
  │               /sessions          ← listado y registro manual
  │               /reports           ← gráficos horas por proyecto/período
  │               /invoices          ← generar y descargar PDF
  └── bot         Telegram bot (opcional, deshabilitado si no hay TELEGRAM_TOKEN)
                  /start → bienvenida + ayuda
                  /log <horas> <proyecto> <descripción> → registra sesión manual
                  /status → sesión activa actual
                  /report → resumen de la semana
                  /stop → detener sesión activa
```

---

## 4. Modelo de Datos

```sql
-- users
id uuid PK
email varchar UNIQUE NOT NULL
name varchar NOT NULL
hashed_password varchar NOT NULL
telegram_chat_id bigint NULL
created_at timestamptz DEFAULT now()

-- clients
id uuid PK
user_id uuid FK users
name varchar NOT NULL
email varchar NULL
hourly_rate numeric(10,2) DEFAULT 0
currency varchar(3) DEFAULT 'USD'
created_at timestamptz

-- projects
id uuid PK
user_id uuid FK users
client_id uuid FK clients NULL
name varchar NOT NULL
description text NULL
color varchar(7) DEFAULT '#6366f1'   -- hex color para UI
is_active boolean DEFAULT true
created_at timestamptz

-- sessions
id uuid PK
user_id uuid FK users
project_id uuid FK projects
description text NULL
started_at timestamptz NOT NULL
ended_at timestamptz NULL           -- NULL = sesión activa
duration_seconds integer NULL       -- computed al hacer stop
created_at timestamptz

-- invoices
id uuid PK
user_id uuid FK users
client_id uuid FK clients
invoice_number varchar UNIQUE NOT NULL  -- INV-2026-001
period_start date NOT NULL
period_end date NOT NULL
total_hours numeric(10,2)
total_amount numeric(10,2)
currency varchar(3)
status varchar DEFAULT 'draft'       -- draft | sent | paid
pdf_path varchar NULL
created_at timestamptz
```

---

## 5. Requisitos Funcionales

### 5.1 Autenticación y Usuarios

**RF-AUTH-01:** Registro con email y contraseña
- Email único, validado
- Password mínimo 8 caracteres, hasheado con bcrypt==4.0.1
- Retorna access token (15 min) + refresh token (30 días)

**RF-AUTH-02:** Login con email y contraseña
- Retorna mismo par de tokens
- Invalida refresh tokens anteriores del usuario

**RF-AUTH-03:** Refresh de access token
- Endpoint `POST /api/v1/auth/refresh` acepta refresh token
- Rota el refresh token (rotation strategy)

**Criterios de aceptación (BDD):**
```gherkin
Feature: Autenticación de usuarios
  Scenario: Registro exitoso
    Given un email no registrado "nuevo@test.com"
    When el usuario se registra con password "Seguro123!"
    Then recibe un access token válido
    And puede acceder a endpoints protegidos

  Scenario: Login con credenciales correctas
    Given un usuario registrado "user@test.com"
    When hace login con su contraseña correcta
    Then recibe access token y refresh token

  Scenario: Acceso denegado sin token
    Given un endpoint protegido
    When se accede sin Authorization header
    Then el servidor retorna 401 Unauthorized
```

---

### 5.2 Gestión de Clientes

**RF-CLIENT-01:** CRUD completo de clientes (nombre, email, tarifa/hora, moneda)
**RF-CLIENT-02:** Un cliente puede tener múltiples proyectos
**RF-CLIENT-03:** No se puede eliminar un cliente con proyectos activos

**Criterios de aceptación:**
```gherkin
Feature: Gestión de clientes
  Scenario: Crear cliente
    Given un usuario autenticado
    When crea un cliente con nombre "Acme Corp" y tarifa $150/h
    Then el cliente aparece en su lista de clientes

  Scenario: Prevenir borrado con proyectos
    Given un cliente con proyectos activos
    When intenta eliminarlo
    Then recibe error 409 con mensaje descriptivo
```

---

### 5.3 Gestión de Proyectos

**RF-PROJ-01:** CRUD de proyectos (nombre, descripción, color, cliente, estado activo/inactivo)
**RF-PROJ-02:** Proyectos pueden existir sin cliente asignado
**RF-PROJ-03:** Solo proyectos activos aceptan nuevas sesiones

---

### 5.4 Registro de Tiempo

**RF-TIME-01:** Timer start/stop
- `POST /api/v1/sessions/start` con `project_id` y descripción opcional
- Solo puede haber una sesión activa por usuario al mismo tiempo
- `POST /api/v1/sessions/stop` calcula `duration_seconds`

**RF-TIME-02:** Registro manual
- `POST /api/v1/sessions` con `started_at`, `ended_at`, `project_id`, `description`
- Validar que ended_at > started_at
- Máximo 24h por sesión

**RF-TIME-03:** Edición y borrado de sesiones pasadas

**RF-TIME-04:** Listado con filtros: `project_id`, `client_id`, `date_from`, `date_to`

**Criterios de aceptación:**
```gherkin
Feature: Timer de trabajo
  Scenario: Iniciar y detener sesión
    Given un usuario con un proyecto activo
    When inicia el timer para ese proyecto
    And detiene el timer 30 minutos después
    Then la sesión registra 30 minutos de duración

  Scenario: No se puede iniciar dos timers
    Given un usuario con un timer ya corriendo
    When intenta iniciar otro timer
    Then recibe error 409 "Ya hay una sesión activa"

  Scenario: Registro manual de tiempo
    Given un usuario autenticado
    When registra 2 horas de trabajo ayer para un proyecto
    Then las horas aparecen en el reporte de ayer
```

---

### 5.5 Reportes y Resumen

**RF-REPORT-01:** `GET /api/v1/reports/summary` con params `period=week|month|custom&date_from&date_to`
Retorna:
```json
{
  "total_hours": 42.5,
  "billable_hours": 38.0,
  "by_project": [
    { "project_id": "...", "name": "Proyecto A", "hours": 20.0, "amount": 3000.0 }
  ],
  "by_client": [
    { "client_id": "...", "name": "Acme", "hours": 20.0, "amount": 3000.0 }
  ],
  "by_day": [
    { "date": "2026-03-22", "hours": 8.5 }
  ]
}
```

**RF-REPORT-02:** Gráfico de barras por día en el dashboard (React + recharts o chart.js)

---

### 5.6 Facturación (PDF)

**RF-INV-01:** Generar factura para un cliente en un período
- Agrupa todas las sesiones de ese cliente en el período
- Calcula total_hours × hourly_rate
- Asigna número de factura secuencial (INV-{AÑO}-{SEQ:03d})

**RF-INV-02:** Generar PDF de la factura
Contenido del PDF:
- Logo / Nombre del freelancer
- Datos del cliente
- Tabla de sesiones agrupadas por proyecto (fecha, descripción, horas, subtotal)
- Total de horas y monto
- Número de factura y período

**RF-INV-03:** Descargar PDF vía `GET /api/v1/invoices/{id}/pdf`
**RF-INV-04:** Estados de factura: draft → sent → paid (transiciones manuales via PATCH)

**Criterios de aceptación:**
```gherkin
Feature: Generación de facturas
  Scenario: Crear factura mensual
    Given un cliente con 40 horas registradas en marzo a $100/h
    When se genera la factura para el período 2026-03-01/2026-03-31
    Then la factura muestra $4,000.00 como total
    And el PDF se puede descargar

  Scenario: Número de factura secuencial
    Given que ya existe INV-2026-001
    When se genera una nueva factura
    Then tiene el número INV-2026-002
```

---

### 5.7 Bot de Telegram

**RF-BOT-01:** Comando `/start` — responde con bienvenida y lista de comandos
**RF-BOT-02:** Comando `/log <horas> <proyecto> <descripción>`
- Ej: `/log 2.5 "Proyecto Alpha" "Reunión de kickoff"`
- Registra sesión manual con la hora actual como ended_at

**RF-BOT-03:** Comando `/status` — muestra sesión activa o "Sin sesión activa"
**RF-BOT-04:** Comando `/report` — resumen de la semana en texto
**RF-BOT-05:** Comando `/stop` — detiene sesión activa y muestra duración
**RF-BOT-06:** El bot responde solo a usuarios registrados (vinculación por telegram_chat_id)
**RF-BOT-07:** Comando `/link <email>` para vincular cuenta de Telegram con cuenta ChronoTrack

---

### 5.8 Dashboard UI (React)

**RF-UI-01:** Página `/dashboard`
- Timer activo con cronómetro en vivo (actualización cada segundo)
- Botón "Start" (seleccionar proyecto) / "Stop"
- Resumen de horas esta semana por proyecto (gráfico de barras)
- Sesiones de hoy (listado con hora inicio/fin y duración)

**RF-UI-02:** Página `/projects` — tabla de proyectos con acciones CRUD inline
**RF-UI-03:** Página `/clients` — tabla de clientes con tarifa/hora editable
**RF-UI-04:** Página `/sessions` — listado paginado con filtros de fecha y proyecto
**RF-UI-05:** Página `/reports`
- Selector de período (esta semana / este mes / personalizado)
- Gráfico de barras: horas por día
- Tabla resumen por cliente y proyecto

**RF-UI-06:** Página `/invoices`
- Formulario para generar factura (seleccionar cliente + período)
- Listado de facturas con estado y botón de descarga PDF

---

## 6. Requisitos No Funcionales

### 6.1 Seguridad
- Passwords hasheados con bcrypt==4.0.1 (pinear en pyproject.toml — ver regla 7 de WORKFLOW.md)
- JWT access tokens expiran en 15 minutos
- Refresh tokens con rotación (invalidar el anterior al rotar)
- Todos los endpoints de datos requieren autenticación
- Un usuario solo puede ver/editar sus propios datos (row-level isolation)
- No hardcodear secrets — usar variables de entorno
- Validación estricta de inputs (Pydantic v2 con Field validators)

### 6.2 Calidad de Código
- Cobertura de tests: >= 80% en backend
- Cero errores de ruff, bandit (sin high/critical)
- Cero secretos hardcodeados
- Type hints completos en Python (mypy-compatible)
- TypeScript strict mode en frontend

### 6.3 Performance
- Endpoints de listado paginados (max 50 items por página)
- Índices en `sessions(user_id, started_at)` y `sessions(project_id)`
- Lazy loading de relaciones SQLAlchemy

### 6.4 Docker Compose
```yaml
# Servicios mínimos requeridos
services:
  db:    # postgres:16, port 5432
  api:   # FastAPI, port 8000
  web:   # React/Vite, port 5173
  bot:   # Telegram bot (solo arranca si TELEGRAM_TOKEN está presente)
```

Variables de entorno necesarias:
```
DATABASE_URL=postgresql+asyncpg://chronotrack:chronotrack@db:5432/chronotrack
JWT_SECRET_KEY=<secret>
JWT_REFRESH_SECRET_KEY=<secret>
TELEGRAM_TOKEN=<opcional>
TELEGRAM_WEBHOOK_URL=<opcional>
```

---

## 7. Criterios de Éxito (Definition of Done por feature)

Un ticket está "Done" cuando:
1. Todos los tests del ticket pasan (pytest / vitest)
2. Cobertura del módulo >= 80%
3. Ruff y bandit sin errores
4. PR mergeado a `develop`
5. Docker compose levanta sin errores
6. Health endpoint responde 200
7. Para features UI: Playwright valida el flujo en el dashboard

---

## 8. Descomposición en Unidades de Trabajo (para el Bridge)

Esta sección guía al Bridge en cómo descomponer el proyecto. El Bridge puede ajustar la granularidad.

### Unidad 1: Foundation — Auth + DB + Docker
**Labels:** backend, infra
**Prioridad:** 1
**Descripción:** Setup completo del proyecto: estructura de directorios, Docker Compose, modelos de base de datos, migraciones Alembic, sistema de autenticación JWT con register/login/refresh.

Incluye:
- `pyproject.toml` con dependencias (fastapi, sqlalchemy[asyncio], alembic, passlib, python-jose, bcrypt==4.0.1)
- `docker-compose.yml` con db + api + web + bot
- Modelos SQLAlchemy: User, Client, Project, Session, Invoice
- Migraciones Alembic iniciales
- Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- Middleware de autenticación (JWT bearer)
- Tests unitarios de auth (register, login, refresh, invalid token)
- `GET /health` endpoint

**Dependencias:** ninguna

---

### Unidad 2: Client & Project Management API
**Labels:** backend
**Prioridad:** 2
**Descripción:** CRUD completo de clientes y proyectos con validaciones de negocio.

Incluye:
- CRUD `/api/v1/clients` — listar, crear, actualizar, eliminar (con guard de proyectos activos)
- CRUD `/api/v1/projects` — listar, crear, actualizar, desactivar
- Filtros: listar proyectos por cliente, filtrar activos/inactivos
- Tests de integración para cada endpoint
- Validaciones: email único de cliente, no borrar cliente con proyectos

**Dependencias:** Unidad 1

---

### Unidad 3: Time Tracking API
**Labels:** backend
**Prioridad:** 3
**Descripción:** Núcleo del producto — registro de sesiones de trabajo con timer y entrada manual.

Incluye:
- `POST /sessions/start` — iniciar timer (guard: solo 1 sesión activa)
- `POST /sessions/stop` — detener y calcular duración
- `POST /sessions` — registro manual (validar ended_at > started_at, max 24h)
- `GET /sessions` — listado con filtros (project_id, date_from, date_to, paginación)
- `PUT /sessions/{id}` — editar sesión pasada
- `DELETE /sessions/{id}` — borrar sesión
- `GET /reports/summary` — resumen por período con breakdown por proyecto/cliente/día
- Tests BDD para el timer (iniciar, detener, no duplicar)

**Dependencias:** Unidad 2

---

### Unidad 4: Invoice Generation
**Labels:** backend
**Prioridad:** 4
**Descripción:** Facturación con generación de PDF.

Incluye:
- `POST /invoices` — crear factura para cliente + período (agrupa sesiones, calcula total)
- `GET /invoices` — listar facturas del usuario
- `GET /invoices/{id}` — detalle de factura
- `GET /invoices/{id}/pdf` — descargar PDF
- `PATCH /invoices/{id}` — actualizar estado (draft → sent → paid)
- Generación de número secuencial (INV-{AÑO}-{SEQ:03d})
- PDF con WeasyPrint: tabla de sesiones, totales, datos del cliente
- Tests: cálculo correcto de totales, generación de número secuencial

**Dependencias:** Unidad 3

---

### Unidad 5: Telegram Bot
**Labels:** backend, bot
**Prioridad:** 5
**Descripción:** Bot de Telegram para registro de tiempo desde móvil.

Incluye:
- Setup de python-telegram-bot v20 async
- Comando `/start`
- Comando `/link <email>` — vincular telegram_chat_id con cuenta
- Comando `/log <horas> <proyecto> <descripción>`
- Comando `/status` — sesión activa
- Comando `/report` — resumen semana
- Comando `/stop` — detener sesión activa
- Webhook endpoint `POST /telegram/webhook`
- Tests unitarios de parsing de comandos y lógica de vinculación

**Dependencias:** Unidad 3

---

### Unidad 6: React Frontend — Auth + Layout + Navigation
**Labels:** frontend, ui
**Prioridad:** 2
**Descripción:** Estructura base del frontend: Vite + React + TypeScript + Tailwind, routing, auth context, páginas de login/registro.

Incluye:
- Setup: `vite.config.ts`, `tsconfig.json`, Tailwind CSS, React Router v6
- `AuthContext` con JWT storage (localStorage), auto-refresh de tokens
- Páginas: `/login`, `/register`
- Layout principal con sidebar de navegación
- Axios client con interceptor para bearer token y refresh automático
- Tipos TypeScript para todos los modelos del API
- Tests Vitest: AuthContext, formularios de login/registro

**Dependencias:** Unidad 1

---

### Unidad 7: Dashboard + Timer UI
**Labels:** frontend, ui
**Prioridad:** 3
**Descripción:** Dashboard principal con timer en vivo y resumen semanal.

Incluye:
- Componente Timer: cronómetro en vivo (intervalo 1s), selector de proyecto, start/stop
- Sesiones del día (listado con duración formateada)
- Resumen de horas esta semana (gráfico de barras con recharts)
- Indicador de sesión activa en el sidebar
- Estado del timer persiste entre recargas (verificar sesión activa al cargar)
- Tests Vitest: render del timer, simulación de start/stop
- Acceptance criteria para Playwright: iniciar timer, ver cronómetro correr, detener y ver sesión en listado

**Dependencias:** Unidades 3, 6

---

### Unidad 8: Projects + Clients + Sessions UI
**Labels:** frontend, ui
**Prioridad:** 4
**Descripción:** Páginas de gestión de clientes, proyectos y sesiones.

Incluye:
- `/clients` — tabla con acciones CRUD, modal de creación/edición, confirmación de borrado
- `/projects` — tabla con color picker, asignación de cliente, toggle activo/inactivo
- `/sessions` — listado paginado con filtros de fecha y proyecto, edición inline de descripción
- Formulario de sesión manual (date picker, time picker, selector de proyecto)
- Feedback visual: loading states, errores de validación, success toasts
- Tests Vitest: renders de tablas, interacción con modales

**Dependencias:** Unidades 3, 6

---

### Unidad 9: Reports + Invoices UI
**Labels:** frontend, ui
**Prioridad:** 5
**Descripción:** Páginas de reportes con gráficos y generación/descarga de facturas.

Incluye:
- `/reports` — selector de período, gráfico de barras por día, tabla por cliente y proyecto
- `/invoices` — formulario de generación (cliente + fechas), listado con estado, botón de descarga PDF
- Cambio de estado de factura (dropdown: draft/sent/paid)
- Export: botón "Descargar PDF" que hace fetch del blob y dispara descarga en browser
- Tests Vitest: renders de gráficos, interacción con formulario de factura

**Dependencias:** Unidades 4, 8

---

## 9. Configuración de Symphony para este Proyecto

En `WORKFLOW.md`, ajustar:

```yaml
tracker:
  project_slug: chronotrack-xxxxx   # slug de tu proyecto en Linear
  active_states:
    - Todo
    - In Progress
    - Quality Check
    - Local Review
    - Rework
    - Ready to Deploy
    - Needs Input
  terminal_states:
    - Done
    - Staging
    - Cancelled
    - Canceled
    - Duplicate

agent:
  max_concurrent_agents: 5
  max_concurrent_agents_by_state:
    todo: 5
    in progress: 5
    quality check: 1
    local review: 1
    rework: 3
    ready to deploy: 1
    needs input: 0
```

Variables de entorno requeridas:
```bash
export LINEAR_API_KEY=lin_api_xxx
export LINEAR_TEAM_ID=uuid-del-equipo
export SYMPHONY_REPO_URL=https://github.com/tu-org/chronotrack.git
```

---

## 10. Validación E2E esperada por el Playwright Agent (Local Review)

Para tickets con label `frontend` o `ui`, el agente Playwright valida:

### Dashboard / Timer
1. Navegar a `http://localhost:5173`
2. Login con `playwright@test.com / Test1234!`
3. Verificar que aparece el dashboard con el timer
4. Click "Start Timer" → seleccionar proyecto → confirmar
5. Verificar que el cronómetro corre (esperar 3s, verificar que el tiempo cambió)
6. Click "Stop" → verificar que la sesión aparece en "Sesiones de hoy"
7. Screenshot de cada paso

### Projects CRUD
1. Navegar a `/projects`
2. Click "Nuevo Proyecto"
3. Rellenar nombre y seleccionar cliente
4. Guardar y verificar que aparece en la tabla

### Reports
1. Navegar a `/reports`
2. Seleccionar "Esta semana"
3. Verificar que el gráfico de barras renderiza
4. Verificar que la tabla de resumen tiene datos

---

## 11. Orden de Waves sugerido por el Bridge

```
Wave 1 (en paralelo):
  - Unidad 1: Foundation (backend)
  - Unidad 6: Frontend base

Wave 2 (en paralelo, desbloquea cuando Wave 1 completa):
  - Unidad 2: Client & Project API
  - Unidad 3: Time Tracking API (parcial — depende de U2)

Wave 3 (en paralelo):
  - Unidad 4: Invoice API
  - Unidad 5: Telegram Bot
  - Unidad 7: Dashboard + Timer UI
  - Unidad 8: Projects + Sessions UI

Wave 4:
  - Unidad 9: Reports + Invoices UI

Total estimado: 4 waves · ~25-30 tickets atómicos
Agentes paralelos máximos en wave 3: 4 simultáneos
```

---

## 12. Checklist de Preparación Previa al Bridge

- [ ] Repositorio GitHub creado con rama `develop` como default
- [ ] Proyecto creado en Linear con todos los estados configurados:
  `Todo · In Progress · Quality Check · Local Review · Rework · Ready to Deploy · Needs Input · Staging · Done`
- [ ] Labels creados en Linear: `backend · frontend · ui · infra · bot`
- [ ] `SYMPHONY_REPO_URL` apunta al repo vacío
- [ ] `LINEAR_API_KEY` y `LINEAR_TEAM_ID` configurados
- [ ] Symphony validado: `symphony validate WORKFLOW.md`
- [ ] Playwright MCP verificado en subprocess: lanzar un ticket de prueba en Local Review y confirmar que el agente tiene acceso a `mcp__playwright__*`
