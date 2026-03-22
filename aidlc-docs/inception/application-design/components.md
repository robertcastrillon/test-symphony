# ChronoTrack — Component Catalog

This document describes every named component in the ChronoTrack system: its layer, responsibility, and key interfaces. Components are grouped by subsystem: Backend, Frontend, and Bot.

---

## Backend Components

### Routers

| Name | Layer | Responsibility | Key Interfaces |
|------|-------|----------------|----------------|
| `AuthRouter` | API / Router | Handles `/auth/register`, `/auth/login`, and `/auth/refresh` endpoints. Validates incoming request bodies via Pydantic schemas and delegates entirely to `AuthService`. Returns `TokenPair` or raises HTTP 401/422. | Input: `RegisterRequest`, `LoginRequest`, `RefreshRequest`; Output: `TokenPairResponse`; Depends on: `AuthService` |
| `ClientRouter` | API / Router | Handles all `/clients` CRUD endpoints. Extracts the authenticated user from the `current_user` dependency and forwards operations to `ClientService`. Returns client representations or 404/409 on errors. | Input: `ClientCreate`, `ClientUpdate`; Output: `ClientResponse`; Depends on: `ClientService`, `Dependencies.current_user` |
| `ProjectRouter` | API / Router | Handles all `/projects` CRUD endpoints plus active/inactive toggling. Passes the authenticated user and path parameters to `ProjectService`. | Input: `ProjectCreate`, `ProjectUpdate`; Output: `ProjectResponse`; Depends on: `ProjectService`, `Dependencies.current_user` |
| `SessionRouter` | API / Router | Handles `/sessions` CRUD and the `/sessions/start` and `/sessions/stop` action endpoints. Delegates timer logic and manual-entry creation to `SessionService`. Supports query-parameter-based filtering and pagination. | Input: `SessionCreate`, `SessionUpdate`, `SessionFilters`; Output: `SessionResponse`, `Page[SessionResponse]`; Depends on: `SessionService`, `Dependencies.current_user` |
| `ReportRouter` | API / Router | Handles `GET /reports/summary`. Accepts `period`, `date_from`, and `date_to` query parameters and returns an aggregated report from `ReportService`. | Input: query params (`period`, `date_from`, `date_to`); Output: `ReportSummaryResponse`; Depends on: `ReportService`, `Dependencies.current_user` |
| `InvoiceRouter` | API / Router | Handles invoice CRUD (`POST`, `GET`, `GET /{id}`, `PATCH /{id}`) and the `GET /{id}/pdf` binary download endpoint. Streams PDF bytes as `application/pdf` responses. | Input: `InvoiceCreate`, `InvoiceStatusUpdate`; Output: `InvoiceResponse`, `StreamingResponse`; Depends on: `InvoiceService`, `Dependencies.current_user` |
| `TelegramRouter` | API / Router | Handles `POST /telegram/webhook`. Receives raw Telegram update JSON and passes it to `TelegramService` for command dispatch. Returns HTTP 200 immediately to satisfy Telegram's webhook contract. | Input: raw Telegram `Update` JSON; Output: HTTP 200; Depends on: `TelegramService` |
| `HealthRouter` | API / Router | Handles `GET /health`. Returns a static JSON payload indicating service liveness. Requires no authentication and no service calls. | Input: none; Output: `{"status": "ok"}`; Depends on: none |

---

### Services

#### AuthService

**Layer:** Business Logic

**Responsibility:** Manages user registration, credential verification, and JWT token lifecycle. Hashes passwords with bcrypt and issues access/refresh token pairs. Implements refresh-token rotation so that each refresh call invalidates the old token and issues a new one.

**Key Interfaces:**

| Method | Inputs | Output | Notes |
|--------|--------|--------|-------|
| `register` | `email`, `name`, `password` | `TokenPair` | Raises `EmailAlreadyExistsError` |
| `login` | `email`, `password` | `TokenPair` | Raises `InvalidCredentialsError` |
| `refresh_token` | `refresh_token: str` | `TokenPair` | Raises `InvalidTokenError`; rotates token |
| `get_current_user` | `token: str` | `User` | Raises `InvalidTokenError` |

