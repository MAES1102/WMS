# Defense-Core Architecture Decisions

| Field | Value |
|---|---|
| Status | `APPROVED — checkpoint 4 architecture baseline` |
| Requirements baseline | `6074fd7ef490ea3b08177e7a786035159f39a91c` |
| Working base | `b5c7da9e51382bb418f017790ae944c8dff26a06` |
| Implementation | `NOT STARTED` |
| Executable verification | `NOT STARTED` |
| Release | `NOT SCHEDULED` |

These seven decisions are accepted as the checkpoint-4 architecture baseline through substantive project review. They are not implemented, runtime-verified, or instructor-approved; Git durability is established by commit f44f0d55349af4e7b1b19b49f5e3b26c67c96181 and the independently verified origin/refactor/defense-core ref. Architectural decisions affect non-functional characteristics and should explicitly address structure, distribution, decomposition, control, evaluation, and documentation (`9 - sw architecture.pdf`, slides 25–26).

## ADR-001 — Single-deployable modular-monolith structure and layer boundaries

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

The target must remain one FastAPI application with persistent storage. The existing baseline provides a single application foundation, while CR-001 excludes microservices and distributed execution. Layered organization supports separation of concerns and localized change but can add crossings and interpretation cost if applied rigidly (`9 - sw architecture.pdf`, slides 102–106 and 110–111).

### Decision

Use one deployable modular monolith with four responsibility layers:

- presentation for browser/static UI and request/response translation;
- application for use-case coordination and execution-strategy selection;
- domain for definition, validation, routing, retry, terminal, and trace semantics;
- infrastructure for persistent storage and run-scoped in-memory event dispatch.

Dependencies point toward domain policy. The browser is a client boundary, while the application and database remain the only runtime server/storage boundary. Concrete modules, classes, endpoint paths, and storage structures are deferred.

### Alternatives considered

- **Retain the baseline structure unchanged:** rejected because linear control and mixed definition/run state cannot satisfy the approved requirements.
- **Adopt microservices or distributed services:** rejected by `CON-001` and unnecessary for the bounded defense.
- **Adopt a separate MVC framework:** not selected; the simple demonstration path does not justify the extra complexity identified for simple interactions (`9 - sw architecture.pdf`, slides 143–145).
- **Use an unstructured monolith:** rejected because shared rules and two control strategies need explicit ownership boundaries.

### Consequences and trade-offs

- One deployment and one process simplify operation and exclude broker/service coordination.
- Layer boundaries improve reviewability and selective replacement.
- Boundary discipline requires later dependency checks; shortcuts across layers could erode the design.
- In-process failure remains a single application failure boundary; no unsupported availability claim is made.

### Traceability

- **Affected requirements:** `FR-013`–`FR-016`, `FR-030`, `NFR-006`.
- **Affected constraints:** `CON-001`, `CON-002`, `CON-003`, `CON-009`, `CON-010`.
- **Related risks:** `RK-002`, `RK-008`, `RK-010`, `RK-012`.
- **Later verification gate:** checkpoint 5 design/implementation inspection; checkpoint 8 deployment inventory and restart check.

## ADR-002 — Workflow-definition versus run-specific state separation

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

The baseline stores mutable status and timestamps on reusable task definitions. The prototype introduces per-run task execution but also continues dual writes to definition and run objects. Approved requirements demand isolated sequential and concurrent runs and forbid mutable run state on definition tasks.

### Decision

Separate the conceptual model into:

- reusable, execution-immutable workflow-definition data: designated start, task definitions, positive attempt bounds, and conditional DAG transitions;
- run-specific mutable data: run mode/scenario/state, task attempts, outcomes, retry observations, selected transitions, ordered trace positions, timestamps, and terminal state.

A run references one accepted definition. Neither execution strategy mutates that definition. Every mutable execution fact references exactly one run. Definition tasks never serve as an execution-state fallback or UI status store. Definition editing and versioning behavior remains outside this checkpoint.

### Alternatives considered

