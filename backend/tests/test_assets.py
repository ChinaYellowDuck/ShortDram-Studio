"""Tests for asset management API."""


def _create_project(client):
    resp = client.post("/api/v1/projects", json={"name": "资产测试项目"})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_character_asset(client):
    """Test creating a character asset."""
    pid = _create_project(client)
    resp = client.post(
        f"/api/v1/assets?project_id={pid}",
        json={
            "type": "character",
            "name": "男主角",
            "description": "25岁都市青年",
            "extra": {"age": "25", "gender": "男"},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "男主角"
    assert data["type"] == "character"
    assert data["source"] == "manual"
    assert data["reference_count"] == 0
    assert data["extra"]["age"] == "25"


def test_create_scene_asset(client):
    """Test creating a scene asset."""
    pid = _create_project(client)
    resp = client.post(
        f"/api/v1/assets?project_id={pid}",
        json={
            "type": "scene",
            "name": "办公室",
            "description": "现代都市写字楼办公室",
            "extra": {"int_ext": "INT", "time_of_day": "日"},
        },
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "scene"


def test_create_prop_asset(client):
    """Test creating a prop asset."""
    pid = _create_project(client)
    resp = client.post(
        f"/api/v1/assets?project_id={pid}",
        json={"type": "prop", "name": "神秘盒子"},
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "prop"


def test_list_assets_filter_by_type(client):
    """Test listing assets with type filter."""
    pid = _create_project(client)
    for i in range(3):
        client.post(f"/api/v1/assets?project_id={pid}", json={"type": "character", "name": f"角色{i}"})
    client.post(f"/api/v1/assets?project_id={pid}", json={"type": "scene", "name": "办公室"})

    r = client.get(f"/api/v1/assets?project_id={pid}&type=character")
    assert r.status_code == 200
    assert r.json()["total"] == 3

    r = client.get(f"/api/v1/assets?project_id={pid}&type=scene")
    assert r.json()["total"] == 1

    r = client.get(f"/api/v1/assets?project_id={pid}&type=prop")
    assert r.json()["total"] == 0


def test_list_assets_search(client):
    """Test searching assets by name."""
    pid = _create_project(client)
    client.post(f"/api/v1/assets?project_id={pid}", json={"type": "character", "name": "张三"})
    client.post(f"/api/v1/assets?project_id={pid}", json={"type": "character", "name": "李四"})

    r = client.get(f"/api/v1/assets?project_id={pid}&search=张")
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["name"] == "张三"


def test_get_update_delete_asset(client):
    """Test CRUD lifecycle of an asset."""
    pid = _create_project(client)
    create_resp = client.post(
        f"/api/v1/assets?project_id={pid}",
        json={"type": "prop", "name": "道具A"},
    )
    aid = create_resp.json()["id"]

    # get
    r = client.get(f"/api/v1/assets/{aid}")
    assert r.status_code == 200
    assert r.json()["name"] == "道具A"

    # update
    r = client.put(f"/api/v1/assets/{aid}", json={"name": "道具B", "image_url": "http://img"})
    assert r.status_code == 200
    assert r.json()["name"] == "道具B"
    assert r.json()["image_url"] == "http://img"

    # delete
    r = client.delete(f"/api/v1/assets/{aid}")
    assert r.status_code == 204

    # verify deleted
    r = client.get(f"/api/v1/assets/{aid}")
    assert r.status_code == 404


def test_nonexistent_asset_404(client):
    """Getting a non-existent asset should return 404."""
    r = client.get("/api/v1/assets/99999")
    assert r.status_code == 404
