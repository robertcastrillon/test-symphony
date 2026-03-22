# ChronoTrack — Unit of Work Dependency Map

**Project:** ChronoTrack
**Total Units:** 9
**Date:** 2026-03-22

---

## 1. Dependency Matrix

The matrix below shows which unit (row) depends on which other unit (column). An **X** in cell `(row, col)` means "the row unit requires the col unit to be complete before it can begin."

| Unit | U1 | U2 | U3 | U4 | U5 | U6 | U7 | U8 | U9 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **U1** Foundation — Auth + DB + Docker | | | | | | | | | |
| **U2** Client & Project Management API | X | | | | | | | | |
| **U3** Time Tracking API | | X | | | | | | | |
| **U4** Invoice Generation | | | X | | | | | | |
| **U5** Telegram Bot | | | X | | | | | | |
| **U6** React Frontend — Auth + Layout | | | | | | | | | |
| **U7** Dashboard + Timer UI | | | X | | | X | | | |
| **U8** Projects + Clients + Sessions UI | | | X | | | X | | | |
| **U9** Reports + Invoices UI | | | | X | | | | X | |

### Dependency Summary

| Unit | Depends On | Reason |
|------|------------|--------|
| U1 | — | Greenfield foundation, no prerequisites |
| U2 | U1 | Requires DB models, auth middleware, and project skeleton from U1 |
| U3 | U2 | Sessions reference projects and clients; requires validated CRUD to exist |
| U4 | U3 | Invoices aggregate sessions; requires session data model and service |
| U5 | U3 | Bot calls sessions start/stop and reports; all API endpoints needed |
| U6 | — | Frontend-only setup; runs in parallel with U1 (no API calls in this unit) |
| U7 | U3, U6 | Timer UI calls `/sessions/start`, `/sessions/stop`, `/reports/summary`; needs React base |
| U8 | U3, U6 | CRUD pages for clients, projects, sessions; needs all three API endpoints and React base |
| U9 | U4, U8 | Invoice UI needs `POST /invoices` and `GET /invoices/{id}/pdf` from U4; needs U8 for routing/layout patterns |

---

## 2. Wave Execution Plan

Units in the same wave execute in parallel. A wave begins only when all its dependencies (from prior waves) are complete.

