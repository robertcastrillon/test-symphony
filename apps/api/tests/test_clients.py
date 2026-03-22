from httpx import AsyncClient


async def test_create_client(client: AsyncClient, test_user: dict):
    """Create a client returns 201 with client data."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    payload = {
        "name": "Acme Corp",
        "email": "acme@example.com",
        "hourly_rate": "100.00",
        "currency": "USD",
    }
    response = await client.post("/api/v1/clients", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["email"] == "acme@example.com"
    assert data["currency"] == "USD"
    assert "id" in data


async def test_list_clients(client: AsyncClient, test_user: dict):
    """List clients returns all clients for the authenticated user."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    await client.post("/api/v1/clients", json={"name": "Client A"}, headers=headers)
    await client.post("/api/v1/clients", json={"name": "Client B"}, headers=headers)

    response = await client.get("/api/v1/clients", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {c["name"] for c in data}
    assert names == {"Client A", "Client B"}


async def test_get_client(client: AsyncClient, test_user: dict):
    """Get a single client by id returns 200."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post("/api/v1/clients", json={"name": "My Client"}, headers=headers)
    client_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == client_id


async def test_update_client(client: AsyncClient, test_user: dict):
    """Update a client returns 200 with updated data."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post("/api/v1/clients", json={"name": "Old Name"}, headers=headers)
    client_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/clients/{client_id}",
        json={"name": "New Name"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_delete_client(client: AsyncClient, test_user: dict):
    """Delete a client with no active projects returns 204."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post("/api/v1/clients", json={"name": "To Delete"}, headers=headers)
    client_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/clients/{client_id}", headers=headers)
    assert response.status_code == 204

    # Confirm it's gone
    get_resp = await client.get(f"/api/v1/clients/{client_id}", headers=headers)
    assert get_resp.status_code == 404


async def test_delete_client_with_active_projects_returns_409(client: AsyncClient, test_user: dict):
    """Deleting a client with active projects returns 409."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post(
        "/api/v1/clients", json={"name": "Busy Client"}, headers=headers
    )
    client_id = create_resp.json()["id"]

    # Create an active project for this client
    await client.post(
        "/api/v1/projects",
        json={"name": "Active Project", "client_id": client_id, "is_active": True},
        headers=headers,
    )

    response = await client.delete(f"/api/v1/clients/{client_id}", headers=headers)
    assert response.status_code == 409
    assert "active projects" in response.json()["detail"].lower()


async def test_unauthenticated_list_clients_returns_403(client: AsyncClient):
    """Accessing clients without a token returns 403."""
    response = await client.get("/api/v1/clients")
    assert response.status_code == 403


async def test_access_another_users_client_returns_404(client: AsyncClient, test_user: dict):
    """Accessing another user's client returns 404."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post(
        "/api/v1/clients", json={"name": "Owner's Client"}, headers=headers
    )
    client_id = create_resp.json()["id"]

    # Register a second user
    resp2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "name": "Other User", "password": "password123"},
    )
    other_token = resp2.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await client.get(f"/api/v1/clients/{client_id}", headers=other_headers)
    assert response.status_code == 404