- **Keep mutable task-definition status:** rejected because sequential and overlapping runs can overwrite shared state.
- **Write both definition and run state for compatibility:** rejected because it creates two sources of truth.
- **Copy the entire definition into each run:** rejected as unnecessary duplication; a run references the accepted definition while its mutable observations remain separate.

### Consequences and trade-offs

- Isolation and historical trace become explicit and reviewable.
- Presentation must retrieve run status rather than infer it from definition tasks.
- Persistence and migration work increase and require checkpoint-5 impact analysis.
- Editing a definition during a run remains outside scope; no versioning mechanism is selected here.

### Traceability

- **Affected requirements:** `FR-013`, `FR-018`–`FR-020`, `FR-023`, `FR-026`, `NFR-003`, `NFR-004`, `NFR-007`.
- **Affected constraints:** `CON-002`, `CON-004`, `CON-010`.
- **Related risks:** `RK-003`, `RK-006`, `RK-008`, `RK-011`.
- **Later verification gate:** checkpoint 5 model/persistence inspection; checkpoint 6 sequential and controlled-concurrency isolation; checkpoint 8 restart retention.

## ADR-003 — Shared validation, TransitionResolver, terminal, and retry semantics

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

The target must accept only valid conditional DAG definitions, give `SUCCESS`/`FAILURE` priority over `ALWAYS`, reject ambiguity, bound retry without a graph cycle, and use identical semantics in both execution modes. The prototype’s cycle-capable traversal and loop counter do not satisfy these rules.

### Decision

Provide one domain-policy path used by both strategies:

1. Validate exactly one start, reachable terminal existence, full reachability, acyclicity/no self-edge, allowed conditions, equal-precedence uniqueness, and a positive maximum-total-attempt bound for every task.
2. Reject invalid definitions before any run or execution state is created.
3. Persist each deterministic attempt outcome.
4. Retry a failed current task if and only if completed attempts remain below its bound; a bound of `1` permits zero retries, and retry traverses no edge.
5. After exhaustion, resolve the final `FAILURE` normally.
6. Resolve matching `SUCCESS` or `FAILURE` before `ALWAYS`.
7. Treat no eligible edge after final `SUCCESS` as successful terminal and after final `FAILURE` as unsuccessful terminal.

One shared conceptual `TransitionResolver` owns selection/terminal semantics. Exact class and function names are deferred.

### Alternatives considered

- **Mode-specific validation or resolvers:** rejected because they invite semantic drift.
- **Priority numbers to break equal-precedence ties:** rejected because `FR-010` requires ambiguity rejection.
- **Retry edges or cycle-capable graphs:** rejected by `FR-005`, `FR-024`, and `CON-006`.
- **Fail immediately without exhaustion routing:** rejected because `FR-025` requires normal `FAILURE` then `ALWAYS` resolution.

### Consequences and trade-offs

- One rule set makes parity checkable and localizes routing change.
- Validation must be complete and occur before persistence of a run.
- Retry and transition observations must be distinct in the trace.
- The resolver remains intentionally serial; fork/join is excluded.

### Traceability

- **Affected requirements:** `FR-001`–`FR-014`, `FR-017`, `FR-021`–`FR-026`, `NFR-002`, `NFR-004`, `NFR-005`.
- **Affected constraints:** `CON-004`, `CON-006`, `CON-007`, `CON-010`.
- **Related risks:** `RK-004`, `RK-005`, `RK-008`, `RK-010`.
- **Later verification gate:** checkpoint 5 domain-policy inspection; checkpoint 6 validation, retry-boundary, resolver, terminal, trace, and paired-mode tests.

## ADR-004 — Centralized orchestration over the shared domain semantics

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

Orchestration is required as the centralized comparison mode. The baseline central loop is linear; the target must advance the accepted graph without duplicating validation, retry, or routing policy.

### Decision

Use an application-level orchestration strategy that:

- invokes shared validation before run creation;
- establishes one isolated run;
- obtains deterministic outcomes from the selected scenario;
- coordinates attempt persistence and retry decisions;
- invokes the shared resolver after a final task outcome;
- advances only the selected next task;
- persists transition and terminal observations in order.

The orchestrator owns sequencing/control, not domain-policy definitions.