```
┌─────────────────────────────────────────────────────────────────────┐
│  WAVE 1  (parallel — no dependencies)                               │
│                                                                     │
│  [U1 Foundation — Auth + DB + Docker]  [U6 React Base + Auth UI]   │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ U1 complete
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  WAVE 2  (sequential — U1 must be done)                             │
│                                                                     │
│  [U2 Client & Project Management API]                               │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ U2 complete
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  WAVE 3  (sequential — U2 must be done)                             │
│                                                                     │
│  [U3 Time Tracking API]                                             │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ U3 + U6 both complete
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  WAVE 4  (parallel — U3 + U6 must be done)                          │
│                                                                     │
│  [U4 Invoice Generation]  [U5 Telegram Bot]                         │
│  [U7 Dashboard + Timer UI]  [U8 Projects/Clients/Sessions UI]       │
│                                                                     │
│  Max parallel agents: 4                                             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ U4 + U8 both complete
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  WAVE 5  (sequential — U4 + U8 must be done)                        │
│                                                                     │
│  [U9 Reports + Invoices UI]                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Wave Summary

| Wave | Units | Parallel? | Gate Condition |
|------|-------|-----------|----------------|
| 1 | U1, U6 | Yes | None (greenfield) |
| 2 | U2 | No | U1 merged to develop |
| 3 | U3 | No | U2 merged to develop |
| 4 | U4, U5, U7, U8 | Yes (4 agents) | U3 merged AND U6 merged |
| 5 | U9 | No | U4 merged AND U8 merged |

---

## 3. Critical Path

The critical path is the longest chain of sequential dependencies. It determines the minimum number of waves required to complete the project.

```
U1 → U2 → U3 → U4 → U9
```

**Chain length:** 5 units (5 waves minimum)

| Step | Unit | Blocking? |
|------|------|-----------|
| 1 | U1 Foundation | Yes — all backend depends on this |
| 2 | U2 Client & Project API | Yes — U3 depends on U2 |
| 3 | U3 Time Tracking API | Yes — U4, U5, U7, U8 all depend on U3 |
| 4 | U4 Invoice Generation | Yes — U9 depends on U4 |
| 5 | U9 Reports + Invoices UI | Terminal — no dependents |

**Off-critical-path units:**
- U6: Starts in Wave 1, completes before Wave 4. Does not extend the critical path.
- U5: Parallel with U4 in Wave 4. Does not extend the critical path.
- U7: Parallel with U4 in Wave 4. Does not extend the critical path.
- U8: Parallel with U4 in Wave 4; U9 depends on it, but U8 is in Wave 4 same as U4, so it does not add a wave.

---

## 4. Integration Points

The table below describes the exact contract that each dependency pair shares — what APIs, data types, or infrastructure must be agreed upon at the boundary.

| Consumer Unit | Provider Unit | Integration Contract |
|---------------|---------------|----------------------|
| U2 → U1 | U1 provides to U2 | **Auth middleware**: `get_current_user` dependency must be importable from `app.core.dependencies`. **ORM models**: `User`, `Client`, `Project` SQLAlchemy models from `app.models.*`. **DB session**: `get_db` async dependency. **Exception types**: `NotFoundError`, `ConflictError`, `AuthenticationError` from `app.core.exceptions`. **Router registration pattern**: U2 registers its routers in the existing `main.py` using `app.include_router()`. |
| U3 → U2 | U2 provides to U3 | **Project model**: `Project.is_active`, `Project.client_id`, `Project.user_id` must be stable. **ProjectService**: `get_project(user_id, project_id)` must validate ownership — U3 calls this to verify project belongs to user before creating session. **Client model**: `Client.hourly_rate`, `Client.currency` needed by ReportService for amount calculation. |
| U4 → U3 | U3 provides to U4 | **Session model**: `Session.duration_seconds`, `Session.project_id`, `Session.started_at`, `Session.ended_at` — InvoiceService queries sessions by client+period. **ReportService**: shared aggregation logic may be reused by InvoiceService for total_hours calculation. **DB indexes**: `idx_sessions_user_started` and `idx_sessions_project` created in U3 migration benefit U4 queries. |
| U5 → U3 | U3 provides to U5 | **HTTP API contract** (Bot calls FastAPI over Docker network `http://api:8000`): `POST /api/v1/sessions/start`, `POST /api/v1/sessions/stop`, `POST /api/v1/sessions` (manual), `GET /api/v1/sessions` (with `?active=true`), `GET /api/v1/reports/summary?period=week`. **Auth**: Bot authenticates users via `telegram_chat_id`; needs `POST /api/v1/auth/telegram/link` endpoint (delivered in U5 but depends on User model from U1). **Response shapes**: `SessionResponse`, `ReportSummaryResponse` JSON schemas must match what `BotApiClient` parses. |
| U6 → U1 | U1 provides to U6 | **API endpoints** (U6 calls these): `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`. **Token shapes**: `{access_token, refresh_token, token_type}` — must match `TokenResponse` TypeScript type in `apps/web/src/types/api.ts`. **Error format**: FastAPI `{detail: string}` error responses — Axios interceptor reads `error.response.data.detail`. **CORS config**: U1 must configure CORS to allow `http://localhost:5173` (Vite dev server). |
| U7 → U3 | U3 provides to U7 | **Session endpoints** (Timer UI calls): `POST /api/v1/sessions/start` (body: `{project_id, description?}`), `POST /api/v1/sessions/stop` (no body), `GET /api/v1/sessions?date_from=&date_to=` (today's sessions), `GET /api/v1/reports/summary?period=week`. **Active session detection**: `GET /api/v1/sessions` must support `active=true` filter OR sessions with `ended_at IS NULL` accessible via the sessions list endpoint. **SessionResponse shape**: `{id, started_at, ended_at, duration_seconds, project_id, description}` — used by `useTimer` to restore elapsed time on reload. |
| U7 → U6 | U6 provides to U7 | **AppLayout**: U7 extends `AppLayout` to add the active session indicator slot; `AppLayout` must export a stable props interface with a slot or context hook. **AuthContext**: `useAuth()` hook for the authenticated axios client. **Route guard**: `/dashboard` route must be registered in `App.tsx` (U6 creates the routing structure). **Axios client**: U7 uses the same `apiClient.ts` with Bearer interceptor from U6. |
| U8 → U3 | U3 provides to U8 | **CRUD endpoints** (pages call): all of `GET/POST/PUT/DELETE /api/v1/clients`, `GET/POST/PUT/PATCH /api/v1/projects`, `GET/POST/PUT/DELETE /api/v1/sessions`. **Pagination contract**: `GET /sessions` returns `{items, total, page, page_size}` — `useSessions` hook reads this shape. **Filter params**: `?project_id=&client_id=&date_from=&date_to=&page=&page_size=` must be supported. **409 error format**: `{detail: "Cannot delete client with active projects"}` — `ClientsPage` shows this message in an error toast. |
| U8 → U6 | U6 provides to U8 | **AppLayout + routing**: U8 registers `/clients`, `/projects`, `/sessions` in `App.tsx` (or confirms they already exist from U6 stub). **Shared components**: modal patterns, form patterns, toast usage — U6 establishes the `react-hot-toast` setup; U8 calls `toast.success()` and `toast.error()`. **React Query client**: `QueryClientProvider` must be initialized in U6's `main.tsx` so U8 hooks can use `useQuery` / `useMutation`. |
| U9 → U4 | U4 provides to U9 | **Invoice endpoints**: `POST /api/v1/invoices` (body: `{client_id, period_start, period_end}`), `GET /api/v1/invoices`, `GET /api/v1/invoices/{id}`, `GET /api/v1/invoices/{id}/pdf` (returns `application/pdf` blob), `PATCH /api/v1/invoices/{id}` (body: `{status}`). **InvoiceResponse shape**: `{id, invoice_number, client_id, period_start, period_end, total_hours, total_amount, currency, status, created_at}` — must match `Invoice` TypeScript type from U6. **PDF download**: `GET /invoices/{id}/pdf` must set `Content-Disposition: attachment; filename="INV-{number}.pdf"` for correct browser download behavior. |
| U9 → U8 | U8 provides to U9 | **Routing and layout**: `/reports` and `/invoices` routes may be stubbed in U8's wave (both are Wave 4); U9 fills in the page content. **useClients hook**: `useInvoices` form uses the client list from `useClients` for the client selector dropdown — this hook is delivered in U8. **Shared patterns**: date pickers, status badge components, table patterns established in U8 are reused in U9. **React Query cache keys**: U9 uses `['invoices']` and `['reports']` as query keys, must not conflict with U8's `['clients']`, `['projects']`, `['sessions']` keys. |

---

## 5. Shared Infrastructure

All 9 units operate within a shared infrastructure layer. The following elements are established in **U1** and relied upon by every subsequent unit.

### Docker Network

All services communicate on the `chronotrack_default` Docker network:
- `db` (postgres:16) — internal port 5432
- `api` (FastAPI) — internal port 8000, external 8000
- `web` (React/Vite) — internal port 5173, external 5173
- `bot` (Telegram bot) — no external port; connects to `api` at `http://api:8000`

The bot calls the API using the internal Docker DNS name `api`, not `localhost`.

### PostgreSQL Database

- Single `chronotrack` database shared by all backend units
- All 5 tables created in the initial Alembic migration (U1)
- Migrations run via `alembic upgrade head` in the API container entrypoint
- Row-level isolation enforced at the service layer (every query filters by `user_id`)

### JWT Authentication

- Access token: 15-minute expiry, signed with `JWT_SECRET_KEY`
- Refresh token: 30-day expiry, signed with `JWT_REFRESH_SECRET_KEY`, rotation-on-use
- `get_current_user` dependency from U1 is used by every protected router in U2–U5
- Token shape: `{"sub": user_id, "exp": timestamp, "type": "access"|"refresh"}`
- The bot does not use JWT directly; it maps `telegram_chat_id` → user and generates API calls with that user's token

### CORS Configuration

- FastAPI `CORSMiddleware` configured in `main.py` (U1):
  - `allow_origins: ["http://localhost:5173", "http://web:5173"]`
  - `allow_credentials: True`
  - `allow_methods: ["*"]`
  - `allow_headers: ["*"]`
- Required for Axios calls from the React frontend

### TypeScript Types (Frontend Shared Contract)

- Single source of truth: `apps/web/src/types/api.ts` (created in U6)
- All frontend units (U6, U7, U8, U9) import types from this file
- Types mirror the FastAPI Pydantic schemas exactly
- Changes to API response shapes require updating both `apps/api/app/schemas/` and `apps/web/src/types/api.ts`

### React Query Client

- `QueryClientProvider` initialized in `apps/web/src/main.tsx` (U6)
- All hooks in U7, U8, U9 use `useQuery` and `useMutation` from `@tanstack/react-query`
- Query key namespaces: `['sessions']`, `['projects']`, `['clients']`, `['reports']`, `['invoices']`
- Default stale time: 30 seconds; cache time: 5 minutes

### Axios Client

- Single `apiClient` instance in `apps/web/src/services/apiClient.ts` (U6)
- Bearer token injected via request interceptor
- 401 auto-refresh via response interceptor
- All service modules (U7, U8, U9) import `apiClient` and make typed API calls through it

### Environment Variables

All services read from `.env` (based on `.env.example` from U1):

| Variable | Used By | Description |
|----------|---------|-------------|
| `DATABASE_URL` | API | PostgreSQL connection string |
| `JWT_SECRET_KEY` | API | Access token signing key |
| `JWT_REFRESH_SECRET_KEY` | API | Refresh token signing key |
| `JWT_ALGORITHM` | API | Default: `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | API | Default: 15 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | API | Default: 30 |
| `TELEGRAM_TOKEN` | Bot | Optional; bot exits gracefully if unset |
| `TELEGRAM_WEBHOOK_URL` | Bot, API | Optional; enables webhook mode |
| `VITE_API_URL` | Web | React API base URL, default `http://localhost:8000/api/v1` |

### CI/CD Pipeline

- `.github/workflows/ci.yml` (U1) runs on every PR to `develop`
- Jobs: `lint` (ruff + bandit, zero tolerance), `test` (pytest with coverage >= 80%)
- All units must pass this gate before merge
- Docker build is validated as part of the test job (`docker-compose -f docker-compose.test.yml up --build`)
