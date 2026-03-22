# AGENT_REPORT — ENG-92: AUTH-01 Database Models, Schemas & Project Scaffolding

## Status: COMPLETE

## What was built

### Project Infrastructure
- `pyproject.toml`: all Python dependencies pinned, including `bcrypt==4.0.1` as required
- `docker-compose.yml`: 4 services (db/postgres:16, api/FastAPI, web/Vite, bot with `profiles: [bot]`)
- `docker-compose.test.yml`: CI test environment
- `.github/workflows/ci.yml`: triggers on PR to `develop`; lint (ruff + bandit) and test (pytest --cov-fail-under=80)
- `Makefile`: `dev`, `test`, `lint`, `migrate` targets
- `.env.example`: all required environment variables
- `.gitignore`: excludes pycache, .env, coverage files
- `.coveragerc`: configured with `concurrency = greenlet` to correctly measure async code coverage

### Application (`apps/api/app/`)
- `main.py`: FastAPI app factory with CORS middleware, lifespan handler, router registration
- `core/config.py`: Pydantic `Settings` class
- `core/security.py`: JWT encode/decode, `verify_password`, `get_password_hash`, `create_access_token`, `create_refresh_token`, `decode_token_safe`
- `core/dependencies.py`: `get_current_user` with `HTTPBearer(auto_error=False)` returning 401 (not 403) when unauthenticated
- `core/exceptions.py`: `ChronoTrackException`, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `ValidationError`
- `db/database.py`: SQLAlchemy async engine, `Base` declarative base
- `db/session.py`: `AsyncSession` factory, `get_db` context manager

### SQLAlchemy Models
- `models/base.py`: UUID primary key + `created_at` timestamptz
- `models/user.py`, `client.py`, `project.py`, `session.py`, `invoice.py`: all 5 models with specified columns, FKs, and indexes

### Alembic
- `alembic/env.py`: async-compatible with `target_metadata = Base.metadata`
- `alembic/versions/0001_initial_schema.py`: creates all 5 tables with constraints, FKs, and indexes

### Auth Endpoints
- `POST /api/v1/auth/register`: 201 + token pair, 409 on duplicate email
- `POST /api/v1/auth/login`: 200 + token pair, 401 on bad credentials
- `POST /api/v1/auth/refresh`: validates refresh token type, rotates tokens
- `GET /api/v1/health`: no auth, returns `{status: "ok", version: "1.0.0"}`
- `GET /api/v1/users/me`: requires auth, returns current user profile

### Tests
- `tests/conftest.py`: function-scoped async engine (avoids asyncio loop conflicts), `db_session`, `client` with `get_db` override, `test_user` fixture
- `tests/test_auth.py`: 11 tests covering all required scenarios

## Test Results

```
11 passed, 3 warnings in 3.64s
Coverage: 87% (gate: 80%)
Lint: ruff + bandit both clean
```

## Key Technical Decisions

1. **`asyncio_default_fixture_loop_scope = "function"`** in `pyproject.toml` — prevents loop conflicts between session-scoped engine connections and function-scoped test coroutines. Engine is created fresh per test inside `db_engine` fixture.

2. **`.coveragerc` with `concurrency = greenlet`** — SQLAlchemy async uses greenlets internally; without this setting, lines inside `await` expressions were reported as uncovered even when executed, giving inaccurate coverage (76% vs actual 87%).

3. **`HTTPBearer(auto_error=False)`** — FastAPI's default `HTTPBearer` returns 403 (not 401) when no Authorization header is present. Using `auto_error=False` lets `get_current_user` raise a proper 401.

## PR

https://github.com/robertcastrillon/test-symphony/pull/4
