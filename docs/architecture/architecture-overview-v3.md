# Invoice-Workflow Architecture Overview v3

| Field | Value |
|---|---|
| Status | `APPROVED — project-level architecture v3 baseline` |
| Requirements baseline | [Requirements v3 3.0](../requirements/requirements-v3.md) |
| Change source | [CR-002](../evolution/CR-002-invoice-approval-reference-application.md) |
| Controlled implementation base | `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` |
| Previous design baseline | Checkpoint-4 defense-core architecture at `f44f0d55349af4e7b1b19b49f5e3b26c67c96181` |
| Implementation | `PBI-E17 FOUNDATION ACCEPTED — project level` |
| Executable verification | `76 FOCUSED FOUNDATION/E18 TESTS PASSED` |
| Release | `NOT SCHEDULED` |

## 1. Purpose

This correction applies the retained workflow engine to a bounded invoice-approval product without mixing business behavior into the shared resolver. The architecture keeps the modular monolith, conditional DAG, shared routing, bounded retry, isolated run state, orchestration, choreography, and persistent trace. It adds immutable workflow revisions, invoice/document state, a task-executor boundary, classified failures, persistent human approval, resumable execution, bounded document storage, and a form-based constructor.

The system is independently implemented. Camunda, n8n, and Temporal remain behavioral references; no external workflow engine is introduced.

## 2. System boundary and actors

The deployment boundary is one FastAPI application plus persistent database and controlled local document storage.

| Actor or boundary | Responsibility |
|---|---|
| Submitter | Supplies one invoice PDF and metadata; reads business status, notification, and trace. |
| Approver | Lists pending work, inspects invoice information, and submits one approve/reject decision. |
| Workflow operator | Configures a draft from the closed task catalog, validates it, activates an immutable revision, and selects execution mode. |
| Academic evaluator | Observes the business result and then compares orchestration with choreography. |
| PDF library adapter | Opens a bounded local PDF and reports technical readability/page information; performs no OCR or interpretation. |
| Persistent database | Owns definitions/revisions, invoices, runs, execution cursor, attempts, approvals, decisions, notifications, and trace. |
| Controlled document storage | Stores documents only under system-generated identities. |

There is no external payment, accounting, email, OCR/AI, broker, or workflow-engine service.

## 3. Quality drivers

| Driver | Requirement coverage | Architectural response |
|---|---|---|
| Understandable product result | `FR-031`–`FR-047`, `FR-053`, `NFR-011` | Invoice application services and business-state projections precede trace/mode details in the presentation boundary. |
| Shared semantics | `FR-013`–`FR-017`, `NFR-002` | Both strategies call the same executor ports, retry policy, resolver, repositories, and trace vocabulary. |
| Durable waiting/resume | `FR-036`–`FR-042`, `NFR-003` | Approval and execution cursor are persistent; no in-memory subscription is retained while waiting. |
| Idempotency and isolation | `FR-018`–`FR-020`, `FR-036`, `FR-041`, `FR-042`, `NFR-007` | Run/invoice keys, one-work-item/one-decision invariants, state version checks, and run-scoped dispatch. |
| Safe bounded documents | Section 6, `NFR-009`, CON-009 | Streaming size guard, generated storage identity, PDF adapter, controlled rejection, no extraction. |
| Maintainability | `FR-045`, `FR-048`–`FR-052`, CON-011–CON-014 | Closed executor registry, ports/adapters, immutable revisions, no arbitrary code or imported workflow engine. |
| Restart retention | `NFR-003`, `NFR-006` | Database-backed execution cursor is authoritative; application recovery can resume committed `RUNNING` work. |

## 4. Architectural style and layers

The target remains a single-deployable layered modular monolith:

| Layer | Owns | Does not own |
|---|---|---|
| Presentation | HTTP/UI translation for submissions, decisions, definitions, status, and trace. | Routing, retry, storage paths, or mode-specific business rules. |
| Application | Submission, approval-decision, definition/revision, execution/resume, query, and recovery use cases. | Reimplemented resolver logic or direct PDF parsing. |
| Domain | Definition rules, task/result vocabulary, failure classification, retry eligibility, transition resolution, invoice/run/work-item state transitions, trace meaning. | FastAPI, SQLAlchemy, file paths, PDF technology, EventBus implementation. |
| Infrastructure | Repositories, transaction boundary, controlled documents, PDF adapter, in-memory EventBus, deterministic fault adapter. | Independent business policy or authoritative in-memory run state. |

Dependencies point inward. Infrastructure implements ports declared by the application/domain boundary.

## 5. Main components and ports

