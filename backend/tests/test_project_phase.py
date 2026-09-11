"""Tests for project phase transitions."""


def test_new_project_has_script_phase(client):
    """New projects should default to script phase."""
    resp = client.post("/api/v1/projects", json={"name": "测试项目"})
    assert resp.status_code == 201
    assert resp.json()["phase"] == "script"


def test_transition_phase_forward(client):
    """Test transitioning phase forward through all stages."""
    resp = client.post("/api/v1/projects", json={"name": "推进测试"})
    pid = resp.json()["id"]

    for phase in ["asset", "storyboard", "video", "completed"]:
        r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": phase})
        assert r.status_code == 200
        assert r.json()["phase"] == phase


def test_transition_phase_backward(client):
    """Test rolling back to an earlier phase."""
    resp = client.post("/api/v1/projects", json={"name": "回退测试"})
    pid = resp.json()["id"]

    client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "video"})
    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "asset"})
    assert r.status_code == 200
    assert r.json()["phase"] == "asset"


def test_completed_phase_updates_status(client):
    """Entering completed phase should update project status to completed."""
    resp = client.post("/api/v1/projects", json={"name": "完成测试"})
    pid = resp.json()["id"]
    assert resp.json()["status"] == "draft"

    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "completed"})
    assert r.json()["phase"] == "completed"
    assert r.json()["status"] == "completed"


def test_first_phase_keeps_draft_status(client):
    """Staying in script phase should keep status as draft."""
    resp = client.post("/api/v1/projects", json={"name": "草稿测试"})
    pid = resp.json()["id"]

    # script -> asset (leaving script phase)
    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "asset"})
    assert r.json()["status"] == "in_progress"
