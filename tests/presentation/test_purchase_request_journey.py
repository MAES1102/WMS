import pytest


def payload(mode="orchestration", scenario="standard", **changes):
    data = dict(requester_name="Alex Morgan", department="Operations", item_or_service="Office chairs", supplier="Supply Co", amount="1200.50", currency="EUR", business_justification="Replace unsafe and damaged office seating.", required_date="2099-09-01", execution_mode=mode, demonstration_scenario=scenario)
    data.update(changes)
    return data


def submit(client, mode="orchestration", scenario="standard", **changes):
    response = client.post("/api/requests", json=payload(mode, scenario, **changes))
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("mode", ("orchestration", "choreography"))
def test_connected_submit_approve_authorize_journey(client, mode):
    waiting = submit(client, mode)
    assert waiting["purchase_request_state"] == "PENDING_APPROVAL"
    item = client.get("/api/approvals").json()[0]
    assert item["item_or_service"] == "Office chairs"
    completed = client.post(f"/api/approvals/{item['work_item_id']}/decision", json={"choice":"APPROVE", "note":"Budget confirmed", "expected_state_version":item["state_version"]}).json()["run"]
    assert completed["run_id"] == waiting["run_id"]
    assert completed["purchase_request_state"] == "AUTHORIZED"
    assert completed["purchase_authorization_code"]
    assert "authorized internally" in completed["notification"]
    assert client.get(f"/api/runs/{waiting['run_id']}").json() == completed


@pytest.mark.parametrize("mode", ("orchestration", "choreography"))
def test_rejection_is_final_and_creates_no_authorization(client, mode):
    waiting = submit(client, mode)
    result = client.post(f"/api/approvals/{waiting['work_item_id']}/decision", json={"choice":"REJECT", "reason":"Department budget is not available", "expected_state_version":waiting["state_version"]}).json()["run"]
    assert result["purchase_request_state"] == "REJECTED"
    assert result["purchase_authorization_code"] is None


def test_invalid_request_never_creates_approval(client):
    result = submit(client, amount="0")
    assert result["purchase_request_state"] == "VALIDATION_FAILED"
    assert result["work_item_id"] is None
    assert client.get("/api/approvals").json() == []


@pytest.mark.parametrize("mode", ("orchestration", "choreography"))
@pytest.mark.parametrize("scenario,state", (("retry_then_success","AUTHORIZED"),("authorization_unavailable","NEEDS_MANUAL_ACTION")))
def test_deterministic_authorization_failures(client, mode, scenario, state):
    waiting = submit(client, mode, scenario)
    result = client.post(f"/api/approvals/{waiting['work_item_id']}/decision", json={"choice":"APPROVE", "expected_state_version":waiting["state_version"]}).json()["run"]
    assert result["purchase_request_state"] == state
    assert sum(row["kind"] == "RETRY_OBSERVATION" for row in result["trace"]) == 1


def test_decision_replay_is_idempotent_and_conflict_is_rejected(client):
    waiting = submit(client); url=f"/api/approvals/{waiting['work_item_id']}/decision"
    body={"choice":"APPROVE", "note":"Approved", "expected_state_version":waiting["state_version"]}
    first=client.post(url,json=body); replay=client.post(url,json=body)
    assert first.status_code == replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert client.post(url,json={"choice":"REJECT","reason":"Changed mind"}).status_code == 409


def test_ui_and_openapi_expose_current_product_only(client):
    page=client.get("/ui"); schema=client.get("/openapi.json").json()
    assert "Event-Driven Workflow Management System" in page.text
    assert "Submit Request" in page.text and "Approver Inbox" in page.text
    assert "Demonstration Controls" in page.text
    assert "/api/requests" in schema["paths"]
    assert all("/api/v3" not in path for path in schema["paths"])
