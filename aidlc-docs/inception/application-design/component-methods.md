# ChronoTrack — Component Method Signatures

This document lists the primary method signatures for every backend service. Each entry includes the full signature, return type, exceptions raised, and a brief description of what the method does.

---

## AuthService

Located at `app/services/auth_service.py`.

### `register`

```python
async def register(
    email: str,
    name: str,
    password: str,
    db: AsyncSession,
) -> TokenPair
```

| Property | Value |
|----------|-------|
| Returns | `TokenPair` — access token + refresh token |
| Raises | `EmailAlreadyExistsError` if the email is already registered |
| Description | Hashes the password with bcrypt, persists a new `UserModel`, and returns a freshly issued token pair. |

---

### `login`

```python
async def login(
    email: str,
    password: str,
    db: AsyncSession,
) -> TokenPair
```

| Property | Value |
|----------|-------|
| Returns | `TokenPair` |
| Raises | `InvalidCredentialsError` if the email is not found or the password does not match |
| Description | Looks up the user by email, verifies the bcrypt hash, and issues a new access + refresh token pair. |

---

### `refresh_token`

```python
async def refresh_token(
    refresh_token: str,
    db: AsyncSession,
) -> TokenPair
```

| Property | Value |
|----------|-------|
| Returns | `TokenPair` — new access token + new refresh token |
| Raises | `InvalidTokenError` if the token is expired, malformed, or has already been rotated |
| Description | Decodes the refresh token, verifies the subject user still exists, invalidates the old refresh token (rotation), and returns a new token pair. |

---

### `get_current_user`

```python
async def get_current_user(
    token: str,
    db: AsyncSession,
) -> User
```

| Property | Value |
|----------|-------|
| Returns | `User` ORM instance |
| Raises | `InvalidTokenError` if the JWT is invalid or expired; `NotFoundError` if the user no longer exists |
| Description | Decodes the access JWT, extracts the `sub` (user ID), and loads the corresponding `UserModel` from the database. Used internally by the `get_current_user` FastAPI dependency. |

---

## ClientService

Located at `app/services/client_service.py`.

### `create`

```python
async def create(
    user_id: int,
    data: ClientCreate,
    db: AsyncSession,
) -> Client
```

| Property | Value |
|----------|-------|
| Returns | Newly created `Client` ORM instance |
| Raises | — |
| Description | Persists a new client record associated with the given user. |

---

### `list`

```python
async def list(
    user_id: int,
    db: AsyncSession,
) -> list[Client]
```

| Property | Value |
|----------|-------|
| Returns | All `Client` records owned by the user, ordered by name |
| Raises | — |
| Description | Returns all clients for the user with no pagination (client count is typically small). |

---

### `get`

```python
async def get(
    user_id: int,
    client_id: int,
    db: AsyncSession,
) -> Client
```

| Property | Value |
|----------|-------|
| Returns | `Client` ORM instance |
| Raises | `NotFoundError` if no matching client exists for this user |
| Description | Fetches a single client by ID, scoped to the authenticated user. |

---

### `update`

```python
async def update(
    user_id: int,
    client_id: int,
    data: ClientUpdate,
    db: AsyncSession,
) -> Client
```

| Property | Value |
|----------|-------|
| Returns | Updated `Client` ORM instance |
| Raises | `NotFoundError` if no matching client exists for this user |
| Description | Applies the fields provided in `ClientUpdate` (partial update semantics) to the existing client record. |

---

### `delete`

```python
async def delete(
    user_id: int,
    client_id: int,
    db: AsyncSession,
) -> None
```

| Property | Value |
|----------|-------|
| Returns | `None` |
| Raises | `NotFoundError` if the client does not exist; `ClientHasActiveProjectsError` if any projects linked to this client have `is_active=True` |
| Description | Permanently deletes the client record after confirming no active projects exist. |

---

## ProjectService

Located at `app/services/project_service.py`.

### `create`

```python
async def create(
    user_id: int,
    data: ProjectCreate,
    db: AsyncSession,
) -> Project
```

| Property | Value |
|----------|-------|
| Returns | Newly created `Project` ORM instance |
| Raises | `NotFoundError` if the referenced `client_id` does not belong to the user |
| Description | Persists a new project linked to the given client and user. Defaults `is_active=True`. |

---

### `list`

```python
async def list(
    user_id: int,
    client_id: int | None = None,
    is_active: bool | None = None,
    db: AsyncSession,
) -> list[Project]
```

| Property | Value |
|----------|-------|
| Returns | Filtered list of `Project` ORM instances |
| Raises | — |
| Description | Returns projects for the user, with optional filtering by client and/or active status. |

---

### `get`

```python
async def get(
    user_id: int,
    project_id: int,
    db: AsyncSession,
) -> Project
```

| Property | Value |
|----------|-------|
| Returns | `Project` ORM instance |
| Raises | `NotFoundError` if no matching project exists for this user |
| Description | Fetches a single project by ID scoped to the authenticated user. |

---

### `update`

```python
async def update(
    user_id: int,
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession,
) -> Project
```

