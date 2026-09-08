"""Tests for agent metadata management endpoints."""


def _create_llm(client, model_type: str = "text") -> int:
    response = client.post(
        "/api/v1/llm-configs",
        json={
            "name": f"{model_type} config",
            "provider": "openai",
            "model_type": model_type,
            "model_name": "test-model",
            "api_key": "test-key",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_agent_crud_enable_toggle_and_default_text_llm(client):
    text_llm_id = _create_llm(client)
    response = client.post(
        "/api/v1/agents/meta",
        json={
            "agent_key": "reviewer",
            "name": "审稿智能体",
            "agent_type": "创作",
            "default_llm_config_id": text_llm_id,
            "default_params": {"temperature": 0.2},
        },
    )
    assert response.status_code == 201
    agent = response.json()
    assert agent["default_llm_config_id"] == text_llm_id

    response = client.patch(
        f"/api/v1/agents/meta/{agent['id']}/enabled", params={"enabled": False}
    )
    assert response.status_code == 200
    assert response.json()["is_enabled"] is False

    response = client.get("/api/v1/agents/meta", params={"is_enabled": False})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.delete(f"/api/v1/agents/meta/{agent['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/agents/meta/{agent['id']}").status_code == 404


def test_agent_rejects_non_text_default_llm(client):
    image_llm_id = _create_llm(client, "image")
    response = client.post(
        "/api/v1/agents/meta",
        json={
            "agent_key": "illustrator",
            "name": "插画智能体",
            "agent_type": "创作",
            "default_llm_config_id": image_llm_id,
        },
    )
    assert response.status_code == 400


def test_agent_edit_binds_mcp_and_skill(client):
    mcp = client.post(
        "/api/v1/mcps", json={"name": "搜索工具", "url": "https://example.com/mcp"}
    ).json()
    skill = client.post(
        "/api/v1/skills", json={"name": "审阅", "content": "审阅剧本内容"}
    ).json()

    agent = client.post(
        "/api/v1/agents/meta",
        json={
            "agent_key": "reviewer",
            "name": "审稿智能体",
            "agent_type": "创作",
            "temperature": 0.3,
            "system_message": "你是严谨的剧本审阅助手。",
        },
    ).json()

    updated = client.put(
        f"/api/v1/agents/meta/{agent['id']}",
        json={"mcp_ids": [mcp["id"]], "skill_ids": [skill["id"]]},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["mcp_ids"] == [mcp["id"]]
    assert body["skill_ids"] == [skill["id"]]
    assert body["temperature"] == 0.3
    assert body["system_message"] == "你是严谨的剧本审阅助手。"

    # Unbind by sending empty lists.
    unbound = client.put(
        f"/api/v1/agents/meta/{agent['id']}",
        json={"mcp_ids": [], "skill_ids": []},
    )
    assert unbound.status_code == 200
    assert unbound.json()["mcp_ids"] == []
    assert unbound.json()["skill_ids"] == []
