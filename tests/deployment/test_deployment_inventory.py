from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_compose_declares_one_application_and_one_persistent_volume() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "  app:\n" in compose
    assert compose.count("  app:\n") == 1
    assert "invoice_data:/data" in compose
    assert "INVOICE_DATABASE_URL: sqlite:////data/invoice_v3.db" in compose
    assert "INVOICE_STORAGE_ROOT: /data/documents" in compose
    assert "kafka" not in compose.lower()
    assert "zookeeper" not in compose.lower()
    assert "pip install" not in compose
    assert "- .:/" not in compose


def test_container_runs_as_non_root_with_a_healthcheck() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.13-slim" in dockerfile
    assert "USER app" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert 'CMD ["uvicorn", "app.main:app"' in dockerfile
    assert "/data/documents" in dockerfile
