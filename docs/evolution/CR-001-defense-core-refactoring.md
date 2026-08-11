# CR-001: Controlled evolution from the linear baseline to the defense-core workflow engine

## Metadata

| Field | Value |
|---|---|
| ID | `CR-001` |
| Title | Controlled evolution from the linear baseline to the defense-core workflow engine |
| Status | `APPROVED — proceed to Requirements v2` |
| Change category | Planned system enhancement with preventive refactoring |
| Baseline | `v1-linear-baseline` / `f5ea4d71ebb4082cebe4f7e7a8a5ad3fcdfbfbaa` |
| Historical prototype | `archive/advanced-prototype` / `5d18b469b77beb22e6721f769fbd1b39223955a3` |
| Target branch | `refactor/defense-core` |
| Creation date | `2026-08-11` |
| Review decision date | `2026-08-11` |
| Approval authority | Project reviewer; this does not claim additional instructor approval |
| Implementation status | `NOT STARTED` |
| Release status | `NOT SCHEDULED` |

This request is approved for Requirements v2 only. Implementation remains NOT STARTED and release remains NOT SCHEDULED.

## Problem statement

The preserved baseline provides a known configuration foundation; its linear, order-based execution paths are `VERIFIED` as source presence in [EV-018](../process/evidence-register.md), not as a current runtime result. The advanced prototype's transition, graph, and per-run execution concepts are likewise `VERIFIED` as source and test-artifact presence in [EV-019](../process/evidence-register.md) and [EV-020](../process/evidence-register.md), without implying successful execution.

The prototype source retains and writes definition-level and run-level runtime state ([EV-021](../process/evidence-register.md)); its graph artifacts permit backward/self edges with loop guards ([EV-022](../process/evidence-register.md)); and its documentation/test-count drift is recorded in [EV-014](../process/evidence-register.md). These verified source and artifact facts support the architectural-debt interpretation, but do not constitute runtime verification. Kafka/ZooKeeper source and configuration presence is `VERIFIED` in [EV-023](../process/evidence-register.md), while Kafka runtime completeness remains `UNVERIFIED` in [EV-024](../process/evidence-register.md). The only historical execution result remains `INCONCLUSIVE — interrupted during initial collection` ([EV-008](../process/evidence-register.md)); it is not a pass or failure result.

Neither preserved state should become the final defense system unchanged. Direct continuation from the prototype would import the evidence-linked infrastructure and architectural risks above; leaving the baseline unchanged would not meet the proposed workflow-evolution objective.

## Requested outcome

The final defense core is intended to provide:

- a conditional directed acyclic workflow graph;
- deterministic `SUCCESS`, `FAILURE`, and `ALWAYS` transition selection;
- one shared workflow model for orchestration and choreography;
- run-specific execution state;
- isolated concurrent and sequential workflow runs;
- bounded retry with persistent retry state;
- a shared `TransitionResolver` concept;
- centralized orchestration;
- in-memory EventBus choreography;
- persistent execution trace;
- deterministic success, retry-then-success, and permanent-failure scenarios;
- one clear UI demonstration path;
- one FastAPI deployment with persistent database storage.

These are anticipated outcomes, not implemented changes.

## Explicit exclusions

- Kafka and ZooKeeper.
- Distributed-broker dependencies.
- Unsupported microservice claims.
- Arbitrary graph cycles.
- Parallel fork/join.
- Distributed execution.
- Random outcomes.
- External business services.
- Mutable runtime state stored on workflow-definition tasks.
- Unrelated feature expansion.

Retrying a task must use an explicit bounded policy and persistent attempt state; it must not require a graph cycle.

## Alternatives considered

| Alternative | Evaluation | Decision |
|---|---|---|
| Keep the linear baseline unchanged | Lowest immediate change risk, but cannot demonstrate conditional workflow semantics or run-specific execution behavior | Rejected |
| Continue directly from the advanced prototype | Retains the source concepts in EV-019 and EV-020, but also retains the classified source/artifact concerns in EV-014 and EV-021 through EV-024 | Rejected |
| Port the entire advanced prototype | Preserves maximum code but defeats controlled scope and imports the evidence-linked architectural risks identified in the problem statement | Rejected |
| Rebuild every component from scratch | Could produce a clean design but discards verified baseline behavior and creates unnecessary regression/schedule risk | Rejected |
| Start from the linear baseline and selectively reimplement or transfer approved capabilities through checkpoints | Preserves a clean configuration while allowing each concept to be reviewed, traced, and verified | Selected — approved to proceed to Requirements v2 |

