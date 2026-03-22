# ChronoTrack — Component Dependencies

This document maps how components depend on one another across the backend, frontend, and bot subsystems. It includes flow diagrams, a cross-service dependency matrix, and the Docker network topology.

---

## 1. Backend Dependency Flow

```
HTTP Request (from web browser or bot)
    │
    ▼
Router  (FastAPI route handler)
    │   ├── Pydantic schema validates request body
    │   └── FastAPI injects dependencies
    ▼
Dependencies
    ├── get_db → yields AsyncSession → passed to Service
    └── get_current_user → decodes JWT → loads UserModel → passed to Service
    │
    ▼
Service  (business logic layer)
    ├── Queries / mutations via AsyncSession
    │       ▼
    │   ORM Model (SQLAlchemy mapped class)
    │       ▼
    │   PostgreSQL 16 (via asyncpg driver)
    │
    └── [InvoiceService only] calls PDFService.render_invoice(...)
            ▼
        WeasyPrint + Jinja2  (synchronous, run in thread executor)
    │
    ▼
Router  returns result (Pydantic response model serialized to JSON)
    │
    OR (on any raised ChronoTrackError)
    ▼
ExceptionHandler → JSON HTTP response (4xx / 5xx)
```

---

## 2. Frontend Dependency Flow

```
React Page  (e.g., DashboardPage, SessionsPage)
    │
    ▼
Custom Hook  (e.g., useSessions, useProjects)
    │   ├── useQuery  → reads server state, caches it, re-fetches automatically
    │   └── useMutation → triggers write operations, invalidates related queries
    ▼
React Query (TanStack Query v5)
    │   └── calls the async function provided by the hook
    ▼
ApiClient  (Axios instance)
    ├── Request interceptor: attaches Authorization: Bearer <accessToken> from AuthContext
    └── Response interceptor:
            on 401 → calls POST /auth/refresh → updates AuthContext → retries request
            on refresh failure → clears AuthContext → redirects to /login
    │
    ▼
FastAPI API  (http://localhost:8000 in dev, VITE_API_URL in production)
    │
    ▼
JSON response
    │
    ▼
React Query cache updated
    │
    ▼
Component re-renders with fresh data
```

**AuthContext interaction:**

```
AuthContext
    ├── Provides: { user, accessToken, refreshToken, isAuthenticated, setTokens, clearTokens }
    ├── Read by: ApiClient (request interceptor), useAuth hook, AppLayout, route guards
    └── Written by: useAuth.login mutation, useAuth.register mutation, ApiClient refresh interceptor
```

---

## 3. Bot Dependency Flow

```
Telegram Platform
    │
    └── POST https://<api-host>/api/v1/telegram/webhook  (Telegram sends update)
            │
            ▼
        TelegramRouter  (FastAPI, api service)
            │
            └── passes raw Update JSON to python-telegram-bot Application dispatcher
                    │
                    ▼
                CommandHandler  (StartHandler / LinkHandler / LogHandler / etc.)
                    │
                    ▼
                TelegramService.handle_xxx(chat_id, ...)
                    │
                    ▼
                BotApiClient  (httpx.AsyncClient, base_url=http://api:8000/api/v1)
                    │
                    └── HTTP GET/POST to FastAPI API endpoints
                            │
                            ▼
                        FastAPI Service layer  (same auth + business rules as web clients)
                            │
                            ▼
                        PostgreSQL
                    │
                    ▼
                TelegramService formats response string
                    │
                    ▼
                CommandHandler replies via context.bot.send_message(chat_id, text)
                    │
                    ▼
            Telegram Platform delivers message to user
```

---

## 4. Cross-Service Dependency Matrix

### Backend Services

The table below shows which component depends on which other component. A checkmark indicates a direct dependency (method call or database model access).

| Depends on →      | UserModel | ClientModel | ProjectModel | SessionModel | InvoiceModel | PDFService | AuthService | Security | Database | Config |
|-------------------|:---------:|:-----------:|:------------:|:------------:|:------------:|:----------:|:-----------:|:--------:|:--------:|:------:|
| **AuthService**   | ✓         |             |              |              |              |            |             | ✓        | ✓        | ✓      |
| **ClientService** | ✓         | ✓           | ✓            |              |              |            |             |          | ✓        |        |
| **ProjectService**|           | ✓           | ✓            |              |              |            |             |          | ✓        |        |
| **SessionService**|           |             | ✓            | ✓            |              |            |             |          | ✓        |        |
| **ReportService** |           | ✓           | ✓            | ✓            |              |            |             |          | ✓        |        |
| **InvoiceService**|           | ✓           |              | ✓            | ✓            | ✓          |             |          | ✓        |        |
| **PDFService**    |           |             |              |              |              |            |             |          |          |        |
| **TelegramService**|          |             |              |              |              |            |             |          |          |        |

