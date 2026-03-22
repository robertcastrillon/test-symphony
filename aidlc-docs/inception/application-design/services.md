# ChronoTrack — Service Layer Orchestration

This document describes how the service layer is organized, how components collaborate, and the cross-cutting concerns (exceptions, authentication, pagination, token rotation) that apply across the system.

---

## 1. Thin Routers, Fat Services

ChronoTrack enforces a strict separation between HTTP concerns and business logic. Routers are deliberately thin: they parse and validate the request body (Pydantic does this automatically), extract the authenticated user from the dependency, call exactly one service method, and return the result.

**Router responsibilities (only):**
- Declare the HTTP method, path, and status codes.
- Accept validated Pydantic schema objects as function parameters.
- Inject `db: AsyncSession` and `current_user: User` via FastAPI dependencies.
- Call a single service method and return its result.
- Let `ExceptionHandlers` translate any raised `ChronoTrackError` into an HTTP response — routers do not catch exceptions themselves.

**Service responsibilities:**
- All business rules and validations beyond schema-level checks.
- All database queries and mutations via the injected `AsyncSession`.
- Raising typed `ChronoTrackError` subclasses for domain violations.
- Orchestrating calls to other services when needed (e.g., `InvoiceService` calling `PDFService`).

Example flow for `POST /sessions/start`:

```
POST /api/v1/sessions/start
  → SessionRouter.start_timer(data, db, current_user)
      → SessionService.start_timer(current_user.id, data.project_id, data.description, db)
          → checks for existing active session (raises ActiveSessionExistsError if found)
          → checks project exists and belongs to user (raises NotFoundError)
          → checks project.is_active (raises InactiveProjectError if False)
          → inserts new Session row with ended_at=NULL
          → returns Session ORM instance
      → router returns SessionResponse (200 OK)
  OR
  → ExceptionHandler catches ActiveSessionExistsError → 409 Conflict
```

---

## 2. Async SQLAlchemy Sessions via Dependency Injection

The database session lifecycle is managed by the `get_db` dependency in `app/core/dependencies.py`.

```python
# app/core/dependencies.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

Key properties:
- One `AsyncSession` per request. It is created at the start of the request and closed (committed or rolled back) when the response completes.
- Services receive the session as a parameter — they do not import or manage sessions directly.
- All database operations use `await session.execute(...)`, `await session.scalar(...)`, etc. from `sqlalchemy.ext.asyncio`.
- Relationships are loaded with `selectinload` or `joinedload` as needed within service queries; lazy loading is disabled for async sessions.

---

## 3. PDFService Orchestration

`InvoiceService.generate_pdf` is the only service that calls another service. The flow:

```
InvoiceService.generate_pdf(user_id, invoice_id, db)
    → loads Invoice ORM (raises NotFoundError if missing)
    → loads associated Client ORM
    → loads list[Session] linked to the invoice's line items
    → calls PDFService.render_invoice(invoice, sessions, client)
        → Jinja2 renders HTML template with invoice data
        → weasyprint.HTML(string=html).write_pdf() produces bytes
        → returns bytes
    → InvoiceService returns bytes to InvoiceRouter
    → InvoiceRouter returns StreamingResponse(content=bytes, media_type="application/pdf")
```

`PDFService.render_invoice` is a synchronous method (WeasyPrint is not async-compatible). `InvoiceService` calls it inside `asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking the async event loop.

---

## 4. TelegramService and BotApiClient

The bot process is a separate Docker service (`bot`) that has no shared code with the `api` service. All state reads and mutations performed by bot commands go through the FastAPI HTTP API on the internal Docker network.

```
Telegram Update (webhook POST to FastAPI)
  → TelegramRouter passes raw Update JSON to python-telegram-bot dispatcher
  → Dispatcher routes to the matching CommandHandler
  → Handler calls TelegramService.handle_xxx(chat_id, ...)
      → TelegramService calls BotApiClient.get/post(path, ...)
          → httpx.AsyncClient sends HTTP request to http://api:8000/api/v1/...
          → FastAPI processes the request and returns JSON
      → TelegramService formats the response as a Telegram reply string
  → Handler sends reply via context.bot.send_message(chat_id, text)
```

`BotApiClient` resolves the bearer token for a command by:
1. Looking up the `telegram_chat_id` → user mapping (via a lightweight `GET /api/v1/telegram/whoami?chat_id=...` call).
2. Storing the returned JWT in memory for the lifetime of the update processing.

The bot never stores JWT tokens persistently — each command re-resolves the token from the API.

---

## 5. Custom Exception Hierarchy

All domain exceptions inherit from a single base class so that a single broad except clause can catch any application error.

