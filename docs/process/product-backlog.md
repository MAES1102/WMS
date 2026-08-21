# Product Backlog

## Delivered product backlog

| ID | User or product outcome | Priority | Status | Evidence |
|---|---|---:|---|---|
| PB-01 | Define and validate an acyclic conditional workflow | Must | Done | Domain validator tests |
| PB-02 | Execute the same workflow by orchestration and choreography | Must | Done | Paired-mode scenario tests |
| PB-03 | Persist run cursor, attempts, trace, and terminal state | Must | Done | Persistence and restart tests |
| PB-04 | Submit structured Purchase Request business data | Must | Done | Submission/domain/API tests |
| PB-05 | Pause for one persistent human approve/reject decision | Must | Done | Approval, idempotency, resume tests |
| PB-06 | Authorize approved purchase requests internally and record the final notification | Must | Done | Business scenario matrix |
| PB-07 | Retry transient authorization failure and handle exhaustion | Must | Done | Deterministic retry/manual-action scenarios |
| PB-08 | Show purchase request state, next action, result, mode, and trace | Must | Done | Integrated runtime and UI tests |
| PB-09 | Configure bounded drafts and activate immutable revisions | Should | Done | Constructor service/API/UI tests |
| PB-10 | Survive process restart while waiting for approval | Should | Done | File-backed and process restart tests |
| PB-11 | Provide one-service local/container deployment | Should | Done | Docker inventory and launcher tests |
| PB-12 | Deliver synchronized requirements, UML, report, and defense script | Must | Done | Link, terminology, build, and visual review |

## Intentionally excluded

| Candidate | Decision |
|---|---|
| Payment or banking execution | Excluded: the product approves purchase requests; it does not move money. |
| Automated content extraction and fraud detection | Excluded: unnecessary for the bounded course objective. |
| Authentication and organizational authorization | Future work: logical roles are sufficient for the demonstration. |
| Kafka, microservices, durable distributed messaging | Excluded: one process is the accepted deployment boundary. |
| Full BPMN/drag-and-drop low-code platform | Excluded: constructor is deliberately closed and form-based. |
| Arbitrary scripts, plugins, or user executors | Excluded for safety and scope control. |
| Fork/join and cyclic workflows | Future research; current engine is a conditional DAG. |
| External email/accounting systems | Future adapters; internal notification is the accepted outcome. |