Depends on: `UserModel`, `Security`, `Database`

---

#### ClientService

**Layer:** Business Logic

**Responsibility:** Manages client CRUD operations scoped to the authenticated user. Enforces the constraint that a client cannot be deleted while it has active projects, raising `ClientHasActiveProjectsError` in that case. Validates uniqueness of client names per user.

**Key Interfaces:**

| Method | Inputs | Output | Notes |
|--------|--------|--------|-------|
| `create` | `user_id`, `data: ClientCreate` | `Client` | |
| `list` | `user_id` | `list[Client]` | |
| `get` | `user_id`, `client_id` | `Client` | Raises `NotFoundError` |
| `update` | `user_id`, `client_id`, `data: ClientUpdate` | `Client` | Raises `NotFoundError` |
| `delete` | `user_id`, `client_id` | `None` | Raises `ClientHasActiveProjectsError` |

Depends on: `ClientModel`, `ProjectModel`, `Database`

---

#### ProjectService

**Layer:** Business Logic

**Responsibility:** Manages project CRUD scoped to the authenticated user and optionally filtered by client. Supports toggling a project's active/inactive state via `deactivate`. Prevents session creation on inactive projects (raises `InactiveProjectError`).

**Key Interfaces:**

| Method | Inputs | Output | Notes |
|--------|--------|--------|-------|
| `create` | `user_id`, `data: ProjectCreate` | `Project` | |
| `list` | `user_id`, `client_id=None`, `is_active=None` | `list[Project]` | |
| `get` | `user_id`, `project_id` | `Project` | Raises `NotFoundError` |
| `update` | `user_id`, `project_id`, `data: ProjectUpdate` | `Project` | Raises `NotFoundError` |
| `deactivate` | `user_id`, `project_id` | `Project` | Sets `is_active=False` |

Depends on: `ProjectModel`, `ClientModel`, `Database`

---

#### SessionService

**Layer:** Business Logic

**Responsibility:** Manages the full session lifecycle: starting and stopping the live timer, creating manual entries, and listing/filtering sessions with pagination. Ensures at most one active session exists per user at any time, raising `ActiveSessionExistsError` on conflicting starts.

**Key Interfaces:**

| Method | Inputs | Output | Notes |
|--------|--------|--------|-------|
| `start_timer` | `user_id`, `project_id`, `description=None` | `Session` | Raises `ActiveSessionExistsError`, `InactiveProjectError` |
| `stop_timer` | `user_id` | `Session` | Raises `NoActiveSessionError` |
| `create_manual` | `user_id`, `data: SessionCreate` | `Session` | |
| `list` | `user_id`, `filters: SessionFilters`, `page`, `size` | `Page[Session]` | |
| `update` | `user_id`, `session_id`, `data: SessionUpdate` | `Session` | Raises `NotFoundError` |
| `delete` | `user_id`, `session_id` | `None` | Raises `NotFoundError` |
| `get_active` | `user_id` | `Session \| None` | Returns `None` if no active session |

Depends on: `SessionModel`, `ProjectModel`, `Database`

---

#### ReportService

**Layer:** Business Logic

**Responsibility:** Aggregates session data for a given user across a requested period (week, month, custom range). Computes total hours grouped by project, client, and day. Returns a structured `ReportSummary` object consumed by both the REST API and the Telegram `/report` command.

**Key Interfaces:**

| Method | Inputs | Output | Notes |
|--------|--------|--------|-------|
| `get_summary` | `user_id`, `period: str`, `date_from=None`, `date_to=None` | `ReportSummary` | `period` values: `week`, `month`, `custom` |

Depends on: `SessionModel`, `ProjectModel`, `ClientModel`, `Database`

---

#### InvoiceService

**Layer:** Business Logic

**Responsibility:** Handles invoice creation with sequential numbering (format `INV-{YEAR}-{SEQ}`), status transitions (`draft` → `sent` → `paid`), and PDF generation. Delegates HTML-to-PDF rendering to `PDFService`. Ensures invoices are scoped to the requesting user.

