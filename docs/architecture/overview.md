# Event-Driven Workflow Management System - Architecture Overview

| Field | Value |
|---|---|
| Status | Implemented and verified |
| Requirements baseline | [Requirements](../requirements/requirements.md) |
| Change record | [CR-003](../evolution/CR-003-purchase-request-reference-workflow.md) |
| Deployment | One modular FastAPI application, one SQLite database |

## 1. System boundary

The product controls one repeatable approval process. A requester submits structured Purchase Request data, an approver decides persistent work, a process owner configures a bounded workflow, and an evaluator can inspect business state and execution evidence. The application produces internal Purchase Authorization and Internal Notification records. It does not place orders, transfer money, reserve budgets, contact suppliers, send email, or integrate with ERP/accounting systems.

The deployable boundary is one FastAPI process plus one SQLite database. An optional Docker Compose file runs the same single application service with a persistent volume. There is no external workflow engine, message broker, or second service.

## 2. Architectural style

The implementation is a layered modular monolith.

| Layer | Responsibility |
|---|---|
| Presentation | FastAPI routes, Pydantic request/response translation, and the four-view browser UI. |
| Application | Submission, automatic step execution, approval lifecycle, orchestration, choreography, recovery, constructor, and queries. |
| Domain | Purchase Request validation, workflow graph rules, transition resolution, retry eligibility, and controlled enums/value objects. |
| Persistence/infrastructure | SQLAlchemy models and repositories, transaction boundaries, SQLite configuration, synchronous EventBus, and deterministic demonstration fault adapter. |

Dependencies point toward application and domain policy. Routes do not implement workflow routing, and the EventBus is never authoritative state.

## 3. Component responsibilities

| Component | Implemented responsibility |
|---|---|
| Submission service | Validate the submission boundary, create the Purchase Request and run, and invoke the selected strategy. |
| Workflow constructor | Create/update/delete drafts, validate bounded definitions, and activate immutable revisions. |
| Graph validator | Reject invalid start/terminal structure, missing references, unreachable tasks, cycles, unsafe task configuration, and ambiguous routing. |
| Automatic executor registry | Map one of three automatic task types to controlled application executors. |
| Automatic step service | Execute and persist attempts, apply bounded retry, call the shared resolver, commit effects/cursor/trace, and report the next state. |
| Human approval service | Create or retrieve one pending work item, persist waiting, validate decisions, enforce idempotency/conflict rules, and resume the same run. |
| Orchestrator | Centrally advance committed steps until waiting or terminal. |
| Choreographer | Temporarily subscribe a run-scoped handler and synchronously trigger committed steps until waiting or terminal. |
| Run query service | Return request state, run/cursor status, approval result, authorization, notification, attempts, and ordered trace. |
| Persistence unit of work | Commit each observable business/execution step consistently in SQLite. |

## 4. Closed task catalog

| Task type | Kind | Meaning |
|---|---|---|
| `REQUEST_VALIDATION` | Automatic | Validate structured Purchase Request fields and produce success or business failure. |
| `HUMAN_APPROVAL` | Human | Persist work and wait for approve/reject input; no automatic attempt is created. |
| `PURCHASE_AUTHORIZATION` | Automatic | Create an internal authorization after approval or expose deterministic retry/manual-action behavior. |
| `CREATE_NOTIFICATION` | Automatic | Persist an internal status message; it does not send email. |

## 5. Persistence ownership

SQLite stores mutable workflow drafts and their task/transition rows; immutable workflow revisions and their snapshots; Purchase Requests; workflow runs; versioned execution cursors; automatic task attempts; approval work items and decisions; Purchase Authorizations; Internal Notifications; and run-local ordered trace entries.

A run references exactly one immutable revision and one Purchase Request. Runtime state belongs to the run/cursor rather than the reusable task definition. Each trace entry receives a run-local position inside the transaction, so ordering does not depend on timestamp precision.

Important uniqueness and consistency rules include one cursor per run, one attempt ordinal per run/task, one work item per run/human task, one authoritative decision per work item, and one trace position per run. State-version checks prevent stale continuation from advancing the cursor.

## 6. Execution contract