```
ChronoTrackError (base, inherits Exception)
├── NotFoundError                    → HTTP 404
├── AuthError (base)
│   ├── InvalidCredentialsError      → HTTP 401
│   └── InvalidTokenError            → HTTP 401
├── ConflictError (base)
│   ├── EmailAlreadyExistsError      → HTTP 409
│   ├── ActiveSessionExistsError     → HTTP 409
│   └── ClientHasActiveProjectsError → HTTP 409
├── ForbiddenError (base)
│   └── InactiveProjectError         → HTTP 403
├── ValidationError                  → HTTP 422
│   └── InvalidStatusTransitionError → HTTP 422
└── PDFRenderError                   → HTTP 500
```

Bot-specific exceptions (not HTTP-mapped):
```
TelegramError (base)
├── TelegramNotLinkedError
├── TelegramAlreadyLinkedError
└── TelegramUserNotFoundError
```

---

## 6. FastAPI Exception Handlers

Exception handlers are registered on the `FastAPI` app instance in `app/core/exception_handlers.py` and applied in `app/main.py`. They convert `ChronoTrackError` subclasses into structured JSON HTTP responses.

```python
# app/core/exception_handlers.py

@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(InvalidCredentialsError)
@app.exception_handler(InvalidTokenError)
async def unauthorized_handler(request, exc):
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.exception_handler(ActiveSessionExistsError)
@app.exception_handler(EmailAlreadyExistsError)
@app.exception_handler(ClientHasActiveProjectsError)
async def conflict_handler(request, exc):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.exception_handler(InactiveProjectError)
async def forbidden_handler(request, exc):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

@app.exception_handler(InvalidStatusTransitionError)
async def unprocessable_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(PDFRenderError)
async def internal_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": "PDF generation failed"})
```

Because routers do not catch exceptions, any `ChronoTrackError` raised anywhere in the call stack — including deep inside a service — propagates up to these handlers automatically.

---

## 7. JWT Dependency Flow

`get_current_user` in `app/core/dependencies.py` is the standard FastAPI dependency injected into every protected router function.

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = Security.decode_token(token)          # raises InvalidTokenError if invalid
    user_id = payload.get("sub")
    user = await db.get(UserModel, int(user_id))
    if user is None:
        raise NotFoundError("User not found")
    return user
```

- `oauth2_scheme` is `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`, which extracts the bearer token from the `Authorization` header.
- The access token TTL is 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES=15` in `Config`).
- `Security.decode_token` raises `InvalidTokenError` for any JWT error (expired, invalid signature, malformed).
- The `ExceptionHandler` for `InvalidTokenError` returns HTTP 401 with a `WWW-Authenticate: Bearer` header.

---

## 8. Pagination

Paginated responses follow a consistent pattern across all list endpoints that support it (currently `SessionService.list`). The response shape is:

```python
class Page(GenericModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int          # = ceil(total / size)
```

Query parameters on paginated endpoints:
- `page: int = 1` (1-indexed)
- `size: int = 20` (capped at 100)

Implementation in services uses SQLAlchemy `limit` / `offset`:

```python
offset = (page - 1) * size
result = await db.execute(query.offset(offset).limit(size))
count  = await db.scalar(count_query)
```

The router passes `page` and `size` as query parameters to the service, and the service returns a populated `Page[T]` object.

---

## 9. Token Refresh Rotation Pattern

ChronoTrack implements single-use refresh tokens to limit the window of exposure if a token is intercepted.

**Issuance:**
- `AuthService.login` and `AuthService.register` each issue one access token (TTL: 15 min) and one refresh token (TTL: 30 days).
- The refresh token's JTI (JWT ID, a UUID4) is stored in the `refresh_tokens` table along with `user_id` and `expires_at`.

**Rotation:**
1. Client calls `POST /auth/refresh` with the current refresh token.
2. `AuthService.refresh_token` decodes the token and extracts its JTI.
3. The JTI is looked up in the database. If it does not exist or is already marked `used=True`, `InvalidTokenError` is raised.
4. The existing record is marked `used=True` (atomically within the transaction).
5. A new access token and a new refresh token (with a new JTI) are issued and persisted.
6. Both the old (invalidated) and new tokens are committed in a single transaction.

**Frontend behavior:**
- The Axios response interceptor in `ApiClient` catches HTTP 401 responses.
- It calls `POST /auth/refresh` with the stored refresh token.
- On success, it updates `AuthContext` with the new token pair and retries the original request.
- On failure (invalid/expired refresh token), it calls `AuthContext.clearTokens()` and redirects to `/login`.

**Expiry cleanup:**
- Expired and used refresh token records are soft-retained for audit purposes. A periodic cleanup job (outside MVP scope) can purge records older than 60 days.