**Key Interfaces:**

| Method | Inputs | Output | Notes |
|--------|--------|--------|-------|
| `create` | `user_id`, `data: InvoiceCreate` | `Invoice` | Calls `get_next_invoice_number` |
| `list` | `user_id` | `list[Invoice]` | |
| `get` | `user_id`, `invoice_id` | `Invoice` | Raises `NotFoundError` |
| `update_status` | `user_id`, `invoice_id`, `status: str` | `Invoice` | Raises `InvalidStatusTransitionError` |
| `generate_pdf` | `user_id`, `invoice_id` | `bytes` | Delegates to `PDFService.render_invoice` |
| `get_next_invoice_number` | `user_id`, `year: int` | `str` | Returns e.g. `INV-2026-0042` |

Depends on: `InvoiceModel`, `SessionModel`, `ClientModel`, `PDFService`, `Database`

---

#### PDFService

**Layer:** Infrastructure / Rendering

**Responsibility:** Converts a populated invoice context (invoice record, associated sessions, and client data) into a PDF binary using WeasyPrint. Renders an HTML template with Jinja2 before passing it to WeasyPrint. Has no database dependency; operates purely on passed-in data objects.

**Key Interfaces:**

| Method | Inputs | Output |
|--------|--------|--------|
| `render_invoice` | `invoice: Invoice`, `sessions: list[Session]`, `client: Client` | `bytes` |

Depends on: `WeasyPrint`, `Jinja2` (template rendering)

---

#### TelegramService

**Layer:** Bot / Integration

**Responsibility:** Parses Telegram command payloads and executes corresponding actions by calling FastAPI HTTP endpoints through `BotApiClient`. Handles user linking (mapping `telegram_chat_id` to a ChronoTrack user account), session logging, status queries, and report retrieval. All state mutations go through the API; this service contains no direct database access.

**Key Interfaces:**

| Method | Inputs | Output |
|--------|--------|--------|
| `handle_start` | `chat_id` | `str` (reply message) |
| `handle_link` | `chat_id`, `email: str` | `str` |
| `handle_log` | `chat_id`, `hours: float`, `project: str`, `description: str` | `str` |
| `handle_status` | `chat_id` | `str` |
| `handle_report` | `chat_id` | `str` |
| `handle_stop` | `chat_id` | `str` |

Depends on: `BotApiClient`

---

### Data Models (SQLAlchemy ORM)

| Name | Layer | Responsibility | Key Fields |
|------|-------|----------------|------------|
| `UserModel` | Data / ORM | Persists user accounts. Stores hashed passwords and the optional `telegram_chat_id` link. | `id`, `email`, `name`, `hashed_password`, `telegram_chat_id`, `created_at` |
| `ClientModel` | Data / ORM | Persists client records scoped to a user. Has a one-to-many relationship with `ProjectModel`. | `id`, `user_id`, `name`, `email`, `created_at` |
| `ProjectModel` | Data / ORM | Persists project records linked to a client and user. Carries an `is_active` flag. | `id`, `user_id`, `client_id`, `name`, `hourly_rate`, `is_active`, `created_at` |
| `SessionModel` | Data / ORM | Persists work sessions. A session with `ended_at=NULL` is the live (active) timer. Duration is computed from `started_at` and `ended_at`. | `id`, `user_id`, `project_id`, `description`, `started_at`, `ended_at`, `duration_seconds` |
| `InvoiceModel` | Data / ORM | Persists invoices with sequential numbers, line-item JSON, and a status field. | `id`, `user_id`, `client_id`, `invoice_number`, `status`, `line_items`, `total_amount`, `issued_at`, `due_at` |

---

### Pydantic Schemas

