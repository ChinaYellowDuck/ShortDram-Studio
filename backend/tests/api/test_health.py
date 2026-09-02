"""Tests for health check endpoints."""


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "env" in data


def test_langsmith_status(client):
    """Test the LangSmith status endpoint."""
    response = client.get("/api/v1/health/langsmith")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
