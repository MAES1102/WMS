# Requirements v3 — Bounded Invoice-Approval Workflow

| Field | Value |
|---|---|
| Document | Requirements v3 — Bounded Invoice-Approval Workflow |
| Status | `APPROVED — project-level Requirements v3 baseline` |
| Version | `3.0` |
| Source change request | [CR-002](../evolution/CR-002-invoice-approval-reference-application.md) |
| Controlled implementation base | `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` |
| Draft date | `2026-08-13` |
| Approval date | `2026-08-13` |
| Approval status | `APPROVED AT PROJECT LEVEL — no instructor approval claimed` |
| Implementation status | `PBI-E18 IN PROGRESS — E18.1 ACCEPTED` |
| Release status | `NOT SCHEDULED` |

CR-002 was approved at project level for progression to this requirements version. Requirements v3 passed substantive project review after identifier, atomicity, boundary, scenario, risk, and bidirectional-traceability checks. No instructor approval is claimed. Requirements v2 remains the historical approved baseline; Requirements v3 is now the current project-level specification baseline. The separately reviewed architecture v3 baseline is the current design baseline.

## 1. Purpose

The system is a workflow-management application demonstrated through one bounded invoice-approval use case. A submitter supplies an invoice PDF and metadata. The system validates the submission, waits for one human decision when validation succeeds, archives an approved invoice or records a controlled non-approved result, creates an internal notification, and preserves an ordered audit trace.

The same accepted workflow revision is executable through centralized orchestration or run-scoped in-memory choreography. The useful result is invoice processing; comparison of the two coordination styles is the architectural contribution demonstrated after the user outcome is visible.

## 2. Actors and user goals

| Actor | User goal |
|---|---|
| Submitter | Submit an invoice and see its validation, approval, archive, failure, and notification state. |
| Approver | See a pending work item, inspect the submitted information, and approve or reject it once. |
| Workflow operator | Configure and validate a bounded invoice workflow, select an execution mode, and inspect runs and trace. |
| Academic evaluator | Follow one understandable invoice outcome and compare both execution modes using equivalent evidence. |

The roles are logical demonstration roles. Authentication, authorization, identity federation, and security certification are outside this version.

## 3. Controlled vocabulary

| Term | Meaning |
|---|---|
| Workflow definition | Reusable graph configuration containing task definitions and directed transitions. |
| Workflow revision | Immutable accepted snapshot of a workflow definition used by one or more runs. |
| Automatic task | `DOCUMENT_VALIDATION`, `ARCHIVE_DOCUMENT`, or `CREATE_NOTIFICATION`; executed by application code. |
| Human task | `HUMAN_APPROVAL`; creates a persistent work item and waits for a decision instead of performing an automatic retry loop. |
| Task outcome | `SUCCESS` or `FAILURE`, passed to the shared transition resolver after retry policy has finished or been bypassed. |
| Business failure | Expected negative business result, such as invalid input or rejection; it is routed immediately and is not retried. |
| Retryable technical failure | Automatic-task failure that may be attempted again while its attempt bound remains. |
| Non-retryable technical failure | Automatic-task failure routed immediately without retry. |
| Attempt bound | Positive maximum number of automatic-task executions within one run. |
| Approval work item | Persistent pending request associated with exactly one invoice, run, and human-approval task. |
| Normalized trace | Ordered business and execution observations with run identifiers, timestamps, and mode-specific transport details excluded for comparison. |
| Internal notification | Persistent application record visible to the submitter; no email or external provider is implied. |

### Controlled states

| Object | Allowed states |
|---|---|
| Run | `RUNNING`, `WAITING_FOR_APPROVAL`, `COMPLETED`, `FAILED` |
| Invoice | `SUBMITTED`, `VALIDATION_FAILED`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `ARCHIVED`, `NEEDS_MANUAL_ACTION` |
| Approval work item | `PENDING`, `APPROVED`, `REJECTED` |

## 4. Change disposition from Requirements v2

