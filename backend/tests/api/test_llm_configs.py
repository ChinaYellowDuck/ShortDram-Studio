"""Tests for LLM config API endpoints."""

import pytest


def _create_config(
    client,
    name: str,
    model_type: str = "text",
    is_default: bool = False,
) -> int:
    response = client.post(
        "/api/v1/llm-configs",
        json={
            "name": name,
            "provider": "openai",
            "model_type": model_type,
            "model_name": "test-model",
            "api_key": "test-key",
            "is_default": is_default,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_get_providers(client):
    """Test getting supported LLM providers."""
    response = client.get("/api/v1/llm-configs/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check that common providers are present
    provider_keys = {p["key"] for p in data}
    assert "openai" in provider_keys
    assert "anthropic" in provider_keys


def test_list_configs_empty(client):
    """Test listing LLM configs when none exist."""
    response = client.get("/api/v1/llm-configs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_create_config(client):
    """Test creating an LLM configuration."""
    response = client.post(
        "/api/v1/llm-configs",
        json={
            "name": "测试配置",
            "provider": "openai",
            "model_name": "gpt-4o",
            "api_key": "sk-test-123",
            "is_default": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试配置"
    assert data["provider"] == "openai"
    assert data["model_name"] == "gpt-4o"
    assert data["is_default"] is True
    # API key should NOT be in response
    assert "api_key" not in data


def test_create_config_unsupported_provider(client):
    """Test creating config with unsupported provider."""
    response = client.post(
        "/api/v1/llm-configs",
        json={
            "name": "无效配置",
            "provider": "unknown_provider",
            "model_name": "test",
            "api_key": "test-key",
        },
    )
    assert response.status_code == 400


def test_get_default_config_empty(client):
    """Test getting default config when none exists."""
    response = client.get("/api/v1/llm-configs/default", params={"model_type": "text"})
    assert response.status_code == 404


def test_default_is_scoped_per_model_type(client):
    """A default applies only within its model type."""
    text_id = _create_config(client, "文字默认", "text", is_default=True)
    image_id = _create_config(client, "图片默认", "image", is_default=True)

    assert client.get(f"/api/v1/llm-configs/{text_id}").json()["is_default"] is True
    assert client.get(f"/api/v1/llm-configs/{image_id}").json()["is_default"] is True

    text2_id = _create_config(client, "文字默认2", "text")
    response = client.post(f"/api/v1/llm-configs/{text2_id}/set-default")
    assert response.status_code == 200

    assert client.get(f"/api/v1/llm-configs/{text_id}").json()["is_default"] is False
    assert client.get(f"/api/v1/llm-configs/{text2_id}").json()["is_default"] is True
    assert client.get(f"/api/v1/llm-configs/{image_id}").json()["is_default"] is True


def test_get_default_by_model_type(client):
    """The default endpoint resolves per model type."""
    _create_config(client, "文字默认", "text", is_default=True)
    _create_config(client, "图片默认", "image", is_default=True)

    text_response = client.get("/api/v1/llm-configs/default", params={"model_type": "text"})
    image_response = client.get("/api/v1/llm-configs/default", params={"model_type": "image"})

    assert text_response.status_code == 200
    assert text_response.json()["name"] == "文字默认"
    assert image_response.status_code == 200
    assert image_response.json()["name"] == "图片默认"


def test_create_and_filter_configs_by_model_type(client):
    """Model type is persisted and can be used to filter configurations."""
    for name, model_type in (("文本模型", "text"), ("绘图模型", "image")):
        response = client.post(
            "/api/v1/llm-configs",
            json={
                "name": name,
                "provider": "openai",
                "model_type": model_type,
                "model_name": "test-model",
                "api_key": "test-key",
            },
        )
        assert response.status_code == 201
        assert response.json()["model_type"] == model_type

    response = client.get("/api/v1/llm-configs", params={"model_type": "image"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "绘图模型"


def test_rejects_unknown_model_type(client):
    response = client.post(
        "/api/v1/llm-configs",
        json={
            "name": "未知类型",
            "provider": "openai",
            "model_type": "unknown",
            "model_name": "test-model",
            "api_key": "test-key",
        },
    )
    assert response.status_code == 422
