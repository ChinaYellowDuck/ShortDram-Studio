"""Tests for storyboard management API."""


def _create_project_with_scene(client, db_session):
    """Helper: create a project + script + scene for storyboard tests."""
    resp = client.post("/api/v1/projects", json={"name": "分镜测试项目"})
    pid = resp.json()["id"]

    from app.models.script import Script, ScriptScene

    script = Script(project_id=pid, title="测试剧本", total_episodes=1)
    db_session.add(script)
    db_session.flush()

    scene = ScriptScene(
        script_id=script.id,
        scene_number="1",
        location="办公室",
        int_ext="INT",
        time_of_day="日",
        description="主角走进办公室",
        order_index=0,
    )
    db_session.add(scene)
    db_session.commit()
    return pid, scene.id


def test_create_storyboard_shot(client, db_session):
    """Test creating a storyboard shot."""
    pid, scene_id = _create_project_with_scene(client, db_session)

    resp = client.post(
        f"/api/v1/storyboard?project_id={pid}",
        json={
            "script_scene_id": scene_id,
            "shot_number": "S01E01-001",
            "composition": "中景",
            "camera_movement": "固定",
            "camera_angle": "平视",
            "visual_description": "主角走进办公室环顾四周",
            "duration_seconds": 5,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["shot_number"] == "S01E01-001"
    assert data["composition"] == "中景"
    assert data["duration_seconds"] == 5
    assert data["project_id"] == pid
    assert data["script_scene_id"] == scene_id


def test_list_storyboard_shots(client, db_session):
    """Test listing storyboard shots."""
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot

    for i in range(3):
        db_session.add(StoryboardShot(
            project_id=pid,
            script_scene_id=scene_id,
            shot_number=f"S01E01-00{i+1}",
            order_index=i,
        ))
    db_session.commit()

    r = client.get(f"/api/v1/storyboard?project_id={pid}")
    assert r.status_code == 200
    assert r.json()["total"] == 3
    assert len(r.json()["items"]) == 3


def test_update_storyboard_shot(client, db_session):
    """Test updating a storyboard shot."""
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot

    shot = StoryboardShot(
        project_id=pid, script_scene_id=scene_id, shot_number="S01E01-001", order_index=0
    )
    db_session.add(shot)
    db_session.commit()

    r = client.put(
        f"/api/v1/storyboard/{shot.id}",
        json={"composition": "特写", "duration_seconds": 10, "visual_description": "新描述"},
    )
    assert r.status_code == 200
    assert r.json()["composition"] == "特写"
    assert r.json()["duration_seconds"] == 10
    assert r.json()["visual_description"] == "新描述"


def test_delete_storyboard_shot(client, db_session):
    """Test deleting a storyboard shot."""
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot

    shot = StoryboardShot(
        project_id=pid, script_scene_id=scene_id, shot_number="S01E01-001", order_index=0
    )
    db_session.add(shot)
    db_session.commit()

    r = client.delete(f"/api/v1/storyboard/{shot.id}")
    assert r.status_code == 204

    r = client.get(f"/api/v1/storyboard/{shot.id}")
    assert r.status_code == 404


def test_reorder_storyboard_shots(client, db_session):
    """Test reordering storyboard shots."""
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot

    shots = []
    for i in range(3):
        s = StoryboardShot(
            project_id=pid, script_scene_id=scene_id, shot_number=f"S{i+1}", order_index=i
        )
        db_session.add(s)
        shots.append(s)
    db_session.commit()

    # reverse order
    new_order = [s.id for s in reversed(shots)]
    r = client.post(
        f"/api/v1/storyboard/reorder?project_id={pid}",
        json={"shot_ids": new_order},
    )
    assert r.status_code == 200

    # verify order in list response
    r = client.get(f"/api/v1/storyboard?project_id={pid}")
    items = r.json()["items"]
    assert items[0]["id"] == new_order[0]
    assert items[1]["id"] == new_order[1]
    assert items[2]["id"] == new_order[2]


def test_nonexistent_storyboard_shot_404(client):
    """Getting a non-existent shot should return 404."""
    r = client.get("/api/v1/storyboard/99999")
    assert r.status_code == 404