| v2 identifiers | v3 disposition | Recorded reason |
|---|---|---|
| `FR-001`–`FR-016`, `FR-018`–`FR-021`, `FR-024`, `FR-025` | Retained | Graph, resolver, execution-mode, isolation, and retry-foundation behavior remains applicable. |
| `FR-017` | Modified | Parity is now defined for the same business input, decision, and deterministic fault schedule rather than an abstract named scenario alone. |
| `FR-022`, `FR-023` | Modified | Retry applies only to retryable technical failures of automatic tasks; persisted attempts include failure classification. |
| `FR-026` | Modified | Trace adds invoice, waiting/resume, approval, business-state, and notification observations. |
| `FR-027`–`FR-029` | Superseded by `FR-045`, `FR-046`, and the v3 acceptance matrix | Deterministic fault adapters remain verification tools but are no longer presented as the product's user purpose. |
| `FR-030` | Superseded by `FR-053` | The UI must lead with invoice work and outcome rather than scenario selectors and abstract task indicators. |
| `NFR-001`–`NFR-008` | Retained with the v3 wording below | Their scope is updated to the bounded invoice scenarios and waiting state. |
| `CON-005`, `CON-008`, `CON-009` | Modified | Real business inputs replace synthetic user outcomes; external services remain unnecessary; internal notification enters scope. |

No retired identifier is assigned a different function.

## 5. Functional requirements

### 5.1 Workflow definition and routing

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `FR-001` | The system shall represent each workflow definition as explicit task nodes connected by directed transitions. | Definition inspection and executable definition test | Stored nodes and transitions can be retrieved without deriving edges from display order. |
| `FR-002` | The system shall require exactly one designated start task in every accepted workflow definition. | Validation test | Zero-start and multiple-start definitions are rejected before revision activation or run creation. |
| `FR-003` | The system shall require at least one terminal task reachable from the designated start. | Validation test | A definition without a reachable terminal is rejected. |
| `FR-004` | The system shall require every task to be reachable from the designated start. | Graph-validation test | Every unreachable task is identified and the definition is rejected. |
| `FR-005` | The system shall reject a workflow definition containing a self-edge or directed cycle. | Graph-validation test | Self-edge and multi-node-cycle examples are rejected; the equivalent DAG is accepted. |
| `FR-006` | The system shall complete all definition validation before activating a revision or creating run state. | Validation/persistence test | Any definition violation creates no active revision, run, attempt, work item, or trace. |
| `FR-007` | The system shall accept only `SUCCESS`, `FAILURE`, or `ALWAYS` as transition conditions. | Validation test | Every other condition is rejected. |
| `FR-008` | The resolver shall select a matching `SUCCESS` or `FAILURE` transition before considering `ALWAYS`. | Resolver test | A matching outcome-specific edge suppresses an `ALWAYS` edge from the same task. |
| `FR-009` | The resolver shall select `ALWAYS` only when no transition matches the final task outcome. | Resolver test | Exactly one fallback is selected only in the absence of a matching specific edge. |
| `FR-010` | The system shall reject equal-precedence transition ambiguity. | Validation test | Duplicate specific or duplicate fallback edges from one task are rejected. |
| `FR-011` | A final `SUCCESS` with no eligible transition shall produce a successful terminal decision. | Terminal test | The run trace ends with a successful terminal observation. |
| `FR-012` | A final `FAILURE` with no eligible transition shall produce an unsuccessful terminal decision. | Terminal test | The run trace ends with an unsuccessful terminal observation. |
| `FR-013` | Both execution modes shall use the same workflow revision. | Paired-mode inspection | One revision identifier is used without mode-specific conversion. |
| `FR-014` | Both execution modes shall use the same transition resolver. | Design inspection and paired resolver test | Equal task result and outgoing transitions produce the same selection or terminal decision. |

