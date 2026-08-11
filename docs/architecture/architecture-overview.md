# Defense-Core Architecture Overview

| Field | Value |
|---|---|
| Status | `APPROVED — checkpoint 4 architecture baseline` |
| Requirements baseline | `6074fd7ef490ea3b08177e7a786035159f39a91c` |
| Working base | `b5c7da9e51382bb418f017790ae944c8dff26a06` |
| Implementation | `NOT STARTED` |
| Executable verification | `NOT STARTED` |
| Release | `NOT SCHEDULED` |

This checkpoint-4 document records the accepted architecture baseline only. It does not establish final Python filenames, concrete classes, API paths, database tables or columns, executable schema, implementation, runtime verification, deployment, or release approval.

## 1. Purpose and decision basis

The defense core evolves the preserved linear baseline into a deterministic conditional-workflow system while retaining a clean, single-application foundation. The baseline and archived prototype were inspected through immutable Git objects. They are comparison evidence only: source presence does not prove runtime correctness, and the prototype is not transferred wholesale.

Architectural models support stakeholder discussion and document components, interfaces, and connections (`9 - sw architecture.pdf`, slide 24). The design therefore uses several focused views rather than one overloaded diagram, consistent with the multiple-view and 4+1 guidance on slides 41–42. The selected style is characterized through its components, connectors, constraints, computational model, invariants, and trade-offs, as prompted by slides 43 and 47–49.

## 2. System boundary and actors

The system boundary is one defense-core workflow-management application. It owns definition validation, run creation, deterministic task attempts, retry decisions, routing, execution-mode control, persistent trace, and trace retrieval.

| Actor or boundary | Responsibility |
|---|---|
| Workflow operator | Defines or selects a workflow, chooses an execution mode and named deterministic scenario, starts a run, and inspects its trace. |
| Academic evaluator | Observes the same bounded demonstration path and compares orchestration with choreography. |
| Browser/static UI | Client-facing presentation boundary hosted by the application; it initiates requests and displays results but does not own workflow semantics. |
| Persistent database storage | Stores accepted definitions and isolated execution evidence across application restarts. |

No external business system participates. Kafka, ZooKeeper, another broker, a microservice, or a distributed executor is not part of the boundary.

## 3. Quality drivers and constraints

| Driver | Requirements and constraints | Architectural response |
|---|---|---|
| Determinism and repeatability | `NFR-001`, `NFR-008`, `CON-005`, `CON-008` | Named scenario input supplies outcomes; randomness and external business calls are absent. |
| Cross-mode semantic parity | `FR-013`–`FR-017`, `NFR-002` | Both strategies use the same accepted definition, validation rules, retry rule, transition resolver, terminal semantics, and trace vocabulary. |
| Persistence and observability | `FR-023`, `FR-026`, `NFR-003`, `NFR-004`, `CON-002` | Attempt outcomes, retry observations, transition selections, ordering, and terminal state are persisted under one run. |
| Isolation | `FR-018`–`FR-020`, `NFR-007`, `CON-004` | Mutable state and subscriptions are scoped by run; definition tasks contain no run state. |
| Validation completeness | `FR-002`–`FR-010`, `FR-021`, `NFR-005` | One pre-execution validation path rejects invalid definitions before any run or execution state exists. |
| Maintainability and controlled evolution | `CON-009`, `CON-010`, `CON-012` | A modular monolith with explicit layers and accepted ADRs localizes change without creating deployment complexity. |
| Bounded deployment | `NFR-006`, `CON-001`, `CON-003` | One FastAPI application and persistent database; choreography stays in memory and has no broker fallback. |

Layering is selected for separation of concerns and reduced change impact, while acknowledging that clean separation can be difficult and unnecessary crossing or interpretation can add cost (`9 - sw architecture.pdf`, slides 102–106 and 110–111). Maintainability favors replaceable components, subject to the project’s bounded scope (slide 38).

## 4. Selected architectural style

The target is a **single-deployable FastAPI modular monolith**. It uses client-server interaction between the browser and application, but it is not a distributed-service architecture. Client-server structure can be implemented on one computer (`9 - sw architecture.pdf`, slides 129–130).

The application combines:

- a layered internal structure for presentation, application, domain, and infrastructure responsibilities;
- two application-level control strategies—centralized orchestration and in-memory EventBus choreography;
- one shared domain model and routing/retry semantics;
- one persistent storage boundary;
- one browser/static-UI boundary.

