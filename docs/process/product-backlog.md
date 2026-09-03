# Product Backlog

## Delivered product backlog

Each item is written as a user story (actor, want, benefit), carries a relative story-point estimate used for the burndown below, and is tagged with the iteration that delivered it. See [sprint-record.md](./sprint-record.md) for what each iteration actually did.

| ID | User story | Points | Priority | Iteration | Status | Evidence |
|---|---|---:|---:|---:|---|---|
| PB-01 | As a workflow operator, I want to define and validate an acyclic conditional workflow, so that no unsafe or ambiguous configuration can ever be activated. | 3 | Must | 1 | Done | Domain validator tests |
| PB-02 | As an academic evaluator, I want the same workflow executed by orchestration and by choreography, so that I can compare the two control strategies under identical business rules. | 3 | Must | 2 | Done | Paired-mode scenario tests |
| PB-03 | As a workflow operator, I want the run cursor, attempts, trace, and terminal state persisted, so that a run's progress and history survive independently of any single request. | 2 | Must | 2 | Done | Persistence and restart tests |
| PB-04 | As a requester, I want to submit structured Purchase Request business data, so that my request is captured completely and unambiguously. | 2 | Must | 3 | Done | Submission/domain/API tests |
| PB-05 | As an approver, I want the run to pause for exactly one persistent human decision, so that I can review context and decide without racing another advancement. | 2 | Must | 3 | Done | Approval, idempotency, resume tests |
| PB-06 | As a requester, I want an approved purchase request authorized internally with the outcome recorded as a notification, so that I have one clear, final result to point to. | 2 | Must | 3 | Done | Business scenario matrix |
| PB-07 | As a requester, I want a temporary authorization failure retried automatically within a bound, and to be told when the bound is exhausted, so that a transient problem never silently stalls or loops my request forever. | 2 | Must | 4 | Done | Deterministic retry/manual-action scenarios |
| PB-08 | As a requester or approver, I want to see the purchase request's state, next action, result, mode, and trace in one place, so that I never have to guess what happened or what happens next. | 1 | Must | 4 | Done | Integrated runtime and UI tests |
| PB-09 | As a workflow operator, I want to configure bounded drafts and activate immutable revisions, so that I can safely change the process without breaking runs already in flight. | 2 | Should | 4 | Done | Constructor service/API/UI tests |
| PB-10 | As an academic evaluator, I want a waiting run to survive a real process restart, so that I can verify recovery is genuine and not just an in-memory illusion. | 2 | Should | 4 | Done | File-backed and process restart tests |
| PB-11 | As a workflow operator, I want one local or containerized deployment path, so that the system is reproducible without extra infrastructure. | 1 | Should | 5 | Done | Docker inventory and launcher tests |
| PB-12 | As an academic evaluator, I want the requirements, UML, report, and defense script kept synchronized, so that what I read matches what I can run. | 1 | Must | 5 | Done | Link, terminology, build, and visual review |

23 points total. Must-priority items were pulled first in every iteration; Should-priority configuration and deployment items (PB-09, PB-10, PB-11) were only pulled once the Must-priority business path for that iteration was already done, which is why they land inside Iteration 4 alongside Must items rather than earlier.

## Burndown

| After | Story points remaining |
|---|---:|
| Backlog start | 23 |
| Iteration 1 | 20 |
| Iteration 2 | 15 |
| Iteration 3 | 9 |
| Iteration 4 | 2 |
| Iteration 5 | 0 |

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
