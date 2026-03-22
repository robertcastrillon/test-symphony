# ChronoTrack — Unit of Work

**Project:** ChronoTrack (Full-Stack Time Tracking App)
**Stack:** FastAPI · PostgreSQL · React · TypeScript · Telegram Bot · Docker Compose
**Total Units:** 9
**Total Waves:** 5
**Date:** 2026-03-22

---

## Overview

ChronoTrack is decomposed into 9 units of work organized across 5 waves. Units within the same wave can execute in parallel. Each unit is scoped to be independently deliverable, testable, and mergeable.

| Unit | Name | Wave | Priority | Labels | Depends On |
|------|------|------|----------|--------|------------|
| U1 | Foundation — Auth + DB + Docker | 1 | 1 | backend, infra | — |
| U2 | Client & Project Management API | 2 | 2 | backend | U1 |
| U3 | Time Tracking API | 3 | 3 | backend | U2 |
| U4 | Invoice Generation | 4 | 4 | backend | U3 |
| U5 | Telegram Bot | 4 | 5 | backend, bot | U3 |
| U6 | React Frontend — Auth + Layout + Navigation | 1 | 2 | frontend, ui | — |
| U7 | Dashboard + Timer UI | 4 | 3 | frontend, ui | U3, U6 |
| U8 | Projects + Clients + Sessions UI | 4 | 4 | frontend, ui | U3, U6 |
| U9 | Reports + Invoices UI | 5 | 5 | frontend, ui | U4, U8 |

---

## Unit 1: Foundation — Auth + DB + Docker

**Wave:** 1
**Labels:** backend, infra
**Priority:** 1 (highest)
**Depends On:** none

### Scope

**Project Infrastructure:**
- `pyproject.toml` with all Python dependencies pinned: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `alembic`, `passlib[bcrypt]`, `python-jose[cryptography]`, `bcrypt==4.0.1` (pinned — critical security constraint), `pydantic-settings`, `asyncpg`, `structlog`, `httpx`, `pytest`, `pytest-asyncio`, `ruff`, `bandit`, `weasyprint`
- `docker-compose.yml` with 4 services: `db` (postgres:16, port 5432), `api` (FastAPI, port 8000), `web` (React/Vite, port 5173), `bot` (Telegram bot, conditional on `TELEGRAM_TOKEN`)
- `docker-compose.test.yml` for CI environment (in-memory or test DB, no volume persistence)
- `.github/workflows/ci.yml`: triggers on PR to `develop`; jobs: lint (ruff + bandit), test (pytest with coverage gate >= 80%)
- `Makefile` with targets: `dev` (docker-compose up), `test` (run pytest in container), `lint` (ruff + bandit), `migrate` (alembic upgrade head)
- `.env.example` with all required environment variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`, `TELEGRAM_TOKEN` (optional), `TELEGRAM_WEBHOOK_URL` (optional)

**Application Directory Structure (`apps/api/app/`):**
- `main.py`: FastAPI app factory, router registration, CORS middleware, lifespan handler
- `core/config.py`: Pydantic `Settings` class loading from env vars
- `core/security.py`: JWT encode/decode, password hashing with bcrypt==4.0.1, `verify_password`, `get_password_hash`, `create_access_token`, `create_refresh_token`
- `core/dependencies.py`: `get_current_user` async dependency, `get_db` session dependency
- `core/exceptions.py`: Custom exception hierarchy — `ChronoTrackException` base, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `ValidationError`
- `db/database.py`: SQLAlchemy async engine creation, `Base` declarative base
- `db/session.py`: `AsyncSession` factory, `get_db` context manager

**SQLAlchemy Models (`apps/api/app/models/`):**
- `base.py`: `BaseModel` with `id` (UUID, default `uuid4`), `created_at` (timestamptz, server default `now()`)
- `user.py`: `User` — `email` (varchar, unique, not null), `name` (varchar, not null), `hashed_password` (varchar, not null), `telegram_chat_id` (bigint, nullable)
- `client.py`: `Client` — `user_id` (FK users), `name` (varchar, not null), `email` (varchar, nullable), `hourly_rate` (numeric(10,2), default 0), `currency` (varchar(3), default 'USD')
- `project.py`: `Project` — `user_id` (FK users), `client_id` (FK clients, nullable), `name` (varchar, not null), `description` (text, nullable), `color` (varchar(7), default '#6366f1'), `is_active` (boolean, default true)
- `session.py`: `Session` — `user_id` (FK users), `project_id` (FK projects), `description` (text, nullable), `started_at` (timestamptz, not null), `ended_at` (timestamptz, nullable — NULL means active), `duration_seconds` (integer, nullable — computed on stop)
- `invoice.py`: `Invoice` — `user_id` (FK users), `client_id` (FK clients), `invoice_number` (varchar, unique, not null — format `INV-{YEAR}-{SEQ:03d}`), `period_start` (date, not null), `period_end` (date, not null), `total_hours` (numeric(10,2)), `total_amount` (numeric(10,2)), `currency` (varchar(3)), `status` (varchar, default 'draft'), `pdf_path` (varchar, nullable)

**Alembic:**
- `alembic/env.py`: async-compatible Alembic env with `target_metadata = Base.metadata`
- `alembic/versions/0001_initial_schema.py`: creates all 5 tables with constraints, foreign keys, and indexes

**Auth Endpoints (`apps/api/app/routers/auth.py`):**
- `POST /api/v1/auth/register`: accepts `{email, password, name}`, validates unique email, hashes password with bcrypt==4.0.1, creates user, returns `{access_token, refresh_token, token_type}`
- `POST /api/v1/auth/login`: accepts `{email, password}`, verifies credentials, invalidates previous refresh tokens, returns token pair
- `POST /api/v1/auth/refresh`: accepts `{refresh_token}`, validates token, rotates (issues new pair, invalidates old refresh token), returns new token pair

**Health Endpoint:**
- `GET /api/v1/health`: returns `{status: "ok", version: "1.0.0"}` — no auth required

**JWT Middleware:**
- `get_current_user` dependency: extracts Bearer token from `Authorization` header, decodes JWT, fetches user from DB, raises `AuthenticationError` (401) on any failure
- Refresh token rotation: stored as hashed value in DB or tracked via `jti` claim to enable invalidation

**Pydantic Schemas (`apps/api/app/schemas/auth.py`):**
- `RegisterRequest`, `LoginRequest`, `TokenResponse`, `RefreshRequest` — all with Field validators (email format, password min length 8)

**Unit Tests (`apps/api/tests/test_auth.py`):**
- `test_register_success`: registers new user, asserts 201 + tokens returned
- `test_register_duplicate_email`: registers same email twice, asserts 409
- `test_login_success`: logs in with correct credentials, asserts 200 + tokens
- `test_login_wrong_password`: asserts 401
- `test_refresh_success`: uses valid refresh token, asserts new tokens returned
- `test_refresh_invalid_token`: uses expired/malformed token, asserts 401
- `test_protected_endpoint_without_token`: accesses `/clients` without auth, asserts 401
- `tests/conftest.py`: async test client, test DB setup/teardown, `test_user` fixture

### Deliverables

| Artifact | Path |
|----------|------|
| Docker Compose | `docker-compose.yml`, `docker-compose.test.yml` |
| CI Workflow | `.github/workflows/ci.yml` |
| Build tooling | `Makefile`, `.env.example` |
| FastAPI app skeleton | `apps/api/app/` (all subdirectories) |
| ORM Models (5) | `apps/api/app/models/` |
| Alembic migration | `apps/api/alembic/versions/0001_initial_schema.py` |
| Auth endpoints (3) | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` |
| Health endpoint | `GET /health` |
| Auth unit tests | `apps/api/tests/test_auth.py` |

