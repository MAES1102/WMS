"""Tests for workflow execution endpoints (orchestration and choreography)."""
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_workflow_with_tasks(client, n_tasks=2):
    """Create a user, workflow, and *n_tasks* tasks; return workflow dict."""
    user = client.post("/users", json={"email": "exec@test.com", "password": "pw"}).json()
    wf = client.post("/workflows", json={"name": "ExecWF", "user_id": user["id"]}).json()
    for i in range(1, n_tasks + 1):
        client.post("/tasks", json={"name": f"Task{i}", "workflow_id": wf["id"], "order": i})
    return wf


def _tasks_for_workflow(client, workflow_id):
    all_tasks = client.get("/tasks").json()
    return sorted(
        [t for t in all_tasks if t["workflow_id"] == workflow_id],
        key=lambda t: t["order"],
    )


# ---------------------------------------------------------------------------
# Nonexistent workflow
# ---------------------------------------------------------------------------

def test_execute_nonexistent_workflow_returns_404(client):
    r = client.post("/execute/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Workflow not found"


def test_execute_choreo_nonexistent_workflow_returns_404(client):
    r = client.post("/execute_choreo/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Workflow not found"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def test_orchestrated_workflow_success(client):
    """With random.random always returning 0.5, no task fails."""
    wf = _make_workflow_with_tasks(client, n_tasks=2)
    with patch("random.random", return_value=0.5):
        r = client.post(f"/execute/{wf['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["workflow_id"] == wf["id"]
    tasks = _tasks_for_workflow(client, wf["id"])
    assert all(t["status"] == "DONE" for t in tasks)


def test_orchestrated_workflow_halts_on_failure(client):
    """With random.random always returning 0.1, task 1 fails and task 2 is skipped."""
    wf = _make_workflow_with_tasks(client, n_tasks=2)
    with patch("random.random", return_value=0.1):
        r = client.post(f"/execute/{wf['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "failed"
    tasks = _tasks_for_workflow(client, wf["id"])
    # Task 1 must be FAILED; Task 2 must remain PENDING (not executed)
    assert tasks[0]["status"] == "FAILED"
    assert tasks[1]["status"] == "PENDING"


# ---------------------------------------------------------------------------
# Choreography
# ---------------------------------------------------------------------------

def test_choreography_success(client):
    """Full choreography chain succeeds when no task fails."""
    wf = _make_workflow_with_tasks(client, n_tasks=3)
    with patch("random.random", return_value=0.5):
        r = client.post(f"/execute_choreo/{wf['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["mode"] == "choreography"
    tasks = _tasks_for_workflow(client, wf["id"])
    assert all(t["status"] == "DONE" for t in tasks)


def test_choreography_stops_on_failure(client):
    """When task 1 fails its event is NOT emitted; task 2 must stay PENDING."""
    wf = _make_workflow_with_tasks(client, n_tasks=2)
    with patch("random.random", return_value=0.1):
        r = client.post(f"/execute_choreo/{wf['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "failed"
    tasks = _tasks_for_workflow(client, wf["id"])
    # Task 1 failed — Task 2 must NOT have been triggered (BUG-02 regression guard)
    assert tasks[0]["status"] == "FAILED"
    assert tasks[1]["status"] == "PENDING", (
        "Task 2 was executed despite Task 1 failing — BUG-02 regression!"
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_execute_empty_workflow_completes(client):
    """A workflow with no tasks should complete immediately without error."""
    user = client.post("/users", json={"email": "empty@test.com", "password": "pw"}).json()
    wf = client.post("/workflows", json={"name": "EmptyWF", "user_id": user["id"]}).json()
    r = client.post(f"/execute/{wf['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_execute_choreo_empty_workflow_completes(client):
    """Choreography on an empty workflow should also complete without error."""
    user = client.post("/users", json={"email": "empty2@test.com", "password": "pw"}).json()
    wf = client.post("/workflows", json={"name": "EmptyWF2", "user_id": user["id"]}).json()
    r = client.post(f"/execute_choreo/{wf['id']}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_workflow_run_history_recorded(client):
    """After execution a WorkflowRun record must be retrievable via GET /workflow_runs/{id}."""
    wf = _make_workflow_with_tasks(client, n_tasks=1)
    with patch("random.random", return_value=0.5):
        client.post(f"/execute/{wf['id']}")
    r = client.get(f"/workflow_runs/{wf['id']}")
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) >= 1
    assert runs[0]["workflow_id"] == wf["id"]
    assert runs[0]["mode"] == "orchestration"
    assert runs[0]["status"] == "COMPLETED"