| Name | Layer | Responsibility |
|------|-------|----------------|
| `AuthSchemas` | API / Validation | `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `TokenPairResponse`. Enforces email format and minimum password length. |
| `ClientSchemas` | API / Validation | `ClientCreate`, `ClientUpdate`, `ClientResponse`. Validates non-empty name and optional contact email. |
| `ProjectSchemas` | API / Validation | `ProjectCreate`, `ProjectUpdate`, `ProjectResponse`. Validates positive `hourly_rate`. |
| `SessionSchemas` | API / Validation | `SessionCreate`, `SessionUpdate`, `SessionResponse`, `SessionFilters`. Validates that `ended_at > started_at` on manual entries. |
| `InvoiceSchemas` | API / Validation | `InvoiceCreate`, `InvoiceStatusUpdate`, `InvoiceResponse`. Validates status transition values. |

---

### Infrastructure / Core

| Name | Layer | Responsibility | Key Interfaces |
|------|-------|----------------|----------------|
| `Database` | Core / DB | Creates the async SQLAlchemy engine and session factory. Exposes `Base` for model inheritance and `get_db` async generator. | `engine`, `AsyncSessionLocal`, `Base`, `async get_db()` |
| `Config` | Core / Config | Reads all environment variables via `pydantic-settings`. Single source of truth for database URL, JWT secrets, token TTLs, and Telegram token. | `DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `TELEGRAM_BOT_TOKEN` |
| `Security` | Core / Auth | Wraps PyJWT and bcrypt. Provides stateless JWT encode/decode and password hash/verify utilities. | `create_access_token(data, expires_delta)`, `create_refresh_token(data)`, `decode_token(token)`, `hash_password(plain)`, `verify_password(plain, hashed)` |
| `Dependencies` | Core / DI | FastAPI dependency functions injected into routers. `get_db` yields an async database session; `get_current_user` extracts and validates the bearer token, returning the active `User`. | `async get_db() -> AsyncSession`, `async get_current_user(token, db) -> User` |
| `ExceptionHandlers` | Core / Error | Registers FastAPI exception handlers that map each custom `ChronoTrackError` subclass to the appropriate HTTP status code and JSON error body. | Registered on the `FastAPI` app instance; maps `NotFoundError→404`, `ActiveSessionExistsError→409`, `ClientHasActiveProjectsError→409`, `InvalidTokenError→401`, `InactiveProjectError→403` |

---

## Frontend Components

### Pages

| Name | Responsibility | Key Interfaces |
|------|----------------|----------------|
| `LoginPage` | Renders email/password login form. Submits via `useAuth().login` mutation. Redirects to `/dashboard` on success. | Uses: `useAuth`; Route: `/login` |
| `RegisterPage` | Renders registration form with name, email, and password fields. Validates via Zod schema before submitting. | Uses: `useAuth`; Route: `/register` |
| `DashboardPage` | Displays the live `TimerComponent`, a `BarChartComponent` of the current week's hours, and today's session list. Polls for the active session. | Uses: `useSessions`, `useReports`; Route: `/dashboard` |
| `ProjectsPage` | Renders a table of projects with inline create, edit, and deactivate actions. | Uses: `useProjects`; Route: `/projects` |
| `ClientsPage` | Renders a table of clients with inline create and edit actions. Confirms deletion when active projects exist. | Uses: `useClients`; Route: `/clients` |
| `SessionsPage` | Renders a paginated session list and a manual-entry form. Supports date-range filtering. | Uses: `useSessions`; Route: `/sessions` |
| `ReportsPage` | Renders a period selector, a `BarChartComponent` of hours per day, and a summary table broken down by project. | Uses: `useReports`; Route: `/reports` |
| `InvoicesPage` | Renders invoice generation form, invoice list with status badges, and PDF download buttons. | Uses: `useInvoices`; Route: `/invoices` |

---

### Layout and Shared Components

| Name | Responsibility | Key Interfaces |
|------|----------------|----------------|
| `AppLayout` | Wraps all authenticated pages. Renders the sidebar navigation links and an active-session status indicator in the header. | Uses: `useSessions` (active session); wraps all route children |
| `TimerComponent` | Displays elapsed time for the active session with 1-second interval updates. Renders start and stop buttons. Calls `useSessions().startTimer` and `stopTimer`. | Props: none (reads from `useSessions`); emits: start/stop actions |
| `BarChartComponent` | A thin recharts wrapper that renders a `BarChart` of hours-per-day data. Accepts a generic data array and axis labels. | Props: `data: {date: string, hours: number}[]`, `xLabel`, `yLabel` |

