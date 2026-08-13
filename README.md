# Invoice Approval Workflow

A bounded invoice-processing application that demonstrates how a real business process can be executed through a workflow engine.

The user submits an invoice PDF and metadata. The system validates the input, pauses for a human decision, archives an approved document, records failures that need manual action, creates a final notification, and preserves an ordered audit trace.

The business result is the purpose of the application. Orchestration and choreography are two internal coordination strategies evaluated over the same process.

## What the application does

The reference workflow is intentionally small and explainable:

1. **Validate invoice** — checks required metadata and whether the stored file is a readable PDF.
2. **Human approval** — creates a persistent work item and safely stops the run while waiting.
3. **Archive document** — preserves the approved document identity and retries bounded technical failures.
4. **Notify result** — records one notification describing the final business state.

The process supports these observable outcomes:

| Input or decision | Result |
|---|---|
| Valid invoice + approval | Document archived; notification created |
| Valid invoice + rejection | Rejection and reason recorded; archive skipped |
| Invalid metadata or PDF | Validation failure recorded; approval skipped |
| Temporary archive failure | Archive retried within its configured bound |
| Exhausted archive failure | Invoice marked `NEEDS_MANUAL_ACTION` |

## Run it

Python 3.12+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

| URL | Purpose |
|---|---|
| `http://127.0.0.1:8000/ui` | Invoice submission, approval, result, audit trace, and bounded workflow constructor |
| `http://127.0.0.1:8000/docs` | OpenAPI documentation |
| `http://127.0.0.1:8000/legacy-ui` | Preserved pre-CR-002 workflow prototype |

On first startup the application creates:

- `invoice_v3.db` — isolated invoice runtime database;
- `invoice_documents/` — controlled PDF storage using generated identities;
- the bounded four-task reference workflow.

The older `workflow.db` and legacy endpoints remain separate during the controlled transition.

## Demonstration path

1. Open `/ui`.
2. Enter supplier, invoice number, date, amount, and currency.
3. Upload a readable PDF and start the process.
4. Observe that validation completes and the run stops at **Waiting for approval**.
5. Approve or reject the invoice.
6. Observe the final business state, notification, and technical audit trace.

This sequence shows why the system exists before discussing its coordination architecture.

Use the **Execution mode** selector to repeat the same invoice case through centralized orchestration or run-scoped choreography. The resulting business path is the same; the selected mode remains visible beside the run identity.

The lower **Workflow constructor** panel can edit safe invoice workflow drafts, validate the graph, and activate an immutable revision. It supports only the four built-in invoice task types and never accepts scripts or plugins.

## Architecture

The new invoice path is a modular monolith with explicit boundaries:

```text
Browser / API
    ↓
Presentation adapters
    ↓
Submission · approval · execution coordinator · status query
    ↓
Shared automatic-step service
    ↓
Retry policy → transition resolver → atomic persistence effects
    ↓
SQLite + controlled document storage
```

Important properties:

- workflow revisions are immutable after activation;
- definition state is separate from run state;
- retries repeat the current automatic task without selecting an edge;
- human decisions are persistent and idempotent, never automatically retried;
- orchestration stops at waiting instead of blocking an HTTP request;
- choreography uses temporary run-keyed events and removes every subscriber at waiting, terminal state, or error;
- archive, notification, cursor, attempt, and trace changes use transaction boundaries;
- user-entered executable code and arbitrary BPMN behavior are outside scope.

## Current implementation status

| Increment | Status |
|---|---|
| Domain validation, routing, retry, and isolated persistence | Implemented and tested |
| Bounded submission and PDF validation | Implemented and tested |
| Persistent human approval and same-run resume | Implemented and tested |
| Centralized invoice orchestration | Implemented; five business scenarios tested |
| Visible invoice runtime and browser path | Integrated; reference Chromium desktop/mobile path accepted |
| Run-scoped choreography and paired-mode parity | Implemented; five scenarios pass in both modes |
| Bounded workflow constructor and immutable revision activation | Implemented and tested |
| Repeatability, restart, isolation, PDF, trace, and status-read matrix | Implemented and tested in isolated reference environments |
| Single-service deployment inventory and process restart | Verified; container image build not claimed |
| Final report reconciliation | Completed at project level; Git durability and instructor approval not claimed |

## Main v3 API

| Method | Endpoint | Result |
|---|---|---|
| `POST` | `/api/v3/invoices` | Store and validate an invoice, then run until waiting or terminal |
| `GET` | `/api/v3/approvals` | List pending approval work |
| `GET` | `/api/v3/approvals/{work_item_id}` | Inspect one approval item |
| `POST` | `/api/v3/approvals/{work_item_id}/decision` | Decide once and resume the same run |
| `GET` | `/api/v3/runs/{run_id}` | Retrieve invoice, approval, archive, notification, run, and trace state |
| `GET/POST` | `/api/v3/workflows/drafts` | List or create bounded workflow drafts |
| `GET/PUT/DELETE` | `/api/v3/workflows/drafts/{draft_id}` | Retrieve, replace, or delete one eligible draft |
| `POST` | `/api/v3/workflows/validate` | Validate a form-bounded definition without activating it |
| `POST` | `/api/v3/workflows/drafts/{draft_id}/activate` | Create a new immutable active revision |

Legacy CRUD/execution endpoints remain available during the transition and are not the primary demonstration path.

## Tests

```bash
pytest -q
```

The test suite uses in-memory and disposable file-backed SQLite plus disposable document directories. It covers domain rules, storage/PDF boundaries, persistence transactions, HTTP validation, human-decision idempotency, both control strategies, scenario parity and repeatability, exact trace completeness, controlled engine and OS-process restart, threaded run isolation, status-read timing, EventBus cleanup, bounded draft CRUD, constructor validation, immutable revision history, deployment inventory, and UI structure/accessibility hooks. The current isolated run reports **220 passing tests**.

## Project records

- [Requirements v3](docs/requirements/requirements-v3.md)
- [Architecture overview v3](docs/architecture/architecture-overview-v3.md)
- [Architecture decisions v3](docs/architecture/architecture-decisions-v3.md)
- [CR-002 product-purpose correction](docs/evolution/CR-002-invoice-approval-reference-application.md)
- [E20 orchestration record](docs/implementation/pbi-e20-invoice-orchestration-record.md)
- [E21 choreography record](docs/implementation/pbi-e21-invoice-choreography-record.md)
- [E22 bounded constructor record](docs/implementation/pbi-e22-workflow-constructor-record.md)
- [E23 acceptance and quality matrix](docs/implementation/pbi-e23-quality-matrix-record.md)
- [E24 browser acceptance](docs/implementation/pbi-e24-browser-acceptance-record.md)
- [E25 deployment verification](docs/implementation/pbi-e25-deployment-verification-record.md)
- [Final report source](docs/FINAL_REPORT.md)
- [Generated final report PDF](output/pdf/invoice-approval-final-report.pdf)
- [Reuse and reference disclosure](docs/REUSE_DISCLOSURE.md)
- [Defense script](docs/DEFENSE_SCRIPT.md)
- [E26 final reconciliation](docs/implementation/pbi-e26-final-reconciliation-record.md)

The earlier consolidated report in `docs/REPORT.md` documents the preserved prototype. It is superseded for submission by the invoice-specific final report above and remains only as historical evidence.
