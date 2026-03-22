from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    """Register a new user returns 201 with access and refresh tokens."""
    payload = {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


async def test_register_duplicate_email(client: AsyncClient, test_user: dict):
    """Registering with an already-used email returns 409."""
    payload = {
        "email": test_user["email"],
        "name": "Another User",
        "password": "anotherpassword123",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


async def test_login_success(client: AsyncClient, test_user: dict):
    """Login with correct credentials returns 200 with tokens."""
    payload = {
        "email": test_user["email"],
        "password": test_user["password"],
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    """Login with wrong password returns 401."""
    payload = {
        "email": test_user["email"],
        "password": "wrongpassword!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


async def test_refresh_success(client: AsyncClient, test_user: dict):
    """Refreshing with a valid refresh token returns new tokens."""
    payload = {"refresh_token": test_user["refresh_token"]}
    response = await client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New tokens should be different from originals
    assert data["refresh_token"] != test_user["refresh_token"]


async def test_refresh_invalid_token(client: AsyncClient):
    """Refreshing with an invalid token returns 401."""
    payload = {"refresh_token": "this.is.not.a.valid.token"}
    response = await client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 401


async def test_protected_endpoint_without_token(client: AsyncClient):
    """Accessing a protected endpoint without a Bearer token returns 403."""
    # /me endpoint requires authentication
    response = await client.get("/api/v1/auth/me")
    # FastAPI HTTPBearer returns 403 when no credentials provided
    assert response.status_code == 403


async def test_health_endpoint(client: AsyncClient):
    """Health endpoint returns 200 with status ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"


async def test_get_me_with_valid_token(client: AsyncClient, test_user: dict):
    """Accessing /me with a valid token returns user info."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["name"] == test_user["name"]


async def test_get_me_with_invalid_token(client: AsyncClient):
    """Accessing /me with an invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    """Login with an email that doesn't exist returns 401."""
    payload = {
        "email": "nobody@example.com",
        "password": "somepassword123",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