### 5.2 Execution, state, retry, and trace

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `FR-015` | Orchestration mode shall advance an accepted run under centralized application control. | Orchestration acceptance test | Only resolver-selected tasks execute and the run records mode `orchestration`. |
| `FR-016` | Choreography mode shall advance an accepted run through run-scoped in-memory EventBus reactions. | Choreography acceptance test | The run records mode `choreography`, advances through in-memory events, and requires no broker. |
| `FR-017` | Both modes shall produce semantic parity for the same workflow revision, invoice input, approval decision, and deterministic fault schedule. | Paired normalized-trace comparison | Reached tasks, final outcomes, selected transitions, retry counts, waiting/resume observations, invoice state, notification result, and terminal run state are equivalent. |
| `FR-018` | The system shall create run-specific execution state for every run. | Persistence inspection | Attempts, decisions, transitions, trace, and terminal state reference exactly one run. |
| `FR-019` | A later sequential run shall not overwrite an earlier run's state or trace. | Sequential isolation test | Both complete histories remain retrievable. |
| `FR-020` | Concurrent runs shall not read or write each other's runtime or business state. | Controlled-concurrency test | No invoice, work item, attempt, decision, notification, or trace crosses run identity. |
| `FR-021` | Every automatic task shall have a positive maximum-total-attempt bound. | Definition-boundary test | Missing, zero, or negative bounds are rejected; one permits one attempt and zero retries. |
| `FR-022` | The system shall retry an automatic task if and only if its result is a retryable technical failure and the completed-attempt count is below its bound. | Two-sided retry test | Retry occurs below the bound; it does not occur for business failure, non-retryable failure, human task, or exhausted bound. |
| `FR-023` | The system shall persist every automatic attempt's ordinal, outcome, failure classification when applicable, reason, start time, and finish time. | Persistence/restart test | Retrieved attempts match the executed sequence before and after restart. |
| `FR-024` | Retry shall repeat the current automatic task without selecting a workflow transition. | Trace inspection | A retry observation occurs between attempts and no transition is selected during that interval. |
| `FR-025` | After attempt exhaustion, the final `FAILURE` shall enter normal `FAILURE` then `ALWAYS` transition resolution. | Exhaustion/resolver test | Specific failure route precedes fallback; absence of both produces `FR-012`. |
| `FR-026` | The system shall persist an ordered trace for each run. | Expected-versus-retrieved trace comparison | The trace contains all applicable run, task, attempt, retry, transition, waiting, resume, approval, invoice-state, notification, and terminal observations in committed order. |

### 5.3 Invoice submission and validation

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `FR-031` | The submitter shall be able to create an invoice submission containing one PDF part and a metadata payload for the fields in section 6. | API/UI acceptance test | A structurally readable request creates one invoice in `SUBMITTED` state with raw submitted values and a generated identity; business-invalid values remain available to `DOCUMENT_VALIDATION`. |
| `FR-032` | `DOCUMENT_VALIDATION` shall validate every required metadata field against section 6 before human approval. | Parameterized validation test | Every invalid field produces business `FAILURE` with a field-specific reason and no approval work item is created. |
| `FR-033` | `DOCUMENT_VALIDATION` shall validate the PDF against section 6 without OCR or invoice-content extraction. | File-validation test | Supported readable input produces `SUCCESS`; empty, oversized, non-PDF, encrypted, or unreadable input produces business `FAILURE` with a visible reason. |
| `FR-034` | An accepted submission shall start one run linked to the invoice, selected active workflow revision, and selected execution mode. | Persistence test | The invoice, run, mode, and revision references are mutually retrievable. |
| `FR-035` | A validation business failure shall set invoice state `VALIDATION_FAILED` and shall create no approval work item. | Invalid-submission scenario | The failure route and notification are recorded, with zero approval work items for the run. |

### 5.4 Human approval and continuation

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `FR-036` | Reaching `HUMAN_APPROVAL` shall create exactly one `PENDING` approval work item for the invoice and run. | Approval-creation test | One pending item exists even if the reach command/event is delivered twice. |
| `FR-037` | After creating the work item, the system shall set the invoice to `PENDING_APPROVAL` and the run to `WAITING_FOR_APPROVAL`. | State test | No successor task or terminal decision occurs before a decision is accepted. |
| `FR-038` | The approver shall be able to list pending work items and inspect the invoice metadata and document identity for one item. | API/UI inspection | The selected pending item displays the associated invoice fields and run identity. |
| `FR-039` | The approver shall be able to approve one pending work item with an optional note of at most 500 characters. | Approval test | The item becomes `APPROVED`, invoice becomes `APPROVED`, and task outcome becomes `SUCCESS`. |
| `FR-040` | The approver shall be able to reject one pending work item with a trimmed reason of 1–500 characters. | Rejection/boundary test | The item becomes `REJECTED`, invoice becomes `REJECTED`, and task outcome becomes `FAILURE`; empty or oversized reasons are rejected. |
| `FR-041` | The first valid decision shall be authoritative; an identical repeat shall be idempotent and a conflicting later decision shall be rejected without state change. | Duplicate/conflict test | One decision record exists, identical replay returns the existing result, and conflicting replay returns a controlled conflict. |
| `FR-042` | An accepted approval decision shall resume the same waiting run exactly once. | Continuation/isolation test | The original run leaves waiting state, no second run is created, and another waiting run is unchanged. |

