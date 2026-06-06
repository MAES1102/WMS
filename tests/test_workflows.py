"""Tests for /workflows and /tasks endpoints."""


def _make_user(client, email="u@test.com"):
    return client.post("/users", json={"email": email, "password": "pw"}).json()


def _make_workflow(client, user_id, name="WF"):
    return client.post("/workflows", json={"name": name, "user_id": user_id}).json()


def test_create_workflow(client):
    user = _make_user(client)
    r = client.post("/workflows", json={"name": "My Workflow", "user_id": user["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "My Workflow"
    assert body["user_id"] == user["id"]


def test_duplicate_task_order_returns_409(client):
    user = _make_user(client)
    wf = _make_workflow(client, user["id"])
    client.post("/tasks", json={"name": "Task A", "workflow_id": wf["id"], "order": 1})
    r = client.post("/tasks", json={"name": "Task B", "workflow_id": wf["id"], "order": 1})
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


def test_list_tasks_returns_only_existing(client):
    user = _make_user(client)
    wf = _make_workflow(client, user["id"])
    client.post("/tasks", json={"name": "T1", "workflow_id": wf["id"], "order": 1})
    client.post("/tasks", json={"name": "T2", "workflow_id": wf["id"], "order": 2})
    tasks = client.get("/tasks").json()
    wf_tasks = [t for t in tasks if t["workflow_id"] == wf["id"]]
    assert len(wf_tasks) == 2
    orders = {t["order"] for t in wf_tasks}
    assert orders == {1, 2}


def test_delete_task_reorders_remaining(client):
    user = _make_user(client)
    wf = _make_workflow(client, user["id"])
    t1 = client.post("/tasks", json={"name": "T1", "workflow_id": wf["id"], "order": 1}).json()
    client.post("/tasks", json={"name": "T2", "workflow_id": wf["id"], "order": 2})
    client.post("/tasks", json={"name": "T3", "workflow_id": wf["id"], "order": 3})
    client.delete(f"/tasks/{t1['id']}")
    tasks = client.get("/tasks").json()
    wf_tasks = sorted([t for t in tasks if t["workflow_id"] == wf["id"]], key=lambda t: t["order"])
    assert [t["order"] for t in wf_tasks] == [1, 2]


def test_delete_workflow_not_found(client):
    r = client.delete("/workflows/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Workflow not found"


def test_get_task_not_found(client):
    r = client.get("/tasks/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Task not found"


def test_delete_task_not_found(client):
    r = client.delete("/tasks/99999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Task not found"


def test_workflow_status_summary(client):
    user = _make_user(client, "summary@test.com")
    wf = _make_workflow(client, user["id"], "StatusWF")
    client.post("/tasks", json={"name": "T1", "workflow_id": wf["id"], "order": 1})
    client.post("/tasks", json={"name": "T2", "workflow_id": wf["id"], "order": 2})
    r = client.get(f"/workflows/{wf['id']}/status")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total_tasks"] == 2
    assert body["summary"]["pending_tasks"] == 2
    assert body["summary"]["done_tasks"] == 0
    assert body["workflow"]["id"] == wf["id"]


def test_workflow_status_not_found(client):
    r = client.get("/workflows/99999/status")
    assert r.status_code == 404
    assert r.json()["detail"] == "Workflow not found"


def test_delete_workflow_cascades_tasks(client):
    """Deleting a workflow must remove all its tasks (FR-07, NFR-05)."""
    user = _make_user(client, "cascade@test.com")
    wf = _make_workflow(client, user["id"], "CascadeWF")
    client.post("/tasks", json={"name": "T1", "workflow_id": wf["id"], "order": 1})
    client.post("/tasks", json={"name": "T2", "workflow_id": wf["id"], "order": 2})

    r = client.delete(f"/workflows/{wf['id']}")
    assert r.status_code == 200

    all_tasks = client.get("/tasks").json()
    orphans = [t for t in all_tasks if t["workflow_id"] == wf["id"]]
    assert orphans == [], f"Expected 0 tasks after cascade delete, got {len(orphans)}"
