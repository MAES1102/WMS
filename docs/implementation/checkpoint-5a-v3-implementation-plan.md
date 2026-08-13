# Checkpoint 5A v3 — C5A Compatibility and Foundation Plan

| Field | Value |
|---|---|
| Status | `APPROVED — project-level implementation plan` |
| Date | `2026-08-13` |
| Requirements baseline | [Requirements v3 3.0](../requirements/requirements-v3.md) |
| Design baseline | [Architecture v3](../architecture/architecture-overview-v3.md) |
| Controlled source base | `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` |
| Backlog item | `PBI-E17` |
| Implementation | `5A.1–5A.3 ACCEPTED — project-level foundation` |
| Instructor approval | `NOT CLAIMED` |

## 1. Decision

Continue in the existing repository and branch. Do not rebuild the project in a new repository and do not keep extending the incompatible prototype runtime. Preserve the published C5A domain core, evolve it through focused commits, and replace the old execution/API paths only when a verified v3 vertical path is ready.

This is an evolutionary cutover, not a hidden rewrite. Git history, approved requirements, C5A source, and retained domain policy remain continuous. The old runtime remains readable as historical compatibility code until its replacement is accepted; it is not allowed to become a second implementation of v3 behavior.

## 2. Source inspection result

The controlled source was inspected before this plan. The incompatibilities are concrete:

| Existing element | Evidence | v3 effect |
|---|---|---|
| Orchestration iterates `Task.order` | `app/engine/orchestrator.py` | Cannot execute the conditional DAG or shared resolver. |
| Choreography registers a handler chain for ordered tasks | `app/engine/choreography.py` | Cannot use a versioned persistent cursor or durable human waiting. |
| Task runner writes `Task.status`, `started_at`, and `finished_at` | `app/engine/task_runner.py` | Mutates definition state and breaks run isolation. |
| Outcomes use `random.random()` | `app/engine/task_runner.py` | Violates deterministic acceptance and classified failure policy. |
| Kafka producer/consumer and fallback exist | `app/engine/events.py`, `requirements.txt` | Violates the approved brokerless boundary. |
| HTTP status views read definition-task status | `app/routes.py` | Cannot show invoice/run/attempt state correctly. |
| Logs are an in-memory global list | `app/routes.py` | Cannot satisfy persistent ordered trace or restart retention. |
| Current models have no revision, invoice, cursor, approval, archive, or notification records | `app/models.py` | Required v3 ownership and waiting state do not exist. |
| Startup uses only `Base.metadata.create_all()` | `app/main.py` | It cannot alter an existing SQLite schema. |
| Existing execution tests patch randomness and assert mutable task status | `tests/test_execution.py` | They verify the superseded prototype, not Requirements v3. |
| README/UI lead with Kafka, abstract task indicators, and historical pass claims | `README.md`, `app/static/index.html` | They must be replaced after backend acceptance, not used as v3 evidence. |

## 3. Retain, extend, replace, and remove

| Disposition | Exact elements | Rule |
|---|---|---|
| Retain | `app/domain/resolver.py`; transition condition/outcome/terminal result concepts | Resolver precedence remains unchanged and invoice-independent. |
| Retain and extend | `app/domain/types.py`, `app/domain/validation.py` | Add controlled task type, executor result/failure vocabulary, revision configuration, and automatic-task bound validation. |
| Retain and extend | `WorkflowTransition`, `TaskAttempt`, `TraceEntry`, `WorkflowRun` concepts in `app/models.py` | Associate state with revision/invoice/run, add cursor/failure/waiting vocabulary, and preserve uniqueness/ordering. |
| Replace after vertical acceptance | `app/engine/orchestrator.py`, `app/engine/choreography.py`, `app/engine/task_runner.py`, execution/status portions of `app/routes.py` | No dual write and no v3 calls into mutable `Task.status`. |
| Remove at cutover | Kafka code in `app/engine/events.py`, `kafka-python`, Kafka/ZooKeeper deployment claims | Choreography uses one run-scoped in-memory EventBus only. |
| Replace later | `app/static/index.html`, stale README execution/deployment/report claims | PBI-E24/PBI-E26 follow executable acceptance evidence. |
| Preserve as historical until superseded | Existing prototype tests | They remain visible but are not counted as v3 acceptance; replacement/deletion occurs in the same commit as the incompatible runtime path. |
| Exclude | Unpublished C5B1 draft in the separate workspace | It is neither evidence nor a merge/copy source. |

## 4. Planned increments

### 5A.1 — Pure domain execution contracts

Authorized source scope:

- extend `app/domain/types.py` with the four controlled task types, failure classification, and immutable `TaskResult`;
- add `app/domain/retry.py` for the two-sided retry decision in `FR-022`;
- extend `app/domain/validation.py` so only automatic tasks require a positive attempt bound and unsupported task types are rejected;
- keep `app/domain/resolver.py` behavior unchanged;
- add focused pure tests under `tests/domain/` for result invariants, retry boundaries, graph validation, and resolver non-regression.

Acceptance:

- business, non-retryable, human, and exhausted results never retry;
- only retryable technical failure below the bound retries;
- retry selects no transition;
- the retained resolver produces the same specific/fallback/terminal decisions;
- domain modules import no FastAPI, SQLAlchemy, routes, engine, or ORM models.

### 5A.2 — V3 persistence ownership