Notes:
- `TelegramService` has no direct model or service dependencies — it communicates exclusively via HTTP through `BotApiClient`.
- `PDFService` has no dependencies at all; it is a pure function receiving data objects.
- `Dependencies.get_current_user` internally uses `AuthService.get_current_user` (or equivalent inline logic using `Security`).

### Router → Service Mapping

| Router | Service |
|--------|---------|
| `AuthRouter` | `AuthService` |
| `ClientRouter` | `ClientService` |
| `ProjectRouter` | `ProjectService` |
| `SessionRouter` | `SessionService` |
| `ReportRouter` | `ReportService` |
| `InvoiceRouter` | `InvoiceService` |
| `TelegramRouter` | (dispatches to python-telegram-bot, which calls `TelegramService`) |
| `HealthRouter` | none |

### Frontend Hook → API Endpoint Mapping

| Hook | API Endpoints Used |
|------|--------------------|
| `useAuth` | `POST /auth/login`, `POST /auth/register`, `POST /auth/refresh` |
| `useSessions` | `GET /sessions`, `POST /sessions/start`, `POST /sessions/stop`, `POST /sessions`, `PATCH /sessions/{id}`, `DELETE /sessions/{id}` |
| `useProjects` | `GET /projects`, `POST /projects`, `PATCH /projects/{id}`, `PATCH /projects/{id}/deactivate` |
| `useClients` | `GET /clients`, `POST /clients`, `PATCH /clients/{id}`, `DELETE /clients/{id}` |
| `useReports` | `GET /reports/summary` |
| `useInvoices` | `GET /invoices`, `POST /invoices`, `GET /invoices/{id}`, `PATCH /invoices/{id}`, `GET /invoices/{id}/pdf` |

### Bot Handler → TelegramService → API Endpoint Mapping

| Handler | TelegramService Method | API Endpoint Called |
|---------|-----------------------|---------------------|
| `StartHandler` | `handle_start` | none |
| `LinkHandler` | `handle_link` | `POST /telegram/link` |
| `LogHandler` | `handle_log` | `POST /sessions` (manual entry) |
| `StatusHandler` | `handle_status` | `GET /sessions/active` |
| `ReportHandler` | `handle_report` | `GET /reports/summary?period=week` |
| `StopHandler` | `handle_stop` | `POST /sessions/stop` |

---

## 5. Docker Network Topology

All four Docker Compose services share a single bridge network named `chronotrack_net`. No service port is exposed to the host except those explicitly listed.

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker bridge network: chronotrack_net                         │
│                                                                 │
│  ┌──────────┐        ┌───────────────────────────────────┐     │
│  │   db     │◄───────│   api                             │     │
│  │ postgres │        │   FastAPI + Uvicorn                │     │
│  │ :5432    │        │   :8000 (internal)                 │     │
│  └──────────┘        │   :8000 (exposed to host for dev)  │     │
│                      └───────────────┬───────────────────┘     │
│                                      │                          │
│                      ┌───────────────┘                          │
│                      │                                          │
│          ┌───────────▼──────────┐   ┌────────────────────┐     │
│          │   bot                │   │   web               │     │
│          │   python-telegram-   │   │   React (Vite dev   │     │
│          │   bot, httpx         │   │   server)           │     │
│          │   calls api:8000     │   │   :5173 (exposed)   │     │
│          └──────────────────────┘   └────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

External traffic:
  Browser       → localhost:5173  (Vite dev) or localhost:80 (nginx prod)
  Browser       → localhost:8000/api/v1      (direct API calls in dev)
  Telegram      → <public-host>/api/v1/telegram/webhook
```

### Service Communication Rules

| Source | Destination | Protocol | Address |
|--------|-------------|----------|---------|
| `api` | `db` | PostgreSQL / asyncpg | `postgresql+asyncpg://db:5432/chronotrack` |
| `bot` | `api` | HTTP | `http://api:8000/api/v1` |
| `web` | `api` (dev) | HTTP | `http://localhost:8000/api/v1` |
| `web` | `api` (prod) | HTTP(S) | `$VITE_API_URL` |
| Telegram Platform | `api` | HTTPS (external ingress) | Configured webhook URL |

### Environment Variable Summary per Service

| Service | Key Variables |
|---------|--------------|
| `db` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| `api` | `DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `TELEGRAM_BOT_TOKEN` |
| `web` | `VITE_API_URL` |
| `bot` | `TELEGRAM_BOT_TOKEN`, `API_BASE_URL=http://api:8000` |

No secrets are hardcoded. All values are injected via Docker Compose environment or a `.env` file excluded from version control.
