# ChronoTrack — Unit of Work Story Map

**Project:** ChronoTrack
**Source:** PRD `prd-chronotrack.md`
**Date:** 2026-03-22

---

## About This Document

ChronoTrack's PRD defines requirements using **functional requirements (RF-*)** and **BDD acceptance criteria (Gherkin scenarios)** rather than traditional user stories. This story map:

1. Maps every RF-* functional requirement to the unit(s) of work that fulfill it
2. Maps every BDD Gherkin scenario from the PRD to the unit(s) that implement and test it
3. Maps non-functional requirements (security, quality, performance, infra) to units
4. Confirms full coverage — every requirement has at least one owner

> **Primary validation mechanism:** BDD acceptance criteria (Gherkin scenarios from the PRD) are the authoritative test of correctness for each unit. Vitest, pytest, and Playwright tests must be structured to directly validate each Gherkin scenario.

---

## Section 1: Functional Requirements Coverage by Unit

### Auth & Users (RF-AUTH-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-AUTH-01 | Registration with email and password (unique email, validated; password min 8 chars, bcrypt==4.0.1 hashed; returns access token 15 min + refresh token 30 days) | **U1** |
| RF-AUTH-02 | Login with email and password (returns token pair; invalidates previous refresh tokens) | **U1** |
| RF-AUTH-03 | Refresh access token via `POST /auth/refresh`; rotates refresh token (invalidates old one) | **U1** |

### Client Management (RF-CLIENT-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-CLIENT-01 | Full CRUD for clients (name, email, hourly_rate, currency) | **U2** (API), **U8** (UI) |
| RF-CLIENT-02 | A client can have multiple projects | **U2** (API — one-to-many relation), **U8** (UI — displays project count or assignment) |
| RF-CLIENT-03 | Cannot delete a client with active projects (HTTP 409) | **U2** (API guard), **U8** (UI — shows error toast) |

### Project Management (RF-PROJ-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-PROJ-01 | CRUD for projects (name, description, color hex, client assignment, active/inactive status) | **U2** (API), **U8** (UI) |
| RF-PROJ-02 | Projects can exist without a client assigned | **U2** (API — `client_id` nullable), **U8** (UI — client dropdown optional) |
| RF-PROJ-03 | Only active projects accept new time sessions | **U3** (API — `SessionService.start_session` validates `project.is_active`), **U8** (UI — inactive projects excluded from session project selector) |

### Time Tracking (RF-TIME-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-TIME-01 | Timer start/stop: `POST /sessions/start` (one active session guard, HTTP 409 if duplicate); `POST /sessions/stop` (computes `duration_seconds`) | **U3** (API), **U7** (UI timer component) |
| RF-TIME-02 | Manual session entry: `POST /sessions` with `started_at`, `ended_at`, `project_id`, `description`; validate `ended_at > started_at`; max 24h per session | **U3** (API), **U8** (UI manual entry form) |
| RF-TIME-03 | Edit and delete past sessions | **U3** (API — `PUT /sessions/{id}`, `DELETE /sessions/{id}`), **U8** (UI — inline edit, delete confirm) |
| RF-TIME-04 | Session list with filters: `project_id`, `client_id`, `date_from`, `date_to` | **U3** (API), **U8** (UI filter bar) |

### Reports (RF-REPORT-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-REPORT-01 | `GET /reports/summary` with `period=week\|month\|custom`; returns `total_hours`, `billable_hours`, `by_project[]`, `by_client[]`, `by_day[]` | **U3** (API ReportService + endpoint), **U9** (UI reports page), **U7** (UI — weekly summary on dashboard) |
| RF-REPORT-02 | Bar chart by day in the dashboard (React + recharts) | **U7** (dashboard bar chart), **U9** (reports page detailed chart) |

### Invoice Generation (RF-INV-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-INV-01 | Generate invoice for a client+period: groups sessions, calculates `total_hours × hourly_rate`, assigns sequential invoice number `INV-{YEAR}-{SEQ:03d}` | **U4** (API InvoiceService), **U9** (UI generate form) |
| RF-INV-02 | Generate PDF: freelancer name, client data, sessions table (date, description, hours, subtotal), totals, invoice number, period | **U4** (API PDFService + WeasyPrint template) |
| RF-INV-03 | Download PDF via `GET /invoices/{id}/pdf` | **U4** (API endpoint returning `FileResponse`), **U9** (UI download button) |
| RF-INV-04 | Invoice status transitions: draft → sent → paid (manual via `PATCH /invoices/{id}`) | **U4** (API status validation), **U9** (UI status dropdown) |

