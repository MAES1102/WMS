# Defense-Core Architecture Traceability

| Field | Value |
|---|---|
| Status | `APPROVED — checkpoint 4 architecture baseline` |
| Requirements baseline | `6074fd7ef490ea3b08177e7a786035159f39a91c` |
| Working base | `b5c7da9e51382bb418f017790ae944c8dff26a06` |
| Implementation | `NOT STARTED` |
| Executable verification | `NOT STARTED` |
| Release | `NOT SCHEDULED` |

This document maps the approved Stage 3 requirements to accepted checkpoint-4 architecture evidence. `D4` means **approved checkpoint-4 design evidence only; it is not implementation or runtime verification, and Git durability requires a separately authorized and verified commit/ref action**. `T6`, `U7`, and `D8` remain future evidence checkpoints and no test or scenario is described as executed or passed.

## 1. Forward architecture coverage

| Requirement | Accepted ADR coverage | Approved UML coverage | Implementation checkpoint | Verification checkpoint | Current state |
|---|---|---|---|---|---|
| `FR-001` | ADR-002, ADR-003 | Domain model; routing/retry activity | 5 | 6 | `D4` |
| `FR-002` | ADR-003 | Domain model; routing/retry activity; run state | 5 | 6 | `D4` |
| `FR-003` | ADR-003 | Domain model; routing/retry activity | 5 | 6 | `D4` |
| `FR-004` | ADR-003 | Domain model; routing/retry activity | 5 | 6 | `D4` |
| `FR-005` | ADR-003 | Domain model; routing/retry activity | 5 | 6 | `D4` |
| `FR-006` | ADR-003, ADR-006 | System context/use cases; both sequence views; routing/retry activity; run state | 5 | 6 | `D4` |
| `FR-007` | ADR-003 | Domain model; routing/retry activity | 5 | 6 | `D4` |
| `FR-008` | ADR-003 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-009` | ADR-003 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-010` | ADR-003 | Routing/retry activity | 5 | 6 | `D4` |
| `FR-011` | ADR-003 | Both sequence views; routing/retry activity; run state | 5 | 6 | `D4` |
| `FR-012` | ADR-003 | Both sequence views; routing/retry activity; run state | 5 | 6 | `D4` |
| `FR-013` | ADR-001, ADR-002 | Component view; domain model | 5 | 6 | `D4` |
| `FR-014` | ADR-003 | Component view; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-015` | ADR-004 | Component view; orchestration sequence | 5 | 6 | `D4` |
| `FR-016` | ADR-005 | Component view; choreography sequence; deployment view | 5 | 6 | `D4` |
| `FR-017` | ADR-003, ADR-004, ADR-005, ADR-007 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-018` | ADR-002, ADR-006 | Domain model; component view; run state | 5 | 6 | `D4` |
| `FR-019` | ADR-002, ADR-004, ADR-005, ADR-006 | Domain model; component view; run state | 5 | 6 | `D4` |
| `FR-020` | ADR-002, ADR-004, ADR-005, ADR-006 | Component view; choreography sequence; run state | 5 | 6 | `D4` |
| `FR-021` | ADR-003 | Domain model; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-022` | ADR-003 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-023` | ADR-002, ADR-003, ADR-006 | Domain model; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-024` | ADR-003 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-025` | ADR-003 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-026` | ADR-002, ADR-004, ADR-005, ADR-006 | Component view; domain model; both sequence views; run state | 5 | 6 and 8 | `D4` |
| `FR-027` | ADR-004, ADR-005, ADR-007 | System context/use cases; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-028` | ADR-003, ADR-004, ADR-005, ADR-007 | System context/use cases; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-029` | ADR-003, ADR-004, ADR-005, ADR-007 | System context/use cases; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `FR-030` | ADR-001, ADR-007 | System context/use cases; component view; deployment view | 7 | 7 | `D4` |
| `NFR-001` | ADR-004, ADR-005, ADR-007 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `NFR-002` | ADR-003, ADR-004, ADR-005 | Both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `NFR-003` | ADR-002, ADR-006, ADR-007 | Domain model; component view; deployment view | 5 and 8 | 8 | `D4` |
| `NFR-004` | ADR-003, ADR-004, ADR-005, ADR-006 | Domain model; both sequence views; routing/retry activity | 5 | 6 | `D4` |
| `NFR-005` | ADR-003 | Routing/retry activity; run state | 5 | 6 | `D4` |
| `NFR-006` | ADR-001, ADR-007 | Component view; deployment view | 8 | 8 | `D4` |
| `NFR-007` | ADR-002, ADR-004, ADR-005, ADR-006 | Domain model; component view; choreography sequence; run state | 5 | 6 | `D4` |
| `NFR-008` | ADR-005, ADR-007 | System context/use cases; component view; both sequence views; deployment view | 5 | 6 | `D4` |

Forward-coverage result: exactly 30 `FR-*` rows and 8 `NFR-*` rows are present, with one row per approved identifier.

## 2. Constraint coverage

| Constraint | Approved architecture preservation | ADRs | UML evidence | Later verification |
|---|---|---|---|---|
| `CON-001` | One FastAPI modular monolith; no microservice/distributed executor | ADR-001, ADR-007 | Component view; deployment view | Checkpoint 8 deployment inventory |
| `CON-002` | Persistent storage required; exact schema deferred | ADR-002, ADR-006 | Domain model; component view; deployment view | Checkpoints 5 and 8 |
| `CON-003` | In-memory EventBus only; no Kafka, ZooKeeper, broker, or fallback | ADR-005, ADR-007 | Component view; choreography sequence; deployment view | Checkpoints 6 and 8 |
| `CON-004` | Definition tasks contain no mutable run state | ADR-002, ADR-006 | Domain model; run state | Checkpoints 5 and 6 |
| `CON-005` | Named deterministic outcomes replace randomness | ADR-004, ADR-005, ADR-007 | Component view; both sequence views | Checkpoint 6 |
| `CON-006` | Retry repeats current task without a graph cycle | ADR-003 | Both sequence views; routing/retry activity | Checkpoint 6 |
| `CON-007` | Serial conditional DAG only; no fork/join | ADR-003, ADR-004, ADR-005 | Domain model; routing/retry activity | Checkpoints 5 and 6 |
| `CON-008` | No external business-service call | ADR-004, ADR-005, ADR-007 | System context/use cases; component view; deployment view | Checkpoint 6 |
| `CON-009` | No unrelated feature expansion | ADR-001, ADR-007 | System context/use cases; deployment view | Every later review gate |
| `CON-010` | Requirements baseline remains design-neutral; checkpoint 4 stays conceptual and defers exact implementation | ADR-001–ADR-007 | All eight UML views | Checkpoint-4 review and checkpoint 5 entry review |
| `CON-011` | No executable tests created or run in checkpoint 4 | ADR-001–ADR-007 | UML sources are design evidence only | Checkpoint 6 authorization |
| `CON-012` | Requirement identifiers remain unchanged; architecture mappings are controlled separately | ADR-001–ADR-007 | This traceability record | Every change review |

Constraint-coverage result: all 12 approved constraints have explicit approved architecture coverage without implementation or pass claims.

## 3. Reverse ADR coverage

| Accepted decision | Primary requirement/constraint coverage | Matching UML views | Current state |
|---|---|---|---|
| ADR-001 | `FR-013`–`FR-016`, `FR-030`, `NFR-006`, `CON-001`–`CON-003` | Component view; deployment view; system context/use cases | `D4` |
| ADR-002 | `FR-018`–`FR-020`, `FR-023`, `NFR-007`, `CON-004` | Domain model; run state | `D4` |
| ADR-003 | `FR-001`–`FR-014`, `FR-021`–`FR-025`, `NFR-005`, `CON-006`, `CON-007` | Domain model; both sequence views; routing/retry activity; run state | `D4` |
| ADR-004 | `FR-015`, `FR-017`, `FR-027`–`FR-029`, `NFR-001`, `NFR-002` | Component view; orchestration sequence | `D4` |
| ADR-005 | `FR-016`, `FR-017`, `FR-027`–`FR-029`, `NFR-002`, `NFR-008`, `CON-003` | Component view; choreography sequence; deployment view | `D4` |
| ADR-006 | `FR-018`–`FR-020`, `FR-023`, `FR-026`, `NFR-003`, `NFR-004`, `NFR-007` | Domain model; component view; both sequence views; run state | `D4` |
| ADR-007 | `FR-027`–`FR-030`, `NFR-001`, `NFR-006`, `NFR-008`, `CON-001`, `CON-005`, `CON-008` | System context/use cases; component view; both sequence views; deployment view | `D4` |

Every accepted ADR has forward use and a matching approved diagram; no ADR is represented as implemented.

## 4. Reverse UML coverage

| UML source | View/purpose | Principal coverage | Current state |
|---|---|---|---|
| [system-context-use-cases.puml](./uml/system-context-use-cases.puml) | Actors, system boundary, validation, run start, trace inspection | `FR-006`, `FR-027`–`FR-030`, `NFR-008`, `CON-008`, `CON-009` | `D4` |
| [component-view.puml](./uml/component-view.puml) | Layered modular-monolith components and connectors | `FR-013`–`FR-020`, `FR-026`, `NFR-006`–`NFR-008`, `CON-001`–`CON-005` | `D4` |
| [domain-model.puml](./uml/domain-model.puml) | Definition/run separation and multiplicities | `FR-001`, `FR-002`, `FR-013`, `FR-018`–`FR-023`, `FR-026`, `CON-004` | `D4` |
| [orchestration-sequence.puml](./uml/orchestration-sequence.puml) | Centralized control and persistence ordering | `FR-006`, `FR-008`–`FR-017`, `FR-021`–`FR-029`, `NFR-004` | `D4` |
| [choreography-sequence.puml](./uml/choreography-sequence.puml) | Run-scoped in-memory event advancement and cleanup | `FR-006`, `FR-008`–`FR-014`, `FR-016`–`FR-029`, `NFR-002`, `NFR-004`, `NFR-008`, `CON-003` | `D4` |
| [routing-retry-activity.puml](./uml/routing-retry-activity.puml) | Complete validation, attempt, retry, routing, and terminal algorithm | `FR-002`–`FR-012`, `FR-021`–`FR-025`, `NFR-005`, `CON-006`, `CON-007` | `D4` |
| [run-state.puml](./uml/run-state.puml) | No-run invalid path and isolated run lifecycle | `FR-006`, `FR-011`, `FR-012`, `FR-018`–`FR-020`, `NFR-007` | `D4` |
| [deployment-view.puml](./uml/deployment-view.puml) | Browser, one application process, persistent database, explicit absences | `FR-016`, `FR-030`, `NFR-003`, `NFR-006`, `NFR-008`, `CON-001`–`CON-003`, `CON-008` | `D4` |

Every UML source has reverse requirement/constraint coverage and one bounded purpose.

## 5. Reverse coverage of CR-001 requested outcomes

| Requested outcome | Approved architecture coverage | UML evidence | Later gate |
|---|---|---|---|
| Conditional DAG | ADR-002, ADR-003 | Domain model; routing/retry activity | 5–6 |
| Deterministic `SUCCESS`/`FAILURE`/`ALWAYS` resolution | ADR-003 | Both sequence views; routing/retry activity | 5–6 |
| One shared workflow model | ADR-001, ADR-002 | Component view; domain model | 5 |
| Run-specific state | ADR-002, ADR-006 | Domain model; run state | 5–6 |
| Sequential and concurrent isolation | ADR-002, ADR-005, ADR-006 | Component view; choreography sequence; run state | 6 |
| Bounded persistent retry | ADR-003, ADR-006 | Both sequence views; routing/retry activity | 5–6 |
| Shared resolver concept | ADR-003 | Component view; both sequence views | 5–6 |
| Centralized orchestration | ADR-004 | Orchestration sequence | 5–6 |
| In-memory EventBus choreography | ADR-005 | Choreography sequence; deployment view | 5–6 |
| Persistent ordered trace | ADR-006 | Domain model; both sequence views; run state | 5–8 |
| Deterministic success scenario | ADR-007 | System context/use cases; both sequence views | 6 |
| Deterministic retry-then-success scenario | ADR-003, ADR-007 | Both sequence views; routing/retry activity | 6 |
| Deterministic permanent-failure scenario | ADR-003, ADR-007 | Both sequence views; routing/retry activity | 6 |
| One browser demonstration path | ADR-001, ADR-007 | System context/use cases; component view | 7 |
| One FastAPI deployment with persistence | ADR-001, ADR-006, ADR-007 | Component view; deployment view | 8 |

All requested outcomes have approved architecture coverage; none is claimed implemented.

## 6. Reverse coverage of exclusions

| Exclusion | Preservation in approved design | UML evidence |
|---|---|---|
| Kafka and ZooKeeper | ADR-005 and ADR-007 allow only the in-memory EventBus | Choreography sequence; deployment view |
| Distributed broker | No broker component or fallback exists | Component view; deployment view |
| Microservices | ADR-001 selects one modular monolith | Component view; deployment view |
| Distributed execution | Both strategies execute inside one process | Component view; deployment view |
| Arbitrary graph cycles | ADR-003 validates a DAG and rejects self/cyclic edges | Domain model; routing/retry activity |
| Retry encoded as a cycle | Retry keeps the current task without an edge | Both sequence views; routing/retry activity |
| Parallel fork/join | Resolver advances one selected next task | Routing/retry activity |
| Random outcomes | ADR-007 uses named finite outcomes | Component view; both sequence views |
| External business services | System boundary and deployment contain none | System context/use cases; deployment view |
| Mutable runtime state on definition tasks | ADR-002 prohibits it | Domain model; run state |
| Authentication, billing, notification, analytics | No component, actor, requirement, or decision introduces them | System context/use cases; component view |
| Final endpoints, executable schema, or implementation classes | Explicitly deferred to checkpoint 5 | All UML sources remain conceptual |
| Unrelated feature expansion | ADR-001/ADR-007 keep a bounded defense path | System context/use cases; deployment view |

All CR-001 exclusions remain explicit and no excluded scope is introduced.

## 7. Six mode-by-scenario cases

The scenario definition, outcomes, routes, retry counts, trace obligations, and terminal states remain exactly those in [Requirements v2 traceability](../requirements/requirements-traceability.md#5-six-case-acceptance-scenario-matrix). Architecture coverage is:

| Acceptance case | Accepted control design | Accepted shared semantic design | Accepted persistent evidence design | Current state |
|---|---|---|---|---|
| Orchestration × success | ADR-004; orchestration sequence | ADR-003; routing/retry activity | ADR-006 | Specified only; unexecuted |
| Orchestration × retry-then-success | ADR-004; orchestration sequence | ADR-003; routing/retry activity | ADR-006 | Specified only; unexecuted |
| Orchestration × permanent failure | ADR-004; orchestration sequence | ADR-003; routing/retry activity | ADR-006 | Specified only; unexecuted |
| Choreography × success | ADR-005; choreography sequence | ADR-003; routing/retry activity | ADR-006 | Specified only; unexecuted |
| Choreography × retry-then-success | ADR-005; choreography sequence | ADR-003; routing/retry activity | ADR-006 | Specified only; unexecuted |
| Choreography × permanent failure | ADR-005; choreography sequence | ADR-003; routing/retry activity | ADR-006 | Specified only; unexecuted |

Six-case result: all six approved specifications have approved architecture coverage; none has been executed or passed, and executable verification remains `NOT STARTED`.

## 8. Related records

- [Architecture overview](./architecture-overview.md)
- [Architecture decisions](./architecture-decisions.md)
- [Requirements v2](../requirements/requirements-v2.md)
- [Requirements traceability](../requirements/requirements-traceability.md)
- [CR-001](../evolution/CR-001-defense-core-refactoring.md)
- [Product backlog](../process/product-backlog.md)
- [Risk register](../process/risk-register.md)
