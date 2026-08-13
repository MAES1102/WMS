# CR-002: Apply the workflow engine to a bounded invoice-approval reference application

## Metadata

| Field | Value |
|---|---|
| ID | `CR-002` |
| Title | Apply the workflow engine to a bounded invoice-approval reference application |
| Status | `APPROVED FOR REQUIREMENTS V3 — project-level review` |
| Change category | Product-purpose clarification and functional enhancement |
| Controlled base | `refactor/defense-core` / `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` |
| Preserved foundation | C5A domain definition, validation, resolver, and persistence concepts |
| Creation date | `2026-08-13` |
| Project-level approval date | `2026-08-13` |
| Approval authority | Project reviewer; no additional instructor approval is claimed |
| Requirements impact | Requirements v3 3.0 subsequently passed project-level substantive review; architecture correction remains required |
| Implementation status | `NOT AUTHORIZED BY THIS REQUEST` |
| Release status | `NOT SCHEDULED` |

The project-level reviewer approved this request for progression to Requirements v3 after confirming the bounded direction in the project conversation. The CR approval itself did not approve downstream artifacts. Requirements v3 3.0 subsequently passed its separate project-level substantive review on `2026-08-13`; no instructor approval is claimed. Architecture changes, implementation, tests, migration, deployment, and release remain unapproved. The unpublished local C5B1 draft is not part of the controlled base and is not implementation evidence for this request.

## Change trigger

The approved workflow proposal states that users can define and execute workflows containing dependent tasks, while orchestration and choreography provide two complex coordination functions. The generic defense-core design implements the corresponding technical semantics, but its current demonstration language is dominated by abstract task outcomes and execution modes.

Student-reported instructor feedback from the earlier live demonstration was that the purpose of the project was not understandable after observing abstract processes, green execution indicators, and an induced failure. The exact date and raw private communication are not committed; the feedback is therefore a `RECONSTRUCTED` project input rather than independently verifiable correspondence.

The product problem is not that conditional execution is absent from the design. The problem is that an academic evaluator or ordinary user cannot identify what useful work the process performs, what business object changes, why a task succeeds or fails, or what result the user receives. Continuing with only `Start`, `Work`, and terminal demonstration nodes would preserve this comprehension risk.

## Requested outcome

Retain the Event-Driven Workflow Management System and apply it to one bounded reference application:

> A submitter uploads an invoice document, the system validates it, an approver approves or rejects it, and the workflow archives or returns the invoice while preserving an auditable execution history.

The reference application is intended to make the already selected workflow semantics observable through a concrete user problem. It is not a replacement workflow engine and not a second unrelated project.

The requested product capabilities are:

- create and inspect invoice records associated with uploaded PDF documents;
- record a small controlled set of invoice metadata supplied with the upload, with the exact fields decided in Requirements v3;
- validate media type, file size, PDF readability/basic structure, and required submitted metadata without OCR or content extraction;
- create one human approval work item for a reached approval task;
- record an approve or reject decision and an optional rejection reason;
- pause a run while approval is pending and resume the same isolated run after the decision;
- archive an approved invoice or return an invalid/rejected invoice to the submitter;
- create an internal user-visible notification record for the final result;
- preserve attempts, retries, decisions, selected transitions, terminal state, and ordered trace under one run identity;
- configure a workflow from a bounded catalog of supported invoice-processing task types;
- execute the same accepted definition through centralized orchestration or run-scoped in-memory EventBus choreography;
- retain deterministic adapters for repeatable cross-mode verification without presenting synthetic outcomes as the product's user value.

## Product boundary

### Included actors

| Actor | Included responsibility |
|---|---|
| Submitter | Upload an invoice and inspect its current and final processing status. |
| Approver | Inspect a pending approval item and record approve or reject with a reason when applicable. |
| Workflow administrator/operator | Configure a bounded invoice workflow, validate it, select an execution mode, and inspect trace. |
| Academic evaluator | Observe the user outcome first, then compare the two internal coordination strategies. |

These are logical application roles. Authentication, authorization policy, identity federation, and security certification are not implied by this request.

### Included task types

| Task type | Observable responsibility |
|---|---|
| `DOCUMENT_VALIDATION` | Check the uploaded PDF's bounded technical properties and the submitted metadata, then return a controlled success or failure result with a reason. |
| `HUMAN_APPROVAL` | Create one pending work item and wait for an explicit approve or reject decision. |
| `ARCHIVE_DOCUMENT` | Persist the approved business result in the application's controlled storage boundary. |
| `CREATE_NOTIFICATION` | Persist an internal notification for the submitter. |