### 5.5 Business completion and notification

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `FR-043` | `ARCHIVE_DOCUMENT` shall preserve the approved document under its generated storage identity, create an archive record, and set the invoice to `ARCHIVED` when execution succeeds. | Approved-invoice scenario | The archive record and document identity are retrievable and the state change is persisted before successor dispatch. |
| `FR-044` | Exhausted archive failure shall set the invoice to `NEEDS_MANUAL_ACTION` before failure routing. | Permanent-failure scenario | Attempts reach the configured bound, invoice state changes once, and normal failure routing follows. |
| `FR-045` | The system shall support a deterministic verification adapter that can inject success, retryable technical failure, and non-retryable technical failure by stable task/run input rather than task display name. | Adapter and rename test | Renaming a task does not change the configured verification result sequence. |
| `FR-046` | `CREATE_NOTIFICATION` shall persist one internal notification describing the invoice's final business state or required manual action. | Scenario inspection | One notification exists for each reference scenario after the notification task succeeds. |
| `FR-047` | The submitter shall be able to retrieve the invoice's current state, approval result/reason when present, notification, run state, and ordered trace. | Status/history test | All values belong to the selected invoice/run and agree with persisted execution records. |

### 5.6 Bounded constructor and user interface

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `FR-048` | The workflow operator shall be able to create, retrieve, update, and delete draft workflow definitions. | CRUD acceptance test | Each operation affects only the selected draft and returns its current representation. |
| `FR-049` | The constructor shall allow tasks only from `DOCUMENT_VALIDATION`, `HUMAN_APPROVAL`, `ARCHIVE_DOCUMENT`, and `CREATE_NOTIFICATION`. | Constructor validation test | Unsupported task types are rejected and no executable code can be supplied. |
| `FR-050` | The constructor shall allow task name, task type, one start designation, automatic-task attempt bound, and `SUCCESS`/`FAILURE`/`ALWAYS` transitions to be configured through bounded form controls. | UI/API inspection | A reference workflow can be configured without editing source or submitting scripts. |
| `FR-051` | The constructor shall visualize the current directed graph and display all definition-validation issues before activation. | UI inspection | Tasks, labeled edges, start designation, and complete validation feedback are visible. |
| `FR-052` | Activating a valid draft shall create an immutable workflow revision; editing a definition used by a run shall require a new revision. | Revision test | Earlier runs continue to reference unchanged revision content after a later edit. |
| `FR-053` | The browser demonstration shall provide connected views for invoice submission/status, pending approval/decision, bounded workflow configuration, execution-mode selection, and run trace. | End-to-end UI inspection | The approved, rejected, invalid, and retry scenarios can be demonstrated in one application without leading with abstract green task indicators. |

## 6. Input boundaries

### Invoice metadata

| Field | Rule |
|---|---|
| `supplier_name` | Required; trimmed length 1–120 characters. |
| `invoice_number` | Required; trimmed length 1–64 characters. |
| `issue_date` | Required; valid ISO calendar date in `YYYY-MM-DD` form. |
| `amount` | Required decimal greater than `0`, no more than `999999999.99`, and no more than two fractional digits. |
| `currency` | Required three uppercase ASCII letters. |

### PDF

| Property | Rule |
|---|---|
| Count | Exactly one file per invoice submission. |
| Size | Greater than zero and no more than 10 MiB (`10,485,760` bytes). |
| Declared media type | `application/pdf`. |
| Basic structure | A selected PDF library can open the document and report at least one page. |
| Rejected content | Encrypted, malformed, empty, unreadable, or non-PDF content. |
| Storage identity | Generated by the system; an original filename is metadata only and cannot select a storage path. |
| Extraction | No OCR, AI extraction, or accounting interpretation. |

## 7. Non-functional requirements