### Telegram Bot (RF-BOT-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-BOT-01 | `/start` command — welcome message + command list | **U5** |
| RF-BOT-02 | `/log <hours> <project> <description>` — registers manual session via API | **U5** |
| RF-BOT-03 | `/status` — shows current active session or "No active session" | **U5** |
| RF-BOT-04 | `/report` — weekly summary in text format | **U5** |
| RF-BOT-05 | `/stop` — stops active session, shows duration | **U5** |
| RF-BOT-06 | Bot only responds to registered/linked users (verified via `telegram_chat_id`) | **U5** |
| RF-BOT-07 | `/link <email>` — links Telegram account to ChronoTrack account | **U5** |

### Dashboard UI (RF-UI-*)

| Requirement ID | Requirement Description | Owner Unit(s) |
|----------------|------------------------|---------------|
| RF-UI-01 | `/dashboard` page: live timer (1s updates), Start/Stop buttons, project selector, weekly bar chart, today's sessions list | **U7** |
| RF-UI-02 | `/projects` page: project table with inline CRUD | **U8** |
| RF-UI-03 | `/clients` page: client table with editable hourly rate | **U8** |
| RF-UI-04 | `/sessions` page: paginated list with date/project filters | **U8** |
| RF-UI-05 | `/reports` page: period selector, bar chart by day, summary table by client and project | **U9** |
| RF-UI-06 | `/invoices` page: generate form (client + period), invoice list with status + PDF download | **U9** |

---

## Section 2: BDD Scenario Coverage by Unit

### Feature: User Authentication

| BDD Scenario | PRD Section | Owner Unit | Test File |
|--------------|-------------|------------|-----------|
| Registro exitoso: user registers with "nuevo@test.com" / "Seguro123!", receives valid access token, can access protected endpoints | §5.1 | **U1** | `apps/api/tests/test_auth.py::test_register_success` |
| Login con credenciales correctas: registered user logs in, receives access token and refresh token | §5.1 | **U1** | `apps/api/tests/test_auth.py::test_login_success` |
| Acceso denegado sin token: accessing protected endpoint without Authorization header returns 401 | §5.1 | **U1** | `apps/api/tests/test_auth.py::test_protected_endpoint_without_token` |

### Feature: Client Management

| BDD Scenario | PRD Section | Owner Unit | Test File |
|--------------|-------------|------------|-----------|
| Crear cliente: authenticated user creates "Acme Corp" at $150/h; client appears in their list | §5.2 | **U2** | `apps/api/tests/test_clients.py::test_create_client_success` |
| Prevenir borrado con proyectos: client with active projects cannot be deleted; returns 409 with descriptive message | §5.2 | **U2** | `apps/api/tests/test_clients.py::test_delete_client_with_active_projects` |

### Feature: Time Tracking (Timer)

| BDD Scenario | PRD Section | Owner Unit | Test File |
|--------------|-------------|------------|-----------|
| Iniciar y detener sesión: user starts timer for active project, stops 30 min later; session records 30 min duration | §5.4 | **U3** (API), **U7** (UI) | `apps/api/tests/test_sessions.py::test_stop_session_computes_duration` + `apps/web/tests/e2e/dashboard.spec.ts::test_full_timer_flow` |
| No se puede iniciar dos timers: user with running timer tries to start another; receives 409 "Ya hay una sesión activa" | §5.4 | **U3** (API guard) | `apps/api/tests/test_sessions.py::test_start_session_duplicate_guard` |
| Registro manual de tiempo: user logs 2 hours yesterday for a project; hours appear in yesterday's report | §5.4 | **U3** (API), **U8** (UI form) | `apps/api/tests/test_sessions.py::test_manual_session_valid` |

### Feature: Invoice Generation

| BDD Scenario | PRD Section | Owner Unit | Test File |
|--------------|-------------|------------|-----------|
| Crear factura mensual: client has 40h in March at $100/h; invoice for 2026-03-01/2026-03-31 shows $4,000.00; PDF downloadable | §5.6 | **U4** (API), **U9** (UI) | `apps/api/tests/test_invoices.py::test_create_invoice_calculates_total_correctly` + `test_download_pdf_returns_file` |
| Número de factura secuencial: INV-2026-001 already exists; new invoice gets INV-2026-002 | §5.6 | **U4** | `apps/api/tests/test_invoices.py::test_invoice_number_sequential` |

