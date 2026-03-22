import pytest


@pytest.mark.asyncio
async def test_register_success(client, test_user_data):
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_user_data):
    await client.post("/api/v1/auth/register", json=test_user_data)
    response = await client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, test_user_data, registered_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user_data, registered_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success(client, registered_user):
    refresh_token = registered_user["refresh_token"]
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid.token.value"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client, registered_user):
    """Old refresh token should be invalidated after rotation."""
    old_refresh = registered_user["refresh_token"]
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    response = await client.get("/api/v1/clients")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(client, registered_user):
    access_token = registered_user["access_token"]
    response = await client.get(
        "/api/v1/clients",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "password123", "name": "Test"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "short", "name": "Test"},
    )
    assert response.status_code == 422
