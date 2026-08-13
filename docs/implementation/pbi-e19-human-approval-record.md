# PBI-E19 — Persistent Human Approval Record

| Field | Value |
|---|---|
| Status | `ACCEPTED — project-level implementation` |
| Date | `2026-08-13` |
| Requirements | `FR-036`–`FR-042`, `NFR-003`, `NFR-007` |
| Entry evidence | PBI-E18 accepted; `EV-038` |
| Instructor approval | `NOT CLAIMED` |

## 1. User-visible outcome

After successful document validation reaches `HUMAN_APPROVAL`, the same invoice run stops in persistent waiting state. An approver can list pending items, inspect invoice/run context, and approve or reject once. The accepted decision changes the invoice state, resolves the human task through the shared resolver, and makes the same versioned cursor ready at its successor.

## 2. Transaction boundaries

Entering waiting commits one work item, invoice `PENDING_APPROVAL`, run/cursor `WAITING_FOR_APPROVAL`, the next state version, and ordered trace together. A decision commits one authoritative decision row, work-item state, invoice `APPROVED` or `REJECTED`, the same run/cursor resume, selected transition or terminal result, and trace together.

Unique work-item/decision constraints and conditional cursor updates protect concurrent delivery. Identical decision replay returns the authoritative result without another write; a conflicting later choice raises a controlled conflict. Human outcomes do not enter automatic retry.

## 3. Presentation boundary

The separate v3 approval router provides pending list, work-item detail, and decision endpoints. List/detail lead with invoice metadata, document identity, business state, run status, and cursor version. Decision responses expose outcome, committed version, replay status, and whether a control strategy must continue the run.

Presentation depends only on application/domain contracts. The router remains unregistered in prototype `main.py` until database/runtime composition is reviewed.

## 4. Verification

Focused cases verify:

- one durable pending item and idempotent duplicate entry;
- reconstruction through a new SQLAlchemy session;
- approve success routing and reject failure routing;
- trimmed rejection reason and bounded decision payloads;
- identical replay, conflicting replay, and stale-version behavior;
- database-race rollback of decision, invoice state, cursor, and trace;
- two-run isolation;
- pending list/detail and controlled HTTP decision responses.

The final isolated combined suite reports `104 passed in 1.09s`. Tests use only in-memory SQLite and disposable storage.

## 5. Explicit limit and next gate

E19 resumes the authoritative same-run cursor and returns a single continuation signal. It does not yet implement orchestration or choreography driving to terminal; E20 and E21 own those control strategies. No process-restart test, prototype runtime registration, migration, developer-database access, application startup, commit, push, deployment, or release is claimed.

Next gate: PBI-E20 invoice orchestration over the shared automatic and human-step services.