| ID | Atomic normative statement | Verification method | Acceptance condition |
|---|---|---|---|
| `NFR-001` | Repeating one acceptance scenario in the same mode from equivalent state shall produce an equivalent normalized trace. | Two runs per mode/scenario | All normalized observations match; only generated identities and timestamps may differ. |
| `NFR-002` | Each acceptance scenario shall satisfy semantic parity across orchestration and choreography. | Five paired comparisons covering ten executions | Every orchestration case has one equivalent choreography case under `FR-017`. |
| `NFR-003` | Workflow revisions, invoices, runs, attempts, waiting work, decisions, notifications, and trace shall survive a controlled application restart. | Restart-retention test | Pre-restart values are retrievable after restart; a waiting item remains decidable and resumes its original run. |
| `NFR-004` | Every trace shall be complete for the committed state changes of its run. | Expected-versus-retrieved comparison | No expected observation is absent, duplicated, out of order, or associated with another run. |
| `NFR-005` | Pre-activation validation shall cover every rule in `FR-002`–`FR-007`, `FR-010`, `FR-021`, and `FR-049`–`FR-052`. | Rule-path inspection and parameterized cases | Every invalid class is rejected without active revision or runtime state; valid boundaries are accepted. |
| `NFR-006` | The deployed target shall remain one FastAPI application backed by persistent database and controlled document storage. | Deployment inventory | One application service is present; no microservice or broker is required. |
| `NFR-007` | All sequential, concurrent, duplicate-decision, and resume tests shall preserve invoice/run isolation. | State-partition comparison | No record contains another case's invoice or run identity and no state is overwritten across cases. |
| `NFR-008` | Acceptance execution shall require no random outcome generation, distributed broker, payment/accounting system, OCR/AI service, or external notification provider. | Dependency/source inspection and isolated execution | All ten cases run with local controlled inputs and no prohibited dependency or call. |
| `NFR-009` | PDF validation shall enforce the complete section 6 boundary before a document reaches human approval. | Boundary and malformed-file suite | Every listed rejected class fails with a controlled reason and creates no approval item. |
| `NFR-010` | On the recorded reference environment, 95 of 100 consecutive reads of invoice status and trace for a completed reference run shall finish within 1 second each. | Timed local acceptance run with environment recorded | At least 95 measured reads meet the threshold; no external service is used. |
| `NFR-011` | The primary invoice-status view shall show invoice identity, current business state, required next human action when any, final result, and execution mode without requiring raw-trace inspection. | UI content inspection | All five items are visible for the selected invoice; trace remains available as secondary technical evidence. |

## 8. System and scope constraints

| ID | Constraint | Verification |
|---|---|---|
| `CON-001` | The target is one FastAPI application, not a microservice or distributed-execution system. | Deployment inventory. |
| `CON-002` | Persistent database and document storage are required; final tables, columns, and paths remain architecture decisions. | Requirements/design boundary inspection. |
| `CON-003` | Choreography uses a run-scoped in-memory EventBus and no Kafka, ZooKeeper, or other broker. | Dependency and deployment inspection. |
| `CON-004` | Workflow task definitions do not store mutable run, attempt, decision, waiting, invoice, or terminal state. | Domain and persistence review. |
| `CON-005` | Product outcomes come from validated input, explicit decisions, and bounded task behavior; verification faults are deterministic and no outcome is random. | Source and fixture inspection. |
| `CON-006` | Retry does not create or require a graph cycle. | Definition and trace inspection. |
| `CON-007` | Parallel fork/join execution remains outside scope. | Requirements/design/implementation review. |
| `CON-008` | Acceptance scenarios make no external business-service calls. | Isolated execution and dependency inspection. |
| `CON-009` | Authentication, authorization, billing, analytics, external email, payment, accounting integration, OCR, AI extraction, and fraud detection remain outside scope; internal notifications are included. | Scope and dependency inspection. |
| `CON-010` | Requirements do not prescribe final endpoint paths, schema layout, classes, or UML structure. | Document inspection. |
| `CON-011` | Users cannot upload or enter executable code, scripts, templates with executable expressions, or executor plugins. | Constructor/API negative tests. |
| `CON-012` | A general BPMN editor, arbitrary drag-and-drop modeler, marketplace, and full low-code platform are outside scope. | UI and scope inspection. |
| `CON-013` | Human approval decisions are never automatically retried. | Retry and decision trace inspection. |
| `CON-014` | Camunda, n8n, and Temporal are behavioral references only; their engines and workflow definitions are not runtime dependencies. | Dependency, source, and report-reference inspection. |

## 9. Reference workflow and acceptance matrix

