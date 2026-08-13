from io import BytesIO

from pypdf import PdfWriter
import pytest

from app.v3_runtime import invoice_event_bus


def one_page_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize("mode", ("orchestration", "choreography"))
def test_visible_invoice_ui_and_full_approval_path(client, mode: str) -> None:
    page = client.get("/ui")
    legacy = client.get("/legacy-ui")

    assert page.status_code == 200
    assert "Invoice Approval Desk" in page.text
    assert "Start invoice process" in page.text
    assert "Choreography — run-scoped events" in page.text
    assert "Workflow constructor (advanced)" in page.text
    assert "Activate revision" in page.text
    assert "Graph projection" in page.text
    assert "no scripts or plugins" in page.text
    assert "Current business state" in page.text
    assert "Required next action" in page.text
    assert "Final result" in page.text
    assert "Technical audit trace" in page.text
    assert legacy.status_code == 200

    submitted = client.post(
        "/api/v3/invoices",
        data={
            "supplier_name": "Acme Supplies",
            "invoice_number": f"INV-VISIBLE-{mode}",
            "issue_date": "2026-08-13",
            "amount": "1250.00",
            "currency": "EUR",
            "mode": mode,
        },
        files={
            "document": (
                "invoice.pdf",
                one_page_pdf(),
                "application/pdf",
            )
        },
    )

    assert submitted.status_code == 201
    waiting = submitted.json()
    assert waiting["invoice_state"] == "PENDING_APPROVAL"
    assert waiting["run_status"] == "WAITING_FOR_APPROVAL"
    assert waiting["execution_mode"] == mode
    assert waiting["supplier_name"] == "Acme Supplies"
    assert waiting["invoice_number"] == f"INV-VISIBLE-{mode}"
    assert waiting["work_item_id"]
    assert waiting["notification"] is None
    assert invoice_event_bus.subscriber_count == 0

    decided = client.post(
        f"/api/v3/approvals/{waiting['work_item_id']}/decision",
        json={
            "choice": "APPROVE",
            "note": "Invoice details match the order",
            "expected_state_version": waiting["state_version"],
        },
    )

    assert decided.status_code == 200
    completed = decided.json()["run"]
    assert completed["invoice_state"] == "ARCHIVED"
    assert completed["execution_mode"] == mode
    assert completed["supplier_name"] == "Acme Supplies"
    assert completed["invoice_number"] == f"INV-VISIBLE-{mode}"
    assert completed["run_status"] == "COMPLETED"
    assert completed["archive_document_identity"]
    assert completed["notification"] == (
        f"Invoice INV-VISIBLE-{mode} was archived successfully."
    )
    assert completed["approval"]["decision"] == "APPROVE"
    assert invoice_event_bus.subscriber_count == 0
    assert client.get(f"/api/v3/runs/{waiting['run_id']}").json() == completed
