# Event-Driven Workflow Management System — Architecture Decisions

| Field | Value |
|---|---|
| Status | `ACCEPTED AND IMPLEMENTED` |
| Requirements baseline | [Requirements](../requirements/requirements.md) |
| Decision set | ADR-001–ADR-009 |

The identifiers preserve the design history. Together these decisions define the final bounded product.

## ADR-001 — Retain the single-deployable layered modular monolith

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** requirements adds business data, human waiting, controlled files, and constructor CRUD but still excludes distributed execution and external business dependencies.

**Decision.** Retain one FastAPI process with presentation, application, domain, and infrastructure layers. Add cohesive purchase request, approval, definition/revision, execution, and query application services. Dependencies point toward shared domain policy. Database and controlled document storage remain infrastructure boundaries.

**Rejected alternatives.** Microservices/broker topology adds unsupported operational complexity; embedding all logic in routes repeats the coupling that made the prototype difficult to evolve; a second purchase request application would split one product into two systems.

**Consequences.** One deployment is easy to demonstrate and preserves C5A reuse. Internal boundaries and transaction ownership must be enforced by review because process separation cannot enforce them.

**Traceability.** `FR-031`–`FR-053`, `NFR-006`, CON-001, CON-002, CON-008; RK-002, RK-010, RK-016.

## ADR-002 — Separate drafts, immutable revisions, run cursor, and purchase request state

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** C5A separates definition and run concepts but lacks immutable revisions, purchase request ownership, human waiting, and a recoverable execution cursor. Old task-definition status/timestamps remain compatibility debt.

**Decision.** Model four ownership boundaries:

- mutable workflow draft;
- immutable activated workflow revision containing task/transition snapshots;
- run-owned execution cursor, attempts, decisions, and trace;
- purchase request-owned document metadata, business state, approval work item, authorization record, and notification.

Every run references one purchase request and one immutable revision. New code never mutates definition-task runtime fields. Earlier runs keep their revision after later draft edits.

**Rejected alternatives.** Mutating an active graph makes old traces uninterpretable; copying state onto task definitions breaks isolation; treating purchase request status as the run status loses the difference between business and execution outcomes.

**Consequences.** History and concurrent runs become intelligible. More records and explicit associations require migration and transaction review.

**Traceability.** `FR-018`–`FR-020`, `FR-034`–`FR-047`, `FR-052`, `NFR-003`, `NFR-007`, CON-004; RK-003, RK-006, RK-017.

## ADR-003 — Use one executor result, retry policy, and transition resolver

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** A single `SUCCESS`/`FAILURE` outcome cannot determine whether a failure should be retried. Invalid purchase requests and human rejection are business outcomes; transient authorization/notification errors may be retried.

**Decision.** Automatic executors implement one port and return `TaskResult(outcome, failure_class, reason)`. Failure class is `BUSINESS`, `RETRYABLE_TECHNICAL`, or `NON_RETRYABLE_TECHNICAL`. Retry policy runs before routing and only for retryable technical failure below the bound. Final result is passed to the retained shared transition resolver. Human approval creates waiting work and later supplies `SUCCESS`/`FAILURE`; it never enters automatic retry.

Executor selection uses controlled task type, never display name. A deterministic verification adapter may wrap an executor using stable run/task configuration.

**Rejected alternatives.** Retrying every failure would repeat rejection/invalid input; embedding retry in graph edges violates the DAG; mode-specific resolvers create semantic drift; task-name lookup makes configuration unsafe.

**Consequences.** Failure behavior is explicit and testable. Executor/result vocabulary expands C5A types and persistence.

**Traceability.** `FR-007`–`FR-014`, `FR-021`–`FR-025`, `FR-032`, `FR-033`, `FR-045`, CON-005, CON-006, CON-013; RK-005, RK-018, RK-019.

## ADR-004 — Central orchestration stops at waiting and resumes from persisted cursor

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** The previous orchestration loop assumed every task immediately produced an outcome. Human approval can wait across requests and restarts.

**Decision.** The orchestration strategy executes shared steps until the cursor is `WAITING_FOR_APPROVAL` or terminal. Reaching human approval atomically persists the work item, purchase request waiting state, run/cursor waiting state, and trace, then returns. An accepted decision updates the same cursor and invokes orchestration for the same run. A central loop remains control owner but contains no purchase request-specific resolver logic.

**Rejected alternatives.** Blocking an HTTP request/thread until a human responds cannot survive restart; polling in the orchestration loop wastes resources; creating a new run on decision breaks identity and audit.

**Consequences.** Central control remains easy to explain while supporting long-lived human work. Resume idempotency and cursor concurrency require explicit tests.

**Traceability.** `FR-015`, `FR-036`–`FR-044`, `NFR-003`, `NFR-007`; RK-017, RK-018.

## ADR-005 — EventBus is a transient trigger over persistent choreography state

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** A run-scoped in-memory EventBus demonstrates choreography but cannot retain waiting work across restart and must not leave stale subscribers.

**Decision.** Choreography creates one temporary run-keyed advance handler for an active processing scope. State/cursor/trace commit before the next synchronous advance event. The event carries run identity and expected state version only. The handler is removed when the cursor waits or terminates; no subscriber survives human waiting or restart. After a decision or recovery, the coordinator rebuilds the temporary scope from persistent state and publishes a new trigger.

EventBus is not an authoritative queue. A missing handler, version conflict, or executor error becomes a controlled error rather than silent success.