---

### Custom Hooks

| Name | Responsibility | Key React Query Operations |
|------|----------------|---------------------------|
| `useAuth` | Manages login, registration, and logout mutations. Reads/writes the JWT state from `AuthContext`. | `useMutation` for login, register, logout |
| `useSessions` | Fetches paginated sessions, the active session, and exposes start/stop/create/update/delete mutations. | `useQuery` for list + active; `useMutation` for CRUD + start/stop |
| `useProjects` | Fetches project list with optional filters and exposes create/update/deactivate mutations. | `useQuery` for list; `useMutation` for CRUD |
| `useClients` | Fetches client list and exposes create/update/delete mutations. | `useQuery` for list; `useMutation` for CRUD |
| `useReports` | Fetches report summary for a given period and date range. | `useQuery` keyed by period + dates |
| `useInvoices` | Fetches invoice list and single invoice, and exposes create/update-status/download-pdf mutations. | `useQuery` for list + single; `useMutation` for create, status update, PDF download |

---

### Context and API Infrastructure

| Name | Responsibility | Key Interfaces |
|------|----------------|----------------|
| `AuthContext` | React context that stores the decoded JWT payload and raw tokens. Provides `setTokens`, `clearTokens`, and `isAuthenticated`. Consumed by all custom hooks and the `ApiClient` interceptor. | `AuthContextValue`: `{ user, accessToken, isAuthenticated, setTokens, clearTokens }` |
| `ApiClient` | Axios instance preconfigured with `baseURL` pointing to the FastAPI backend. Attaches the bearer token from `AuthContext` on every request via a request interceptor. A response interceptor catches HTTP 401 errors, calls `/auth/refresh`, updates the stored tokens, and retries the original request once. | `apiClient.get/post/patch/delete`; interceptors handle auth transparently |

---

## Bot Components

| Name | Layer | Responsibility | Key Interfaces |
|------|-------|----------------|----------------|
| `BotApp` | Bot / Setup | Instantiates the `python-telegram-bot` `Application` with the bot token from config. Registers all command handlers and calls the Telegram API to set the webhook URL pointing to the FastAPI `/telegram/webhook` endpoint. | `Application.builder()`, `app.add_handler()`, `app.bot.set_webhook()` |
| `StartHandler` | Bot / Command | Handles the `/start` command. Calls `TelegramService.handle_start` and replies with a welcome message explaining available commands. | `CommandHandler("start", callback)` |
| `LinkHandler` | Bot / Command | Handles the `/link <email>` command. Passes the email argument to `TelegramService.handle_link`, which calls the API to associate the Telegram `chat_id` with the matching user account. | `CommandHandler("link", callback)`; expects one argument: email |
| `LogHandler` | Bot / Command | Handles the `/log <hours> <project> <description>` command. Parses arguments and calls `TelegramService.handle_log` to create a manual session entry via the API. | `CommandHandler("log", callback)`; expects three arguments |
| `StatusHandler` | Bot / Command | Handles the `/status` command. Returns the user's current active session information (project, elapsed time) via `TelegramService.handle_status`. | `CommandHandler("status", callback)` |
| `ReportHandler` | Bot / Command | Handles the `/report` command. Returns a text summary of the current week's tracked hours per project via `TelegramService.handle_report`. | `CommandHandler("report", callback)` |
| `StopHandler` | Bot / Command | Handles the `/stop` command. Calls `TelegramService.handle_stop` to stop the active timer session via the API. | `CommandHandler("stop", callback)` |
| `BotApiClient` | Bot / HTTP | An async `httpx.AsyncClient` configured with `base_url=http://api:8000/api/v1`. Holds the resolved JWT token for the linked user and attaches it as a bearer header. Used exclusively by `TelegramService` to call FastAPI endpoints. | `async get(path, **kwargs)`, `async post(path, json, **kwargs)` |
