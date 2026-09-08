"""Tests for MCP management endpoints."""


def test_mcp_crud(client):
    created = client.post(
        "/api/v1/mcps",
        json={"name": "搜索工具", "url": "https://example.com/mcp"},
    )
    assert created.status_code == 201
    mcp = created.json()
    assert mcp["transport"] == "streamable_http"
    assert mcp["is_enabled"] is True

    got = client.get(f"/api/v1/mcps/{mcp['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "搜索工具"

    updated = client.put(
        f"/api/v1/mcps/{mcp['id']}",
        json={"transport": "sse", "description": "搜索外部知识库"},
    )
    assert updated.status_code == 200
    assert updated.json()["transport"] == "sse"

    assert client.delete(f"/api/v1/mcps/{mcp['id']}").status_code == 204
    assert client.get(f"/api/v1/mcps/{mcp['id']}").status_code == 404


def test_mcp_name_unique(client):
    client.post("/api/v1/mcps", json={"name": "工具", "url": "https://a.com"})
    duplicate = client.post("/api/v1/mcps", json={"name": "工具", "url": "https://b.com"})
    assert duplicate.status_code == 400
