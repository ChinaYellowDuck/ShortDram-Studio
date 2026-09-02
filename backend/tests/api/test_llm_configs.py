"""Tests for LLM config API endpoints."""

import pytest


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


def test_create_config(client, monkeypatch):
    """Test creating an LLM configuration."""
    # Mock encryption to avoid needing ENCRYPTION_KEY
    from app.utils import crypto

    monkeypatch.setattr(crypto, "encrypt", lambda x: f"encrypted:{x}")

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


def test_create_config_unsupported_provider(client, monkeypatch):
    """Test creating config with unsupported provider."""
    from app.utils import crypto

    monkeypatch.setattr(crypto, "encrypt", lambda x: f"encrypted:{x}")

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
    response = client.get("/api/v1/llm-configs/default")
    assert response.status_code == 404
