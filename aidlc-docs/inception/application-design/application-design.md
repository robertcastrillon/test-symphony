# ChronoTrack — Application Design

This document is the top-level design reference for the ChronoTrack project. It provides a system overview, references the detailed component and service documents, records key architectural decisions, maps work to delivery units, and states the security baseline requirements that shape the design.

---

## 1. System Overview

ChronoTrack is a time-tracking application built for independent freelancers. It allows users to track work sessions against client projects, generate reports, and produce invoices — from both a web browser and a Telegram bot.

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| Backend API | Python 3.12, FastAPI, SQLAlchemy async, Alembic, PostgreSQL 16, asyncpg |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query v5, recharts |
| Bot | python-telegram-bot v20 (async), httpx |
| PDF generation | WeasyPrint, Jinja2 |
| Authentication | JWT (PyJWT), bcrypt 4.0.1, access token 15 min, refresh token 30 days with rotation |
| Infrastructure | Docker Compose, GitHub Actions |

### ASCII Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│  External Clients                                                       │
│                                                                         │
│  ┌─────────────────┐          ┌──────────────────────────────────────┐ │
│  │  Browser (React │          │  Telegram App                        │ │
│  │  + Vite + TQ)   │          │  (user mobile / desktop)             │ │
│  └────────┬────────┘          └───────────────┬──────────────────────┘ │
│           │ HTTPS/HTTP                         │ Telegram Bot API       │
└───────────┼─────────────────────────────────── │ ──────────────────────┘
            │                                     │
            ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Docker Compose — network: chronotrack_net                               │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  api  (FastAPI + Uvicorn, :8000)                                 │    │
│  │                                                                   │    │
│  │  Routers: Auth · Client · Project · Session · Report             │    │
│  │           Invoice · Telegram · Health                            │    │
│  │                                                                   │    │
│  │  Services: AuthService · ClientService · ProjectService          │    │
│  │            SessionService · ReportService · InvoiceService       │    │
│  │            PDFService · TelegramService                          │    │
│  │                                                                   │    │
│  │  Core: Config · Security · Dependencies · ExceptionHandlers      │    │
│  │  ORM: User · Client · Project · Session · Invoice                │    │
│  └──────────────────────────┬───────────────────────────────────────┘    │
│                             │ asyncpg                                     │
│  ┌──────────────────────┐   │                  ┌───────────────────────┐ │
│  │  db  (PostgreSQL 16) │◄──┘                  │  bot                  │ │
│  │  :5432               │                      │  (python-telegram-bot │ │
│  └──────────────────────┘                      │   + httpx)            │ │
│                                                 │  calls api:8000       │ │
│  ┌──────────────────────┐                      └───────────────────────┘ │
│  │  web  (Vite, :5173)  │──────────────────────────► api:8000/api/v1     │
│  └──────────────────────┘  HTTP (VITE_API_URL)                           │
└──────────────────────────────────────────────────────────────────────────┘

