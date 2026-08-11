"""Tests for WorkflowRun + TaskExecution instance isolation in orchestration.

Verifies that:
1. Executing the same workflow twice creates two independent WorkflowRun rows,
   each with its own set of TaskExecution records.
2. Run history is preserved after a second execution — the first run's state
   is never overwritten by the second run.
"""
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_workflow_with_tasks(client, n_tasks=2):
    user = client.post("/users", json={"email": "inst@test.com", "password": "pw"}).json()
    wf = client.post("/workflows", json={"name": "InstanceWF", "user_id": user["id"]}).json()
    for i in range(1, n_tasks + 1):
        client.post("/tasks", json={"name": f"T{i}", "workflow_id": wf["id"], "order": i})
    return wf


# ---------------------------------------------------------------------------
# Test 1: two executions → two independent WorkflowRun + TaskExecution rows
# ---------------------------------------------------------------------------

def test_two_executions_produce_independent_run_instances(client):
    """Running the same workflow twice must produce two separate WorkflowRun rows,
    each owning its own TaskExecution records with distinct run_ids."""
    wf = _make_workflow_with_tasks(client, n_tasks=2)

    with patch("random.random", return_value=0.5):
        r1 = client.post(f"/execute/{wf['id']}")
        r2 = client.post(f"/execute/{wf['id']}")

    assert r1.status_code == 200
    assert r2.status_code == 200

    run_id_1 = r1.json()["run_id"]
    run_id_2 = r2.json()["run_id"]
    assert run_id_1 != run_id_2, "Each execution must produce a unique run_id"

    # Both WorkflowRun rows must be visible via GET /workflow_runs/{workflow_id}
    runs = client.get(f"/workflow_runs/{wf['id']}").json()
    assert len(runs) == 2, "Two executions must produce exactly two WorkflowRun rows"
    run_ids_in_db = {r["id"] for r in runs}
    assert run_id_1 in run_ids_in_db
    assert run_id_2 in run_ids_in_db

    # Each run must have independent TaskExecution records
    execs_1 = client.get(f"/workflow_runs/{run_id_1}/task_executions").json()
    execs_2 = client.get(f"/workflow_runs/{run_id_2}/task_executions").json()

    assert len(execs_1) == 2, "Run 1 must have one TaskExecution per task"
    assert len(execs_2) == 2, "Run 2 must have one TaskExecution per task"

    # All TaskExecution rows for each run carry that run's id
    assert all(te["run_id"] == run_id_1 for te in execs_1)
    assert all(te["run_id"] == run_id_2 for te in execs_2)

    # The two runs share the same task definitions but have distinct execution rows
    task_ids_1 = {te["task_id"] for te in execs_1}
    task_ids_2 = {te["task_id"] for te in execs_2}
    assert task_ids_1 == task_ids_2, "Both runs cover the same task definitions"

    exec_ids_1 = {te["id"] for te in execs_1}
    exec_ids_2 = {te["id"] for te in execs_2}
    assert exec_ids_1.isdisjoint(exec_ids_2), "TaskExecution rows must be distinct across runs"


# ---------------------------------------------------------------------------
# Test 2: run history is preserved — first run not overwritten by second
# ---------------------------------------------------------------------------

def test_first_run_history_preserved_after_second_execution(client):
    """After a second execution the first run's WorkflowRun record (and its
    finished_at / status) must remain unchanged in the database."""
    wf = _make_workflow_with_tasks(client, n_tasks=1)

    # First execution — succeeds
    with patch("random.random", return_value=0.5):
        r1 = client.post(f"/execute/{wf['id']}")
    assert r1.json()["status"] == "completed"
    run_id_1 = r1.json()["run_id"]

    # Second execution — also succeeds
    with patch("random.random", return_value=0.5):
        r2 = client.post(f"/execute/{wf['id']}")
    assert r2.json()["status"] == "completed"
    run_id_2 = r2.json()["run_id"]

    runs = client.get(f"/workflow_runs/{wf['id']}").json()
    assert len(runs) == 2, "Both run records must persist after two executions"

    by_id = {r["id"]: r for r in runs}

    # First run record still present with its original status
    assert run_id_1 in by_id, "First run must still exist after a second execution"
    assert by_id[run_id_1]["status"] == "COMPLETED", \
        "First run status must not be overwritten by the second run"

    # Second run is independently tracked
    assert run_id_2 in by_id
    assert by_id[run_id_2]["status"] == "COMPLETED"

    # TaskExecution rows for run 1 are preserved and undisturbed
    execs_1 = client.get(f"/workflow_runs/{run_id_1}/task_executions").json()
    assert len(execs_1) >= 1
    assert all(te["run_id"] == run_id_1 for te in execs_1), \
        "Run 1 TaskExecution rows must still point to run_id_1, not overwritten"
