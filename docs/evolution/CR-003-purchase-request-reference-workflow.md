# CR-002 — Purchase Request Approval Reference Application

| Field | Value |
|---|---|
| Category | Product-purpose clarification and bounded functional extension |
| Trigger | Earlier demonstration did not communicate useful product behavior |
| Decision | Apply the existing workflow core to one Purchase Request Approval product |
| Status | Implemented in the project repository |
| Academic approval | Final acceptance remains the professor's decision |

## Problem

The original workflow prototype could execute tasks through orchestration and choreography, but a demonstration of green nodes and a synthetic failure did not answer three basic questions:

1. What real problem does the system solve?
2. Why does a task succeed or fail?
3. What useful result does the user receive?

Student-reported instructor feedback identified this comprehension gap. The private conversation is not stored in the repository, so the feedback is treated as reconstructed project input rather than quoted evidence.

## Approved project response

Retain the independently implemented workflow capabilities and apply them to a bounded process:

> A submitter uploads an purchase request structured purchase request data. The system validates the submission, pauses for a human approve/reject decision, resumes the same persisted run, authorizations an approved document or records a controlled negative outcome, creates an internal notification, and preserves an audit trace.

Orchestration and choreography remain the two compared control strategies. They are not separate products and they do not own separate business rules.

## Included scope

- bounded purchase request metadata and structured input submission;
- real metadata and structured input validation without OCR;
- persistent human approval work item and idempotent decision;
- same-run waiting and resume;
- authorization and internal notification records;
- deterministic retry-success and retry-exhaustion demonstrations;
- ordered audit trace and business-state projection;
- bounded workflow drafts and immutable activated revisions;
- one FastAPI/SQLite deployment with no broker.

## Preserved custom core

- directed-graph validation;
- `SUCCESS`/`FAILURE`/`ALWAYS` resolver precedence;
- retry classification and attempt bounds;
- run isolation and persistent cursor;
- centralized orchestration;
- run-scoped EventBus choreography;
- transactionally ordered trace.

## Explicit exclusions

- payment or banking execution;
- accounting certification;
- OCR, AI extraction, fraud detection, and analytics;
- authentication/authorization infrastructure;
- external email or accounting integration;
- Kafka, microservices, and distributed workflow engines;
- full BPMN, fork/join, cycles, arbitrary scripts, and plugins.

## Product references and reuse boundary

Camunda, n8n, and Temporal were consulted as behavioral references for human work, workflow history, and retry concerns. No external workflow engine, process definition, UI, diagram, or source code was copied into the project. Runtime libraries and references are listed in [REUSE_DISCLOSURE.md](../REUSE_DISCLOSURE.md).

## Acceptance scenarios

| Scenario | Result |
|---|---|
| Valid and approved | Request authorized and notification created |
| Valid and rejected | Rejection reason recorded; authorization skipped |
| Invalid metadata/structured input | Validation failure; no approval work item |
| Temporary authorization failure | One bounded retry followed by authorization success |
| Authorization unavailable | Attempt bound exhausted; manual action recorded |

Every scenario is verified in both execution modes. The dashboard makes the business state primary and exposes the technical trace only as supporting evidence.

## Impact summary

| Area | Change |
|---|---|
| Requirements | Added purchase request, approval, authorization, notification, constructor, and UI outcomes |
| Architecture | Added executor boundary, persistent cursor/waiting, document adapter, and immutable revisions |
| Persistence | Added purchase request-owned run, work item, attempt, authorization, notification, and trace records |
| UI | Replaced abstract node-first demonstration with purchase request submission and status |
| Verification | Added five paired scenarios, retry, restart, isolation, structured input, constructor, and deployment checks |
| Documentation | Reconciled requirements, ADRs, UML, report, reuse disclosure, and defense script |
