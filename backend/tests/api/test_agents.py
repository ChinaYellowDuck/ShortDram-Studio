"""Tests for the agent execution endpoints."""


def test_agent_chat_unknown_key(client):
    response = client.post(
        "/api/v1/agents/chat",
        params={"agent_key": "does_not_exist", "message": "你好"},
    )
    assert response.status_code == 404


def test_agent_chat_disabled_agent(client):
    created = client.post(
        "/api/v1/agents/meta",
        json={
            "agent_key": "hello_agent",
            "name": "Hello Agent",
            "agent_type": "测试",
        },
    )
    hello_id = created.json()["id"]

    client.patch(
        f"/api/v1/agents/meta/{hello_id}/enabled",
        params={"enabled": False},
    )

    response = client.post(
        "/api/v1/agents/chat",
        params={"agent_key": "hello_agent", "message": "你好"},
    )
    assert response.status_code == 409
