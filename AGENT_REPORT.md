## Agent Report — ENG-97: AUTH-06: Core functionality

**Mode:** Implementation
**Branch:** `eng-97`
**PR:** https://github.com/robertcastrillon/test-symphony/pull/6

### What was implemented

- **Project infrastructure**: `pyproject.toml` (all deps pinned, `bcrypt==4.0.1`), `docker-compose.yml` (4 services), `docker-compose.test.yml`, `.github/workflows/ci.yml`, `Makefile`, `.env.example`
- **FastAPI application**: `app/main.py` factory with CORS, lifespan handler, exception handlers; `core/` (config, security, dependencies, exceptions)
- **Database layer**: async SQLAlchemy engine (`db/database.py`), session factory (`db/session.py`), 5 ORM models (User, Client, Project, Session, Invoice), Alembic async env + initial migration
- **Auth service + endpoints**: register (unique email, bcrypt hash), login (credential verify), refresh (token rotation — old token invalidated via bcrypt hash comparison; bcrypt-safe via SHA-256 pre-hash to avoid 72-byte truncation issue)
- **Unit tests**: 21 tests across `test_auth.py` (HTTP integration) and `test_auth_service.py` (service layer direct), using SQLite in-memory via dependency override

### Files changed

- `.env.example`
- `.gitignore`
- `.github/workflows/ci.yml`
- `Makefile`
- `docker-compose.yml`
- `docker-compose.test.yml`
- `pyproject.toml`
- `apps/api/Dockerfile`
- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/versions/0001_initial_schema.py`
- `apps/api/pyproject.toml`
- `apps/api/app/main.py`
- `apps/api/app/core/config.py`
- `apps/api/app/core/security.py`
- `apps/api/app/core/dependencies.py`
- `apps/api/app/core/exceptions.py`
- `apps/api/app/db/database.py`
- `apps/api/app/db/session.py`
- `apps/api/app/models/base.py`
- `apps/api/app/models/user.py`
- `apps/api/app/models/client.py`
- `apps/api/app/models/project.py`
- `apps/api/app/models/session.py`
- `apps/api/app/models/invoice.py`
- `apps/api/app/schemas/auth.py`
- `apps/api/app/services/auth.py`
- `apps/api/app/routers/auth.py`
- `apps/api/app/routers/health.py`
- `apps/api/app/routers/clients.py`
- `apps/api/tests/conftest.py`
- `apps/api/tests/test_auth.py`
- `apps/api/tests/test_auth_service.py`

### Quality results

| Check | Result |
|-------|--------|
| Unit tests | 21 passed in 8.10s |
| Coverage | 91% (gate: 80%) |
| Lint (ruff) | Clean — 0 errors |
| Security (bandit) | No high/critical findings |

### Notable implementation decisions

- **bcrypt 72-byte truncation**: JWT refresh tokens (~248 chars) were being silently truncated by bcrypt. Fixed by SHA-256 hashing the token string before passing to bcrypt — standard pattern for long secrets.
- **Token rotation**: Each refresh token gets a unique `jti` (UUID) claim. Old token is rejected by comparing bcrypt hash after rotation.
- **Test isolation**: SQLite in-memory DB via `StaticPool` + `dependency_overrides[get_db]` — no external DB required for tests.

### Next step

Quality Check agent will run the full test pyramid and deploy locally.