---

## Section 3: Non-Functional Requirements Coverage by Unit

### NFR: Security (§6.1)

| Non-Functional Requirement | Owner Unit(s) | Implementation Notes |
|---------------------------|---------------|----------------------|
| Passwords hashed with bcrypt==4.0.1 (pinned version) | **U1** | `pyproject.toml` pins `bcrypt==4.0.1`; `security.py` uses `passlib[bcrypt]` |
| JWT access tokens expire in 15 minutes | **U1** | `create_access_token` sets exp claim; configurable via env var |
| Refresh tokens use rotation strategy (invalidate on use) | **U1** | Rotation implemented in `AuthService.refresh_token()` |
| All data endpoints require authentication | **U1** (auth dependency), **U2–U5** (use the dependency) | `get_current_user` FastAPI dependency applied to all routers |
| Row-level isolation: users see only their own data | **U2, U3, U4, U5** | Every service query filters by `user_id` |
| No hardcoded secrets; all config via environment variables | **U1** | `pydantic-settings` `Settings` class; `.env.example` documents all vars; bandit CI check |
| Strict input validation (Pydantic v2 with Field validators) | **U1** (auth schemas), **U2** (client/project schemas), **U3** (session schemas), **U4** (invoice schemas) | All schemas use `Field(...)` with validators; regex for hex color, email format, etc. |

### NFR: Code Quality (§6.2)

| Non-Functional Requirement | Owner Unit(s) | Implementation Notes |
|---------------------------|---------------|----------------------|
| Backend test coverage >= 80% | **U1** (auth tests), **U2** (client/project tests), **U3** (session/report tests), **U4** (invoice tests), **U5** (bot tests) | Enforced by `--cov-fail-under=80` in pytest config; checked in CI |
| Zero ruff errors | **U1** (CI setup), all backend units | `ruff check` in `.github/workflows/ci.yml`; all units must pass |
| Zero bandit high/critical findings | **U1** (CI setup), all backend units | `bandit -r app/` in CI |
| Zero hardcoded secrets | **U1** (bandit + env setup), all units | bandit B105/B106/B107 rules catch hardcoded secrets |
| Complete Python type hints (mypy-compatible) | **U1–U5** | All function signatures must have type annotations; enforced by ruff |
| TypeScript strict mode in frontend | **U6** (tsconfig.json), **U7, U8, U9** | `"strict": true` in `tsconfig.json`; `tsc --noEmit` in CI |

### NFR: Performance (§6.3)

| Non-Functional Requirement | Owner Unit(s) | Implementation Notes |
|---------------------------|---------------|----------------------|
| Paginated endpoints (max 50 items per page) | **U3** (`GET /sessions` pagination), **U4** (`GET /invoices` if needed), **U8** (frontend pagination controls) | `page_size` parameter with max enforcement via Pydantic `Field(le=50)` |
| DB indexes on `sessions(user_id, started_at)` and `sessions(project_id)` | **U3** | Alembic migration in U3 adds both indexes |
| Lazy loading of SQLAlchemy relationships | **U1** (model definitions), **U2–U4** (service queries) | `lazy="noload"` or explicit `selectinload` only when needed; avoid N+1 queries |

### NFR: Docker Compose Infrastructure (§6.4)

| Non-Functional Requirement | Owner Unit(s) | Implementation Notes |
|---------------------------|---------------|----------------------|
| `db` service (postgres:16, port 5432) | **U1** | Defined in `docker-compose.yml` |
| `api` service (FastAPI, port 8000) | **U1** | Defined in `docker-compose.yml` with `Dockerfile` |
| `web` service (React/Vite, port 5173) | **U1** (service stub in compose), **U6** (actual `Dockerfile`) | Compose defines service; U6 provides the `apps/web/Dockerfile` |
| `bot` service (only starts if TELEGRAM_TOKEN is set) | **U1** (service stub), **U5** (actual bot + Dockerfile) | `command` in compose uses shell check: `[ -z "$$TELEGRAM_TOKEN" ] && exit 0 || python -m bot.main` |
| All environment variables in `.env.example` | **U1** | Documents all required and optional env vars |