## Anticipated impact analysis

No impact below is an implemented change.

| Area | Anticipated impact | Required control/evidence |
|---|---|---|
| Requirements | New observable routing, run isolation, retry, trace, UI, and persistence behavior must be specified; exclusions must be normative | Requirements v2 is required after CR-001 approval; no final requirement identifiers are assigned in this checkpoint. |
| Domain model | Separate workflow definitions from run and task-execution state; represent conditional DAG transitions and persistent retry/trace concepts | Reviewed domain model and traceability |
| Persistence/schema | Add or reshape persistent entities and constraints without relying on mutable task-definition state | Schema impact review, migration strategy, isolated and restart verification |
| Transition resolution | Define deterministic outcome matching, priority/tie rules, start/end semantics, validation, and DAG constraints | Shared resolver design and focused tests |
| Orchestration | Replace fixed-order control with central traversal of the approved shared model | Same scenario expectations as choreography |
| Choreography | Use in-memory EventBus reactions with the same resolver and persistent state; no broker path | Event sequencing, cleanup, isolation, and semantic-parity tests |
| API | Expose only operations needed to define, execute, inspect, and demonstrate the approved core | Requirements/API review before endpoint work |
| UI | Reduce to one clear demonstration path for definition, execution mode, deterministic scenario, and persistent trace | Backend tests complete before UI gate |
| Tests | Add six focused execution tests first, then regression and persistence checks as approved | Exact isolated results; no historical pass claim reuse |
| UML | Replace historical drift with reviewed static and dynamic views matching the approved design | ADR/UML checkpoint before implementation |
| Documentation | Update evidence, traceability, backlog, risks, and final report only as each gate completes | Evidence classification and link validation |
| Deployment | Remove broker services and provide a single FastAPI deployment with persistent database storage | Restart-retention verification |

## Quality impact

| Quality attribute | Anticipated effect | Main risk/control |
|---|---|---|
| Maintainability | Smaller scope, shared semantics, and separated state should reduce coupling | Avoid wholesale prototype transfer; review focused diffs |
| Testability | Deterministic scenarios and shared resolver should improve reproducibility | Resolve verification environment at test gate without rewriting history |
| Reliability | Bounded retries, persisted state, and DAG validation should prevent uncontrolled execution | Explicit policy and terminal-state tests |
| Observability | Persistent trace should make task outcomes and retries inspectable | Define trace content and persistence acceptance conditions |
| Modifiability | Clean baseline and staged decisions should make later changes localized | Keep requirements/UML/code synchronized at each checkpoint |

## Dependencies and risks

- Requirements v2 must follow approval of this request.
- Architecture/UML review must precede backend implementation.
- Domain/persistence work must precede execution-mode implementation.
- Deterministic execution verification must precede UI and deployment work.
- Current risks and triggers are recorded in the [risk register](../process/risk-register.md).
- Backlog sequencing is recorded in the [product backlog](../process/product-backlog.md).
- Historical evidence is recorded in the [evidence register](../process/evidence-register.md).

## Acceptance gate

CR-001 may proceed to Requirements v2 only after review confirms:

- the problem and objectives are accurate;
- included and excluded scope is explicit;
- impact analysis is complete;
- risks are registered;
- alternatives are recorded;
- historical claims are evidence-classified;
- no implementation has started;
- CR status remained pending until this explicit approval was recorded.

The acceptance gate passed after independent review of the exact r2 bundle, `SE_M-stage2-review-20260811-r2.tar.gz` (15,350 bytes; SHA-256 `314659649d1ad9df7d270a238bf97431373ee4aa2edfa785df7718ab477e24dd`). This is project-reviewer approval for progression to Requirements v2 only, not a claim of additional instructor approval. Requirements v2 has not started, implementation remains `NOT STARTED`, and release remains `NOT SCHEDULED`.
