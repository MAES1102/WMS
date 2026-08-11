# Event-Driven Workflow Management System

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green)
![Tests](https://img.shields.io/badge/tests-27%20passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A Python REST API and browser dashboard implementing two workflow execution patterns side-by-side:

- **Orchestration** — central controller drives every task in sequence; fail-fast on first error
- **Choreography** — each task triggers the next by emitting an event; no central coordinator

Workflows are modelled as a **directed graph** (`WorkflowTransition` edges), not just a flat ordered list: tasks can branch on `SUCCESS`/`FAILURE`/`ALWAYS`, and edges may loop back to an earlier task (e.g. a payment retry). Both execution modes share the same `TransitionResolver` so branching/looping behave identically whether run centrally or reactively. Workflows with no transitions defined keep the original linear `order`-based behavior (fully backward compatible).

Built as a Software Engineering semester project (Scrum, 3 × 1-week sprints).  
Full project report: `docs/REPORT.md`

---

## Architecture Overview

```
POST /execute/{id}          →  orchestrator.py  →  task_runner.py (loop)
POST /execute_choreo/{id}   →  choreography.py  →  EventBus / Kafka  →  task_runner.py (handlers)
```

```
app/
├── main.py            FastAPI app entry point
├── db.py              SQLAlchemy engine + PRAGMA foreign_keys=ON
├── models.py          ORM models: User, Workflow, WorkflowRun, Task, WorkflowTransition
├── routes.py          All REST endpoints (CRUD + transitions + execution + logs + UI)
├── engine/
│   ├── orchestrator.py    Central-controller: graph traversal (with legacy order fallback)
│   ├── choreography.py    Reactive handler-chain execution (graph-aware via TransitionResolver)
│   ├── transitions.py     TransitionResolver: graph lookups, start-node detection, loop-limit constant
│   ├── task_runner.py     Atomic task execution, retry simulation, event emission
│   └── events.py          In-memory EventBus + optional Kafka producer/consumer
└── static/
    └── index.html     Browser dashboard (polling, branching canvas graph, execution controls)

scripts/
├── seed_all_demos.py           Seeds all three demo workflows in one command
├── seed_payment_workflow.py    Payment Workflow — decision gateway + retry loop
├── seed_order_delivery.py      Order Delivery Workflow — branching on inventory check
└── seed_document_approval.py  Document Approval Workflow — review/revise loop
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| API Framework | FastAPI + Uvicorn |
| ORM / Database | SQLAlchemy 2.0 + SQLite |
| Event Transport | In-memory EventBus (Kafka optional) |
| Containerisation | Docker Compose (app + Kafka + Zookeeper) |
| Testing | pytest + httpx (21 integration tests) |

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the server

```bash
uvicorn app.main:app --reload
```

| URL | Description |
|---|---|
| `http://localhost:8000/ui` | Interactive browser dashboard |
| `http://localhost:8000/docs` | Auto-generated OpenAPI / Swagger UI |
| `http://localhost:8000/` | Health check |

### 3. (Optional) Seed demo workflows

```bash
python -m scripts.seed_all_demos
```

Seeds all three demo workflows under `demo@payment.com`, demonstrating the engine is domain-independent:

| Workflow | Graph features |
|---|---|
| **Payment Workflow** | Decision gateway (Fraud Check → Capture/Cancel) + retry loop (Capture ↔ Retry) |
| **Order Delivery Workflow** | Conditional branch on inventory check result (Package → Ship or Notify Customer) |
| **Document Approval Workflow** | Review/revise loop (Review → Request Changes → Review) until approved |

Open `/ui` after seeding — all three workflows appear in the selector, the graph canvas renders each one's branching structure, and both execution modes work unchanged.

### 4. Run with Docker (includes Kafka)

```bash
docker-compose up
```

Starts three services: the FastAPI app on port 8000, Zookeeper on 2181, and Kafka on 9092. The app waits for Kafka to be healthy. Kafka is optional — the app falls back to the in-memory EventBus automatically.

---

## Running Tests

```bash
pytest tests/ -v
```

Expected output (27 tests, 0 failures) — includes `tests/test_workflow_graph.py`, which covers conditional branching, the FAILURE/retry path, a retry loop, the `MAX_LOOP_ITERATIONS` safety valve, and graph-based choreography:

```
tests/test_execution.py::test_execute_nonexistent_workflow_returns_404       PASSED
tests/test_execution.py::test_execute_choreo_nonexistent_workflow_returns_404 PASSED
tests/test_execution.py::test_orchestrated_workflow_success                  PASSED
tests/test_execution.py::test_orchestrated_workflow_halts_on_failure         PASSED
tests/test_execution.py::test_choreography_success                           PASSED
tests/test_execution.py::test_choreography_stops_on_failure                  PASSED
tests/test_execution.py::test_execute_empty_workflow_completes               PASSED
tests/test_execution.py::test_execute_choreo_empty_workflow_completes        PASSED
tests/test_execution.py::test_workflow_run_history_recorded                  PASSED
tests/test_users.py::test_create_user_success                                PASSED
tests/test_users.py::test_duplicate_email_returns_409                        PASSED
tests/test_workflow_graph.py::test_conditional_success_path                  PASSED
tests/test_workflow_graph.py::test_failure_branch_execution                  PASSED
tests/test_workflow_graph.py::test_workflow_loop_retry                       PASSED
tests/test_workflow_graph.py::test_loop_limit_prevents_infinite_execution    PASSED
tests/test_workflow_graph.py::test_choreography_transition_based_execution   PASSED
tests/test_workflow_graph.py::test_max_loop_iterations_constant_is_reasonable PASSED
tests/test_workflows.py::test_create_workflow                                PASSED
tests/test_workflows.py::test_duplicate_task_order_returns_409               PASSED
tests/test_workflows.py::test_list_tasks_returns_only_existing               PASSED
tests/test_workflows.py::test_delete_task_reorders_remaining                 PASSED
tests/test_workflows.py::test_delete_workflow_not_found                      PASSED
tests/test_workflows.py::test_get_task_not_found                             PASSED
tests/test_workflows.py::test_delete_task_not_found                          PASSED
tests/test_workflows.py::test_workflow_status_summary                        PASSED
tests/test_workflows.py::test_workflow_status_not_found                      PASSED
tests/test_workflows.py::test_delete_workflow_cascades_tasks                 PASSED
```

Tests use an in-memory SQLite database (`StaticPool`) and mock `random.random` for deterministic failure paths. No Kafka broker required.

---

## API Endpoints

| Method | Path | Description | Status Codes |
|---|---|---|---|
| `GET` | `/` | Health check | 200 |
| `GET` | `/ui` | Browser dashboard | 200 |
| `POST` | `/users` | Create user account | 200, 409 |
| `GET` | `/users` | List all users | 200 |
| `POST` | `/workflows` | Create workflow | 200 |
| `GET` | `/workflows` | List all workflows | 200 |
| `DELETE` | `/workflows/{id}` | Delete workflow + all its tasks | 200, 404 |
| `GET` | `/workflows/{id}/status` | Workflow task status summary | 200, 404 |
| `POST` | `/tasks` | Create task in workflow | 200, 409 |
| `GET` | `/tasks` | List all tasks | 200 |
| `GET` | `/tasks/{id}` | Get single task | 200, 404 |
| `DELETE` | `/tasks/{id}` | Delete task (auto-renumbers remaining) | 200, 404 |
| `POST` | `/workflows/{id}/transitions` | Create a graph edge (from_task, to_task, condition, priority) | 200, 404, 422 |
| `GET` | `/workflows/{id}/transitions` | List transitions for a workflow | 200, 404 |
| `DELETE` | `/transitions/{id}` | Delete a transition edge | 200, 404 |
| `GET` | `/workflow_runs/{workflow_id}` | List execution history for a workflow | 200 |
| `POST` | `/execute/{workflow_id}` | Execute workflow (orchestration mode) | 200, 404 |
| `POST` | `/execute_choreo/{workflow_id}` | Execute workflow (choreography mode) | 200, 404 |
| `GET` | `/logs` | Get structured backend execution logs | 200 |

---

## Project Report

The complete project report (requirements, Scrum artifacts, UML diagrams, architecture analysis, NFR verification, and testing) is consolidated in a single document:

**`docs/REPORT.md`** — all 23 sections plus three appendices, 15 embedded UML diagrams, RTM, and sprint backlogs

---

## Building the PDF Report

`build_pdf.py` generates `REPORT_FINAL.pdf` from `docs/REPORT.md`. It requires:

| Tool | Install |
|---|---|
| `plantuml.jar` (v1.2024+) | Download from [plantuml.com](https://plantuml.com/download) and place in project root |
| Mermaid CLI (`mmdc`) | `npm install` in project root (reads `package.json`) |
| Pandoc | `brew install pandoc` |
| WeasyPrint | `pip install weasyprint` |

```bash
npm install                          # install mmdc
python build_pdf.py                  # renders all 13 diagrams, builds PDF
```

> **Note:** The generated PDF (`REPORT_FINAL.pdf`) and rendered diagram images (`docs/figures/*.png`) are git-ignored. They are build artifacts.

---

## Known Limitations

- Passwords stored in plaintext — add `passlib[bcrypt]` for production use
- No authentication on any endpoint — add JWT middleware for production use
- Execution blocks the HTTP thread — use `BackgroundTasks` or Celery for async execution
- `execution_logs` is an in-memory ring buffer (max 100 entries); not persistent across restarts