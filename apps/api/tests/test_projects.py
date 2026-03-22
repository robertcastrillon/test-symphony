from httpx import AsyncClient


async def _create_client(client: AsyncClient, headers: dict, name: str = "Test Client") -> str:
    resp = await client.post("/api/v1/clients", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_project_without_client(client: AsyncClient, test_user: dict):
    """Create a project without a client_id returns 201."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    payload = {"name": "Internal Project", "description": "No client", "color": "#abcdef"}
    response = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Internal Project"
    assert data["client_id"] is None
    assert data["color"] == "#abcdef"
    assert data["is_active"] is True


async def test_create_project_with_client(client: AsyncClient, test_user: dict):
    """Create a project linked to a client returns 201."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    client_id = await _create_client(client, headers)

    payload = {"name": "Client Project", "client_id": client_id}
    response = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["client_id"] == client_id


async def test_list_projects(client: AsyncClient, test_user: dict):
    """List projects returns all projects for the authenticated user."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    await client.post("/api/v1/projects", json={"name": "P1"}, headers=headers)
    await client.post("/api/v1/projects", json={"name": "P2"}, headers=headers)

    response = await client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_projects_filter_by_client(client: AsyncClient, test_user: dict):
    """List projects filtered by client_id returns only matching projects."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    client_id = await _create_client(client, headers)

    await client.post(
        "/api/v1/projects", json={"name": "P1", "client_id": client_id}, headers=headers
    )
    await client.post("/api/v1/projects", json={"name": "P2"}, headers=headers)

    response = await client.get(f"/api/v1/projects?client_id={client_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "P1"


async def test_list_projects_filter_by_is_active(client: AsyncClient, test_user: dict):
    """List projects filtered by is_active returns matching projects."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    r1 = await client.post("/api/v1/projects", json={"name": "Active"}, headers=headers)
    p_id = r1.json()["id"]
    await client.patch(f"/api/v1/projects/{p_id}/deactivate", headers=headers)
    await client.post("/api/v1/projects", json={"name": "Still Active"}, headers=headers)

    active_resp = await client.get("/api/v1/projects?is_active=true", headers=headers)
    assert active_resp.status_code == 200
    active_names = [p["name"] for p in active_resp.json()]
    assert "Still Active" in active_names
    assert "Active" not in active_names

    inactive_resp = await client.get("/api/v1/projects?is_active=false", headers=headers)
    assert inactive_resp.status_code == 200
    inactive_names = [p["name"] for p in inactive_resp.json()]
    assert "Active" in inactive_names


async def test_deactivate_project(client: AsyncClient, test_user: dict):
    """Deactivating a project sets is_active to False."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post(
        "/api/v1/projects", json={"name": "To Deactivate"}, headers=headers
    )
    project_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/projects/{project_id}/deactivate", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_update_project_color(client: AsyncClient, test_user: dict):
    """Updating a project's color returns 200 with new color."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post("/api/v1/projects", json={"name": "Colorful"}, headers=headers)
    project_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"color": "#ff0000"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["color"] == "#ff0000"


async def test_update_project_invalid_color_returns_422(client: AsyncClient, test_user: dict):
    """Updating a project with an invalid hex color returns 422."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post("/api/v1/projects", json={"name": "Bad Color"}, headers=headers)
    project_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"color": "red"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_unauthenticated_list_projects_returns_403(client: AsyncClient):
    """Accessing projects without a token returns 403."""
    response = await client.get("/api/v1/projects")
    assert response.status_code == 403


async def test_get_another_users_project_returns_404(client: AsyncClient, test_user: dict):
    """Accessing another user's project returns 404."""
    headers = {"Authorization": f"Bearer {test_user['access_token']}"}
    create_resp = await client.post("/api/v1/projects", json={"name": "Secret"}, headers=headers)
    project_id = create_resp.json()["id"]

    resp2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "other2@example.com", "name": "Other2", "password": "password123"},
    )
    other_token = resp2.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = await client.get(f"/api/v1/projects/{project_id}", headers=other_headers)
    assert response.status_code == 404