| Property | Value |
|----------|-------|
| Returns | Updated `Project` ORM instance |
| Raises | `NotFoundError` if no matching project exists |
| Description | Applies partial field updates to the project. Does not change `is_active`; use `deactivate` for that. |

---

### `deactivate`

```python
async def deactivate(
    user_id: int,
    project_id: int,
    db: AsyncSession,
) -> Project
```

| Property | Value |
|----------|-------|
| Returns | Updated `Project` ORM instance with `is_active=False` |
| Raises | `NotFoundError` if no matching project exists |
| Description | Sets `is_active=False` on the project. Active sessions belonging to this project are not affected, but new sessions cannot be started on it. |

---

## SessionService

Located at `app/services/session_service.py`.

### `start_timer`

```python
async def start_timer(
    user_id: int,
    project_id: int,
    description: str | None = None,
    db: AsyncSession,
) -> Session
```

| Property | Value |
|----------|-------|
| Returns | Newly created `Session` ORM instance with `ended_at=None` |
| Raises | `ActiveSessionExistsError` if the user already has an open session; `NotFoundError` if the project does not belong to the user; `InactiveProjectError` if the project has `is_active=False` |
| Description | Creates a new session record with `started_at=utcnow()` and no end time, representing the live running timer. |

---

### `stop_timer`

```python
async def stop_timer(
    user_id: int,
    db: AsyncSession,
) -> Session
```

| Property | Value |
|----------|-------|
| Returns | Completed `Session` ORM instance with `ended_at` and `duration_seconds` populated |
| Raises | `NoActiveSessionError` if the user has no open session |
| Description | Finds the open session (where `ended_at IS NULL`), sets `ended_at=utcnow()`, computes `duration_seconds`, and persists the result. |

---

### `create_manual`

```python
async def create_manual(
    user_id: int,
    data: SessionCreate,
    db: AsyncSession,
) -> Session
```

| Property | Value |
|----------|-------|
| Returns | Newly created `Session` ORM instance |
| Raises | `NotFoundError` if the project does not belong to the user; `InactiveProjectError` if the project is inactive; `ValidationError` if `ended_at <= started_at` |
| Description | Creates a completed session entry with explicit start and end times supplied by the user. Computes and stores `duration_seconds`. |

---

### `list`

```python
async def list(
    user_id: int,
    filters: SessionFilters,
    page: int,
    size: int,
    db: AsyncSession,
) -> Page[Session]
```

| Property | Value |
|----------|-------|
| Returns | `Page[Session]` containing items, total count, current page, and page size |
| Raises | — |
| Description | Returns a paginated, filtered list of sessions. `SessionFilters` may include `project_id`, `client_id`, `date_from`, and `date_to`. |

---

### `update`

```python
async def update(
    user_id: int,
    session_id: int,
    data: SessionUpdate,
    db: AsyncSession,
) -> Session
```

| Property | Value |
|----------|-------|
| Returns | Updated `Session` ORM instance |
| Raises | `NotFoundError` if the session does not belong to the user |
| Description | Applies partial field updates (description, start/end times) to a completed session. Recalculates `duration_seconds` if times change. |

---

### `delete`

```python
async def delete(
    user_id: int,
    session_id: int,
    db: AsyncSession,
) -> None
```

| Property | Value |
|----------|-------|
| Returns | `None` |
| Raises | `NotFoundError` if the session does not belong to the user |
| Description | Permanently deletes the session record. |

---

### `get_active`

```python
async def get_active(
    user_id: int,
    db: AsyncSession,
) -> Session | None
```

| Property | Value |
|----------|-------|
| Returns | The open `Session` instance, or `None` if no active session exists |
| Raises | — |
| Description | Queries for a session with `ended_at IS NULL` for the given user. Used by the `TimerComponent` polling and the Telegram `/status` handler. |

---

## ReportService

Located at `app/services/report_service.py`.

### `get_summary`

```python
async def get_summary(
    user_id: int,
    period: str,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession,
) -> ReportSummary
```

| Property | Value |
|----------|-------|
| Returns | `ReportSummary` containing `total_hours`, `by_project: list[ProjectSummary]`, `by_client: list[ClientSummary]`, `by_day: list[DaySummary]` |
| Raises | `ValidationError` if `period="custom"` and either `date_from` or `date_to` is missing |
| Description | Aggregates all completed sessions within the resolved date range. `period` values are `week` (current ISO week), `month` (current calendar month), or `custom` (uses explicit `date_from`/`date_to`). Returns zero-value entries for days with no tracked time to simplify chart rendering. |

---

## InvoiceService

Located at `app/services/invoice_service.py`.

### `create`

```python
async def create(
    user_id: int,
    data: InvoiceCreate,
    db: AsyncSession,
) -> Invoice
```

| Property | Value |
|----------|-------|
| Returns | Newly created `Invoice` ORM instance |
| Raises | `NotFoundError` if the referenced client does not belong to the user |
| Description | Generates the next sequential invoice number for the current year, persists the invoice with status `draft`, and stores the provided line items as JSON. |

---

### `list`

