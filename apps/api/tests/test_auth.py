from httpx import AsyncClient

from app.models.user import User


async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": test_user.email, "password": "password123", "name": "Dup"},
    )
    assert response.status_code == 409


async def test_login_success(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_refresh_success(client: AsyncClient, test_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_protected_endpoint_without_token(client: AsyncClient):
    # Try to access a protected route without token - will return 403 (no bearer) or 401
    response = await client.get("/api/v1/clients")
    assert response.status_code in (401, 403, 404)