### Acceptance Criteria

- `docker-compose up` starts all 4 services without errors
- `GET /api/v1/health` returns HTTP 200
- `POST /auth/register` with valid data returns 201 and a valid JWT access token
- `POST /auth/login` with correct credentials returns 200 and token pair
- `POST /auth/refresh` rotates the refresh token (old token is invalidated)
- Any protected endpoint without a valid Bearer token returns 401
- Duplicate email registration returns 409
- All unit tests pass; coverage >= 80% on `app/routers/auth.py` and `app/services/auth.py`
- `ruff` and `bandit` report zero errors

---

## Unit 2: Client & Project Management API

**Wave:** 2
**Labels:** backend
**Priority:** 2
**Depends On:** U1

### Scope

**ClientService (`apps/api/app/services/client.py`):**
- `list_clients(user_id)`: returns all clients owned by the authenticated user
- `create_client(user_id, data)`: validates and persists new client
- `get_client(user_id, client_id)`: fetches single client, raises `NotFoundError` if not found or wrong owner
- `update_client(user_id, client_id, data)`: partial update, validates ownership
- `delete_client(user_id, client_id)`: checks for active projects — if any exist, raises `ConflictError` (HTTP 409) with message "Cannot delete client with active projects"; otherwise hard deletes

**ClientRouter (`apps/api/app/routers/clients.py`):**
- `GET /api/v1/clients` — list all clients for authenticated user
- `POST /api/v1/clients` — create client; body: `{name, email?, hourly_rate?, currency?}`
- `GET /api/v1/clients/{id}` — get single client
- `PUT /api/v1/clients/{id}` — full update
- `DELETE /api/v1/clients/{id}` — delete with active-projects guard

**ProjectService (`apps/api/app/services/project.py`):**
- `list_projects(user_id, client_id?, is_active?)`: filtered listing
- `create_project(user_id, data)`: validates client ownership if `client_id` provided
- `get_project(user_id, project_id)`: ownership check
- `update_project(user_id, project_id, data)`: update name, description, color, client assignment
- `deactivate_project(user_id, project_id)`: sets `is_active=False`

**ProjectRouter (`apps/api/app/routers/projects.py`):**
- `GET /api/v1/projects` — list with optional `?client_id=&is_active=` filters
- `POST /api/v1/projects` — create; body: `{name, description?, color?, client_id?, is_active?}`
- `GET /api/v1/projects/{id}` — single project
- `PUT /api/v1/projects/{id}` — update project
- `PATCH /api/v1/projects/{id}/deactivate` — soft deactivate

