"""Tests for the BPMN-like graph execution engine: conditional transitions,
branching, retry loops, and the MAX_LOOP_ITERATIONS safety valve.

Both orchestration and choreography share the same TransitionResolver, so
these tests exercise both execution modes.
"""
from unittest.mock import patch

from app.engine.transitions import MAX_LOOP_ITERATIONS


def _make_user_and_workflow(client, email="graph@test.com", name="GraphWF"):
    user = client.post("/users", json={"email": email, "password": "pw"}).json()
    wf = client.post("/workflows", json={"name": name, "user_id": user["id"]}).json()
    return wf


def _make_task(client, workflow_id, name, order):
    return client.post(
        "/tasks", json={"name": name, "workflow_id": workflow_id, "order": order}
    ).json()


def _make_transition(client, workflow_id, from_task_id, to_task_id, condition, priority=0):
    r = client.post(
        f"/workflows/{workflow_id}/transitions",
        json={
            "from_task_id": from_task_id,
            "to_task_id": to_task_id,
            "condition": condition,
            "priority": priority,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _task_status(client, task_id):
    return client.get(f"/tasks/{task_id}").json()["status"]


# ---------------------------------------------------------------------------
# 1. Conditional SUCCESS path
# ---------------------------------------------------------------------------

def test_conditional_success_path(client):
    """A --SUCCESS--> B: when A succeeds, B must run next."""
    wf = _make_user_and_workflow(client, "cond@test.com", "CondWF")
    a = _make_task(client, wf["id"], "A", 1)
    b = _make_task(client, wf["id"], "B", 2)
    _make_transition(client, wf["id"], a["id"], b["id"], "SUCCESS")

    with patch("random.random", return_value=0.5):  # always succeeds
        r = client.post(f"/execute/{wf['id']}")

    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert _task_status(client, a["id"]) == "DONE"
    assert _task_status(client, b["id"]) == "DONE"


# ---------------------------------------------------------------------------
# 2. FAILURE branch execution (retry path)
# ---------------------------------------------------------------------------

def test_failure_branch_execution(client):
    """Payment failure executes the retry path (FAILURE transition)."""
    wf = _make_user_and_workflow(client, "fail@test.com", "FailWF")
    charge = _make_task(client, wf["id"], "ChargeCard", 1)
    retry = _make_task(client, wf["id"], "RetryPayment", 2)
    _make_transition(client, wf["id"], charge["id"], retry["id"], "FAILURE")

    # ChargeCard: two random() calls both < 0.3 -> hard fail.
    # RetryPayment: one random() call >= 0.3 -> succeeds, no further edge.
    with patch("random.random", side_effect=[0.1, 0.1, 0.5]):
        r = client.post(f"/execute/{wf['id']}")

    assert r.status_code == 200
    assert _task_status(client, charge["id"]) == "FAILED"
    assert _task_status(client, retry["id"]) == "DONE"
    # RetryPayment has no outgoing edge and succeeded -> branch reached END.
    assert r.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# 3. Loop: task can return to a previous task
# ---------------------------------------------------------------------------

def test_workflow_loop_retry(client):
    """ChargeCard -FAILURE-> RetryPayment -SUCCESS-> ChargeCard -SUCCESS-> Ship."""
    wf = _make_user_and_workflow(client, "loop@test.com", "LoopWF")
    charge = _make_task(client, wf["id"], "ChargeCard", 1)
    retry = _make_task(client, wf["id"], "RetryPayment", 2)
    ship = _make_task(client, wf["id"], "Ship", 3)
    _make_transition(client, wf["id"], charge["id"], retry["id"], "FAILURE")
    _make_transition(client, wf["id"], retry["id"], charge["id"], "SUCCESS")
    _make_transition(client, wf["id"], charge["id"], ship["id"], "SUCCESS")

    # ChargeCard#1 fails (2 calls), RetryPayment succeeds (1 call),
    # ChargeCard#2 succeeds (1 call), Ship succeeds (1 call).
    with patch("random.random", side_effect=[0.1, 0.1, 0.5, 0.5, 0.5]):
        r = client.post(f"/execute/{wf['id']}")

    assert r.status_code == 200
    assert r.json()["status"] == "completed"
    assert _task_status(client, charge["id"]) == "DONE"
    assert _task_status(client, retry["id"]) == "DONE"
    assert _task_status(client, ship["id"]) == "DONE"

    # ChargeCard must have been executed (RUNNING) at least twice — proof of the loop.
    logs = client.get("/logs").json()["logs"]
    charge_running_events = [
        entry for entry in logs
        if isinstance(entry, dict)
        and entry.get("task_id") == charge["id"]
        and entry.get("status") == "RUNNING"
    ]
    assert len(charge_running_events) >= 2


# ---------------------------------------------------------------------------
# 4. Loop limit prevents infinite execution
# ---------------------------------------------------------------------------

def test_loop_limit_prevents_infinite_execution(client):
    """A self-looping FAILURE edge must stop after MAX_LOOP_ITERATIONS."""
    wf = _make_user_and_workflow(client, "loopfail@test.com", "LoopFailWF")
    a = _make_task(client, wf["id"], "A", 1)
    _make_transition(client, wf["id"], a["id"], a["id"], "FAILURE")

    with patch("random.random", return_value=0.1):  # always hard-fails
        r = client.post(f"/execute/{wf['id']}")

    assert r.status_code == 200
    assert r.json()["status"] == "failed"


# ---------------------------------------------------------------------------
# 5. Choreography uses the same transition-based resolution
# ---------------------------------------------------------------------------

def test_choreography_transition_based_execution(client):
    """Choreography mode also follows WorkflowTransition edges (no order chain)."""
    wf = _make_user_and_workflow(client, "choreo-graph@test.com", "ChoreoGraphWF")
    a = _make_task(client, wf["id"], "A", 1)
    b = _make_task(client, wf["id"], "B", 2)
    _make_transition(client, wf["id"], a["id"], b["id"], "SUCCESS")

    with patch("random.random", return_value=0.5):  # always succeeds
        r = client.post(f"/execute_choreo/{wf['id']}")

    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "choreography"
    assert body["status"] == "completed"
    assert _task_status(client, a["id"]) == "DONE"
    assert _task_status(client, b["id"]) == "DONE"


def test_max_loop_iterations_constant_is_reasonable():
    """Sanity check on the safety-valve constant itself."""
    assert MAX_LOOP_ITERATIONS == 10