The architecture deliberately avoids an unnecessary MVC claim. The lecture notes that MVC can add code and complexity when interactions are simple (`9 - sw architecture.pdf`, slides 143–145); the required defense path needs only a bounded presentation boundary, not a commitment to a separate MVC framework.

## 5. Layer responsibilities

| Layer | Responsibilities | Must not own |
|---|---|---|
| Presentation | Browser/static assets, request/response translation, selection of workflow/mode/scenario, trace display, validation feedback. | Routing precedence, retry rules, mutable persistence decisions. |
| Application | Use-case coordination, pre-execution validation invocation, run lifecycle coordination, strategy selection, orchestration control, choreography subscription lifecycle. | Mode-specific copies of domain rules or definition-level run state. |
| Domain | Workflow-definition concepts, graph invariants, transition conditions, attempt-bound policy, resolver precedence, terminal semantics, run-state vocabulary, trace-observation meaning. | Database technology, browser concerns, broker transport, random outcomes. |
| Infrastructure | Persistent storage adapters, transaction boundaries, ordered trace storage, run-scoped in-memory EventBus implementation, deterministic scenario input adapter. | Independent business routing policy or silent fallback to excluded infrastructure. |

Dependencies point inward toward domain policy. Presentation calls application capabilities; application coordinates domain policy and infrastructure ports; infrastructure realizes storage and in-memory dispatch contracts. Concrete module names are deferred to checkpoint 5.

## 6. Shared conceptual model

### Definition data

A reusable workflow definition contains:

- one designated start task;
- task definitions, each with a positive maximum-total-attempt bound;
- directed transitions whose conditions are `SUCCESS`, `FAILURE`, or `ALWAYS`;
- no self-edge or directed cycle;
- at least one reachable terminal task;
- no unreachable task or equal-precedence ambiguity.

Accepted definition data is reusable and execution-immutable: neither execution strategy mutates it. It contains no mutable run status, attempt count, retry count, timestamps, selected transition, trace position, or terminal state. Definition editing and versioning behavior remains outside this checkpoint.

### Run-specific data

Each run owns:

- the accepted definition identity;
- execution mode and named scenario identity;
- current and terminal run state;
- task-attempt state and outcomes;
- retry observations and counts;
- selected-transition observations;
- a persistently ordered trace;
- its choreography subscription lifecycle when choreography is selected.

Sequential and overlapping runs share definition data but never mutable execution state.

The conceptual class view follows the purpose of early class models: represent system concepts and their associations without committing to detailed implementation classes (`7 - modeling.pdf`, slides 115–117).

## 7. Shared validation and transition resolution

One validation path runs before creation of a workflow run. A rejected definition creates no run, attempt, retry, transition-selection, or trace state.

For an accepted definition, one shared resolver applies these invariants in both modes:

1. A task attempt uses the next deterministic outcome supplied for that run and task.
2. The attempt number and outcome are persisted in trace order.
3. If the final outcome is `FAILURE` and completed attempts are below the positive attempt bound, a retry observation is persisted and the same task is attempted again without selecting or traversing a graph edge.
4. A bound of `1` therefore permits one attempt and zero retries.
5. At the bound, no further retry is permitted. Exhaustion returns the final `FAILURE` to normal transition resolution.
6. A matching `SUCCESS` or `FAILURE` transition is considered before `ALWAYS`.
7. `ALWAYS` is selected only when no outcome-specific transition matches.
8. Equal-precedence ambiguity has already been rejected before execution.
9. No eligible transition after final `SUCCESS` produces a successful terminal run.
10. No eligible transition after final `FAILURE` produces an unsuccessful terminal run.

The complete activity is modeled in [routing-retry-activity.puml](./uml/routing-retry-activity.puml). Activity diagrams are appropriate for workflow and internal process logic (`7 - modeling.pdf`, slide 109).

## 8. Two control strategies over one semantics

### Centralized orchestration

The orchestration strategy is an application-level controller. It creates the run after validation, requests attempts, persists observations, applies the shared retry and resolver semantics, advances the selected task, and records the terminal state. It does not duplicate transition policy.

### In-memory EventBus choreography

The choreography strategy advances the same run through a run-scoped, in-memory event contract. Implicit invocation can decouple components because an announcer broadcasts and registered handlers react (`9 - sw architecture.pdf`, slides 92–93 and 100). It also creates risks: an announcer ordinarily cannot assume subscribers, response ordering, or completion (`9 - sw architecture.pdf`, slides 96 and 101).

The accepted design bounds those risks:

