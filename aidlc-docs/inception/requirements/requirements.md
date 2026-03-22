# Requirements Document — ChronoTrack

## Intent Analysis Summary

| Field | Value |
|-------|-------|
| **User Request** | Build ChronoTrack time-tracking application from PRD |
| **Request Type** | New Project (Greenfield) |
| **Scope Estimate** | System-wide — full stack application |
| **Complexity Estimate** | Complex — multi-service, multi-component |
| **Depth Level** | Standard |

**Key decisions from requirements verification:**
- **Project root**: `/workspace/trabajo/test-symphony/` (monorepo root)
- **PDF library**: WeasyPrint (HTML/CSS-based PDF generation)
- **CI/CD**: GitHub Actions `.github/workflows/ci.yml` included
- **Symphony/Linear**: Omitted — standalone development
- **Telegram Bot**: Fully implemented, conditionally started via `TELEGRAM_TOKEN`
- **Chart library**: recharts (React-native integration)
- **Security baseline**: All rules SECURITY-01 through SECURITY-15 enforced

---

## 1. Functional Requirements

### 1.1 Authentication (RF-AUTH)

| ID | Requirement |
|----|-------------|
| RF-AUTH-01 | User registration with unique email + password (min 8 chars, bcrypt==4.0.1) — returns JWT access token (15 min) + refresh token (30 days) |
| RF-AUTH-02 | User login — returns token pair; invalidates previous refresh tokens |
| RF-AUTH-03 | Token refresh via `POST /api/v1/auth/refresh` with token rotation strategy |
| RF-AUTH-04 | All non-auth endpoints require Bearer JWT authentication |
| RF-AUTH-05 | Row-level isolation — users can only access their own data |

### 1.2 Client Management (RF-CLIENT)

| ID | Requirement |
|----|-------------|
| RF-CLIENT-01 | CRUD for clients: name, email (optional), hourly_rate, currency |
| RF-CLIENT-02 | A client can have multiple projects |
| RF-CLIENT-03 | Cannot delete client with active projects — returns HTTP 409 |

### 1.3 Project Management (RF-PROJ)

| ID | Requirement |
|----|-------------|
| RF-PROJ-01 | CRUD for projects: name, description, hex color, client (optional), active/inactive |
| RF-PROJ-02 | Projects can exist without an assigned client |
| RF-PROJ-03 | Only active projects accept new sessions |

### 1.4 Time Tracking (RF-TIME)

| ID | Requirement |
|----|-------------|
| RF-TIME-01 | `POST /api/v1/sessions/start` — starts timer for a project; only 1 active session per user (HTTP 409 if duplicate) |
| RF-TIME-02 | `POST /api/v1/sessions/stop` — stops active session, computes `duration_seconds` |
| RF-TIME-03 | `POST /api/v1/sessions` — manual entry: `started_at`, `ended_at`, `project_id`, `description`; validates ended_at > started_at and max 24h duration |
| RF-TIME-04 | `GET /api/v1/sessions` — paginated list with filters: `project_id`, `client_id`, `date_from`, `date_to` |
| RF-TIME-05 | `PUT /api/v1/sessions/{id}` — edit past session |
| RF-TIME-06 | `DELETE /api/v1/sessions/{id}` — delete session |

### 1.5 Reports (RF-REPORT)

| ID | Requirement |
|----|-------------|
| RF-REPORT-01 | `GET /api/v1/reports/summary` with `period=week\|month\|custom&date_from&date_to` — returns total_hours, billable_hours, breakdown by_project, by_client, by_day |
| RF-REPORT-02 | Bar chart (recharts) showing hours per day in the React dashboard |

### 1.6 Invoicing (RF-INV)

| ID | Requirement |
|----|-------------|
| RF-INV-01 | `POST /api/v1/invoices` — create invoice for client+period; groups sessions, calculates total_hours × hourly_rate; sequential invoice number INV-{YEAR}-{SEQ:03d} |
| RF-INV-02 | Generate PDF (WeasyPrint): freelancer name, client data, session table (date, description, hours, subtotal), totals, invoice number, period |
| RF-INV-03 | `GET /api/v1/invoices/{id}/pdf` — download PDF |
| RF-INV-04 | Invoice status transitions: `draft → sent → paid` via `PATCH /api/v1/invoices/{id}` |
| RF-INV-05 | `GET /api/v1/invoices` — list user invoices |

### 1.7 Telegram Bot (RF-BOT)

| ID | Requirement |
|----|-------------|
| RF-BOT-01 | `/start` — welcome + command list |
| RF-BOT-02 | `/link <email>` — link Telegram `chat_id` to ChronoTrack account |
| RF-BOT-03 | `/log <hours> <project> <description>` — register manual session |
| RF-BOT-04 | `/status` — show active session or "No active session" |
| RF-BOT-05 | `/report` — weekly summary in text |
| RF-BOT-06 | `/stop` — stop active session, show duration |
| RF-BOT-07 | Only responds to linked users (by `telegram_chat_id`) |
| RF-BOT-08 | `POST /api/v1/telegram/webhook` — webhook endpoint |
| RF-BOT-09 | Bot only starts if `TELEGRAM_TOKEN` env var is present |

### 1.8 React Frontend (RF-UI)

