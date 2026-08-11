# Sprint Record

## Interpretation

The baseline and prototype reports describe three one-week delivery sprints and one evolution sprint. Git verifies final snapshots and artifact presence, but it does not provide a commit series mapped cleanly to each sprint. Intended objectives below come from historical documentation and are `RECONSTRUCTED`; outputs are `VERIFIED` only where the durable repository directly supports them.

No calendar dates, meeting attendance, daily Scrum record, approval event, velocity, story point total, or contemporaneous burndown is inferred here.

## Delivery Sprint 1

| Field | Record |
|---|---|
| Intended objective | Establish data models, database access, and CRUD API (`RECONSTRUCTED` from the report). |
| Verifiable output | Baseline contains FastAPI routes, SQLAlchemy models, SQLite configuration, and CRUD-oriented tests (`VERIFIED` as final artifact presence). |
| Reconstructed information | Backlog selection, internal task sequence, and claimed sprint review/retrospective. |
| Missing evidence | No durable sprint-start snapshot, dated Sprint Backlog, ceremony record, contemporaneous test result, or day-by-day progress record. |
| Review status | Historical review status is `UNVERIFIED`; final artifact exists. |
| Retrospective lesson | Future increments must produce verification evidence inside the same checkpoint rather than relying on later narrative. |

## Delivery Sprint 2

| Field | Record |
|---|---|
| Intended objective | Add linear orchestration, choreography, EventBus behavior, and run records (`RECONSTRUCTED`). |
| Verifiable output | Baseline contains orchestration, choreography, EventBus/Kafka adapter code, task runner, and workflow-run persistence (`VERIFIED` as final artifact presence). |
| Reconstructed information | The precise order of implementation, BUG-02 discovery timing, manual review activity, and retrospective actions. |
| Missing evidence | No sprint boundary commit, durable manual-test record, Kafka verification evidence, or contemporaneous review minutes. |
| Review status | Historical review status is `UNVERIFIED`; code presence does not prove the reported ceremony. |
| Retrospective lesson | Shared behavior needs deterministic tests and explicit transport scope before a feature is described as complete. |

## Delivery Sprint 3

| Field | Record |
|---|---|
| Intended objective | Add UI, broader tests, bug fixes, deployment material, UML, and consolidated reporting (`RECONSTRUCTED`). |
| Verifiable output | Baseline contains a dashboard, three test modules with 21 test functions, Docker Compose, README, and an embedded report/UML set (`VERIFIED` as artifact presence). |
| Reconstructed information | Claimed backlog commitment, review, retrospective, velocity, and burndown. |
| Missing evidence | No independent durable execution proving the historical 21-pass claim; no contemporaneous chart source or dated ceremony evidence. |
| Review status | Final submission commit exists; detailed sprint acceptance is `UNVERIFIED`. |
| Retrospective lesson | Test definitions and reports are not substitutes for reproducible test results, and process evidence must be captured when the work occurs. |

## Evolution Sprint

| Field | Record |
|---|---|
| Intended objective | Evolve the linear workflow toward conditional execution and stronger run isolation (`RECONSTRUCTED` for the historical prototype; `PLANNED` for defense core). |
| Verifiable output | The advanced prototype is preserved at `archive/advanced-prototype`; it contains transition, graph, task-execution, seed, UI, and additional test artifacts (`VERIFIED` as content). Stage 1 refs are preserved locally and remotely (`VERIFIED`). |
| Reconstructed information | The archive report’s Sprint 4 task sequence, points, burndown, reviews, and claimed 27-test result. |
| Missing evidence | No contemporaneous sprint record and no conclusive archive test run. The archive contains 34 test functions while its documentation claims 27. |
| Review status | Preservation is complete. [CR-001](../evolution/CR-001-defense-core-refactoring.md) is approved for progression to Requirements v2 only; Requirements v2 has not started; implementation remains `NOT STARTED`; release remains `NOT SCHEDULED`. |
| Retrospective lesson | Start from an immutable baseline, classify historical evidence, approve impact before requirements/design, and port only bounded capabilities. |

## Burndown limitation

No contemporaneous source data has been found that can substantiate a burndown chart for any sprint. Historical charts in reports may be retrospective reconstructions and must not be presented as measured daily evidence. No replacement chart is fabricated in this checkpoint.

Related records: [development process](./development-process.md), [product backlog](./product-backlog.md), [evidence register](./evidence-register.md), and [feedback register](./feedback-register.md).
