from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_compose_declares_one_application_and_one_persistent_volume() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "  app:\n" in compose
    assert compose.count("  app:\n") == 1
    assert "invoice_data:/data" in compose
    assert "INVOICE_DATABASE_URL: sqlite:////data/invoice.db" in compose
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


def test_local_launcher_avoids_repository_wide_reload_by_default() -> None:
    launcher = (ROOT / "scripts" / "run_local.sh").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "-m uvicorn app.main:app" in launcher
    assert "--reload" not in launcher
    assert "--reload --reload-dir app" in readme
    assert "invoice_documents/" in gitignore


def test_repository_exposes_one_invoice_application_only() -> None:
    obsolete_paths = (
        "app/db.py",
        "app/models.py",
        "app/routes.py",
        "app/engine",
        "app/static/index.html",
        "build_pdf.py",
        "package.json",
        "package-lock.json",
        "docs/implementation",
    )

    assert all(not (ROOT / path).exists() for path in obsolete_paths)

    main_source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "legacy-ui" not in main_source
    assert "workflow.db" not in compose