```python
async def list(
    user_id: int,
    db: AsyncSession,
) -> list[Invoice]
```

| Property | Value |
|----------|-------|
| Returns | All `Invoice` records for the user, ordered by `issued_at` descending |
| Raises | — |
| Description | Returns the full invoice list for the user. Pagination is not required given typical invoice volumes for freelancers. |

---

### `get`

```python
async def get(
    user_id: int,
    invoice_id: int,
    db: AsyncSession,
) -> Invoice
```

| Property | Value |
|----------|-------|
| Returns | `Invoice` ORM instance |
| Raises | `NotFoundError` if the invoice does not belong to the user |
| Description | Fetches a single invoice by ID scoped to the authenticated user. |

---

### `update_status`

```python
async def update_status(
    user_id: int,
    invoice_id: int,
    status: str,
    db: AsyncSession,
) -> Invoice
```

| Property | Value |
|----------|-------|
| Returns | Updated `Invoice` ORM instance |
| Raises | `NotFoundError` if the invoice does not belong to the user; `InvalidStatusTransitionError` if the requested transition is not allowed (e.g. `paid` → `draft`) |
| Description | Updates the invoice status following the allowed transition graph: `draft → sent → paid`. Stores the updated value. |

---

### `generate_pdf`

```python
async def generate_pdf(
    user_id: int,
    invoice_id: int,
    db: AsyncSession,
) -> bytes
```

| Property | Value |
|----------|-------|
| Returns | Raw PDF bytes |
| Raises | `NotFoundError` if the invoice does not belong to the user |
| Description | Loads the invoice, its associated sessions (line items), and the client. Passes these to `PDFService.render_invoice` and returns the resulting PDF bytes to the router for streaming. |

---

### `get_next_invoice_number`

```python
async def get_next_invoice_number(
    user_id: int,
    year: int,
    db: AsyncSession,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Invoice number string, e.g. `INV-2026-0042` |
| Raises | — |
| Description | Counts existing invoices for the user in the given year and returns the next number zero-padded to 4 digits. Called internally by `create`. |

---

## PDFService

Located at `app/services/pdf_service.py`.

### `render_invoice`

```python
def render_invoice(
    invoice: Invoice,
    sessions: list[Session],
    client: Client,
) -> bytes
```

| Property | Value |
|----------|-------|
| Returns | Raw PDF bytes |
| Raises | `PDFRenderError` if WeasyPrint fails to produce output |
| Description | Renders the Jinja2 HTML invoice template with the supplied data, then passes the HTML string to `weasyprint.HTML(string=...).write_pdf()`. Returns the resulting bytes. This method is synchronous and should be called in a thread executor from the async `InvoiceService.generate_pdf`. |

---

## TelegramService

Located at `bot/services/telegram_service.py`. All network calls are made through `BotApiClient` (httpx) to the FastAPI API at `http://api:8000/api/v1`. This service contains no direct database access.

### `handle_start`

```python
async def handle_start(
    chat_id: int,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Welcome message string listing available commands |
| Raises | — |
| Description | Returns a static help message. No API call required. |

---

### `handle_link`

```python
async def handle_link(
    chat_id: int,
    email: str,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Confirmation message string |
| Raises | `TelegramUserNotFoundError` if the email does not match any user; `TelegramAlreadyLinkedError` if this chat_id is already linked |
| Description | Calls `POST /api/v1/telegram/link` with `{"chat_id": chat_id, "email": email}` to associate the Telegram identity with the ChronoTrack account. Returns a success or error message. |

---

### `handle_log`

```python
async def handle_log(
    chat_id: int,
    hours: float,
    project: str,
    description: str,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Confirmation string with session details |
| Raises | `TelegramNotLinkedError` if the chat_id is not linked to a user; `NotFoundError` if no project matches the name |
| Description | Resolves the linked user's JWT, looks up the project by name, and calls `POST /api/v1/sessions` to create a manual session entry. Converts `hours` to start/end timestamps anchored at the current time. |

---

### `handle_status`

```python
async def handle_status(
    chat_id: int,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Status string describing the active session (project name, elapsed time) or a "no active session" message |
| Raises | `TelegramNotLinkedError` if the chat_id is not linked |
| Description | Calls `GET /api/v1/sessions/active` using the linked user's token and formats the result as a human-readable status message. |

---

### `handle_report`

```python
async def handle_report(
    chat_id: int,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Text summary of the current week's hours grouped by project |
| Raises | `TelegramNotLinkedError` if the chat_id is not linked |
| Description | Calls `GET /api/v1/reports/summary?period=week` and formats the `by_project` breakdown as a plain-text message suitable for Telegram. |

---

### `handle_stop`

```python
async def handle_stop(
    chat_id: int,
) -> str
```

| Property | Value |
|----------|-------|
| Returns | Confirmation string with the stopped session's duration |
| Raises | `TelegramNotLinkedError` if the chat_id is not linked; `NoActiveSessionError` if there is no running timer |
| Description | Calls `POST /api/v1/sessions/stop` using the linked user's token and formats the closed session as a confirmation message. |
