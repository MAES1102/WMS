import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import httpx
from pypdf import PdfWriter
import pytest


ROOT = Path(__file__).parents[2]


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def one_page_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def local_request(method: str, url: str, **kwargs) -> httpx.Response:
    with httpx.Client(trust_env=False) as client:
        return client.request(method, url, **kwargs)


@contextmanager
def running_service(data_root: Path, port: int):
    environment = os.environ.copy()
    environment.update(
        {
            "DATABASE_URL": f"sqlite:///{data_root / 'workflow.db'}",
            "INVOICE_DATABASE_URL": (
                f"sqlite:///{data_root / 'invoice_v3.db'}"
            ),
            "INVOICE_STORAGE_ROOT": str(data_root / "documents"),
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(f"service exited during startup:\n{output}")
            try:
                if local_request("GET", f"{url}/", timeout=0.5).status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.05)
        else:
            raise AssertionError("service did not become ready within 10 seconds")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.parametrize("mode", ("orchestration", "choreography"))
def test_waiting_invoice_survives_process_restart_and_resumes(
    tmp_path: Path,
    mode: str,
) -> None:
    port = available_port()
    number = f"INV-RESTART-{mode}"

    with running_service(tmp_path, port) as url:
        response = local_request(
            "POST",
            f"{url}/api/v3/invoices",
            data={
                "supplier_name": "Restart Supplier",
                "invoice_number": number,
                "issue_date": "2026-08-13",
                "amount": "42.00",
                "currency": "EUR",
                "mode": mode,
            },
            files={
                "document": (
                    "restart.pdf",
                    one_page_pdf(),
                    "application/pdf",
                )
            },
            timeout=10,
        )
        assert response.status_code == 201
        waiting = response.json()
        assert waiting["invoice_state"] == "PENDING_APPROVAL"
        assert waiting["run_status"] == "WAITING_FOR_APPROVAL"

    assert (tmp_path / "workflow.db").exists()
    assert (tmp_path / "invoice_v3.db").exists()
    assert any((tmp_path / "documents").iterdir())

    with running_service(tmp_path, port) as restarted_url:
        restored = local_request(
            "GET",
            f"{restarted_url}/api/v3/runs/{waiting['run_id']}",
            timeout=10,
        )
        assert restored.status_code == 200
        assert restored.json()["invoice_number"] == number
        assert restored.json()["invoice_state"] == "PENDING_APPROVAL"

        decision = local_request(
            "POST",
            f"{restarted_url}/api/v3/approvals/{waiting['work_item_id']}/decision",
            json={
                "choice": "APPROVE",
                "note": "Approved after service restart",
                "expected_state_version": restored.json()["state_version"],
            },
            timeout=10,
        )
        assert decision.status_code == 200
        completed = decision.json()["run"]
        assert completed["run_id"] == waiting["run_id"]
        assert completed["invoice_state"] == "ARCHIVED"
        assert completed["run_status"] == "COMPLETED"
        assert completed["execution_mode"] == mode
        assert completed["archive_document_identity"]
