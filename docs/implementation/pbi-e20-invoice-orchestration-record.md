# PBI-E20 — Invoice Orchestration Record

| Field | Value |
|---|---|
| Status | `ACCEPTED — project-level implementation` |
| Date | `2026-08-13` |
| Requirements | `FR-015`, `FR-024`–`FR-026`, `FR-035`, `FR-042`–`FR-047` |
| Entry evidence | PBI-E18 and PBI-E19 accepted; `EV-038`, `EV-039` |
| Instructor approval | `NOT CLAIMED` |

## 1. User-visible outcome

Centralized orchestration now processes one submitted invoice until it either waits for an approver or reaches a terminal result. After a decision, the execution coordinator resumes the same run and cursor. The useful output is persisted business state: an archive record for approved invoices or a manual-action state after exhausted archive failures, followed by exactly one internal notification.

The five orchestration cases now cover approved, rejected, invalid, retry-then-archive, and exhausted-to-manual-action behavior. Mode comparison is not presented as the product result; it remains the later architectural comparison.

## 2. Control and policy ownership

`InvoiceOrchestrator` reads only committed cursor state. While the cursor is `READY`, it delegates automatic tasks to `AutomaticStepService` and human work to `HumanApprovalService`. It stops and returns at `WAITING_FOR_APPROVAL` or `TERMINAL`. `InvoiceExecutionCoordinator.decide_and_resume` commits the authoritative decision and then drives the same run.

The controller contains no invoice transition table, retry condition, attempt update, or SQLAlchemy dependency. The existing shared retry policy and resolver remain the only owners of retry and routing semantics. A positive controller safety bound protects against accidental non-progress without being used as workflow-cycle policy.

## 3. Archive, notification, and transaction effects

`ArchiveDocumentExecutor` accepts only an approved invoice with its controlled document identity. On success, the automatic-step transaction creates one archive record referencing that unchanged identity and sets the invoice to `ARCHIVED`. A retryable failure below the bound changes no invoice state and selects no transition. A final archive failure sets `NEEDS_MANUAL_ACTION` before the shared resolver follows the failure edge.

`CreateNotificationExecutor` runs only for `VALIDATION_FAILED`, `REJECTED`, `ARCHIVED`, or `NEEDS_MANUAL_ACTION`. Its successful step transaction creates one run-unique notification and records `NOTIFICATION_CREATED`. The final notification task has no outgoing edge, so its success completes the run.

## 4. Status and history projection

The isolated query service returns invoice state, run/cursor state and version, terminal decision, approval decision and reason when present, archive document identity, notification, and position-ordered trace for one run. It does not combine records from different runs.

## 5. Verification

Focused application and in-memory SQLAlchemy cases verify:

- central automatic progression, persistent waiting, same-run resume, terminal stop, mode rejection, and the safety bound;
- archive identity preservation and atomic archive/state effects;
- no manual-action effect during a permitted retry;
- manual-action state before failure routing after exhaustion;
- one notification describing each scenario's final business state;
- `S1` approved, `S2` rejected, `S3` invalid, `S4` retry then archive, and `S5` manual action;
- ordered trace, attempt counts, approval reason, archive presence/absence, and consistent status/history projection.

The final isolated repository suite reports `138 passed in 1.85s`. Tests use disposable storage and in-memory SQLite only.

## 6. Explicit limit and next gate

E20 verifies only centralized orchestration. Choreography, cross-mode parity, runtime/router composition, process-restart retention, constructor, final UI, migration, developer database, application startup, commit, push, deployment, and release remain outside this increment.

Next gate: PBI-E21 run-scoped in-memory choreography over the same automatic, approval, resolver, retry, effect, and query services.