CI/CD: GitHub Actions (lint → test → build → deploy)
```

---

## 2. Design Document References

The following four documents provide the detailed component and service specifications. This document consolidates and cross-references them.

### 2.1 components.md — Component Catalog

Lists every named component in the system: backend routers, services, ORM models, Pydantic schemas, core infrastructure modules, frontend pages, hooks, layout components, and bot handlers.

For each component it provides: layer, responsibility (2–3 sentences), and key interfaces (inputs, outputs, dependencies).

**Key sections:**
- Backend Routers (8 routers — Auth, Client, Project, Session, Report, Invoice, Telegram, Health)
- Backend Services (8 services — Auth, Client, Project, Session, Report, Invoice, PDF, Telegram)
- Data Models (5 SQLAlchemy ORM models)
- Pydantic Schemas (5 schema groups)
- Core Infrastructure (Database, Config, Security, Dependencies, ExceptionHandlers)
- Frontend Pages (8 pages), Layout (AppLayout, TimerComponent, BarChartComponent)
- Custom Hooks (6 hooks — useAuth, useSessions, useProjects, useClients, useReports, useInvoices)
- AuthContext + ApiClient
- Bot Components (BotApp, 6 command handlers, BotApiClient)

### 2.2 component-methods.md — Method Signatures

Lists the primary method signatures for every backend service with: full Python signature, return type, exceptions raised, and a description of behavior.

**Services covered:** AuthService, ClientService, ProjectService, SessionService, ReportService, InvoiceService, PDFService, TelegramService (8 services, ~30 total methods).

### 2.3 services.md — Service Layer Orchestration

Explains the runtime behavior and patterns that govern how components interact:

- Thin-router / fat-service pattern with annotated request flow examples
- Async SQLAlchemy session lifecycle via `get_db` dependency
- `PDFService` orchestration (synchronous WeasyPrint in a thread executor)
- `TelegramService` + `BotApiClient` HTTP-call pattern
- Custom exception hierarchy with full class tree
- FastAPI exception handler registration and mapping
- `get_current_user` dependency implementation
- Pagination pattern (`Page[T]` response shape, limit/offset implementation)
- JWT refresh-token rotation pattern (JTI tracking, single-use enforcement)

### 2.4 component-dependency.md — Component Dependencies

Maps structural dependencies between components:

- Backend, Frontend, and Bot dependency flow diagrams
- Cross-service dependency matrix (which services read which models)
- Router → Service mapping table
- Frontend Hook → API endpoint mapping table
- Bot Handler → TelegramService → API endpoint mapping table
- Docker network topology diagram
- Service communication rules (protocols, internal addresses)
- Environment variable summary per Docker service

---

## 3. Key Architectural Decisions

### 3.1 Layered Backend Architecture

Routers handle HTTP concerns only (request parsing, response serialization, dependency injection). All business rules live in service classes. This makes services independently testable without the HTTP stack, and keeps routers below ~20 lines per endpoint.

### 3.2 Async SQLAlchemy with Dependency Injection

SQLAlchemy async sessions are managed by the `get_db` FastAPI dependency. One session per request, committed on success and rolled back on any exception. Services receive the session as a function parameter and never import database state directly. Lazy loading is disabled; relationships are loaded explicitly with `selectinload`.

### 3.3 Custom Exception Hierarchy with FastAPI Exception Handlers

All domain errors are typed subclasses of `ChronoTrackError`. A set of FastAPI exception handlers registered at application startup converts each exception type to the correct HTTP status code and a consistent `{"detail": "..."}` JSON body. Routers never contain try/except blocks; the handler layer is the single point of error-to-HTTP translation.

### 3.4 React Query for All Frontend Server State

All data that originates from the API is managed exclusively by TanStack Query (`useQuery` and `useMutation`). Components do not hold server state in `useState`. This provides automatic caching, background refetching, optimistic updates, and consistent loading/error states without manual orchestration.

### 3.5 Bot Communicates with API via HTTP

The Telegram bot is a separate Docker service with no shared Python modules with the API. All bot commands that require data access call FastAPI endpoints over the internal Docker network (`http://api:8000`). This means the bot respects the same authentication, validation, and business rules as any other API client, and the API surface is the only integration point.

### 3.6 WeasyPrint for PDF Generation

PDF invoices are generated server-side using WeasyPrint. The invoice HTML is templated with Jinja2 and rendered to PDF bytes by WeasyPrint in a thread executor (to avoid blocking the async event loop). The bytes are returned to the router and streamed as `application/pdf`.

### 3.7 JWT with 15-Minute Access Tokens and 30-Day Rotating Refresh Tokens

Access tokens are short-lived (15 minutes) to limit exposure if intercepted. Refresh tokens are long-lived (30 days) but single-use: each call to `/auth/refresh` invalidates the presented token (by JTI) and issues a new pair. The Axios response interceptor handles transparent token refresh for the web client.

---

## 4. Units of Work

The following 9 units of work are defined for the ChronoTrack project. Each unit is independently deliverable and represents a coherent vertical slice of functionality.

