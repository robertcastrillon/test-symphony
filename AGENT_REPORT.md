## Deploy Report — ENG-93: AUTH-02: Registration & account creation

NEXT_STATE: Staging

**Deployed at:** 2026-03-22 18:02 UTC
**Branch merged:** `eng-93` → `develop` (via PR #1)
**PR:** Merged

### Staging access

| Service | URL | Status |
|---------|-----|--------|
| API | http://localhost:8003 | Running |
| API docs | http://localhost:8003/docs | Available |
| Web app | N/A (web frontend is U6, parallel unit) | — |

### Credentials
- Email: test@example.com
- Password: password123

### Smoke test results

| Check | Result |
|-------|--------|
| Health endpoint `GET /api/v1/health` | `{"status":"ok","version":"1.0.0"}` PASS |
| `POST /api/v1/auth/register` (new user) | HTTP 201 + JWT tokens PASS |
| `POST /api/v1/auth/register` (duplicate email) | HTTP 409 PASS |
| `POST /api/v1/auth/login` (valid credentials) | HTTP 200 + JWT tokens PASS |
| Alembic migration `0001_initial_schema` | Applied successfully PASS |

### What to verify in staging

1. `POST /api/v1/auth/register` with `{"email":"test@example.com","password":"password123","name":"Test User"}` returns HTTP 201 with `access_token` and `refresh_token`
2. `POST /api/v1/auth/login` with same credentials returns HTTP 200 with token pair
3. `POST /api/v1/auth/register` with same email returns HTTP 409
4. `POST /api/v1/auth/refresh` with a valid refresh token from step 1/2 returns new token pair (HTTP 200)
5. `GET /api/v1/health` returns `{"status":"ok","version":"1.0.0"}`
6. API docs available at http://localhost:8003/docs for interactive exploration

### Deployment notes

- Docker Compose deployed on localhost with non-conflicting ports: API on `8003`, DB on `5436` (other eng workspaces occupy 8000–8002 and 5433–5435)
- Added `email-validator>=2.0.0` and `fastapi[standard]` to `pyproject.toml` — required for Pydantic `EmailStr` validation at runtime
- Alembic migration `0001_initial_schema` applied: created all 5 tables (`users`, `clients`, `projects`, `sessions`, `invoices`) with FK constraints and indexes
- JWT secrets supplied via environment variables for staging
- Web service (`apps/web`) is not yet built — it is part of U6 (a parallel frontend unit, not a U1 dependency)
- Bot service requires `TELEGRAM_TOKEN` env var and is gated behind a Docker Compose profile (`--profile bot`)