### NFR: Definition of Done (§7)

All 9 units must satisfy the following before being considered "Done":

| Criterion | Verified By |
|-----------|-------------|
| All unit tests pass (pytest / vitest) | CI job in `.github/workflows/ci.yml` |
| Module coverage >= 80% | `pytest --cov-fail-under=80` |
| Ruff and bandit report zero errors | CI lint job |
| PR merged to `develop` | GitHub PR merge gate |
| `docker-compose up` starts without errors | CI integration test |
| `GET /api/v1/health` returns 200 | CI smoke test |
| For frontend units (U6–U9): Playwright validates the UI flow | Playwright job in CI or Local Review stage |

---

## Section 4: Full Unit-to-Requirement Mapping Table

A consolidated view of every requirement and which unit owns it.

| Unit | Functional Requirements | BDD Scenarios | Non-Functional Requirements |
|------|------------------------|---------------|----------------------------|
| **U1** | RF-AUTH-01, RF-AUTH-02, RF-AUTH-03 | Auth: registro exitoso, login correcto, acceso denegado sin token | NFR: bcrypt pinning, JWT expiry, refresh rotation, no hardcoded secrets, ruff/bandit in CI, Docker Compose (db+api), .env.example |
| **U2** | RF-CLIENT-01, RF-CLIENT-02, RF-CLIENT-03, RF-PROJ-01, RF-PROJ-02 | Client: crear cliente, prevenir borrado con proyectos | NFR: row-level isolation, input validation (Pydantic), type hints |
| **U3** | RF-TIME-01, RF-TIME-02, RF-TIME-03, RF-TIME-04, RF-REPORT-01 | Timer: iniciar y detener, no duplicar timers, registro manual | NFR: DB indexes on sessions, pagination (max 50), lazy loading |
| **U4** | RF-INV-01, RF-INV-02, RF-INV-03, RF-INV-04 | Invoice: crear factura mensual con total correcto, número secuencial | NFR: type hints, test coverage >= 80% |
| **U5** | RF-BOT-01, RF-BOT-02, RF-BOT-03, RF-BOT-04, RF-BOT-05, RF-BOT-06, RF-BOT-07 | (Bot-specific BDD: see unit scope) | NFR: TELEGRAM_TOKEN conditional start, bot exits gracefully if unset |
| **U6** | (Frontend base — enables RF-UI-* pages) | (Auth UI flows for RF-AUTH-01/02/03) | NFR: TypeScript strict mode, Vite setup, Docker web service |
| **U7** | RF-UI-01, RF-TIME-01 (UI side), RF-REPORT-02 | Timer E2E: login → start → wait 3s → stop → verify session | NFR: TypeScript strict mode, Playwright E2E in CI |
| **U8** | RF-UI-02, RF-UI-03, RF-UI-04, RF-CLIENT-01 (UI), RF-PROJ-01 (UI), RF-TIME-02 (UI), RF-TIME-03 (UI), RF-TIME-04 (UI) | (Implicit: all CRUD operations visible through UI) | NFR: TypeScript strict mode, Zod form validation |
| **U9** | RF-UI-05, RF-UI-06, RF-INV-01 (UI), RF-INV-03 (UI), RF-INV-04 (UI), RF-REPORT-01 (UI) | Invoice UI: generate invoice form, download PDF, change status | NFR: TypeScript strict mode, PDF blob download |

---

## Section 5: Coverage Completeness

### Functional Requirements Coverage Audit

The following table confirms that every RF-* requirement from the PRD is assigned to at least one unit.