**Business Rules:**
- A client with one or more active projects (`is_active=True`) cannot be deleted — HTTP 409
- Projects can exist without a `client_id` (freelancer's internal projects)
- Only active projects (`is_active=True`) can accept new time sessions (enforced in U3)
- All operations are row-level isolated: user can only see/modify their own clients and projects
- Color field must be a valid hex color string (validated via Pydantic regex `^#[0-9a-fA-F]{6}$`)

**Pydantic Schemas (`apps/api/app/schemas/`):**
- `client.py`: `ClientCreate`, `ClientUpdate`, `ClientResponse`
- `project.py`: `ProjectCreate`, `ProjectUpdate`, `ProjectResponse`

**Integration Tests (`apps/api/tests/`):**
- `test_clients.py`: create, list, get, update, delete (happy path); delete with active projects (409); unauthenticated access (401); access another user's client (404)
- `test_projects.py`: create with and without client, list with filters, deactivate, update color; unauthenticated access (401)

### Deliverables

| Artifact | Path |
|----------|------|
| Client CRUD | `GET/POST/GET/{id}/PUT/{id}/DELETE/{id} /api/v1/clients` |
| Project CRUD | `GET/POST/GET/{id}/PUT/{id}/PATCH/{id}/deactivate /api/v1/projects` |
| Services | `apps/api/app/services/client.py`, `apps/api/app/services/project.py` |
| Schemas | `apps/api/app/schemas/client.py`, `apps/api/app/schemas/project.py` |
| Integration tests | `apps/api/tests/test_clients.py`, `apps/api/tests/test_projects.py` |

### Acceptance Criteria

- All 5 client endpoints return correct status codes (200/201/204/404/409)
- All 5 project endpoints return correct status codes
- `DELETE /clients/{id}` returns 409 when client has at least one active project
- `GET /projects?is_active=true` returns only active projects
- `GET /projects?client_id={id}` returns only that client's projects
- Unauthenticated requests return 401; cross-user access returns 404
- All integration tests pass

---

## Unit 3: Time Tracking API

**Wave:** 3
**Labels:** backend
**Priority:** 3
**Depends On:** U2

### Scope

**SessionService (`apps/api/app/services/session.py`):**
- `start_session(user_id, project_id, description?)`: checks no active session exists for user (raises `ConflictError` 409 if one does); validates project is active and owned by user; creates session with `started_at=now()`, `ended_at=NULL`
- `stop_session(user_id)`: finds the one active session (`ended_at IS NULL`) for the user; sets `ended_at=now()`, computes `duration_seconds = (ended_at - started_at).total_seconds()`; raises `NotFoundError` if no active session
- `create_manual_session(user_id, data)`: validates `ended_at > started_at`; validates duration <= 86400 seconds (24h); validates project ownership and active status; persists
- `list_sessions(user_id, filters)`: paginated query (default page_size=20, max=50) with optional filters: `project_id`, `client_id` (join through project), `date_from`, `date_to`
- `update_session(user_id, session_id, data)`: validates ownership; cannot edit an active session's `ended_at` to NULL; validates time constraints
- `delete_session(user_id, session_id)`: ownership check, hard delete

**SessionRouter (`apps/api/app/routers/sessions.py`):**
- `POST /api/v1/sessions/start` — body: `{project_id, description?}`; returns created session
- `POST /api/v1/sessions/stop` — no body; returns updated session with `duration_seconds`
- `POST /api/v1/sessions` — manual entry; body: `{project_id, started_at, ended_at, description?}`
- `GET /api/v1/sessions` — paginated list; query params: `project_id`, `client_id`, `date_from`, `date_to`, `page`, `page_size`
- `PUT /api/v1/sessions/{id}` — full update of past session
- `DELETE /api/v1/sessions/{id}` — delete session

**ReportService (`apps/api/app/services/report.py`):**
- `get_summary(user_id, period, date_from?, date_to?)`: aggregates sessions by project, client, and day
  - `period=week`: last 7 days from today
  - `period=month`: current calendar month
  - `period=custom`: uses `date_from` and `date_to`
  - Returns: `total_hours`, `billable_hours` (sessions linked to projects with a client that has `hourly_rate > 0`), `by_project[]`, `by_client[]`, `by_day[]`

**ReportRouter (`apps/api/app/routers/reports.py`):**
- `GET /api/v1/reports/summary` — query params: `period=week|month|custom`, `date_from`, `date_to`

**Database Indexes (in Alembic migration):**
- `CREATE INDEX idx_sessions_user_started ON sessions(user_id, started_at DESC)`
- `CREATE INDEX idx_sessions_project ON sessions(project_id)`

**Pydantic Schemas (`apps/api/app/schemas/`):**
- `session.py`: `SessionStartRequest`, `SessionManualCreate`, `SessionUpdate`, `SessionResponse`, `SessionListResponse`
- `report.py`: `ReportSummaryResponse`, `ProjectBreakdown`, `ClientBreakdown`, `DayBreakdown`

**BDD / Integration Tests (`apps/api/tests/test_sessions.py`):**
- `test_start_session_success`
- `test_start_session_duplicate_guard`: second start returns 409 "Already have an active session"
- `test_stop_session_computes_duration`
- `test_stop_session_no_active`: returns 404
- `test_manual_session_valid`
- `test_manual_session_invalid_time_order`: `ended_at < started_at` returns 422
- `test_manual_session_exceeds_24h`: returns 422
- `test_list_sessions_filters`
- `test_report_summary_week`
- `test_report_summary_custom_range`

### Deliverables

| Artifact | Path |
|----------|------|
| Timer endpoints | `POST /sessions/start`, `POST /sessions/stop` |
| Session CRUD | `POST/GET/PUT/{id}/DELETE/{id} /sessions` |
| Report endpoint | `GET /reports/summary` |
| Services | `apps/api/app/services/session.py`, `apps/api/app/services/report.py` |
| Schemas | `apps/api/app/schemas/session.py`, `apps/api/app/schemas/report.py` |
| DB indexes | Alembic migration for performance indexes |
| BDD tests | `apps/api/tests/test_sessions.py`, `apps/api/tests/test_reports.py` |

### Acceptance Criteria

- `POST /sessions/start` with an already-active session returns 409
- `POST /sessions/stop` correctly populates `duration_seconds`
- `POST /sessions` with `ended_at <= started_at` returns 422
- `POST /sessions` with duration > 24h returns 422
- `GET /sessions?date_from=2026-03-01&date_to=2026-03-31` returns only sessions in that range
- `GET /reports/summary?period=week` returns correct `total_hours`, `by_project`, `by_client`, `by_day`
- All BDD test scenarios pass

---

## Unit 4: Invoice Generation

**Wave:** 4
**Labels:** backend
**Priority:** 4
**Depends On:** U3

### Scope

**InvoiceService (`apps/api/app/services/invoice.py`):**
- `create_invoice(user_id, client_id, period_start, period_end)`:
  - Fetches all sessions in the period for sessions linked to projects owned by that client
  - Calculates `total_hours` (sum of `duration_seconds / 3600`)
  - Calculates `total_amount = total_hours * client.hourly_rate`
  - Generates sequential `invoice_number`:
    - Queries MAX sequence for current year: `SELECT MAX(seq) FROM invoices WHERE invoice_number LIKE 'INV-{year}-%' AND user_id = ?`
    - Formats as `INV-{YEAR}-{SEQ:03d}` (e.g., `INV-2026-001`)
  - Sets `status='draft'`, `currency=client.currency`
  - Triggers PDF generation, stores `pdf_path`
- `list_invoices(user_id)`: returns all invoices for user, ordered by created_at DESC
- `get_invoice(user_id, invoice_id)`: with ownership check
- `update_invoice_status(user_id, invoice_id, status)`: validates transition (draft→sent→paid only); raises `ConflictError` for invalid transitions
- `get_invoice_pdf(user_id, invoice_id)`: returns file path or raises `NotFoundError`

**PDFService (`apps/api/app/services/pdf.py`):**
- `generate_invoice_pdf(invoice, client, sessions)`: renders HTML template to PDF using WeasyPrint
- PDF content:
  - Header: freelancer name (from `user.name`), invoice number, period, generated date
  - Client section: client name, email
  - Sessions table: columns — Date, Project, Description, Hours, Rate, Subtotal
  - Totals row: total hours, total amount, currency
  - Footer: invoice status, payment instructions placeholder
- PDF stored to `apps/api/static/invoices/{invoice_id}.pdf` or configured storage path
- Returns file path as string

**InvoiceRouter (`apps/api/app/routers/invoices.py`):**
- `POST /api/v1/invoices` — body: `{client_id, period_start, period_end}`; returns invoice with `invoice_number`
- `GET /api/v1/invoices` — list all user invoices
- `GET /api/v1/invoices/{id}` — invoice detail
- `GET /api/v1/invoices/{id}/pdf` — returns `FileResponse` with `Content-Type: application/pdf`
- `PATCH /api/v1/invoices/{id}` — body: `{status: "sent"|"paid"}`; updates status

**Pydantic Schemas (`apps/api/app/schemas/invoice.py`):**
- `InvoiceCreate`, `InvoiceResponse`, `InvoiceStatusUpdate`

**Tests (`apps/api/tests/test_invoices.py`):**
- `test_create_invoice_calculates_total_correctly`
- `test_invoice_number_sequential`: creates two invoices, asserts `INV-2026-001` and `INV-2026-002`
- `test_invoice_number_resets_per_year`: (mock year change)
- `test_pdf_generated_on_create`: asserts `pdf_path` is not null and file exists
- `test_download_pdf_returns_file`: `GET /invoices/{id}/pdf` returns 200 with `application/pdf`
- `test_status_transition_draft_to_sent`
- `test_status_transition_paid_to_draft_rejected`: invalid transition returns 409

### Deliverables

| Artifact | Path |
|----------|------|
| Invoice CRUD | `POST/GET/GET/{id}/GET/{id}/pdf/PATCH/{id} /api/v1/invoices` |
| Invoice service | `apps/api/app/services/invoice.py` |
| PDF service | `apps/api/app/services/pdf.py` |
| Schemas | `apps/api/app/schemas/invoice.py` |
| HTML template | `apps/api/app/templates/invoice.html` |
| Tests | `apps/api/tests/test_invoices.py` |

### Acceptance Criteria

- `POST /invoices` generates `invoice_number` in format `INV-{YEAR}-{SEQ:03d}`
- Second invoice in same year gets `SEQ` incremented by 1
- `total_amount` equals sum of `(session.duration_seconds / 3600) * client.hourly_rate`
- `GET /invoices/{id}/pdf` returns HTTP 200 with `Content-Type: application/pdf`
- `PATCH /invoices/{id}` with `status: "paid"` when current status is `draft` follows the chain (draft→sent→paid)
- Invalid status transitions return 409
- All tests pass

---

## Unit 5: Telegram Bot

**Wave:** 4
**Labels:** backend, bot
**Priority:** 5
**Depends On:** U3

### Scope

**Bot Service Setup (`apps/bot/`):**
- `apps/bot/pyproject.toml`: dependencies — `python-telegram-bot==20.*`, `httpx`, `python-dotenv`, `pytest`, `pytest-asyncio`
- `apps/bot/Dockerfile`: Python 3.12, installs deps, runs `python -m bot.main`
- `apps/bot/bot/main.py`: application entry point; creates `Application` using `ApplicationBuilder`; registers all handlers; starts polling or webhook mode depending on `TELEGRAM_WEBHOOK_URL` env var; **exits gracefully if `TELEGRAM_TOKEN` is not set** (logs warning, exits 0)

**Bot Handlers (`apps/bot/bot/handlers/`):**
- `start.py`: `/start` — responds with welcome message listing all available commands
- `link.py`: `/link <email>` — calls `POST /api/v1/auth/telegram/link` (new endpoint in FastAPI) with `{email, telegram_chat_id}`; responds with success/failure message
- `log.py`: `/log <hours> <project_name> <description>` — parses args; calls `POST /api/v1/sessions` as manual entry (`ended_at=now()`, `started_at=now() - hours*3600`); responds with confirmation
- `status.py`: `/status` — calls `GET /api/v1/sessions?active=true`; responds with active session info or "No active session"
- `report.py`: `/report` — calls `GET /api/v1/reports/summary?period=week`; formats and responds with text summary (total hours, top 3 projects)
- `stop.py`: `/stop` — calls `POST /api/v1/sessions/stop`; responds with session duration; error if no active session

**BotApiClient (`apps/bot/bot/services/api_client.py`):**
- `BotApiClient(base_url: str)` — uses `httpx.AsyncClient`
- `authenticate(telegram_chat_id)`: fetches API token for linked user; raises `UnlinkedUserError` if not linked
- `get_active_session(token)`, `stop_session(token)`, `create_manual_session(token, data)`, `get_report(token)` — all pass `Authorization: Bearer {token}` header
- Every handler calls `authenticate()` first; if user is not linked, responds with "Please link your account using /link <email>"

**FastAPI Webhook Endpoint (`apps/api/app/routers/telegram.py`):**
- `POST /api/v1/telegram/webhook` — receives Telegram update JSON; dispatches to `python-telegram-bot` dispatcher; no auth required (secured via secret token in URL or header)
- New endpoint: `POST /api/v1/auth/telegram/link` — accepts `{email, telegram_chat_id}`, finds user by email, updates `user.telegram_chat_id`; no auth required (triggered by bot)

**Unit Tests (`apps/bot/tests/`):**
- `test_start_handler`: assert welcome message sent
- `test_link_handler_success`: mock API call, assert success message
- `test_link_handler_invalid_email`: mock API returning 404, assert error message
- `test_log_handler_parsing`: test `"2.5 'Project Alpha' Meeting notes"` parses correctly
- `test_log_handler_api_call`: mock `create_manual_session`, assert called with correct args
- `test_status_handler_active_session`
- `test_status_handler_no_session`
- `test_stop_handler_success`
- `test_unlinked_user_rejected`: any command from unlinked user gets link prompt

### Deliverables

| Artifact | Path |
|----------|------|
| Bot service | `apps/bot/` (complete service) |
| Bot handlers (6) | `/start`, `/link`, `/log`, `/status`, `/report`, `/stop` |
| API client | `apps/bot/bot/services/api_client.py` |
| Webhook endpoint | `POST /api/v1/telegram/webhook` |
| Link endpoint | `POST /api/v1/auth/telegram/link` |
| Dockerfile | `apps/bot/Dockerfile` |
| Unit tests | `apps/bot/tests/` |

### Acceptance Criteria

- Bot starts if `TELEGRAM_TOKEN` is set; exits gracefully if not
- `/start` returns a welcome message with all command descriptions
- `/link valid@email.com` links the Telegram account to the ChronoTrack user
- `/log 2 "My Project" "Work description"` creates a manual session via the API
- `/status` returns current active session or "No active session"
- `/stop` stops the active session and reports duration
- Unlinked users receive a prompt to `/link` their account on any command
- All unit tests pass with mocked HTTP calls

---

## Unit 6: React Frontend — Auth + Layout + Navigation

**Wave:** 1
**Labels:** frontend, ui
**Priority:** 2
**Depends On:** none (can run in parallel with U1)

### Scope

**Project Setup (`apps/web/`):**
- `apps/web/package.json`: all dependencies — `react@18`, `react-dom@18`, `react-router-dom@6`, `axios`, `@tanstack/react-query@5`, `recharts`, `tailwindcss`, `postcss`, `autoprefixer`, `zod`, `react-hook-form`, `@hookform/resolvers`, `react-hot-toast`; dev dependencies: `vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `jsdom`, `@playwright/test`
- `apps/web/vite.config.ts`: React plugin, `@/` path alias to `src/`, test config with `jsdom` environment
- `apps/web/tsconfig.json`: strict mode enabled (`"strict": true`), `baseUrl: "."`, `paths: {"@/*": ["src/*"]}`
- `apps/web/tailwind.config.js`: content paths covering all `src/**/*.{ts,tsx}`
- `apps/web/Dockerfile`: Node 20 alpine, `npm ci`, `npm run build`, served via nginx or Vite preview

**TypeScript Types (`apps/web/src/types/api.ts`):**
- `User`: `{id, email, name, telegram_chat_id?}`
- `Client`: `{id, user_id, name, email?, hourly_rate, currency, created_at}`
- `Project`: `{id, user_id, client_id?, name, description?, color, is_active, created_at}`
- `Session`: `{id, user_id, project_id, description?, started_at, ended_at?, duration_seconds?, created_at}`
- `Invoice`: `{id, user_id, client_id, invoice_number, period_start, period_end, total_hours, total_amount, currency, status, pdf_path?, created_at}`
- `ReportSummary`: `{total_hours, billable_hours, by_project: ProjectBreakdown[], by_client: ClientBreakdown[], by_day: DayBreakdown[]}`
- `ProjectBreakdown`, `ClientBreakdown`, `DayBreakdown`
- `TokenResponse`: `{access_token, refresh_token, token_type}`
- `PaginatedResponse<T>`: `{items: T[], total: number, page: number, page_size: number}`

**AuthContext (`apps/web/src/context/AuthContext.tsx`):**
- State: `user: User | null`, `isLoading: boolean`, `isAuthenticated: boolean`
- Actions: `login(email, password)`, `register(email, password, name)`, `logout()`, `refreshToken()`
- JWT storage: access token and refresh token stored in `localStorage`
- On app load: reads token from storage, validates expiry, auto-refreshes if needed
- Exposes `AuthContext` and `useAuth()` hook

**Axios Client (`apps/web/src/services/apiClient.ts`):**
- `axiosClient` instance with `baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'`
- Request interceptor: attaches `Authorization: Bearer {access_token}` if available
- Response interceptor: on 401 — attempts token refresh once; if refresh fails, calls `logout()` and redirects to `/login`; if refresh succeeds, retries original request

**React Router v6 (`apps/web/src/App.tsx`):**
- `BrowserRouter` wrapping all routes
- Public routes (no auth required): `/login`, `/register`
- Protected routes (require `isAuthenticated`): `/dashboard`, `/projects`, `/clients`, `/sessions`, `/reports`, `/invoices`
- Default redirect: `/` → `/dashboard` if authenticated, `/login` if not
- `ProtectedRoute` HOC: checks `isAuthenticated`, redirects to `/login` with `?from=` param if not

**AppLayout (`apps/web/src/components/AppLayout.tsx`):**
- Sidebar navigation with links to all pages
- Active route highlighted (using `NavLink`)
- Active session indicator slot in sidebar (shows running timer chip if a session is active — fed by context/hook from U7)
- Logout button
- Responsive: sidebar collapses on mobile

**LoginPage (`apps/web/src/pages/LoginPage.tsx`):**
- Form fields: email, password
- Zod schema: `email` (valid email), `password` (min 8 chars)
- On submit: calls `useAuth().login()`; on success redirects to `/dashboard` (or `?from=` param)
- Shows error message on invalid credentials
- Link to `/register`

**RegisterPage (`apps/web/src/pages/RegisterPage.tsx`):**
- Form fields: name, email, password, confirm password
- Zod schema: all required, password min 8, passwords match
- On submit: calls `useAuth().register()`; on success redirects to `/dashboard`
- Shows field-level errors
- Link to `/login`

**Vitest Tests (`apps/web/tests/`):**
- `test_auth_context.test.tsx`: `AuthContext` initial state, login updates state, logout clears state, 401 triggers refresh
- `test_login_page.test.tsx`: renders form, validates empty submit shows errors, successful login redirects
- `test_register_page.test.tsx`: renders form, password mismatch shows error, successful register redirects

### Deliverables

| Artifact | Path |
|----------|------|
| Web app skeleton | `apps/web/` (complete setup) |
| TypeScript types | `apps/web/src/types/api.ts` |
| Auth context | `apps/web/src/context/AuthContext.tsx` |
| Axios client | `apps/web/src/services/apiClient.ts` |
| Router config | `apps/web/src/App.tsx` |
| App layout | `apps/web/src/components/AppLayout.tsx` |
| Auth pages | `apps/web/src/pages/LoginPage.tsx`, `RegisterPage.tsx` |
| Dockerfile | `apps/web/Dockerfile` |
| Vitest tests | `apps/web/tests/` (auth tests) |

### Acceptance Criteria

- `npm run dev` starts Vite dev server on port 5173
- TypeScript compiles with zero errors (`tsc --noEmit`)
- `/login` and `/register` routes render correctly
- Unauthenticated access to `/dashboard` redirects to `/login`
- Successful login persists tokens and redirects to `/dashboard`
- 401 response triggers automatic token refresh
- Vitest tests pass

---

## Unit 7: Dashboard + Timer UI

**Wave:** 4
**Labels:** frontend, ui
**Priority:** 3
**Depends On:** U3 (sessions API), U6 (React base)

### Scope

**DashboardPage (`apps/web/src/pages/DashboardPage.tsx`):**
- Top section: `TimerComponent` (live timer or start prompt)
- Middle section: "Today's Sessions" — list of sessions from today with formatted `started_at`, `ended_at`, `duration`
- Bottom section: "This Week" — weekly hours bar chart using `recharts BarChart`
- On mount: checks for active session via `GET /sessions?active=true` to restore timer state

**TimerComponent (`apps/web/src/components/TimerComponent.tsx`):**
- State machine: `idle` | `running`
- `running` state: shows elapsed time as `HH:MM:SS` updated every second via `setInterval`
- Start flow: shows project selector dropdown (populated from `GET /projects?is_active=true`), then "Start" button; calls `POST /sessions/start`
- Stop flow: "Stop" button; calls `POST /sessions/stop`; displays completed session duration as toast
- Active session restored on mount: reads `started_at` from API, computes elapsed seconds since then
- Displays project name when running

**Active Session Indicator in Sidebar:**
- `AppLayout` subscribes to timer context or polls for active session
- Shows a pulsing green dot + elapsed time chip in the sidebar when a session is running

**useTimer hook (`apps/web/src/hooks/useTimer.ts`):**
- Returns: `{ isRunning, elapsedSeconds, activeSession, startTimer(projectId), stopTimer() }`
- Manages `setInterval` lifecycle (cleared on unmount)
- On `startTimer`: calls API, sets `isRunning=true`, stores `started_at`
- On `stopTimer`: calls API, clears interval, returns final session

**useDashboard hook (`apps/web/src/hooks/useDashboard.ts`):**
- Returns: `{ todaySessions, weeklySummary, isLoading }`
- Uses `react-query` (`useQuery`) for `GET /sessions?date_from=today` and `GET /reports/summary?period=week`
- Invalidates `todaySessions` query after timer stops

**Weekly Bar Chart:**
- `recharts BarChart` with X-axis = day labels (Mon–Sun), Y-axis = hours
- Data sourced from `by_day` array in report summary response
- Displays "No data" state if no sessions this week

**Playwright E2E Test (`apps/web/tests/e2e/dashboard.spec.ts`):**
- `test('full timer flow')`:
  1. Navigate to `http://localhost:5173`
  2. Login with `playwright@test.com / Test1234!`
  3. Assert dashboard visible with timer in idle state
  4. Click "Start Timer", select a project, confirm
  5. Assert timer shows `00:00:XX` and is incrementing
  6. Wait 3 seconds; assert elapsed time >= 3 seconds
  7. Click "Stop"
  8. Assert session appears in "Today's Sessions" list
  9. Assert active session indicator in sidebar is gone

**Vitest Tests (`apps/web/tests/`):**
- `test_timer_component.test.tsx`: renders idle state, start triggers API call, displays elapsed time
- `test_dashboard_page.test.tsx`: renders with mocked data, chart renders with correct data
- `test_use_timer_hook.test.ts`: start/stop lifecycle, interval management

### Deliverables

| Artifact | Path |
|----------|------|
| Dashboard page | `apps/web/src/pages/DashboardPage.tsx` |
| Timer component | `apps/web/src/components/TimerComponent.tsx` |
| useTimer hook | `apps/web/src/hooks/useTimer.ts` |
| useDashboard hook | `apps/web/src/hooks/useDashboard.ts` |
| Weekly chart | Embedded in `DashboardPage.tsx` using recharts |
| Sidebar indicator | Updated `apps/web/src/components/AppLayout.tsx` |
| Playwright E2E | `apps/web/tests/e2e/dashboard.spec.ts` |
| Vitest tests | `apps/web/tests/` (timer + dashboard) |

### Acceptance Criteria

- Dashboard renders live timer updating every second
- Start timer: project selector appears; after selection, timer starts and shows `HH:MM:SS`
- Timer state persists across page reloads (active session restored from API)
- Stop timer: session appears in "Today's Sessions" list below the timer
- Weekly bar chart renders with at least one bar when sessions exist this week
- Sidebar shows active session indicator when timer is running
- Playwright E2E passes end-to-end: login → start → wait 3s → stop → verify session

---

## Unit 8: Projects + Clients + Sessions UI

**Wave:** 4
**Labels:** frontend, ui
**Priority:** 4
**Depends On:** U3 (sessions/projects/clients API), U6 (React base)

### Scope

**ClientsPage (`apps/web/src/pages/ClientsPage.tsx`):**
- Table columns: Name, Email, Hourly Rate (editable inline), Currency, Actions (Edit, Delete)
- Inline edit for `hourly_rate`: click to edit, save on blur or Enter, cancel on Escape; calls `PUT /clients/{id}`
- "New Client" button: opens `ClientModal` — form with Name (required), Email, Hourly Rate, Currency (dropdown: USD/EUR/GBP); Zod validation; calls `POST /clients`
- Delete: shows confirmation dialog ("Are you sure? This cannot be undone if the client has no active projects"); calls `DELETE /clients/{id}`; handles 409 with user-friendly error toast ("Cannot delete: client has active projects")
- `useClients` hook with `react-query` for data fetching and cache invalidation

**ProjectsPage (`apps/web/src/pages/ProjectsPage.tsx`):**
- Table columns: Color (swatch), Name, Client, Status (Active/Inactive badge), Actions
- Color picker: small `<input type="color">` inline; updates `color` field; calls `PUT /projects/{id}`
- Client assignment: dropdown of user's clients (nullable — "No client")
- Active/Inactive toggle: switch component; calls `PATCH /projects/{id}/deactivate` or `PUT /projects/{id}` with `is_active`
- "New Project" button: opens `ProjectModal` — Name, Description, Color, Client (optional), Is Active; Zod validation
- `useProjects` hook with `react-query`

**SessionsPage (`apps/web/src/pages/SessionsPage.tsx`):**
- Paginated table: Date, Project, Description (editable inline), Duration, Actions (Delete)
- Filter bar: Date From (date picker), Date To (date picker), Project (dropdown); filters applied via query params to API
- Pagination controls: previous/next, shows "Page X of Y", configurable page size
- "Log Time" button: opens `ManualSessionForm` — Project (required dropdown), Started At (datetime picker), Ended At (datetime picker), Description; Zod validation (ended_at > started_at, max 24h); calls `POST /sessions`
- Inline description edit: click to edit, save on blur; calls `PUT /sessions/{id}`
- Delete: confirmation then `DELETE /sessions/{id}`
- `useSessions` hook with `react-query`, pagination state

**Shared UI:**
- All forms use `react-hook-form` + `@hookform/resolvers/zod`
- Loading states: skeleton loaders or spinner overlay on tables during fetch
- Error toasts: `react-hot-toast.error()` for API errors (show `detail` from FastAPI response)
- Success toasts: `react-hot-toast.success()` after create/update/delete
- All modals trap focus and close on Escape

**Hooks (`apps/web/src/hooks/`):**
- `useClients.ts`: `{ clients, isLoading, createClient, updateClient, deleteClient }`
- `useProjects.ts`: `{ projects, isLoading, createProject, updateProject, deactivateProject }`
- `useSessions.ts`: `{ sessions, pagination, isLoading, createSession, updateSession, deleteSession, setFilters }`

**Vitest Tests (`apps/web/tests/`):**
- `test_clients_page.test.tsx`: table renders with mock data, inline edit triggers PUT, delete 409 shows correct error
- `test_projects_page.test.tsx`: table renders, color picker changes color, active toggle works
- `test_sessions_page.test.tsx`: table renders paginated, filter bar filters data, manual entry form validates

### Deliverables

| Artifact | Path |
|----------|------|
| Clients page | `apps/web/src/pages/ClientsPage.tsx` |
| Projects page | `apps/web/src/pages/ProjectsPage.tsx` |
| Sessions page | `apps/web/src/pages/SessionsPage.tsx` |
| Hooks | `useClients.ts`, `useProjects.ts`, `useSessions.ts` |
| Modals | `ClientModal.tsx`, `ProjectModal.tsx`, `ManualSessionForm.tsx` |
| Vitest tests | `apps/web/tests/` (clients + projects + sessions) |

### Acceptance Criteria

- `/clients` page renders client table; inline edit saves on blur
- "New Client" modal validates with Zod (email format, required name)
- Delete client with active projects shows toast "Cannot delete: client has active projects"
- `/projects` page renders project table with color swatches; color picker updates live
- Active/Inactive toggle correctly calls the deactivate/reactivate endpoint
- `/sessions` page paginates correctly; filters by date range and project
- Manual session form rejects `ended_at <= started_at` with inline error
- All success/error operations show appropriate toasts
- All Vitest tests pass

---

## Unit 9: Reports + Invoices UI

**Wave:** 5
**Labels:** frontend, ui
**Priority:** 5
**Depends On:** U4 (invoice API), U8 (sessions/clients UI)

### Scope

**ReportsPage (`apps/web/src/pages/ReportsPage.tsx`):**
- Period selector: three buttons — "This Week", "This Month", "Custom Range"
- Custom range: two date pickers (from/to) that appear when "Custom Range" is selected
- Bar chart: `recharts BarChart` — X-axis = day labels, Y-axis = hours; data from `by_day` array; bars colored with app primary color
- Summary table — "By Client" section: columns: Client Name, Hours, Amount (hourly_rate * hours), Currency
- Summary table — "By Project" section: columns: Project Name, Client, Hours
- Loading skeleton while data fetches
- Empty state message if no sessions in selected period
- `useReports` hook

**InvoicesPage (`apps/web/src/pages/InvoicesPage.tsx`):**
- "Generate Invoice" form panel at top:
  - Client selector dropdown (required)
  - Period Start date picker (required)
  - Period End date picker (required, must be >= Period Start)
  - "Generate" button: calls `POST /invoices`; on success shows invoice number in toast + adds to list
  - Zod validation on all fields
- Invoice list table: columns: Invoice #, Client, Period, Hours, Amount, Status (badge), Actions
- Status badge colors: `draft` = gray, `sent` = blue, `paid` = green
- Status dropdown per row: `<select>` with options; calls `PATCH /invoices/{id}` on change; disabled for `paid` invoices
- "Download PDF" button: fetches `GET /invoices/{id}/pdf` as blob → creates object URL → triggers `<a download>` click → revokes URL; shows loading spinner during fetch
- `useInvoices` hook

**useReports hook (`apps/web/src/hooks/useReports.ts`):**
- State: `{ period, dateFrom, dateTo }`
- Returns: `{ summary, isLoading, setPeriod, setCustomRange }`
- Uses `react-query` with query key including period + dates

**useInvoices hook (`apps/web/src/hooks/useInvoices.ts`):**
- Returns: `{ invoices, isLoading, createInvoice, updateInvoiceStatus, downloadPdf }`
- `downloadPdf(invoiceId)`: fetches blob, creates object URL, triggers browser download, cleans up

**Vitest Tests (`apps/web/tests/`):**
- `test_reports_page.test.tsx`: period selector switches data, chart renders with mock data, custom range shows date pickers
- `test_invoices_page.test.tsx`: generate form validates, invoice list renders with status badges, status dropdown triggers PATCH
- `test_pdf_download.test.tsx`: simulates blob fetch, asserts anchor click triggered with correct filename

### Deliverables

| Artifact | Path |
|----------|------|
| Reports page | `apps/web/src/pages/ReportsPage.tsx` |
| Invoices page | `apps/web/src/pages/InvoicesPage.tsx` |
| useReports hook | `apps/web/src/hooks/useReports.ts` |
| useInvoices hook | `apps/web/src/hooks/useInvoices.ts` |
| Vitest tests | `apps/web/tests/` (reports + invoices) |

### Acceptance Criteria

- `/reports` renders period selector; switching periods re-fetches and re-renders chart
- Custom date range: both date pickers appear; "Generate" fetches with correct params
- Bar chart renders with correct day labels and hour values
- `/invoices` "Generate Invoice" form validates all fields with Zod
- Generating invoice adds it to the list with status `draft`
- Status dropdown updates invoice status; `paid` invoices have dropdown disabled
- "Download PDF" triggers browser download of `.pdf` file without page navigation
- All Vitest tests pass

---

## Code Organization

Full monorepo directory structure for ChronoTrack:

```
/workspace/trabajo/test-symphony/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── core/
│   │   │   │   ├── config.py        # Pydantic Settings, env vars
│   │   │   │   ├── security.py      # JWT encode/decode, bcrypt hashing
│   │   │   │   ├── dependencies.py  # get_current_user, get_db
│   │   │   │   └── exceptions.py    # Custom exception hierarchy
│   │   │   ├── db/
│   │   │   │   ├── database.py      # Async engine, Base
│   │   │   │   └── session.py       # AsyncSession factory
│   │   │   ├── models/
│   │   │   │   ├── base.py          # BaseModel with id + created_at
│   │   │   │   ├── user.py
│   │   │   │   ├── client.py
│   │   │   │   ├── project.py
│   │   │   │   ├── session.py
│   │   │   │   └── invoice.py
│   │   │   ├── schemas/
│   │   │   │   ├── auth.py
│   │   │   │   ├── client.py
│   │   │   │   ├── project.py
│   │   │   │   ├── session.py
│   │   │   │   ├── invoice.py
│   │   │   │   └── report.py
│   │   │   ├── routers/
│   │   │   │   ├── auth.py
│   │   │   │   ├── clients.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── sessions.py
│   │   │   │   ├── reports.py
│   │   │   │   ├── invoices.py
│   │   │   │   ├── telegram.py
│   │   │   │   └── health.py
│   │   │   └── services/
│   │   │       ├── auth.py
│   │   │       ├── client.py
│   │   │       ├── project.py
│   │   │       ├── session.py
│   │   │       ├── report.py
│   │   │       ├── invoice.py
│   │   │       ├── pdf.py
│   │   │       └── telegram.py
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   ├── test_auth.py
│   │   │   ├── test_clients.py
│   │   │   ├── test_projects.py
│   │   │   ├── test_sessions.py
│   │   │   ├── test_reports.py
│   │   │   └── test_invoices.py
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   │       └── 0001_initial_schema.py
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   │
│   ├── web/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── AppLayout.tsx
│   │   │   │   ├── TimerComponent.tsx
│   │   │   │   ├── BarChartComponent.tsx
│   │   │   │   ├── ClientModal.tsx
│   │   │   │   ├── ProjectModal.tsx
│   │   │   │   └── ManualSessionForm.tsx
│   │   │   ├── pages/
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── RegisterPage.tsx
│   │   │   │   ├── DashboardPage.tsx
│   │   │   │   ├── ProjectsPage.tsx
│   │   │   │   ├── ClientsPage.tsx
│   │   │   │   ├── SessionsPage.tsx
│   │   │   │   ├── ReportsPage.tsx
│   │   │   │   └── InvoicesPage.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   ├── useTimer.ts
│   │   │   │   ├── useDashboard.ts
│   │   │   │   ├── useSessions.ts
│   │   │   │   ├── useProjects.ts
│   │   │   │   ├── useClients.ts
│   │   │   │   ├── useReports.ts
│   │   │   │   └── useInvoices.ts
│   │   │   ├── services/
│   │   │   │   ├── apiClient.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── clients.ts
│   │   │   │   ├── projects.ts
│   │   │   │   ├── sessions.ts
│   │   │   │   ├── reports.ts
│   │   │   │   └── invoices.ts
│   │   │   ├── types/
│   │   │   │   └── api.ts
│   │   │   ├── context/
│   │   │   │   └── AuthContext.tsx
│   │   │   ├── App.tsx
│   │   │   └── main.tsx
│   │   ├── tests/
│   │   │   ├── test_auth_context.test.tsx
│   │   │   ├── test_login_page.test.tsx
│   │   │   ├── test_register_page.test.tsx
│   │   │   ├── test_timer_component.test.tsx
│   │   │   ├── test_dashboard_page.test.tsx
│   │   │   ├── test_clients_page.test.tsx
│   │   │   ├── test_projects_page.test.tsx
│   │   │   ├── test_sessions_page.test.tsx
│   │   │   ├── test_reports_page.test.tsx
│   │   │   ├── test_invoices_page.test.tsx
│   │   │   └── e2e/
│   │   │       └── dashboard.spec.ts
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── tsconfig.json
│   │
│   └── bot/
│       ├── bot/
│       │   ├── main.py
│       │   ├── handlers/
│       │   │   ├── start.py
│       │   │   ├── link.py
│       │   │   ├── log.py
│       │   │   ├── status.py
│       │   │   ├── report.py
│       │   │   └── stop.py
│       │   └── services/
│       │       └── api_client.py
│       ├── tests/
│       │   ├── test_handlers.py
│       │   └── test_api_client.py
│       ├── Dockerfile
│       └── pyproject.toml
│
├── packages/
│   └── shared/                  # Placeholder for shared constants
│
├── docker-compose.yml
├── docker-compose.test.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── Makefile
├── .env.example
└── aidlc-docs/
    └── inception/
        └── application-design/
            ├── unit-of-work.md          # This document
            ├── unit-of-work-dependency.md
            └── unit-of-work-story-map.md
```