| # | Unit | Delivers |
|---|------|---------|
| 1 | **Project Scaffolding and Infrastructure** | Docker Compose setup (db, api, web, bot services), GitHub Actions CI pipeline, Alembic migration baseline, environment variable structure, project directory layout. |
| 2 | **Authentication** | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` endpoints; `UserModel`; JWT issuance with refresh rotation; `get_current_user` dependency; `LoginPage` and `RegisterPage` in the frontend; `useAuth` hook and `AuthContext`. |
| 3 | **Client and Project Management** | Full CRUD for clients and projects; `ClientModel`, `ProjectModel`; `ClientService` deletion guard; `ProjectService` deactivate; `ClientsPage`, `ProjectsPage`; `useClients`, `useProjects` hooks. |
| 4 | **Session Tracking** | Timer start/stop endpoints; manual session entry; `SessionModel`; `SessionService` with active-session guard; `SessionsPage` with paginated list and manual entry form; `TimerComponent`; `useSessions` hook; `GET /sessions/active`. |
| 5 | **Dashboard** | `DashboardPage` with live timer, today's session list, and weekly bar chart; `BarChartComponent`; `GET /health` endpoint. |
| 6 | **Reports** | `GET /reports/summary` with period/date-range support; `ReportService` aggregation; `ReportsPage` with period selector, bar chart, and summary table; `useReports` hook. |
| 7 | **Invoices and PDF** | `POST /invoices`, `GET /invoices`, `GET /invoices/{id}`, `PATCH /invoices/{id}`; `GET /invoices/{id}/pdf` PDF streaming; `InvoiceModel`; sequential invoice numbering; `PDFService` with WeasyPrint; `InvoicesPage`; `useInvoices` hook. |
| 8 | **Telegram Bot** | `python-telegram-bot` v20 setup; `/start`, `/link`, `/log`, `/status`, `/report`, `/stop` command handlers; `BotApiClient`; `TelegramService`; `POST /telegram/webhook` API endpoint. |
| 9 | **Hardening and Observability** | Rate limiting on auth endpoints; structured logging; Alembic migration for all models; input validation edge case coverage; README and deployment documentation. |

---

## 5. Security Baseline Requirements

The following security requirements are non-negotiable and directly influence component design.

| Requirement | Implementation |
|-------------|---------------|
| No hardcoded secrets | All secrets (`JWT_SECRET`, `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, etc.) are read from environment variables via `pydantic-settings` (`Config`). The `.env` file is in `.gitignore` and never committed. |
| bcrypt password hashing | `bcrypt==4.0.1` is pinned. `Security.hash_password` uses `bcrypt.hashpw` with a generated salt. `Security.verify_password` uses `bcrypt.checkpw`. The plain-text password never leaves `AuthService`. |
| Input validation — backend | All API input is validated by Pydantic v2 schemas before reaching service code. FastAPI's automatic 422 response handles schema violations. Services apply additional domain-level validation (e.g., `ended_at > started_at`). |
| Input validation — frontend | All form inputs are validated client-side with Zod schemas before submission, matching the backend Pydantic schema constraints. |
| Short-lived access tokens | Access tokens expire in 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES=15`). The Axios interceptor silently refreshes them, so users are not logged out unless the refresh token also expires or is rotated away. |
| Refresh token rotation | Single-use refresh tokens with JTI tracking prevent replay attacks. A stolen refresh token becomes invalid after first use. |
| Rate limiting on auth endpoints | `POST /auth/register`, `POST /auth/login`, and `POST /auth/refresh` are rate-limited (implementation via `slowapi` or equivalent). This mitigates brute-force and credential-stuffing attacks. |
| Row-level data scoping | Every service method accepts `user_id` and adds it as a `WHERE` clause condition. A user can never access or mutate another user's data, regardless of ID guessing. |
| Telegram link verification | The `/link` command verifies the email exists in the database before storing `telegram_chat_id`. No unauthenticated Telegram command can modify user data; all mutations require the linked user's resolved JWT. |