Automatic executors return `TaskResult` with `SUCCESS` or `FAILURE`; a failure also carries `BUSINESS`, `RETRYABLE_TECHNICAL`, or `NON_RETRYABLE_TECHNICAL` classification and an optional reason. Retry is evaluated before transition selection. A retryable technical failure below the positive attempt bound repeats the same task and selects no edge. Business failure, non-retryable failure, or exhausted retry enters normal transition resolution.

The resolver first considers the edge matching the final outcome, then an `ALWAYS` fallback. If neither exists, success becomes a successful terminal and failure becomes an unsuccessful terminal. Equal-precedence ambiguity is rejected during definition validation.

## 7. Persistent human wait and resume

When the cursor reaches `HUMAN_APPROVAL`, the application creates or retrieves the unique work item, updates request/run/cursor state to waiting, records trace observations, commits, and returns. No database transaction, HTTP request, or EventBus subscription remains open.

An approval decision is validated and committed against the work item. Repeating an identical decision returns the established result; a different decision conflicts and cannot mutate the run. The cursor resumes on the outcome appropriate to approve or reject and the coordinator invokes the original run's stored execution mode.

## 8. Orchestration and choreography

Orchestration uses a central application loop. It repeatedly reads the shared step result and advances until waiting or terminal. This makes control ownership explicit and easy to trace.

Choreography registers one handler keyed to the active run, publishes a synchronous `AdvanceRun` trigger carrying stable run identity and expected state version, and removes the handler at waiting, terminal state, or error. The next handler scope is reconstructed after a decision or recovery. The EventBus does not persist events, perform asynchronous delivery, coordinate services, or provide exactly-once transport.

Both strategies use the same revision, executor registry, retry policy, resolver, unit of work, approval service, and business effects. Their comparison is limited to control ownership inside one process.

## 9. Workflow Designer and immutable activation

The designer accepts task keys/names, exactly one start marker, the four task types, `SUCCESS`/`FAILURE`/`ALWAYS` transitions, and positive maximum-attempt values for automatic tasks. Validation precedes activation. Activation copies the accepted draft into an immutable revision; existing runs are never redirected when a later draft changes.

Arbitrary code, scripts, expressions, plugins, unknown task types, cycles, parallel fork/join, nested workflows, and general BPMN semantics are excluded.

## 10. Run-state model and recovery

The cursor phase is `READY`, `WAITING_FOR_APPROVAL`, or `TERMINAL`; the run records its broader status and execution mode. A committed `READY` cursor can be re-entered by recovery after application restart. A waiting cursor resumes only through the approval decision use case. A terminal cursor cannot advance.

The restart tests start a real Uvicorn process, create a waiting run, terminate the process, start another process against the same isolated database, submit the decision, and verify that the same run reaches `AUTHORIZED`. The sequence is covered in both modes.

## 11. Deployment view

The local command starts Uvicorn and points SQLAlchemy at `WORKFLOW_DATABASE_URL` or the default `workflow.db`. Compose supplies `sqlite:////data/workflow.db` and one named persistent volume. This is a local academic deployment topology, not evidence of high availability, horizontal scaling, or production operations.

## 12. 4+1 UML views

| View | Sources |
|---|---|
| Logical | [domain-model.puml](./uml/domain-model.puml), [run-state.puml](./uml/run-state.puml) |
| Process | [orchestration-sequence.puml](./uml/orchestration-sequence.puml), [choreography-sequence.puml](./uml/choreography-sequence.puml), [routing-retry-activity.puml](./uml/routing-retry-activity.puml) |
| Development | [component-view.puml](./uml/component-view.puml) |
| Physical | [deployment-view.puml](./uml/deployment-view.puml) |
| Scenarios | [system-context-use-cases.puml](./uml/system-context-use-cases.puml) plus both sequence views |

## 13. Limitations

The architecture has no authentication/RBAC, external procurement integration, durable broker, distributed services, parallel graph execution, high availability, measured performance, or production security evidence. SQLite and synchronous in-process event dispatch are appropriate to the bounded academic scope but are not presented as universal production choices.

## Related records

- [Architecture decisions](./decisions.md)
- [Architecture traceability](./traceability.md)
- [Requirements](../requirements/requirements.md)
- [CR-003](../evolution/CR-003-purchase-request-reference-workflow.md)
