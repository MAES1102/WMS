"""Tests for WorkflowRun + TaskExecution instance isolation in choreography.

Verifies that:
1. Executing the same workflow twice via choreography produces two independent
   WorkflowRun records (mode="choreography"), each with its own TaskExecution rows.
2. Run history is preserved — the first run's state is not overwritten by the
   second run.
3. A graph-transition workflow (A --SUCCESS--> B) executed via choreography
   produces TaskExecution rows for both A and B, both ending DONE.
"""
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_workflow(client, email, name, n_tasks=2):
    user = client.post("/users", json={"email": email, "password": "pw"}).json()
    wf = client.post("/workflows", json={"name": name, "user_id": user["id"]}).json()
    tasks = []
    for i in range(1, n_tasks + 1):
        t = client.post(
            "/tasks", json={"name": f"T{i}", "workflow_id": wf["id"], "order": i}
        ).json()
        tasks.append(t)
    return wf, tasks


def _make_transition(client, workflow_id, from_id, to_id, condition="SUCCESS"):
    r = client.post(
        f"/workflows/{workflow_id}/transitions",
        json={"from_task_id": from_id, "to_task_id": to_id,
              "condition": condition, "priority": 0},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _task_executions(client, run_id):
    return client.get(f"/workflow_runs/{run_id}/task_executions").json()


# ---------------------------------------------------------------------------
# Test 1: two choreography executions → two independent instances
# ---------------------------------------------------------------------------

def test_two_choreo_executions_produce_independent_run_instances(client):
    """Running the same workflow twice via choreography must create two separate
    WorkflowRun records (mode='choreography'), each owning distinct
    TaskExecution rows."""
    wf, _ = _make_workflow(client, "choreo1@test.com", "ChoreoWF1", n_tasks=2)

    with patch("random.random", return_value=0.5):
        r1 = client.post(f"/execute_choreo/{wf['id']}")
        r2 = client.post(f"/execute_choreo/{wf['id']}")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["mode"] == "choreography"
    assert r2.json()["mode"] == "choreography"

    run_id_1 = r1.json()["run_id"]
    run_id_2 = r2.json()["run_id"]
    assert run_id_1 != run_id_2, "Each execution must produce a unique run_id"

    # Both WorkflowRun rows must appear in GET /workflow_runs/{workflow_id}
    runs = client.get(f"/workflow_runs/{wf['id']}").json()
    run_ids_in_db = {r["id"] for r in runs}
    assert len(runs) == 2
    assert run_id_1 in run_ids_in_db
    assert run_id_2 in run_ids_in_db
    assert all(r["mode"] == "choreography" for r in runs)

    # Each run must own independent TaskExecution records
    execs_1 = _task_executions(client, run_id_1)
    execs_2 = _task_executions(client, run_id_2)

    assert len(execs_1) == 2, "Run 1 must have one TaskExecution per task"
    assert len(execs_2) == 2, "Run 2 must have one TaskExecution per task"

    assert all(te["run_id"] == run_id_1 for te in execs_1)
    assert all(te["run_id"] == run_id_2 for te in execs_2)

    # TaskExecution IDs must be distinct across runs
    ids_1 = {te["id"] for te in execs_1}
    ids_2 = {te["id"] for te in execs_2}
    assert ids_1.isdisjoint(ids_2), "TaskExecution rows must be distinct across runs"

    # Both runs cover the same task definitions
    task_ids_1 = {te["task_id"] for te in execs_1}
    task_ids_2 = {te["task_id"] for te in execs_2}
    assert task_ids_1 == task_ids_2


# ---------------------------------------------------------------------------
# Test 2: run history preserved — first run not overwritten by second
# ---------------------------------------------------------------------------

def test_choreo_first_run_history_preserved_after_second_execution(client):
    """After a second choreography execution, the first run's WorkflowRun record
    and its TaskExecution rows must remain intact and unmodified."""
    wf, _ = _make_workflow(client, "choreo2@test.com", "ChoreoWF2", n_tasks=1)

    with patch("random.random", return_value=0.5):
        r1 = client.post(f"/execute_choreo/{wf['id']}")
    assert r1.json()["status"] == "completed"
    run_id_1 = r1.json()["run_id"]

    with patch("random.random", return_value=0.5):
        r2 = client.post(f"/execute_choreo/{wf['id']}")
    assert r2.json()["status"] == "completed"
    run_id_2 = r2.json()["run_id"]

    runs = client.get(f"/workflow_runs/{wf['id']}").json()
    assert len(runs) == 2, "Both run records must persist after two executions"

    by_id = {r["id"]: r for r in runs}
    assert run_id_1 in by_id, "First run must still exist after the second execution"
    assert by_id[run_id_1]["status"] == "COMPLETED", \
        "First run status must not be overwritten by the second run"
    assert by_id[run_id_2]["status"] == "COMPLETED"

    # First run's TaskExecution rows still present and still point to run_id_1
    execs_1 = _task_executions(client, run_id_1)
    assert len(execs_1) >= 1
    assert all(te["run_id"] == run_id_1 for te in execs_1), \
        "Run 1 TaskExecution rows must not be overwritten by run 2"


# ---------------------------------------------------------------------------
# Test 3: graph-transition choreography creates DONE TaskExecution for A and B
# ---------------------------------------------------------------------------

def test_choreo_graph_transition_creates_task_executions_for_both_tasks(client):
    """A --SUCCESS--> B executed via choreography must produce TaskExecution
    rows for both A (DONE) and B (DONE), with the run completing successfully."""
    wf, tasks = _make_workflow(client, "choreo3@test.com", "ChoreoGraphWF", n_tasks=2)
    task_a, task_b = tasks[0], tasks[1]
    _make_transition(client, wf["id"], task_a["id"], task_b["id"], "SUCCESS")

    with patch("random.random", return_value=0.5):  # always succeeds
        r = client.post(f"/execute_choreo/{wf['id']}")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["mode"] == "choreography"

    run_id = body["run_id"]
    execs = _task_executions(client, run_id)

    assert len(execs) == 2, "Must have one TaskExecution per task definition"

    exec_by_task = {te["task_id"]: te for te in execs}
    assert task_a["id"] in exec_by_task, "TaskExecution for Task A must exist"
    assert task_b["id"] in exec_by_task, "TaskExecution for Task B must exist"

    assert exec_by_task[task_a["id"]]["status"] == "DONE", \
        "Task A's TaskExecution must be DONE"
    assert exec_by_task[task_b["id"]]["status"] == "DONE", \
        "Task B's TaskExecution must be DONE"