The acceptance workflow uses these task definitions:

| Task | Type | Attempt bound |
|---|---|---|
| Validate invoice | `DOCUMENT_VALIDATION` | 1 |
| Review invoice | `HUMAN_APPROVAL` | 1; retained as a positive definition value but not used for automatic retry |
| Archive invoice | `ARCHIVE_DOCUMENT` | 2 |
| Notify submitter | `CREATE_NOTIFICATION` | 2 |

Transitions are:

- Validate `SUCCESS` → Review;
- Validate `FAILURE` → Notify;
- Review `SUCCESS` → Archive;
- Review `FAILURE` → Notify;
- Archive `SUCCESS` → Notify;
- Archive `FAILURE` → Notify;
- Notify has no outgoing transition.

Each scenario shall be executed once in orchestration and once in choreography, producing ten acceptance cases:

| Scenario | Controlled input/action | Expected business path and result | Critical trace evidence |
|---|---|---|---|
| `S1 Approved` | Valid PDF/metadata; approver approves; no injected fault | `SUBMITTED → PENDING_APPROVAL → APPROVED → ARCHIVED`; one final notification; run `COMPLETED` | One wait/resume pair, approval `SUCCESS`, archive success, zero retries. |
| `S2 Rejected` | Valid PDF/metadata; approver rejects with reason | `SUBMITTED → PENDING_APPROVAL → REJECTED`; one notification; run `COMPLETED` | One decision, failure route from Review, rejection reason, no automatic retry of the human task. |
| `S3 Invalid` | Malformed PDF or invalid required metadata | `SUBMITTED → VALIDATION_FAILED`; no approval item; one notification; run `COMPLETED` | Validation business failure, failure route, zero approval/wait observations. |
| `S4 Retry then archive` | Valid and approved; Archive receives one injected retryable failure then success | Final invoice `ARCHIVED`; one notification; run `COMPLETED` | Two archive attempts, one retry, no transition during retry, then success route. |
| `S5 Manual action` | Valid and approved; Archive receives retryable failures through bound exhaustion | Final invoice `NEEDS_MANUAL_ACTION`; one notification; run `COMPLETED` after controlled failure handling | Two archive failures, one retry, failure route after exhaustion, notification of manual action. |

PBI-E20 executed the five orchestration cases. PBI-E21 subsequently executed all five choreography counterparts and five normalized pair comparisons in disposable storage and in-memory SQLite. PBI-E22 implemented and verified the constructor-dependent activation boundary. PBI-E23 verified repeated normalized traces, exact trace completeness, file-backed waiting restart/resume, threaded two-run isolation, complete PDF-to-no-approval boundaries, prohibited-dependency absence, and the recorded 100-read threshold. PBI-E24 verified the reference Chromium UI. PBI-E25 verified one-service/no-broker inventory and both-mode waiting/resume across real process recreation; container image build remains unexecuted because no engine was available.

## 10. Review result and next checkpoint

Substantive review confirmed:

- each active requirement is atomic, observable, and testable;
- modified and superseded v2 identifiers have explicit reasons;
- input limits, state vocabularies, decision idempotency, retry classification, and ten acceptance cases are internally consistent;
- the bounded constructor cannot execute user code;
- both modes retain shared business semantics;
- at requirements approval time, C5A compatibility and affected architecture work were not represented as complete;
- the requirements approval record invents no instructor approval, implementation, test result, migration, deployment, or release.

Review result: `APPROVED — project-level Requirements v3 baseline` on `2026-08-13`. Static coverage found 49 active functional requirements, 11 non-functional requirements, and 14 constraints; every active FR and NFR has a forward trace. That requirements-review result alone establishes no executable behavior.

The affected architecture/ADR/UML checkpoint subsequently passed, followed by PBI-E17 through PBI-E23. The current next checkpoint is PBI-E24 final user-outcome-first browser acceptance; no instructor approval is claimed.

## 11. Related records

- [CR-002](../evolution/CR-002-invoice-approval-reference-application.md)
- [Requirements v2](./requirements-v2.md)
- [Requirements v3 traceability](./requirements-traceability-v3.md)
- [Product backlog](../process/product-backlog.md)
- [Risk register](../process/risk-register.md)
- [Development process](../process/development-process.md)
- [Definition of Done](../process/definition-of-done.md)
