# Invoice Approval Workflow

An explainable invoice-processing application built for the Software Engineering course. A user submits an invoice PDF, the system validates it, pauses for a human decision, archives approved documents, records failures, and preserves an ordered audit trail.

The application answers a concrete business question: **what happened to this invoice, why, and what should happen next?** Orchestration and choreography are two internal coordination strategies applied to the same business process.

## Business process

| Step | Responsibility | Observable result |
|---|---|---|
| Validate invoice | Check metadata and the stored PDF | Valid invoice or controlled validation failure |
| Human approval | Create a persistent work item | Waiting, approved, or rejected |
| Archive document | Preserve an approved document identity | Archived, retried, or sent to manual action |
| Notify result | Record the final outcome | One persistent notification |

The dashboard demonstrates five cases without random behavior:

1. valid invoice approved;
2. valid invoice rejected;
3. invalid PDF rejected before approval;
4. archive fails once and succeeds on retry;
5. archive remains unavailable and the invoice requires manual action.

## Local start

Python 3.12 or 3.13 is recommended. Keeping the virtual environment outside the repository prevents file watchers and IDE indexing from scanning thousands of dependency files.

```bash
cd /path/to/SE_M
python3.13 -m venv ~/.virtualenvs/SE_M
source ~/.virtualenvs/SE_M/bin/activate
python -m pip install -r requirements.txt
./scripts/run_local.sh
```

Open:

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/ui` | Submit, decide, inspect, and configure invoice workflows |
| `http://127.0.0.1:8000/docs` | OpenAPI documentation |

Stop the server with `Ctrl-C`. Normal execution does not watch the repository, so startup and shutdown stay predictable. For active development only:

```bash
./scripts/run_local.sh --reload --reload-dir app
```

Set another port without editing files: `PORT=8080 ./scripts/run_local.sh`.

On first startup the application creates `invoice.db` and `invoice_documents/`. Both are local runtime data ignored by Git.

## Five-minute demonstration

1. Open `/ui`, keep **Standard processing**, choose a mode, enter unique invoice metadata, and upload a readable PDF.
2. Start the process. Show validation completing and the run stopping at **Waiting for approval**.
3. Approve the work item. Show the archived document, final notification, and ordered trace.
4. Repeat in the other execution mode to show the same business result under a different control strategy.
5. Select **Archive fails once, then succeeds** and show the bounded retry.
6. Select **Archive remains unavailable** and show the controlled `NEEDS_MANUAL_ACTION` result.
7. Open **Workflow constructor**, modify a draft within the closed four-task catalog, validate it, and activate a new immutable revision.

Use a unique invoice number for every submission. A valid sample PDF is the generated report at `output/pdf/invoice-approval-final-report.pdf`.

## Design

The application is a modular monolith with explicit boundaries:

```text
Browser / HTTP API
        ↓
Presentation adapters
        ↓
Submission · approval · execution · status query
        ↓
Shared automatic-step service
        ↓
Retry policy · transition resolver · atomic effects
        ↓
SQLite · controlled document storage
```

Key guarantees:

- activated workflow revisions are immutable;
- definition state and run state are separate;
- human decisions are persistent, one-time, and never automatically retried;
- retries repeat the current automatic task before any transition is selected;
- orchestration and choreography share executors, retry rules, and persistence;
- choreography subscriptions are run-scoped and removed at waiting or terminal state;
- attempts, transitions, business effects, and trace entries are persisted atomically;
- the constructor accepts only four built-in task types, never scripts or plugins.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v3/invoices` | Submit an invoice and execute until waiting or terminal |
| `GET` | `/api/v3/runs/{run_id}` | Read business state and the ordered trace |
| `GET` | `/api/v3/approvals` | List pending human work |
| `POST` | `/api/v3/approvals/{id}/decision` | Decide once and resume the same run |
| `GET/POST` | `/api/v3/workflows/drafts` | List or create bounded drafts |
| `GET/PUT/DELETE` | `/api/v3/workflows/drafts/{id}` | Manage an eligible draft |
| `POST` | `/api/v3/workflows/validate` | Validate a definition without activation |
| `POST` | `/api/v3/workflows/drafts/{id}/activate` | Create an immutable active revision |

The `/api/v3` prefix is the published API contract version. It does not denote a second application.

## Verification

```bash
source ~/.virtualenvs/SE_M/bin/activate
python -m pytest tests/ -q
```

The suite uses in-memory or disposable file-backed SQLite databases and temporary document directories. It covers domain validation, PDF safety, submission, approval idempotency, both coordination modes, deterministic fault scenarios, retry exhaustion, exact trace order, restart/resume, run isolation, constructor revision rules, deployment inventory, startup hygiene, and UI structure.

## Container start

```bash
docker compose up --build
```

The deployment contains one application service and one persistent data volume. Open `http://127.0.0.1:8000/ui`; stop with `Ctrl-C`, then `docker compose down`.

## Submission artifacts

- [Requirements](docs/requirements/requirements.md)
- [Requirements traceability](docs/requirements/traceability.md)
- [Architecture overview](docs/architecture/overview.md)
- [Architecture decisions](docs/architecture/decisions.md)
- [Change request CR-002](docs/evolution/CR-002-invoice-approval-reference-application.md)
- [Development process](docs/process/development-process.md)
- [Final report source](docs/FINAL_REPORT.md)
- [Final report PDF](output/pdf/invoice-approval-final-report.pdf)
- [Defense script](docs/DEFENSE_SCRIPT.md)
- [Reuse disclosure](docs/REUSE_DISCLOSURE.md)