### Alternatives considered

- **Continue sorted task order:** rejected because it cannot express conditional routing.
- **Embed resolver rules in the controller:** rejected because choreography would duplicate them.
- **Use events for both modes:** rejected because the defense explicitly compares centralized and event-driven control strategies.

### Consequences and trade-offs

- The control path is explicit and straightforward to reason about.
- The centralized controller is coupled to the application use case, but domain rules remain reusable.
- Semantic parity depends on using the same scenario, persistence contract, and resolver as choreography.

### Traceability

- **Affected requirements:** `FR-015`, `FR-017`, `FR-019`, `FR-020`, `FR-026`–`FR-029`, `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`.
- **Affected constraints:** `CON-001`, `CON-004`, `CON-005`, `CON-007`, `CON-008`.
- **Related risks:** `RK-003`, `RK-004`, `RK-007`, `RK-008`.
- **Later verification gate:** checkpoint 5 strategy inspection; checkpoint 6 orchestration cases and normalized trace comparison.

## ADR-005 — In-memory EventBus choreography and deterministic run-scoped event contract

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

Choreography must use an in-memory EventBus and the shared resolver without Kafka, ZooKeeper, or another broker. Implicit invocation supports decoupling, but ordinary event announcers cannot assume response, ordering, or completion (`9 - sw architecture.pdf`, slides 92–93, 96, and 100–101).

### Decision

Use one run-scoped in-memory event contract for workflow advancement:

- create the subscription only after validation and run creation;
- scope the event channel and payload to one run identity;
- register exactly one controlled workflow-advance handler for the run event;
- dispatch synchronously and deterministically, or preserve an explicitly ordered equivalent if a later reviewed implementation changes the mechanism;
- persist the attempt/retry/transition observation before publishing downstream advancement;
- let the handler invoke the same retry/resolver/terminal policy used by orchestration;
- unsubscribe and release run-scoped handler state at either terminal result and on controlled failure cleanup;
- never derive business semantics from unrelated subscriber order;
- treat a missing controlled handler as an execution error rather than successful completion;
- provide no broker fallback.

### Alternatives considered

- **Kafka/ZooKeeper transport:** rejected by `CON-003` and unsupported by durable runtime evidence.
- **Global subscriber collection:** rejected because it risks cross-run leakage and retained handlers.
- **Multiple business handlers whose ordering selects a route:** rejected because subscriber ordering cannot be the resolver.
- **Asynchronous unordered dispatch:** not selected because it would undermine deterministic trace ordering without a separately designed ordering mechanism.

### Consequences and trade-offs

- Event-driven control remains visible while deployment stays single-process.
- Run-scoped lifecycle and one advance handler constrain implicit-invocation nondeterminism.
- Synchronous dispatch limits scalability claims, which are neither required nor made.
- Cleanup and persistence-before-publish become mandatory correctness controls.

### Traceability

- **Affected requirements:** `FR-016`, `FR-017`, `FR-019`, `FR-020`, `FR-026`–`FR-029`, `NFR-001`, `NFR-002`, `NFR-004`, `NFR-007`, `NFR-008`.
- **Affected constraints:** `CON-001`, `CON-003`, `CON-004`, `CON-005`, `CON-007`, `CON-008`.
- **Related risks:** `RK-003`, `RK-004`, `RK-007`, `RK-010`.
- **Later verification gate:** checkpoint 5 event-contract/lifecycle inspection; checkpoint 6 choreography cases, cleanup, isolation, and parity tests.

## ADR-006 — Persistence, transaction boundaries, run isolation, and ordered trace

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

The system must retain definitions, isolated run state, attempts, retries, trace, and terminal results. The trace must remain ordered and survive restart. Exact schema and transaction APIs are outside checkpoint 4.

### Decision

Use one persistence boundary shared by both strategies with these transaction intents:

- validation performs no run-state write;
- run creation and initial run observation form one durable boundary;
- each attempt outcome is durably recorded before retry or routing;
- each retry observation is recorded before repeating the task;
- each selected transition is recorded before downstream advancement;
- terminal state and terminal trace observation are committed together;
- each trace entry has a stable run-local ordering position;
- all mutable records are keyed or associated to exactly one run;
- retrieval and updates always include run identity.