Authorized source scope:

- split the current monolithic model declarations into cohesive model modules only if doing so reduces the reviewed diff; otherwise keep one model file for this increment;
- add mutable workflow draft and immutable workflow revision ownership;
- move task/transition definitions under a revision;
- add invoice, document identity, execution cursor, approval work item/decision, archive record, internal notification, extended automatic attempt, and expanded trace records;
- add database invariants for one work item per run/human task, one decision per work item, one attempt ordinal per run/task, one trace position per run, and a monotonic cursor version;
- make `WAITING_FOR_APPROVAL` an allowed run state;
- never add invoice/run state to definition-task rows.

Acceptance:

- metadata creates a fresh isolated v3 schema;
- constraint tests reject cross-run duplicates and invalid controlled values;
- one revision remains immutable after a run references it;
- no existing developer `workflow.db` is opened, modified, or used as test evidence.

Schema rule: `create_all()` is not a migration. Before the application runtime switches to v3 models, a separate reviewed decision must either introduce a repeatable SQLite migration or intentionally initialize a new v3 development database. Silent operation against the old schema is forbidden.

### 5A.3 — Shared executor and one-step service

Authorized source scope:

- add application/domain ports for a closed `TaskExecutor` registry;
- implement a deterministic fault adapter keyed by stable run/task input, never display name;
- implement one transaction-bounded step service that loads the cursor, invokes one automatic executor, persists attempt/result/trace, applies retry, and otherwise calls the retained resolver;
- use repository/unit-of-work ports so the domain policy remains ORM-independent;
- do not yet expose invoice submission or human-decision HTTP endpoints.

Acceptance:

- a fake repository test demonstrates one success route, one retry-then-success route, and one exhausted failure route;
- state and trace commit before any next control trigger;
- orchestration and choreography are not allowed to duplicate step policy.

## 5. Later vertical cutover order

1. PBI-E18: invoice submission, bounded document adapter, and `DOCUMENT_VALIDATION`.
2. PBI-E19: persistent `HUMAN_APPROVAL`, one decision, and exact same-run resume.
3. PBI-E20: orchestration over the shared one-step service.
4. PBI-E21: run-scoped choreography over the same service, then remove Kafka paths.
5. PBI-E22: form-based constructor and immutable activation.
6. PBI-E23: five paired business scenarios and restart/isolation/quality checks.
7. PBI-E24–PBI-E26: user-outcome-first UI, deployment evidence, report/reuse disclosure.

The first end-to-end v3 route must coexist with old prototype routes only behind separate endpoints and persistence objects. Once the paired v3 route is accepted, the corresponding old route/test/runtime path is removed in that same checkpoint. No request writes both models.

## 6. Planned commit shape

Commits remain focused and natural:

1. `docs: approve invoice workflow requirements and architecture`
2. `feat(domain): add typed task results and retry policy`
3. `feat(persistence): add invoice workflow revision and run state`
4. `feat(execution): add shared executor step service`

These are proposed subjects, not created commits. Staging, commit, and push require separate explicit approval after each reviewed diff.

## 7. Verification boundary

For each implementation increment:

- run only isolated tests against disposable storage;
- report exact collected/passed/failed counts;
- run import-boundary, formatting, and `git diff --check` checks;
- inspect the complete diff and status before requesting commit approval;
- do not start the server, touch the developer database, or claim deployment/restart evidence unless that checkpoint explicitly authorizes it.

## 8. Risks controlled

This plan directly controls RK-002–RK-008, RK-012, and RK-015–RK-021. It prevents a second hidden product, dual runtime writes, accidental use of the old database, copied external-engine implementation, unbounded scope, and misleading green-indicator demonstrations.

## 9. Current execution record

PBI-E17 planning and increments 5A.1–5A.3 are complete at project level. Increment 5A.1 adds the closed task catalog, failure classification, immutable executor result, pure retry policy, v3 validation changes, and focused domain tests. Syntax compilation, domain import-boundary inspection, `git diff --check`, an eight-assertion direct domain smoke run, and the focused pytest suite passed.

The active Python initially lacked pytest and the offline package cache lacked the requirements. No installation was performed. An existing isolated audit environment contained pytest 8.3.4 dependencies; using its `site-packages` with the current Python produced `29 passed in 0.02s` for `tests/domain`.

Increment 5A.2 adds an isolated v3 persistence model with 15 draft/revision/invoice/run/cursor/attempt/approval/archive/notification/trace tables. Its suite created and dropped only an in-memory SQLite schema and reported `8 passed in 0.07s`.

Increment 5A.3 adds an ORM-independent automatic-executor port and complete closed registry, a deterministic fault adapter keyed by `(run_id, task_id, attempt_ordinal)`, an optimistic-versioned unit-of-work command, and one shared automatic-step service. Fake-unit-of-work cases verify success routing, retry without transition, success after retry, exhaustion through normal failure routing, human/stale-cursor rejection before execution, and commit-before-next-trigger ordering. Its final focused suite reported `8 passed in 0.02s`; rechecks reported 29 domain and 8 persistence passes.

The prototype models/runtime were not changed and no request performs dual writes. PBI-E17 is accepted at project level; PBI-E18 bounded invoice submission/document validation is the next controlled increment. No real repository adapter, endpoint, PDF processing, developer database change, migration, commit, push, application startup, deployment, or release is established.