| RF Code | Description | Assigned To | Status |
|---------|-------------|-------------|--------|
| RF-AUTH-01 | Registration with email/password | U1, U6 | Covered |
| RF-AUTH-02 | Login with token pair | U1, U6 | Covered |
| RF-AUTH-03 | Refresh token rotation | U1, U6 | Covered |
| RF-CLIENT-01 | Client CRUD | U2, U8 | Covered |
| RF-CLIENT-02 | Client has multiple projects | U2, U8 | Covered |
| RF-CLIENT-03 | Cannot delete client with active projects | U2, U8 | Covered |
| RF-PROJ-01 | Project CRUD with color and status | U2, U8 | Covered |
| RF-PROJ-02 | Projects without client | U2, U8 | Covered |
| RF-PROJ-03 | Only active projects accept sessions | U3, U8 | Covered |
| RF-TIME-01 | Timer start/stop (one active, duration computed) | U3, U7 | Covered |
| RF-TIME-02 | Manual session entry with time validation | U3, U8 | Covered |
| RF-TIME-03 | Edit and delete past sessions | U3, U8 | Covered |
| RF-TIME-04 | Session list with filters | U3, U8 | Covered |
| RF-REPORT-01 | Summary endpoint with breakdown by project/client/day | U3, U7, U9 | Covered |
| RF-REPORT-02 | Bar chart by day in dashboard | U7, U9 | Covered |
| RF-INV-01 | Invoice generation with sequential numbering | U4, U9 | Covered |
| RF-INV-02 | PDF generation with sessions table | U4 | Covered |
| RF-INV-03 | PDF download endpoint | U4, U9 | Covered |
| RF-INV-04 | Invoice status transitions | U4, U9 | Covered |
| RF-BOT-01 | `/start` command | U5 | Covered |
| RF-BOT-02 | `/log` command | U5 | Covered |
| RF-BOT-03 | `/status` command | U5 | Covered |
| RF-BOT-04 | `/report` command | U5 | Covered |
| RF-BOT-05 | `/stop` command | U5 | Covered |
| RF-BOT-06 | Bot only responds to linked users | U5 | Covered |
| RF-BOT-07 | `/link` command | U5 | Covered |
| RF-UI-01 | Dashboard page with live timer | U7 | Covered |
| RF-UI-02 | Projects page with inline CRUD | U8 | Covered |
| RF-UI-03 | Clients page with editable hourly rate | U8 | Covered |
| RF-UI-04 | Sessions page with paginated list + filters | U8 | Covered |
| RF-UI-05 | Reports page with period selector and charts | U9 | Covered |
| RF-UI-06 | Invoices page with generate form and PDF download | U9 | Covered |

**Result: All 32 functional requirements are covered by at least one unit. No gaps.**

### BDD Scenario Coverage Audit

| Gherkin Feature | Scenarios | Covered By Unit(s) |
|-----------------|-----------|-------------------|
| Autenticación de usuarios | Registro exitoso, login correcto, acceso denegado sin token | U1, U6 |
| Gestión de clientes | Crear cliente, prevenir borrado con proyectos | U2, U8 |
| Timer de trabajo | Iniciar y detener sesión, no se puede iniciar dos timers, registro manual | U3, U7, U8 |
| Generación de facturas | Crear factura mensual, número secuencial | U4, U9 |

**Result: All 10 PRD Gherkin scenarios are covered. Each scenario maps to at least one unit with a corresponding test.**

### Non-Functional Requirements Coverage Audit

| NFR Category | Requirements | Covered By |
|-------------|-------------|-----------|
| Security (§6.1) | 7 requirements | U1 (foundation), U2–U5 (enforcement) |
| Code Quality (§6.2) | 6 requirements | U1 (CI tooling), all units (compliance) |
| Performance (§6.3) | 3 requirements | U1 (lazy loading), U3 (indexes, pagination), U8 (frontend pagination) |
| Docker / Infra (§6.4) | 5 requirements | U1 (compose), U5 (bot), U6 (web Dockerfile) |

**Result: All non-functional requirements are addressed.**

---

## Section 6: Validation Mechanism Note

BDD acceptance criteria (Gherkin scenarios defined in the PRD) are the **primary validation mechanism** for ChronoTrack. Each unit's "Done" state is confirmed when:

1. **Backend units (U1–U5):** pytest test functions are written to directly correspond to each Gherkin scenario. Test names should reference the scenario title (e.g., `test_cannot_start_duplicate_timer` maps to "No se puede iniciar dos timers").

2. **Frontend units (U6–U9):** Vitest component tests validate individual behaviors; Playwright E2E tests (for U7 and optionally U8/U9) validate full user flows matching the PRD §10 validation checklist.

3. **Integration:** The PRD Gherkin scenarios that touch both API and UI (e.g., "Iniciar y detener sesión" used in U3 API tests AND U7 Playwright E2E) serve as cross-unit integration contracts.

No requirement is considered fully implemented until its corresponding Gherkin scenario can be demonstrated passing in the test suite.