Concrete tables, columns, indexes, migration steps, locking, and isolation-level configuration are deferred to checkpoint 5.

### Alternatives considered

- **In-memory trace only:** rejected because persistence and restart retention are required.
- **Definition-task status as execution truth:** rejected by ADR-002 and `CON-004`.
- **Persist after dispatch:** rejected because a downstream action could become visible before its causal evidence.
- **One global trace order only:** rejected as insufficient for simple, explicit run isolation; a run-local order is required regardless of any later global identifier.

### Consequences and trade-offs

- Causal observations can be reconstructed and compared across modes.
- More transaction boundaries may add overhead; no unsupported performance target is stated.
- Concurrency and restart behavior require later isolated executable evidence.
- Migration compatibility remains an open checkpoint-5 control under `RK-006`.

### Traceability

- **Affected requirements:** `FR-018`–`FR-020`, `FR-023`, `FR-026`, `NFR-003`, `NFR-004`, `NFR-007`.
- **Affected constraints:** `CON-002`, `CON-004`, `CON-010`.
- **Related risks:** `RK-003`, `RK-006`, `RK-008`, `RK-011`.
- **Later verification gate:** checkpoint 5 persistence/schema impact review; checkpoint 6 trace/isolation checks; checkpoint 8 restart-retention verification.

## ADR-007 — Named deterministic scenarios and single-service deployment boundary

**Status:** `ACCEPTED — checkpoint 4 architecture baseline`

### Context

The defense requires repeatable success, retry-then-success, and permanent-failure scenarios in both modes, plus one browser path and one FastAPI deployment with persistent storage. The baseline and prototype use random outcomes and include optional broker paths, which are excluded.

### Decision

Represent scenario input as one named, finite task-outcome sequence selected at run start. The same scenario specification is consumed by both modes. No random generator or external business service participates.

Deploy conceptually as:

- one browser/static-UI client boundary;
- one FastAPI application process containing all four layers and both strategies;
- one persistent database/storage resource.

No Kafka, ZooKeeper, broker, microservice, external service, or distributed executor appears in the runtime topology.

### Alternatives considered

- **Random failure simulation:** rejected because it prevents repeatable acceptance evidence.
- **External scenario service:** rejected by `CON-008` and unnecessary for three fixed demonstrations.
- **Separate service per execution mode:** rejected because semantic comparison does not require distributed deployment.
- **Broker-backed choreography:** rejected by `CON-003`.

### Consequences and trade-offs

- The six cases become repeatable and comparable.
- Scenario input is demonstration/test control, not a production integration claim.
- One application is simple to deploy but intentionally makes no horizontal-scale or fault-tolerance claim.
- Browser interaction remains bounded to selection, start, and trace inspection.

### Traceability

- **Affected requirements:** `FR-017`, `FR-027`–`FR-030`, `NFR-001`–`NFR-003`, `NFR-006`, `NFR-008`.
- **Affected constraints:** `CON-001`, `CON-003`, `CON-005`, `CON-008`, `CON-009`, `CON-010`.
- **Related risks:** `RK-007`, `RK-010`, `RK-011`, `RK-013`.
- **Later verification gate:** checkpoint 6 six deterministic cases; checkpoint 7 bounded UI inspection; checkpoint 8 deployment inventory and restart retention.

## Decision-set consistency

The accepted decisions are complementary:

- ADR-001 supplies the bounded structure.
- ADR-002 defines ownership of reusable and mutable data.
- ADR-003 supplies the only validation/routing/retry/terminal semantics.
- ADR-004 and ADR-005 provide distinct control strategies over ADR-003.
- ADR-006 makes causal run evidence persistent and isolated.
- ADR-007 supplies deterministic inputs and the bounded physical topology.

No accepted decision introduces an excluded capability or claims implementation. The decision set and the matching [UML sources](./uml/) must be considered together with [architecture traceability](./architecture-traceability.md); runtime verification remains future work.
