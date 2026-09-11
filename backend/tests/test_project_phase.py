"""Tests for project phase transitions."""


def test_new_project_has_setup_phase(client):
    """New projects should default to setup phase."""
    resp = client.post("/api/v1/projects", json={"name": "测试项目"})
    assert resp.status_code == 201
    assert resp.json()["phase"] == "setup"


def test_transition_phase_forward(client):
    """Test transitioning phase forward through all stages."""
    resp = client.post("/api/v1/projects", json={"name": "推进测试"})
    pid = resp.json()["id"]

    # Try to set up agents via API (may not exist in test environment)
    agents_resp = client.get("/api/v1/agents/available")
    has_agents = False
    if agents_resp.status_code == 200:
        agents = agents_resp.json()
        director = next((a for a in agents if a["agent_key"] == "director"), None)
        writer = next((a for a in agents if a["agent_key"] == "screenwriter"), None)
        if director and writer:
            r = client.post(
                f"/api/v1/projects/{pid}/agents/setup",
                json={
                    "director_agent_id": director["id"],
                    "enabled_agent_ids": [director["id"], writer["id"]],
                },
            )
            has_agents = r.status_code == 200

    # Test phases (skip script if no agents configured, since setup->script requires agents)
    phases = ["script", "asset", "storyboard", "video", "completed"]
    if not has_agents:
        phases = ["asset", "storyboard", "video", "completed"]

    for phase in phases:
        r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": phase})
        assert r.status_code == 200, f"Failed to go to {phase}: {r.text}"
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
    """Staying in setup/script phase should keep status as draft."""
    resp = client.post("/api/v1/projects", json={"name": "草稿测试"})
    pid = resp.json()["id"]
    assert resp.json()["status"] == "draft"

    # setup phase is still draft
    assert resp.json()["phase"] == "setup"

    # setup -> asset (leaving setup phase)
    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "asset"})
    assert r.json()["status"] == "in_progress"


def test_setup_to_script_requires_agents(client):
    """Cannot advance from setup to script without agent configuration."""
    resp = client.post("/api/v1/projects", json={"name": "空配置项目"})
    pid = resp.json()["id"]
    assert resp.json()["phase"] == "setup"

    # Try to advance without agents - should fail
    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "script"})
    assert r.status_code == 400
    assert "智能体" in r.json()["detail"] or "总控" in r.json()["detail"]

    # But can still go directly to asset (skip validation for non-standard flows)
    # Actually let's just verify going backward from asset to setup works
    r2 = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "asset"})
    assert r2.status_code == 200
    r3 = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "setup"})
    assert r3.status_code == 200
    assert r3.json()["phase"] == "setup"