The catalog is intentionally closed for this increment. Users do not upload arbitrary executable code or define new executor implementations through the UI.

### Bounded constructor

The requested constructor is form-based configuration plus graph visualization. It may create tasks from the supported catalog, designate one start task, configure positive attempt bounds, add `SUCCESS`, `FAILURE`, or `ALWAYS` transitions, validate the definition, and save it.

A general BPMN modeler, arbitrary drag-and-drop canvas behavior, executable scripting, plugin marketplace, and complete low-code platform are outside scope.

## Reference-product use

Established products are used as behavioral references, not as implementation dependencies. The following pages were verified on `2026-08-13`:

| Reference | Behavior considered | Explicit non-transfer boundary |
|---|---|---|
| Camunda, [Testing process definitions](https://docs.camunda.io/docs/components/best-practices/development/testing-process-definitions/) | An invoice-approval example distinguishes approved, rejected, timeout, and archive-failure paths and recommends a readable happy-path test. | No Camunda engine, BPMN model, test code, or product architecture is transferred. |
| Camunda, [Creating readable process models](https://docs.camunda.io/docs/components/best-practices/modeling/creating-readable-process-models/) | Participant responsibilities and document archive/storage are shown as understandable parts of an invoice process. | The project retains its own bounded graph model and course-required UML artifacts. |
| n8n, [Automate document approvals with multi-level workflows](https://n8n.io/workflows/8174-automate-document-approvals-with-multi-level-workflows-using-supabase-and-gmail/) | An official-catalog, community-created template demonstrates document submission, persisted approval records, approve/reject interaction, and audit-oriented storage. | The project does not import the template, its nodes, Supabase/Gmail dependencies, or multi-level scope. |
| Temporal, [Error handling — Python SDK](https://docs.temporal.io/develop/python/best-practices/error-handling) and [Activity Definition](https://docs.temporal.io/activity-definition) | Transient and permanent failures require different handling; retries and side-effect idempotency are explicit design concerns. | No Temporal SDK/runtime is introduced and no Temporal-level durability guarantee is claimed. |

No Camunda, n8n, or Temporal workflow engine is introduced. Their source code, diagrams, report text, and complete product architecture are not transfer sources. Validation, resolver, retry, orchestration, choreography, persistence, trace, API, and UI remain independently implemented project work. Specific referenced pages must be listed in the final report's related-systems section.

## Representative user scenarios

Requirements v3 distinguishes these business paths in an approved project-level matrix of five paired-mode scenarios:

1. A valid invoice is submitted, approved, archived, and reported to the submitter.
2. A valid invoice is rejected by an approver with a visible reason and returned to the submitter.
3. A malformed/unsupported PDF or missing/invalid submitted metadata fails real bounded validation with a visible reason and creates no human approval work item.
4. A transient automatic-task failure is retried within its configured bound and then succeeds without traversing a retry edge.
5. An automatic task that exhausts its attempt bound follows normal failure routing to a controlled manual-action or unsuccessful terminal result.

Both execution modes must use the same accepted workflow definition, business input, retry rule, transition resolver, and normalized trace vocabulary. The requirements review must decide which scenarios require paired-mode executable acceptance evidence without creating an unnecessarily large matrix.

## Alignment with instructor recommendations

| Instructor recommendation or approved proposal element | Proposed response |
|---|---|
| Focus requirements on a problem or functionality rather than a solution or technology | State invoice submission, validation, approval, rejection, archiving, notification, and audit as user-visible behavior. |
| Provide balanced data/repository functionality | Persist invoices, workflow definitions/revisions, approval work items, runs, attempts, decisions, notifications, and trace; logical roles do not imply an identity subsystem. |
| Use third-party libraries, APIs, tools, or services where appropriate | Reuse a PDF-processing library and FastAPI/OpenAPI; optional external email remains deferred and is not required for acceptance. |
| Implement and motivate complex custom logic | Independently implement validation, conditional routing, retry, human-task continuation, orchestration, choreography, isolation, and trace. |
| Compare orchestration and choreography as two complex functions | Execute the same invoice workflow under both strategies using shared semantics. |
| Adopt event-driven architecture | Preserve run-scoped in-memory EventBus choreography and make approval/advancement events observable. |
| Describe complex functionality algorithmically | Update activity, sequence, state, class/domain, component, use-case, and deployment UML only after Requirements v3 approval. |
| Define user and system requirements with measurable acceptance conditions | Produce atomic Requirements v3 statements and trace each to a test or inspection method. |
| Maintain a prioritized backlog and sprint evidence | Refine the backlog only after change approval and preserve change-to-requirement-to-test links. |
| Keep all relevant figures, tables, and artifacts accessible in the report | Embed the final reviewed views and evidence rather than requiring navigation across unsubmitted files. |

## Explicit exclusions

- Full Camunda, n8n, Temporal, BPMN, or low-code-platform reproduction.
- Reuse of another product's workflow-engine implementation.
- Arbitrary user-supplied code or executor plugins.
- General-purpose drag-and-drop modeling parity with commercial products.
- Parallel fork/join, graph cycles, and retry edges.
- Real payment execution, banking integration, accounting certification, or legal-compliance claims.
- OCR, AI extraction, fraud detection, analytics, billing, and unrelated domain expansion.
- Kafka, ZooKeeper, distributed brokers, microservices, or distributed execution.
- External email as a mandatory acceptance dependency; internal notifications are sufficient for the bounded product path.
- Unsupported security, performance, availability, scalability, or fault-tolerance claims.
- Replacement of the shared transition resolver with mode-specific business rules.
- Describing referenced product behavior, unexecuted tests, or unpublished drafts as project implementation evidence.

## Alternatives considered

| Alternative | Evaluation | Decision |
|---|---|---|
| Continue the abstract defense-core demonstration unchanged | Preserves the smallest implementation scope but does not address the reported inability to understand the product's purpose. | Rejected |
| Replace the workflow project with a standalone invoice CRUD application | Makes the domain visible but discards the approved orchestration, choreography, routing, retry, and trace objective. | Rejected |
| Integrate Camunda, n8n, or Temporal as the runtime engine | Reduces implementation effort but delegates the complex custom logic the project is expected to demonstrate. | Rejected |
| Reproduce a complete commercial workflow platform | Exceeds the feasible solo academic scope and introduces many unrelated features. | Rejected |
| Apply one bounded invoice-approval reference application to the existing independently implemented engine | Preserves the approved technical core while making its user value concrete and testable. | Selected for review |

## Impact analysis

No impact listed below is approved or implemented by this request.

| Area | Anticipated change | Required control before implementation |
|---|---|---|
| Requirements | Replace the abstract operator-only defense path with user-visible invoice and approval behavior while preserving the validated graph, two modes, retry, isolation, and trace rules. | Requirements v3 review; preserve existing identifiers or record every replacement/retirement reason and update bidirectional traceability. |
| Stakeholders and use cases | Add submitter and approver goals; keep workflow operator and academic evaluator. | Reviewed use-case text and UML after requirements approval. |
| Domain model | Add invoice/document metadata, approval work item/decision, internal notification, task type, execution context, and waiting run state. | Domain ownership and lifecycle review; keep workflow-definition data separate from run/business state. |
| Persistence | Store business records and waiting/resume state; associate every execution record with one run and applicable invoice. | Schema and migration impact review; no access to or mutation of an existing database during the documentation checkpoint. |
| Validation | Validate task-type configuration in addition to graph rules and prevent unsupported executor types. | Atomic definition rules and focused negative cases. |
| Execution contract | Introduce an executor boundary so deterministic verification and real bounded task behavior return the same controlled domain outcomes. | Shared contract review; no task-name-dependent scenario semantics. |
| Human task lifecycle | Pause without marking success/failure, persist pending work, accept one decision, and resume the same run. | State-machine and concurrency review; idempotent duplicate-decision behavior specified before coding. |
| Orchestration | Central controller must stop at pending approval and resume through an application use case. | Updated sequence view and paired-mode acceptance conditions. |
| Choreography | Approval decision must advance through a run-scoped in-memory event while preserving persistence-before-dispatch and cleanup rules. | Event lifecycle/recovery review; no global subscriber state or broker fallback. |
| Retry and routing | Automatic failures remain bounded; human rejection is a business decision and must not be confused with infrastructure retry. | Outcome vocabulary decision in Requirements v3 and shared resolver review. |
| API/OpenAPI | Add bounded invoice upload, pending approval, decision, definition configuration, run status, and trace operations. | API behavior review after requirements; no endpoint names fixed by this request. |
| UI | Lead with invoice submission/status and pending approvals; keep workflow configuration and architecture comparison secondary. | Backend behavior verified before the revised UI checkpoint. |
| Third-party reuse | Select a maintained PDF-processing library for bounded validation. | Dependency/license review and adapter boundary; reused library is identified in the report. |
| Verification | Add business-path, pause/resume, duplicate-decision, paired-mode, retry, trace, isolation, and persistence cases. | New verification plan after requirements/architecture approval; no tests created or run under this request. |
| UML and report | Replace abstract-only defense narratives with user-visible use cases while retaining explicit orchestration/choreography algorithm views. | Only UML notation for the controlled views; render and visually inspect final diagrams. |
| Backlog and process | Insert change review, Requirements v3, architecture correction, implementation, verification, UI, and report work ahead of affected pending checkpoints. | Backlog refinement after CR-002 review; no fabricated sprint completion. |
| Published C5A | Preserve definition/run separation, validation, resolver, attempts, and trace concepts where compatible. | Focused compatibility review; C5A remains durable evidence and is not rewritten. |
| Unpublished C5B1 draft | Treat as disposable implementation exploration, not as approved progress. | Do not commit, merge, or use it as evidence before Requirements v3 and architecture decisions determine compatibility. |

## Quality impact

| Quality attribute | Anticipated effect | Main risk and control |
|---|---|---|
| Understandability | A concrete business object, actors, decisions, and outcomes should make product purpose visible. | UI and report may still lead with engine terminology; require a user-outcome-first demonstration review. |
| Functional suitability | Real validation and approval provide useful behavior beyond synthetic task indicators. | Avoid claiming accounting or payment capabilities that are not implemented. |
| Maintainability | A closed task catalog and executor boundary localize domain-specific behavior. | Prevent invoice rules from leaking into the shared resolver or both strategy implementations. |
| Testability | Deterministic adapters preserve repeatability while real validation supplies an understandable failure reason. | Separate business input from synthetic verification outcomes and normalize paired-mode evidence. |
| Reliability | Persistent waiting state, bounded retry, idempotent decisions, and trace improve recoverability and diagnosis. | Pause/resume and event cleanup increase state complexity; specify and test every state transition. |
| Observability | Invoice status, pending approval, decisions, retries, and terminal result become traceable to user-visible records. | Ensure business status and technical trace cannot silently disagree. |
| Scope control | One reference application limits the domain while retaining the reusable engine. | Reject full BPMN, external integrations, and unrelated invoice features at every gate. |

## New or changed risks requiring registration

- The product remains technically correct but incomprehensible because UI and report still lead with execution modes rather than the user's invoice result.
- Invoice functionality expands into accounting, OCR, AI extraction, payment, compliance, or a full commercial workflow platform.
- Human approval pause/resume introduces duplicate decisions, cross-run advancement, stale in-memory subscriptions, or unrecoverable waiting runs.
- Mode-specific code interprets approve/reject differently and breaks semantic parity.
- Task outcomes remain bound to demonstration task names and prevent configured workflows from executing correctly.
- PDF handling introduces unsafe filenames, uncontrolled storage, or malformed-file failures without a bounded validation response.
- Referenced-product behavior is represented as original implementation or copied implementation replaces the student's complex logic.

These risks must receive identifiers, mitigations, triggers, and verification gates before Requirements v3 is approved.

## Proposed checkpoint reset

CR-002 changes previously approved requirements and architecture assumptions. If approved, the controlled sequence becomes:

1. Review and approve or reject CR-002.
2. Produce and review Requirements v3 plus updated traceability.
3. Correct affected ADRs and UML; retain unaffected decisions explicitly.
4. Review the C5A foundation against the corrected architecture.
5. Implement the executor boundary and run/business-state foundation.
6. Implement and verify orchestration, choreography, waiting/resume, retry, and trace.
7. Implement the bounded invoice application and constructor APIs.
8. Execute the approved isolated verification plan.
9. Implement the user-outcome-first UI.
10. Verify persistence/deployment and reconcile the final report.

This is a controlled return to requirements and architecture for an affected scope, not a rewrite of preserved Git history and not a claim that completed C5A work never occurred.

## Acceptance gate

CR-002 proceeded to Requirements v3 after project-level review confirmed:

- the reference application clarifies rather than replaces the approved workflow project;
- the instructor recommendations are mapped without inventing an approval claim;
- included task types, actors, scenarios, and constructor behavior are bounded;
- the student's complex custom logic remains independently implemented;
- reuse sources and exclusions are explicit;
- human approval, persistence, event lifecycle, schema, UI, testing, and report impacts are complete;
- new risks are registered;
- C5A preservation and unpublished C5B1 treatment are explicit;
- no implementation, test, database, migration, commit, push, or release action is claimed by this request.

That gate passed at project level on `2026-08-13`, followed by separate Requirements v3 and architecture v3 approval. Requirements v3 is the current project-level specification baseline; Requirements v2 remains historical. Architecture v3 is the current project-level design baseline. C5A remains the latest published implementation foundation, and v3 implementation has not started.