**Rejected alternatives.** Keeping subscribers while waiting leaks memory and cannot survive restart; a global subscriber risks cross-run advancement; Kafka/another broker violates scope; duplicating business state in events creates two sources of truth.

**Consequences.** Choreography remains visibly event-driven while persistence provides durability. It does not claim distributed durable messaging or exactly-once transport.

**Traceability.** `FR-016`, `FR-017`, `FR-020`, `FR-036`–`FR-042`, `NFR-002`, `NFR-003`, `NFR-007`, CON-003; RK-004, RK-017, RK-018.

## ADR-006 — Persist an execution cursor and commit one observable step per unit of work

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** Restart and idempotent resume require more than an ordered trace. The system must know the current task/phase even if an in-memory trigger disappears.

**Decision.** Persist one versioned execution cursor per run. Each business/execution step commits its state changes and ordered trace together. Use unique invariants for `(run, task, attempt ordinal)`, `(run, human task work item)`, `(work item, authoritative decision)`, and `(run, trace position)`. State-version comparison prevents concurrent advancement. Recovery may invoke committed `RUNNING`/`READY` cursors; waiting cursors resume only through the decision use case.

**Rejected alternatives.** Reconstructing state only from timestamps is ambiguous; keeping cursor in memory fails restart; holding a database transaction open while waiting is invalid; treating EventBus as durable storage contradicts ADR-005.

**Consequences.** Restart behavior and duplicate decisions are controllable. Schema/migration and conflict response require focused implementation design and tests.

**Traceability.** `FR-018`–`FR-020`, `FR-023`, `FR-026`, `FR-034`–`FR-047`, `NFR-003`, `NFR-004`, `NFR-007`; RK-003, RK-006, RK-011, RK-017.

## ADR-007 — Keep deterministic verification adapters and one local deployment

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** Real purchase request inputs and decisions create understandable behavior, while repeatable retry/parity verification still needs controlled technical failures.

**Decision.** Normal product execution uses structured request data, explicit approval decisions, and bounded local task behavior. Test/defense configuration may select a deterministic fault schedule keyed by stable run/task configuration. It wraps the executor port and is never selected by task display name. Both modes use the same schedule. Deployment remains one FastAPI application with database and controlled document storage and no external business service or broker.

**Rejected alternatives.** Random outcomes destroy reproducibility; task-name scenarios prevent safe constructor edits; real third-party failures make acceptance unstable; replacing the engine with Temporal/Camunda/n8n delegates the required custom logic.

**Consequences.** Product value and verification mechanism are clearly separated. Reports must disclose the structured input library and behavioral references without presenting them as custom implementation.

**Traceability.** `FR-017`, `FR-045`, section 9, `NFR-001`, `NFR-002`, `NFR-008`, CON-005, CON-008, CON-014; RK-007, RK-019, RK-021.

## ADR-008 — Use a bounded structured input/document adapter and generated storage identities

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** The product must handle a useful document while excluding OCR, AI extraction, unsafe paths, and unbounded storage input.

**Decision.** The request boundary enforces a streaming size limit. A document-storage port generates the storage identity; original filename is metadata only. A selected maintained structured input library behind an adapter checks openability, encryption/readability, and page count. Domain validation owns metadata rules. Authorization records reference the generated document identity. Rejected temporary content follows an explicit cleanup path selected during implementation design.

**Rejected alternatives.** Original filenames as paths enable collisions/traversal; reading unbounded files into memory violates the boundary; OCR/AI expands scope and external dependencies; embedding structured input APIs in routes couples infrastructure to use cases.

**Consequences.** Validation is real but bounded. Library/license selection, malformed-input handling, cleanup, and disposable test storage require evidence.

**Traceability.** `FR-031`–`FR-035`, `FR-043`, section 6, `NFR-009`, CON-009; RK-020, RK-021.

## ADR-009 — Use closed task types, draft CRUD, and immutable revision activation

**Status:** `ACCEPTED AND IMPLEMENTED`

**Context.** A constructor demonstrates configurable workflows, but a general low-code/BPMN platform or arbitrary executor code would exceed scope and weaken safety.

**Decision.** Draft definitions support CRUD through bounded fields. Task type is one of four controlled values resolved through an internal executor registry. Validation runs before activation. Activation snapshots the draft into an immutable revision; runs never reference mutable drafts. The UI renders a graph projection and validation issues but accepts no scripts, executable expressions, plugins, or arbitrary task types.

**Rejected alternatives.** Hard-coding one graph hides configurability; editing active graphs corrupts history; general BPMN/drag-and-drop parity is unnecessary; user plugins make validation/security unbounded.

**Consequences.** The constructor is useful and defensible while remaining feasible. Revision storage and graph projection add implementation work.

**Traceability.** `FR-001`–`FR-010`, `FR-048`–`FR-052`, `NFR-005`, CON-011, CON-012; RK-005, RK-016.

## Decision-set consistency

- ADR-001 owns deployment/layer boundaries.
- ADR-002 owns data/state ownership and revision immutability.
- ADR-003 owns executor result, retry, and routing order.
- ADR-004 and ADR-005 vary control style only.
- ADR-006 makes persistent cursor/state authoritative for both modes.
- ADR-007 separates product input from deterministic fault verification.
- ADR-008 owns structured input/storage integration.
- ADR-009 bounds constructor extensibility.

The decision set was checked against the final implementation, requirements, UML, and automated evidence.

## Related records

- [Architecture overview](./overview.md)
- [Architecture traceability](./traceability.md)
- [Requirements](../requirements/requirements.md)
- [CR-002](../evolution/CR-002-purchase-request-approval-reference-application.md)
