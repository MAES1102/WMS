from pathlib import Path
ROOT=Path(__file__).parents[2]
def test_single_service_container_inventory():
    compose=(ROOT/'docker-compose.yml').read_text(); docker=(ROOT/'Dockerfile').read_text()
    assert compose.count('  app:\n')==1 and 'workflow_data:/data' in compose
    assert 'WORKFLOW_DATABASE_URL: sqlite:////data/workflow.db' in compose
    assert 'kafka' not in compose.lower() and 'USER app' in docker and 'HEALTHCHECK' in docker
def test_primary_launcher_and_obsolete_runtime():
    assert '--reload' not in (ROOT/'scripts/run_local.sh').read_text()
    obsolete=('app/domain/invoice.py','app/infrastructure/pdf.py','app/infrastructure/documents.py','app/application/document_ports.py','app/static/invoices.html')
    assert all(not (ROOT/p).exists() for p in obsolete)
    assert 'pypdf' not in (ROOT/'requirements.txt').read_text().lower()