| ID | Requirement |
|----|-------------|
| RF-UI-01 | `/dashboard` — live timer (1s interval), start/stop controls, weekly hours bar chart, today's sessions list |
| RF-UI-02 | `/projects` — CRUD table with inline actions |
| RF-UI-03 | `/clients` — CRUD table with editable hourly_rate |
| RF-UI-04 | `/sessions` — paginated list with date/project filters, manual entry form |
| RF-UI-05 | `/reports` — period selector, bar chart by day, summary table by client/project |
| RF-UI-06 | `/invoices` — invoice generation form, list with status, PDF download button |
| RF-UI-07 | `/login` and `/register` pages |
| RF-UI-08 | Sidebar navigation with active session indicator |
| RF-UI-09 | AuthContext with JWT storage (localStorage), auto-refresh via Axios interceptor |

---

## 2. Non-Functional Requirements

### 2.1 Security (enforced by SECURITY-01 through SECURITY-15)

| ID | Requirement |
|----|-------------|
| NFR-SEC-01 | Passwords hashed with `bcrypt==4.0.1` (pinned in pyproject.toml) |
| NFR-SEC-02 | JWT access tokens expire in 15 minutes; refresh tokens expire in 30 days with rotation |
| NFR-SEC-03 | No hardcoded secrets — all secrets via environment variables |
| NFR-SEC-04 | Strict input validation: Pydantic v2 with Field validators (backend), Zod (frontend) |
| NFR-SEC-05 | HTTPS enforced in production; CORS configured for dev/prod |
| NFR-SEC-06 | HTTP security headers (HSTS, CSP, X-Frame-Options, etc.) |
| NFR-SEC-07 | Rate limiting on auth endpoints |
| NFR-SEC-08 | Structured application-level logging (no PII in logs) |
| NFR-SEC-09 | No OWASP Top 10 vulnerabilities |

### 2.2 Quality

| ID | Requirement |
|----|-------------|
| NFR-QA-01 | Backend test coverage >= 80% (pytest) |
| NFR-QA-02 | Zero ruff errors; zero bandit high/critical findings |
| NFR-QA-03 | TypeScript strict mode in frontend |
| NFR-QA-04 | Full type hints in Python (mypy-compatible) |
| NFR-QA-05 | Playwright E2E for UI tickets |

### 2.3 Performance

| ID | Requirement |
|----|-------------|
| NFR-PERF-01 | Paginated endpoints (max 50 items/page) |
| NFR-PERF-02 | DB indexes on `sessions(user_id, started_at)` and `sessions(project_id)` |
| NFR-PERF-03 | Async SQLAlchemy with lazy loading of relations |

### 2.4 Infrastructure

| ID | Requirement |
|----|-------------|
| NFR-INFRA-01 | Docker Compose with 4 services: `db`, `api`, `web`, `bot` |
| NFR-INFRA-02 | `GET /api/v1/health` returns HTTP 200 |
| NFR-INFRA-03 | GitHub Actions CI: tests + lint on every PR to `develop` |
| NFR-INFRA-04 | Alembic migrations — reversible (downgrade support) |

---

## 3. Data Model

```
users          id (uuid PK), email (unique), name, hashed_password, telegram_chat_id, created_at
clients        id (uuid PK), user_id (FK), name, email, hourly_rate, currency, created_at
projects       id (uuid PK), user_id (FK), client_id (FK nullable), name, description, color, is_active, created_at
sessions       id (uuid PK), user_id (FK), project_id (FK), description, started_at, ended_at (nullable), duration_seconds (nullable), created_at
invoices       id (uuid PK), user_id (FK), client_id (FK), invoice_number (unique), period_start, period_end, total_hours, total_amount, currency, status, pdf_path, created_at
```

---

## 4. API Surface

```
GET  /api/v1/health
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
CRUD /api/v1/clients
CRUD /api/v1/projects
CRUD /api/v1/sessions
POST /api/v1/sessions/start
POST /api/v1/sessions/stop
GET  /api/v1/reports/summary
POST /api/v1/invoices
GET  /api/v1/invoices
GET  /api/v1/invoices/{id}
GET  /api/v1/invoices/{id}/pdf
PATCH /api/v1/invoices/{id}
POST /api/v1/telegram/webhook
```

---

## 5. Tech Stack (Confirmed)

| Layer | Technology |
|-------|-----------|
| API | Python 3.12 · FastAPI · SQLAlchemy async · Alembic |
| Database | PostgreSQL 16 |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · recharts |
| Auth | JWT · passlib[bcrypt] · `bcrypt==4.0.1` |
| PDF | WeasyPrint |
| Bot | python-telegram-bot v20 (async) |
| Infra | Docker Compose (api + web + db + bot) · GitHub Actions |
| Tests API | pytest · pytest-asyncio · httpx |
| Tests UI | Vitest · React Testing Library |
| E2E | Playwright |

---

## 6. Units of Work (from PRD Section 8)

| Unit | Name | Labels | Priority | Depends On |
|------|------|--------|----------|-----------|
| U1 | Foundation — Auth + DB + Docker | backend, infra | 1 | — |
| U2 | Client & Project Management API | backend | 2 | U1 |
| U3 | Time Tracking API | backend | 3 | U2 |
| U4 | Invoice Generation | backend | 4 | U3 |
| U5 | Telegram Bot | backend, bot | 5 | U3 |
| U6 | React Frontend — Auth + Layout | frontend, ui | 2 | U1 |
| U7 | Dashboard + Timer UI | frontend, ui | 3 | U3, U6 |
| U8 | Projects + Clients + Sessions UI | frontend, ui | 4 | U3, U6 |
| U9 | Reports + Invoices UI | frontend, ui | 5 | U4, U8 |
