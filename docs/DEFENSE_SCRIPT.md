# Defense Script - Event-Driven Workflow Management System

## Opening (about 40 seconds)

This project helps a small organization control repeatable approval processes. A requester submits structured purchase information, a manager receives persistent approval work, and the system records the decision, resumes safely after waiting or restart, retries temporary automatic failures, and retains an audit history. Purchase Request Approval is the reference process.

The professor approved the Event-Driven Workflow Management System direction and accepted orchestration and choreography as the two complex functionalities. Purchase Request Approval is my final reference scenario for explaining that direction; I do not claim that the professor separately approved the scenario or every design decision.

## Demonstration sequence (7-10 minutes)

### 1. Real-world problem (45 seconds)

Small organizations can lose status, ownership, and decision history when approvals are handled through messages and spreadsheets. This system creates one visible process state and ordered evidence. It is an approval-control system, not an ordering, accounting, or payment system.

### 2. Requester and useful outcome (40 seconds)

Open `/ui`. Identify the requester, approver, and process owner. The useful outcome is a validated, rejected, internally authorized, or manual-action state with a notification and audit history.

### 3. Structured request submission (55 seconds)

In **1. Submit Request**, show requester, department, item or service, supplier, amount, currency, justification, and required date. Submit the prepared example in orchestration mode. Point out that the payload is structured business data and that no purchase order or payment is created.

### 4. Persistent human approval (70 seconds)

Show `PENDING_APPROVAL` and open **2. Approver Inbox**. Explain that the submission request has finished: the approval work item, run, cursor, and trace are stored in SQLite. The system is not holding an HTTP request or EventBus subscription while the manager decides. Approve the item once.

### 5. Final Purchase Authorization (45 seconds)

Open **3. Run Status / History** and show `AUTHORIZED`, the Purchase Authorization identifier, internal notification, and ordered technical audit trace. State clearly: Purchase Authorization is an internal record of approval. It does not place an order, reserve funds, contact a supplier, or transfer money.

### 6. Retry or restart evidence (75 seconds)

Open **Demonstration Controls**, select **Temporary failure, then retry success**, and repeat the approval path. Show two authorization attempts, the retry observation, and final `AUTHORIZED`. Explain that retry repeats the current automatic task without selecting an edge. If asked about restart, cite the two integration tests that start a real Uvicorn process, stop it at the human wait, start a new process against the same isolated database, and resume the same run in orchestration and choreography.

### 7. Bounded Workflow Designer (55 seconds)

Open **4. Workflow Designer**. Show the closed catalog: `REQUEST_VALIDATION`, `HUMAN_APPROVAL`, `PURCHASE_AUTHORIZATION`, and `CREATE_NOTIFICATION`. Demonstrate validation and immutable activation. Emphasize that task keys, names, start marker, transitions, and automatic attempt bounds are configurable, but scripts, expressions, plugins, arbitrary task types, cycles, and fork/join are excluded.

### 8. Orchestration and choreography comparison (70 seconds)

Run or show the equivalent choreography case. Both modes use the same revision, executors, retry policy, transition resolver, database, and business effects. Orchestration owns advancement in a central loop. Choreography uses a temporary synchronous run-scoped `AdvanceRun` handler. The database cursor is authoritative; this is not distributed choreography and there is no durable message broker.

### 9. Custom logic and architecture (60 seconds)

Show the activity, component, and sequence diagrams. The custom logic includes graph validation, deterministic transition resolution, bounded retry, persistent cursor and wait/resume, idempotent approval decisions with conflict detection, immutable revisions, run isolation, ordered trace, and the two control strategies. The deployment is one modular FastAPI application with one SQLite database. The final unchanged suite reports **98 passed**.

### 10. Limitations and close (40 seconds)

This is a bounded academic prototype. It has no authentication or RBAC, external procurement or accounting integration, supplier communication, email delivery, durable broker, distributed execution, high availability, or production security and scalability evidence.

Closing sentence: The engineering contribution is controlled workflow behavior across failure and time: invalid input cannot reach approval, retries are bounded, a human decision can arrive after restart, duplicate decisions cannot advance a run twice, and both control strategies preserve the same business meaning.

## Difficult questions and concise answers

| Question | Concise answer | Evidence to show |
|---|---|---|
| What problem does it solve? | It makes repeatable approvals visible, resumable, and auditable for a small organization. | Submit, Inbox, Status views and context diagram. |
| What is the final business result? | An internal Purchase Authorization after approval, or a controlled rejected, invalid, or manual-action result. | Run status and persisted effects. |
| Does authorization place an order? | No. It is an internal record only; ordering, funds, suppliers, and payments are outside scope. | UI boundary text and limitations. |
| Why two execution modes? | They compare control ownership while holding revision, rules, persistence, and outcomes constant. | Paired sequence diagrams and scenario tests. |
| Is choreography distributed? | No. It uses a synchronous in-process EventBus with a temporary run-scoped handler. | Component/choreography diagrams and `event_bus.py`. |
| Why no Kafka? | One-process comparison does not require broker operations; durable state is stored in SQLite. | Deployment diagram and Compose configuration. |
| What survives restart? | Revision, request, run, cursor, attempts, approval work, decision, effects, and trace. EventBus handlers do not. | Restart tests and persistence model. |
| How are duplicates handled? | Repeating the same decision returns the existing result; a conflicting decision is rejected without advancing state. | Approval service tests. |
| What is configurable? | Safe task definitions and transitions inside a closed four-type catalog; activated revisions are immutable. | Workflow Designer and constructor tests. |
| What is genuinely custom? | Validator, resolver integration, retry order, cursor lifecycle, approval semantics, isolation, trace, and both control strategies. | Source-to-test traceability table. |
| How is failure demonstrated? | An explicit deterministic adapter produces standard, retry-then-success, or exhausted authorization behavior. | Demonstration Controls and retry tests. |
| Why only 98 tests? | That is the exact collected and passing repository suite after final consolidation; quality is reported by coverage categories and scenarios, not inflated counts. | Cache-suppressed pytest output. |
| What would come next? | Authentication/RBAC, external procurement adapters, durable messaging only if distribution is required, and measured usability/security work. | Limitations and future-work section. |

## Statements to avoid

- Do not say the system processes payments, places orders, reserves budgets, or contacts suppliers.
- Do not call the EventBus distributed, durable, asynchronous, or exactly-once.
- Do not claim production deployment, performance, scalability, penetration testing, or user-research results.
- Do not claim the professor approved Purchase Request Approval or every architecture choice.
- Do not call the Workflow Designer a general low-code or BPMN platform.
- Do not quote any test count other than the current verified **98 passed**.
- Do not describe demonstration failures as real third-party failures.

## Evidence checklist

- Four current browser views with meaningful Purchase Request data.
- Authorized run and Purchase Authorization identifier.
- Retry observation and attempt sequence.
- Current UML SVGs.
- `98 passed` output from the unchanged suite.
- Restart tests for both modes.
- OpenAPI route list and single-service Compose validation.
- Final report, CR-003, reuse disclosure, and limitations.