| Component | Responsibility |
|---|---|
| Definition service | CRUD for drafts, validation, graph projection, and immutable revision activation. |
| Invoice submission service | Accept bounded raw input, create invoice/run, and invoke the selected strategy. |
| Approval decision service | Enforce one decision, persist business/run state, and resume the original run. |
| Execution coordinator | Load revision and cursor, invoke one strategy, and recover committed runnable work. |
| Orchestration strategy | Perform centralized step-by-step execution until waiting or terminal. |
| Choreography strategy | Use a temporary run-scoped EventBus handler to perform the same steps until waiting or terminal. |
| Executor registry | Resolve one of four supported task types to a `TaskExecutor` port. |
| Task executors | Validate document/metadata, create approval waiting work, archive document, or create notification. |
| Retry policy | Retry only retryable technical failure from an automatic task while the bound remains. |
| Transition resolver | Select outcome-specific edge, then `ALWAYS`, then terminal; never owns retry or invoice rules. |
| Repositories/unit of work | Persist one transactionally consistent business/execution step and ordered trace. |
| Query service | Return invoice projection, pending approvals, revisions, run status, and ordered trace. |

## 6. Shared execution contract

Automatic executors return a controlled `TaskResult`:

- `outcome`: `SUCCESS` or `FAILURE`;
- `failure_class`: absent for success, otherwise `BUSINESS`, `RETRYABLE_TECHNICAL`, or `NON_RETRYABLE_TECHNICAL`;
- `reason`: bounded diagnostic/business explanation;
- optional controlled business-state changes produced through the current unit of work.

The execution algorithm is shared:

1. Load the immutable revision, run, invoice, and execution cursor.
2. If the task is human approval, create/get one pending work item, persist `WAITING_FOR_APPROVAL`, record trace, and return without resolving a transition.
3. Otherwise invoke the registered automatic executor and persist the attempt/result.
4. Retry only `RETRYABLE_TECHNICAL` failure below the configured bound; do not select an edge.
5. Convert final executor result to `SUCCESS` or `FAILURE` and call the shared resolver.
6. Persist the selected transition and next cursor, or terminal decision, before the next control trigger.

Business failure and human rejection are expected route inputs, not technical retries. Task display names never select executor or verification behavior.

## 7. Persistent execution cursor

Each run has one authoritative cursor containing, conceptually:

- current task definition identity;
- phase `READY`, `WAITING_FOR_APPROVAL`, or `TERMINAL`;
- monotonic state version;
- terminal decision when present;
- selected workflow revision and execution mode.

Each step commits the cursor, affected invoice/work-item records, attempt/decision/notification records, and trace observations in one unit of work. Uniqueness constraints enforce one work item per `(run, human task)`, one authoritative decision per work item, one attempt ordinal per `(run, task)`, and one trace position per run.

The cursor, not EventBus memory, determines what may execute. A recovery use case may safely identify `RUNNING` cursors in `READY` phase and invoke their selected strategy after a controlled restart. State-version checks prevent two handlers from advancing the same cursor concurrently.

## 8. Human approval lifecycle

Reaching `HUMAN_APPROVAL` is not an automatic attempt:

1. create or retrieve the unique pending work item;
2. set invoice `PENDING_APPROVAL` and run/cursor waiting state;
3. persist trace and finish the current request/dispatch scope;
4. retain no EventBus subscriber while waiting;
5. on decision, atomically create the authoritative decision and set outcome/invoice/cursor state;
6. an identical repeated decision returns the existing result; a conflicting decision does not change state;
7. invoke the original run's selected strategy from the persisted cursor.

Approve produces routing outcome `SUCCESS`; reject produces `FAILURE`. Neither is automatically retried.

## 9. Orchestration and choreography

### Orchestration

The coordinator invokes the orchestration strategy. A central loop performs shared steps until the cursor becomes waiting or terminal. After a decision, the approval service invokes the coordinator for the same run and mode.

### Choreography

For each active processing scope, the choreography strategy registers exactly one run-keyed advance handler, publishes a synchronous internal advance event, and removes the handler when the cursor becomes waiting or terminal. The handler uses the same shared step service as orchestration.

State is committed before publishing the next event. EventBus carries a trigger containing only stable run identity and expected state version; it does not carry the authoritative invoice or execution state. Missing handler, version conflict, or executor error becomes a controlled execution error. No subscriber survives the waiting period or application restart.

## 10. Workflow revisions and constructor

Definitions have mutable drafts and immutable activated revisions:

- draft CRUD is separate from run execution;
- validation covers graph rules, closed task types, task configuration, and positive automatic attempt bounds;
- activation snapshots tasks/transitions/configuration into a revision;
- a run references exactly one revision;
- editing an activated definition creates another revision and never changes previous runs;
- the constructor is form-based and renders a graph projection; it accepts no executable expressions or plugins.

## 11. Document handling

The request boundary reads at most the configured limit plus one byte, rejects oversize input, and never uses the original filename as a path. A generated storage identity is created before persistence. The PDF adapter checks declared type, recognizable/openable structure, encryption/readability, and page count. Metadata validation is domain policy. Failed validation retains only the controlled evidence required by the approved requirements; architecture implementation review must specify cleanup of rejected temporary content.

Archive success creates an archive record and preserves the generated document identity. Archive exhaustion sets `NEEDS_MANUAL_ACTION` before normal failure routing.

