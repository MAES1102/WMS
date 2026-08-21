# CR-003 - Purchase Request Approval Reference Workflow

| Field | Value |
|---|---|
| Category | Final product clarification and documentation reconciliation |
| Trigger | Earlier demonstrations did not communicate workflow-management value clearly |
| Implemented response | Apply the preserved workflow core to structured Purchase Request Approval |
| Status | Implemented and verified in the repository |
| Academic status | Final academic acceptance remains the professor's decision |

## Evolution context

The earliest implementation demonstrated workflow nodes, conditional transitions, retries, and two execution styles with an abstract scenario. That version was technically useful but node-focused: a viewer could see execution progress without immediately understanding the organizational problem, responsible user, or useful result.

The professor's difficulty understanding the product value was treated as actionable feedback. The professor approved the Event-Driven Workflow Management System direction and accepted orchestration and choreography as the two complex functionalities. The repository does not claim that every later scenario or architecture decision received separate approval.

An intermediate Invoice Approval direction introduced uploaded PDF processing. It made the example more concrete, but file handling, storage safety, format readability, and PDF-specific validation drew attention away from the central Software Engineering subject: configurable workflows, persistent human work, safe continuation, retries, control ownership, and audit evidence.

## Final project correction

Purchase Request Approval was selected as the final reference workflow. A requester submits structured fields; the system validates the request, creates persistent approval work, waits for one manager decision, resumes the same run, and records an internal Purchase Authorization or a controlled negative outcome. An Internal Notification and ordered trace make the result observable.

This scenario is a final design decision used to explain the professor-approved system direction. It does not imply that the professor explicitly approved this exact workflow or each final implementation choice.

## Preserved workflow core

- directed-graph validation with deterministic issue ordering;
- `SUCCESS`, `FAILURE`, and `ALWAYS` transition precedence;
- bounded retry of retryable automatic failures before routing;
- immutable workflow revisions;
- run-specific state, cursor versioning, and isolation;
- centralized orchestration;
- synchronous run-scoped EventBus choreography;
- persistent human wait and same-run resume;
- idempotent approval decisions and conflict detection;
- transactionally ordered audit trace;
- recovery from committed cursor state after restart.

## Removed intermediate components

The active product no longer contains Invoice domain services, uploaded-file endpoints, PDF parsing, file validation, file persistence, file cleanup, or file identity fields. The PDF-oriented application modules, dependencies, UI, tests, and screenshots were removed. Historical references remain only in evolution explanations such as this one.

## Changed artifacts

| Area | Implemented correction |
|---|---|
| Requirements | Reframed submission as structured JSON/form data and aligned states, task types, NFRs, constraints, and acceptance criteria. |
| Architecture | Reconciled one FastAPI application, SQLite persistence, transient EventBus semantics, revisions, cursor, attempts, approval records, authorization, notification, and trace. |
| UI | Replaced the earlier demonstration with Submit Request, Approver Inbox, Run Status/History, and bounded Workflow Designer views. |
| Tests | Consolidated around Purchase Request rules, workflow algorithms, paired modes, persistence, API journeys, isolation, restart, and deployment evidence. |
| UML | Updated context, components, domain ownership, run state, routing/retry, sequences, and deployment. |
| Report | Rebuilt as a standalone Software Engineering report with claim classification, traceability, verification, limitations, and defense evidence. |

## Reference scenarios

| Scenario | Expected result |
|---|---|
| Valid and approved | `AUTHORIZED`, Purchase Authorization and Internal Notification recorded. |
| Valid and rejected | `REJECTED`, reason recorded, authorization skipped. |
| Invalid structured fields | `VALIDATION_FAILED`, no approval work item. |
| Temporary authorization failure | Bounded retry, then authorization success. |
| Authorization unavailable | Attempt bound exhausted and `NEEDS_MANUAL_ACTION`. |
| Restart at human wait | New application process resumes the same persisted run after the decision. |

## Acceptance boundary

Implementation and automated evidence demonstrate the correction in the repository. Final academic acceptance, grading, and any decision to extend the scope remain the professor's responsibility.
