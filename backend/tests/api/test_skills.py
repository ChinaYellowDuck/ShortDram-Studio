"""Tests for skill management endpoints."""


def test_skill_crud(client):
    created = client.post(
        "/api/v1/skills",
        json={
            "name": "剧本审阅",
            "content": "检查剧本的节奏、冲突与人物弧光。",
        },
    )
    assert created.status_code == 201
    skill = created.json()
    assert skill["is_enabled"] is True

    got = client.get(f"/api/v1/skills/{skill['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "剧本审阅"

    updated = client.put(
        f"/api/v1/skills/{skill['id']}",
        json={"description": "对剧本进行质量审阅"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "对剧本进行质量审阅"

    assert client.delete(f"/api/v1/skills/{skill['id']}").status_code == 204
    assert client.get(f"/api/v1/skills/{skill['id']}").status_code == 404
