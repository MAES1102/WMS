from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPLICATION_SOURCE = (
    ROOT / "app" / "domain",
    ROOT / "app" / "application",
    ROOT / "app" / "infrastructure",
    ROOT / "app" / "persistence",
    ROOT / "app" / "presentation",
)


def test_runtime_dependencies_require_no_broker_or_external_business_system() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()

    assert "kafka" not in requirements
    assert "zookeeper" not in requirements
    assert "stripe" not in requirements
    assert "ocr" not in requirements


def test_execution_source_has_no_random_or_prohibited_integration_imports() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for folder in APPLICATION_SOURCE
        for path in folder.rglob("*.py")
    ).lower()
    source += (ROOT / "app" / "runtime.py").read_text(encoding="utf-8").lower()

    prohibited = (
        "import random",
        "from random",
        "import kafka",
        "from kafka",
        "import stripe",
        "from stripe",
        "import requests",
        "from requests",
    )
    assert all(fragment not in source for fragment in prohibited)
