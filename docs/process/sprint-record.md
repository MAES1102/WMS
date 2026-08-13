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
| Review status | Preservation is complete. At the historical Stage 2 approval boundary, [CR-001](../evolution/CR-001-defense-core-refactoring.md) was approved for progression to Requirements v2 only and Requirements v2 had not started. Requirements v2 was subsequently drafted; r4 passed final substantive review, and the approved Stage 3 baseline is established by the Stage 3 documentation commit. Implementation remains `NOT STARTED`; release remains `NOT SCHEDULED`. |
| Retrospective lesson | Start from an immutable baseline, classify historical evidence, approve impact before requirements/design, and port only bounded capabilities. |

## Requirements v2 approval checkpoint

| Field | Record |
|---|---|
| Entry state | Stage 2 is committed at `6a5e42c6fa5d4d71fd599d606d7c805e95177b2f`; CR-001 is approved for progression to Requirements v2 only. |
| Drafting activity | Requirements v2 and its traceability record were drafted from approved CR-001 and evidence-classified baseline/prototype inspection. |
| Review status | The r1 substantive review identified narrow corrections to attempt-bound applicability, the `FR-006`/`FR-021` dependency cycle, `NFR-005` verification alignment, and `NFR-008` clarity. The r2 substantive re-review then identified the remaining `FR-017`/`FR-027` dependency cycle, the incomplete retry obligation in `FR-022`, and the checkpoint-misaligned dependency in `NFR-008`. Final review of r3 identified the stale `NFR-006` brokerless-choreography cross-reference. The corrected r4 passed final substantive review, and the approved Requirements v2 baseline is established by the Stage 3 documentation commit. |
| Verification status | Documentation checks only; no executable test was created or run. |
| Later checkpoints | Architecture/UML and implementation remain not started. |
| Release status | `NOT SCHEDULED` |

## Burndown limitation

No contemporaneous source data has been found that can substantiate a burndown chart for any sprint. Historical charts in reports may be retrospective reconstructions and must not be presented as measured daily evidence. No replacement chart is fabricated in this checkpoint.

## Checkpoint-4 architecture/UML approval record

| Field | Record |
|---|---|
| Entry state | Requirements v2 remains the approved Stage 3 baseline at `6074fd7ef490ea3b08177e7a786035159f39a91c`; checkpoint-4 drafting starts from the post-push consistency correction `b5c7da9e51382bb418f017790ae944c8dff26a06`. |
| Authorized scope | Architecture decisions, architecture overview/traceability, and matching PlantUML sources only. |
| Artifact manifest | `docs/architecture/architecture-overview.md`; `docs/architecture/architecture-decisions.md`; `docs/architecture/architecture-traceability.md`; `docs/architecture/uml/system-context-use-cases.puml`; `docs/architecture/uml/component-view.puml`; `docs/architecture/uml/domain-model.puml`; `docs/architecture/uml/orchestration-sequence.puml`; `docs/architecture/uml/choreography-sequence.puml`; `docs/architecture/uml/routing-retry-activity.puml`; `docs/architecture/uml/run-state.puml`; `docs/architecture/uml/deployment-view.puml`. |
| Controlled record updates | Requirements traceability, development process, evidence register, feedback register, product backlog, and this sprint record. |
| Course sources inspected | `9 - sw architecture.pdf`, slides 24–26, 38, 41–43, 47–49, 92–93, 96, 100–106, 110–111, 129–130, and 143–145; `7 - modeling.pdf`, slides 67, 69–70, 86–87, 95–96, 109, 115–117, 146–147, and printed slide 161. |
| Review status | The r2 architecture review passed substantive project review; the architecture/ADR/UML set is the `APPROVED — checkpoint 4 architecture baseline`, and all seven ADRs are `ACCEPTED — checkpoint 4 architecture baseline`. Git durability of the accepted architecture baseline is established by commit f44f0d55349af4e7b1b19b49f5e3b26c67c96181 and the independently verified origin/refactor/defense-core ref. |
| Implementation and verification | No implementation or executable test was created or run; both remain `NOT STARTED`. |
| Later checkpoints | Checkpoint 5 remains `NOT STARTED`; no schema, endpoint, UI, configuration, deployment, or final-report work began. |
| Release status | `NOT SCHEDULED` |

Related records: [development process](./development-process.md), [product backlog](./product-backlog.md), [evidence register](./evidence-register.md), and [feedback register](./feedback-register.md).
