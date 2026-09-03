"""NFR-010: purchase_request status/trace reads stay responsive on the local target."""

import time


def _completed_run(client) -> str:
    payload = {
        "requester_name": "Alex Morgan", "department": "Operations", "item_or_service": "Office chairs",
        "supplier": "Supply Co", "amount": "1200.50", "currency": "EUR",
        "business_justification": "Replace unsafe and damaged office seating.",
        "required_date": "2099-09-01", "execution_mode": "orchestration", "demonstration_scenario": "standard",
    }
    waiting = client.post("/api/requests", json=payload).json()
    item = client.get("/api/approvals").json()[0]
    client.post(
        f"/api/approvals/{item['work_item_id']}/decision",
        json={"choice": "APPROVE", "expected_state_version": item["state_version"]},
    )
    return waiting["run_id"]


def test_95_of_100_status_reads_finish_within_one_second(client) -> None:
    run_id = _completed_run(client)

    under_bound = 0
    for _ in range(100):
        started = time.perf_counter()
        response = client.get(f"/api/runs/{run_id}")
        elapsed = time.perf_counter() - started
        assert response.status_code == 200
        if elapsed < 1.0:
            under_bound += 1

    assert under_bound >= 95