- subscriptions are scoped to one run;
- one controlled workflow-advance handler consumes each run-advance event;
- dispatch is synchronous and deterministic, or must retain an explicitly ordered equivalent if later implementation evidence justifies a change;
- attempt, retry, transition, and terminal observations are persisted before downstream advancement;
- terminal completion always removes the run subscription;
- unrelated subscriber ordering never carries business semantics;
- absence of the controlled handler is an execution error, not a silent success;
- there is no Kafka, ZooKeeper, distributed-broker, or broker-fallback path.

Event-driven and state-machine views are used to show responses to internal events and run state (`7 - modeling.pdf`, slides 95–96). Sequence diagrams preserve interaction order (`7 - modeling.pdf`, slides 86–87).

## 9. Persistence and ordered trace

The persistence boundary treats run creation, attempt outcomes, retry decisions, selected transitions, and terminal state as durable execution facts. The architecture requires an explicit, monotonically ordered position within each run’s trace; the exact column, sequence mechanism, and transaction API are deferred.

Required transaction intent is:

- validate without creating execution state;
- atomically establish the run and its initial trace state;
- persist each attempt outcome before deciding or announcing advancement;
- persist a retry observation before repeating the current task;
- persist transition selection before the next task is advanced;
- persist terminal state and its trace observation together;
- retrieve state by run identity so one run cannot overwrite another.

Concurrency-control mechanics and migration details remain checkpoint-5 design/implementation work and must later demonstrate `NFR-007` and restart retention.

## 10. Deterministic scenario input

One scenario provider supplies named, finite outcome sequences for the approved success, retry-then-success, and permanent-failure scenarios. Both execution modes consume the same scenario specification. Generated run identifiers and timestamps may differ, but normalized outcomes, retry counts, transition selections, ordering, and terminal state must match.

The six mode-by-scenario cases remain specification only. None has been executed or passed; executable verification is `NOT STARTED` until checkpoint 6.

## 11. Explicit exclusions

The approved architecture contains no:

- Kafka, ZooKeeper, distributed broker, or broker fallback;
- microservice or distributed-execution topology;
- external business-service call;
- random outcome selection;
- arbitrary graph cycle or retry edge;
- parallel fork/join;
- mutable run state on workflow-definition tasks;
- authentication, authorization, billing, notification, analytics, or unrelated feature expansion.

## 12. 4+1 view coverage

| 4+1 view | Question answered | Checkpoint-4 UML source |
|---|---|---|
| Logical | What are the core abstractions and relationships? | [domain-model.puml](./uml/domain-model.puml), [run-state.puml](./uml/run-state.puml) |
| Process | How do runtime interactions advance in each mode? | [orchestration-sequence.puml](./uml/orchestration-sequence.puml), [choreography-sequence.puml](./uml/choreography-sequence.puml), [routing-retry-activity.puml](./uml/routing-retry-activity.puml) |
| Development | How is the application decomposed for development? | [component-view.puml](./uml/component-view.puml) |
| Physical | Where do the executable application and storage reside? | [deployment-view.puml](./uml/deployment-view.puml) |
| Scenarios (+1) | How does the operator use the bounded defense path? | [system-context-use-cases.puml](./uml/system-context-use-cases.puml), plus both sequence views and the activity view |

UML separates structural, behavioral, and interaction concerns (`7 - modeling.pdf`, slides 67 and 69–70). Component views describe software-component dependencies (slides 146–147), and the deployment view identifies runtime nodes and allocations (printed slide 161).

## 13. Limitations and deferred details

- Checkpoint-4 substantive review passed and the architecture decisions are accepted; Git durability requires a separately authorized and verified commit/ref action.
- Concrete Python modules, classes, function signatures, endpoint paths, tables, columns, indexes, migration steps, and concurrency primitives are deferred to checkpoint 5 or later authorized work.
- No latency, throughput, availability, security, or hardware threshold is invented.
- PlantUML rendering is not runtime or implementation evidence.
- Source inspection establishes historical structure only; it does not establish current target behavior.
- Checkpoint 5, implementation, executable verification, deployment, and release remain `NOT STARTED` or `NOT SCHEDULED` as applicable.

## 14. Related records

- [Architecture decisions](./architecture-decisions.md)
- [Architecture traceability](./architecture-traceability.md)
- [Requirements v2](../requirements/requirements-v2.md)
- [Requirements traceability](../requirements/requirements-traceability.md)
- [CR-001](../evolution/CR-001-defense-core-refactoring.md)
- [Risk register](../process/risk-register.md)
