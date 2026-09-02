"""Tests for project API endpoints."""


def test_list_projects_empty(client):
    """Test listing projects when none exist."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_create_project(client):
    """Test creating a new project."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "测试短剧项目", "description": "这是一个测试项目"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试短剧项目"
    assert data["description"] == "这是一个测试项目"
    assert data["status"] == "draft"
    assert "id" in data
    assert "created_at" in data


def test_get_project(client):
    """Test getting a project by ID."""
    # Create first
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "项目A", "description": "描述A"},
    )
    project_id = create_response.json()["id"]

    # Get
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "项目A"


def test_update_project(client):
    """Test updating a project."""
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "旧名称"},
    )
    project_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "新名称", "description": "新描述"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新名称"
    assert data["description"] == "新描述"


def test_delete_project(client):
    """Test deleting a project."""
    create_response = client.post(
        "/api/v1/projects",
        json={"name": "待删除项目"},
    )
    project_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 404


def test_get_nonexistent_project(client):
    """Test getting a project that doesn't exist."""
    response = client.get("/api/v1/projects/9999")
    assert response.status_code == 404
