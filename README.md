# Event-Driven Workflow Management System

A bounded workflow-management application for a small organization. The reference workflow is **Purchase Request Approval**: a requester submits structured business data, a manager receives persistent approval work, and the same run resumes after a decision or process restart. Approved requests create an internal `PurchaseAuthorization`; no order or payment is performed.

The reusable core provides immutable workflow revisions, graph validation, deterministic routing, bounded retry, persistent waiting, an ordered audit trace, centralized orchestration, and run-scoped synchronous EventBus choreography.

## Primary local start

```bash
python3.13 -m venv ~/.virtualenvs/SE_M
source ~/.virtualenvs/SE_M/bin/activate
python -m pip install -r requirements.txt
./scripts/run_local.sh
```

Open `http://127.0.0.1:8000/ui`; API documentation is at `/docs`. Stop with `Ctrl-C`. Development reload is explicit: `./scripts/run_local.sh --reload --reload-dir app`.

The application creates `workflow.db`. Old Invoice Approval development data is incompatible and is not migrated.

## Product views

1. **Submit Request** — structured requester, department, item/service, supplier, amount, currency, justification, and required date.
2. **Approver Inbox** — persistent pending work with full decision context.
3. **Run Status / History** — business result, next action, authorization, notification, and ordered trace.
4. **Workflow Designer** — a bounded four-task catalog with validation and immutable activation.

Execution mode and deterministic failure selection are isolated in a collapsed **Demonstration Controls** panel. Choreography is synchronous and in-process; no broker or microservices are used.

## API

- `POST /api/requests`
- `GET /api/approvals`
- `GET /api/approvals/{work_item_id}`
- `POST /api/approvals/{work_item_id}/decision`
- `GET /api/runs/{run_id}`
- workflow operations under `/api/workflows`

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -q
```

## Optional container start

`Dockerfile` builds the one application image. `docker-compose.yml` starts that image with port mapping and a persistent SQLite volume; it is not a second Dockerfile. Docker is optional; local startup is the primary defense path.

```bash
docker compose up --build
```

## Authoritative artifacts

- [Requirements](docs/requirements/requirements.md)
- [Traceability](docs/requirements/traceability.md)
- [Architecture](docs/architecture/overview.md)
- [Decisions](docs/architecture/decisions.md)
- [Evolution](docs/evolution/CR-003-purchase-request-reference-workflow.md)
- [Reuse disclosure](docs/REUSE_DISCLOSURE.md)
- [Defense script](docs/DEFENSE_SCRIPT.md)
- [Final report](output/pdf/event-driven-workflow-management-system.pdf)