## 12. Persistence and trace ordering

The unit-of-work boundary commits business state and its trace observations together. Required transaction groups are:

- submission + invoice + run + initial cursor/trace;
- automatic attempt + result + retry/next cursor/terminal trace;
- pending approval + waiting invoice/run/cursor trace;
- decision + approval/invoice outcome + resumed cursor trace;
- archive/notification record + invoice state + trace;
- terminal run/cursor + terminal trace.

Run-local trace positions are allocated inside the transaction. Implementation must not derive ordering from timestamps.

## 13. C5A compatibility decision

| C5A element | Disposition | Required correction |
|---|---|---|
| Frozen domain definition/result types | Retain and extend | Add task type/configuration and executor-result/failure vocabulary without invoice rules in resolver. |
| Graph validation | Retain | Validate revision/task-type configuration and automatic-task bounds; preserve deterministic issue ordering. |
| Transition resolver | Retain | Keep `SUCCESS`/`FAILURE`/`ALWAYS` semantics unchanged. |
| `WorkflowTransition` concept | Retain | Associate with immutable revision rather than mutable definition execution. |
| `TaskAttempt` concept | Retain and extend | Add failure class/reason and ensure only automatic executions create attempts. |
| `TraceEntry` concept | Retain and extend | Add waiting, resume, work-item, decision, invoice-state, notification, and controlled-error kinds. |
| `WorkflowRun` concept | Change | Add revision/invoice association, `WAITING_FOR_APPROVAL`, and persistent cursor/version. |
| Mutable `Task.status`/timestamps compatibility fields | Replace after cutover | New code never reads/writes them; remove when old routes/engines are retired. |
| Named task scenario lookup | Replace | Use real input/decision and an optional deterministic adapter keyed by stable run/task configuration. |
| Existing runtime routes/engines | Replace through vertical increments | Do not layer invoice/waiting conditionals over incompatible linear/prototype control paths. |

The unpublished C5B1 draft is not a transfer source or evidence.

## 14. 4+1 view set

| View | UML v3 source |
|---|---|
| Logical | [domain-model.puml](./uml-v3/domain-model.puml), [run-state.puml](./uml-v3/run-state.puml) |
| Process | [orchestration-sequence.puml](./uml-v3/orchestration-sequence.puml), [choreography-sequence.puml](./uml-v3/choreography-sequence.puml), [routing-retry-activity.puml](./uml-v3/routing-retry-activity.puml) |
| Development | [component-view.puml](./uml-v3/component-view.puml) |
| Physical | [deployment-view.puml](./uml-v3/deployment-view.puml) |
| Scenarios | [system-context-use-cases.puml](./uml-v3/system-context-use-cases.puml) and both sequence views |

## 15. Explicit exclusions

- full BPMN/general low-code platform;
- arbitrary user code or executor plugins;
- payment, accounting integration, OCR/AI, fraud detection, analytics, authentication, or external notification;
- Kafka, ZooKeeper, distributed broker, microservices, or distributed execution;
- parallel fork/join, graph cycles, or retry edges;
- another product's engine, code, diagrams, or architecture as implementation;
- unsupported durability, security, availability, or scale claims.

## 16. Review result and next gate

The ADR/UML/traceability consistency review passed on `2026-08-13`. All nine ADRs agree with Requirements v3, all eight PlantUML sources passed syntax and render checks, and every rendered view passed visual inspection after correcting the run-state label layout. This is project-level design approval, not instructor approval.

The focused PBI-E17 compatibility plan is recorded in [Checkpoint 5A v3](../implementation/checkpoint-5a-v3-implementation-plan.md). Increments 5A.1–5A.3 passed focused domain, persistence, and application-step suites. PBI-E18 passes bounded submission/validation and its HTTP boundary. PBI-E19 passes persistent waiting, authoritative decision, same-cursor resume, approval query, and HTTP-boundary suites. PBI-E20/E21 pass five business scenarios in both strategies, five normalized pair comparisons, and choreography subscriber cleanup. PBI-E22 adds bounded draft CRUD, closed-catalog validation, graph feedback, and immutable revision activation. PBI-E23 verifies repeated traces, file-backed waiting/resume, threaded isolation, complete PDF gating, prohibited-dependency absence, and reference status-read timing. PBI-E24 verifies the persisted user-outcome projection in reference Chromium desktop/mobile paths. PBI-E25 verifies one-service/no-broker inventory and both modes across real process recreation. These results do not establish production migration, a built container image, external deployment, or release.

## 17. Related records

- [Architecture decisions v3](./architecture-decisions-v3.md)
- [Architecture traceability v3](./architecture-traceability-v3.md)
- [Requirements v3](../requirements/requirements-v3.md)
- [CR-002](../evolution/CR-002-invoice-approval-reference-application.md)
- [Product backlog](../process/product-backlog.md)
- [Risk register](../process/risk-register.md)
