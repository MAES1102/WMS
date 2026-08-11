# Requirements v2 — Defense Core

| Field | Value |
|---|---|
| Document | Requirements v2 — Defense Core |
| Status | `APPROVED — Stage 3 requirements baseline` |
| Version | `2.0` |
| Source change request | `CR-001` |
| Source checkpoint | `6a5e42c6fa5d4d71fd599d606d7c805e95177b2f` |
| Draft date | `2026-08-11` |
| Approval date | `2026-08-11` |
| Implementation status | `NOT STARTED` |
| Release status | `NOT SCHEDULED` |

[CR-001](../evolution/CR-001-defense-core-refactoring.md) authorized progression to Requirements v2. Requirements v2 r4 passed substantive project review and is the approved Stage 3 requirements baseline. Its approval authority is the project reviewer; no separate instructor approval is claimed. Architecture, ADRs, UML, implementation, executable tests, deployment work, and release decisions remain outside this checkpoint and have not started.

## 1. Purpose and intended readership

This document defines the controlled Stage 3 requirements baseline for evolving the preserved linear workflow baseline into the approved defense-core workflow system. It states observable behavior and constraints without choosing final endpoints, database schema, classes, modules, or diagrams.

The intended readers are:

- the project reviewer, who evaluates scope, testability, consistency, and traceability;
- the student developer, who will use an approved baseline as input to later architecture and implementation checkpoints;
- an academic evaluator, who needs a concise, evidence-classified description of the intended defense demonstration.

## 2. Version rationale and change summary

The preserved baseline contains linear, order-based orchestration and choreography artifacts. The approved change introduces conditional acyclic routing, run-specific state, bounded retry, persistent trace, deterministic demonstrations, and semantic parity while retaining a single FastAPI application and persistent storage.

The archived prototype is a comparison source, not the target specification. It contains useful transition and per-run concepts, but also cycle-capable graphs, definition-level runtime fields alongside run-level state, random outcomes, and Kafka/ZooKeeper artifacts. Its only historical execution result remains `INCONCLUSIVE — interrupted during initial collection`. No source presence or test definition is treated as proof of successful runtime behavior.

## 3. System context and defense objective

The defense core is a single workflow-management application used to define, validate, execute, and inspect a small conditional workflow. A human operator interacts through one browser demonstration path or an application interface. The application supports centralized orchestration and in-memory EventBus choreography over the same accepted workflow definition and transition semantics. Run state, retry attempts, terminal state, and trace are persistent and isolated by run.

The defense objective is to demonstrate, reproducibly and visibly, how the two execution modes reach equivalent results for the same accepted definition and deterministic scenario.

## 4. Stakeholders and actors

| Actor or stakeholder | Interest or responsibility |
|---|---|
| Project reviewer | Reviews requirements scope, quality, traceability, and later checkpoint evidence. |
| Student developer | Maintains the requirements and later produces separately approved design, implementation, and verification artifacts. |
| Workflow operator | Defines or selects a workflow, chooses an execution mode and deterministic scenario, starts a run, and inspects the result and trace. |
| Academic evaluator | Observes the defense path and compares orchestration with choreography without requiring distributed infrastructure. |

No private identity or contact information is required by these requirements.

## 5. Glossary

| Term | Controlled meaning |
|---|---|
| Workflow definition | A reusable, non-runtime description of task nodes, directed transitions, a designated start task, and terminal possibilities. |
| Task node | One unit in a workflow definition. It does not carry mutable state for a particular run. |
| Transition | A directed edge labeled `SUCCESS`, `FAILURE`, or `ALWAYS` from one task to another. |
| Conditional DAG | A directed workflow graph with no self-edge or directed cycle. |
| Start task | The single task designated as the entry point of a valid workflow. |
| Terminal task | A reachable task for which no transition is eligible after its final outcome. |
| Outcome-specific transition | A `SUCCESS` or `FAILURE` transition matching the final task outcome. |
| Fallback transition | An `ALWAYS` transition used only when no outcome-specific transition exists. |
| Run | One execution instance of one accepted workflow definition in one execution mode and deterministic scenario. |
| Task attempt | One execution of a task within a run. |
| Attempt bound | A positive integer configured for every task in an accepted workflow definition; it gives the maximum total attempts for that task in one run, so a bound of one permits zero retries. |
| Retry count | The number of attempts after the first attempt for a task in one run. |
| Persistent trace | Ordered stored observations of attempts, outcomes, retries, transition selections, and terminal run state. |
| Orchestration | Execution in which a centralized controller advances the workflow. |
| Choreography | Execution in which in-memory EventBus reactions advance the workflow without a distributed broker. |
| Semantic parity | Equivalent task outcomes, transition selections, retry counts, trace ordering, and terminal run state for the same accepted definition and deterministic scenario. |
| Deterministic scenario | A named, repeatable sequence of task outcomes selected without randomness. |

## 6. User-level goals

- Define or select one valid conditional workflow and understand why invalid definitions are rejected.
- Run the same workflow by orchestration or choreography.
- Select success, retry-then-success, or permanent-failure behavior without randomness.
- Observe the selected route, attempts, retries, outcomes, and terminal state after execution.
- Repeat or overlap runs without one run changing another run or the reusable definition.
- Restart the application and retrieve the previously persisted definition and execution evidence.

## 7. Normative scope

The normative scope is limited to:

- conditional DAG definitions with explicit task nodes and transitions;
- deterministic transition resolution and terminal semantics;
- one shared workflow model and one shared rule set for both modes;
- centralized orchestration and in-memory EventBus choreography;
- run-specific isolated state;
- bounded retry with persistent attempt state and no retry edge;
- persistent execution trace;
- three deterministic scenarios in each execution mode;
- one browser demonstration path;
- one FastAPI application with persistent database storage and restart retention.

The baseline identifiers are controlled. An identifier shall not be reused or renumbered in a later version without a recorded change reason and traceability update.

## 8. Functional requirements

| ID | Atomic normative statement | Rationale | Source | Verification method | Acceptance condition | Dependencies |
|---|---|---|---|---|---|---|
| `FR-001` | The system shall represent each workflow definition as explicit task nodes connected by directed transitions. | Conditional behavior requires an explicit graph rather than implicit task order. | CR-001 requested outcome; EV-018 and EV-019 | Later requirements-based inspection and executable definition test | A definition can be inspected as a finite set of named task nodes and directed transition records without deriving edges from task order. | None |
| `FR-002` | The system shall require exactly one designated start task in every accepted workflow definition. | Execution needs one deterministic entry point. | Approved minimal rule 1 | Later validation test | Definitions with zero or multiple designated starts are rejected before a run is created; a definition with one designated start may proceed to the remaining checks. | `FR-001` |
| `FR-003` | The system shall require every accepted workflow definition to contain at least one terminal task reachable from its start task. | A valid run must have a reachable end condition. | Approved minimal rule 1 | Later validation test | A definition with no reachable terminal task is rejected before execution. | `FR-001`, `FR-002` |
| `FR-004` | The system shall require every task node in an accepted workflow definition to be reachable from the designated start task. | Unreachable tasks make the definition incomplete and misleading. | Approved minimal rule 2 | Later graph-validation test | A definition containing any unreachable task is rejected and identifies the unreachable task or tasks. | `FR-001`, `FR-002` |
| `FR-005` | The system shall reject every workflow definition containing a self-edge or directed cycle. | The approved target is a conditional DAG; retry is not graph traversal. | Approved minimal rule 3; CR-001 exclusions; EV-022 | Later graph-validation test | Self-edge and multi-node-cycle examples are rejected before execution, while an otherwise equivalent acyclic example is accepted. | `FR-001` |
| `FR-006` | The system shall validate every workflow definition against all normative pre-execution definition rules before creating any execution state. | Invalid definitions must not produce partial runtime state. | CR-001 impact analysis; RK-005 | Later validation-path inspection and validation/persistence tests covering `FR-002` through `FR-005`, `FR-007`, `FR-010`, and `FR-021` | When any listed definition rule fails, the definition is rejected and creates no run, task-attempt, retry, transition-selection, or execution-trace state. | `FR-002`–`FR-005`, `FR-007`, `FR-010`, `FR-021` |
| `FR-007` | The system shall accept only `SUCCESS`, `FAILURE`, or `ALWAYS` as transition conditions. | A closed condition set makes routing reviewable and deterministic. | CR-001 requested outcome | Later validation test | A transition with any other condition is rejected before execution. | `FR-001` |
| `FR-008` | The system shall select a matching `SUCCESS` or `FAILURE` transition before considering an `ALWAYS` transition for the same completed task. | Outcome-specific routing has approved precedence. | Approved minimal rule 4 | Later resolver unit test and scenario trace inspection | When both a matching outcome-specific transition and `ALWAYS` exist, the trace records selection of the outcome-specific transition. | `FR-007` |
| `FR-009` | The system shall select an `ALWAYS` transition only when no transition matches the completed task's `SUCCESS` or `FAILURE` outcome. | `ALWAYS` is a fallback, not a competing branch. | Approved minimal rule 5 | Later resolver unit test | A task with no matching outcome-specific transition and exactly one `ALWAYS` transition selects that fallback; a matching outcome-specific transition suppresses it. | `FR-007`, `FR-008` |
| `FR-010` | The system shall reject a workflow definition when more than one transition could be selected at the same precedence for any task outcome. | Multiple equally eligible transitions are ambiguous. | Approved minimal rule 6; CR-001 impact analysis | Later validation test | Duplicate matching outcome-specific transitions or duplicate eligible `ALWAYS` transitions cause rejection before execution. | `FR-007`–`FR-009` |
| `FR-011` | The system shall complete a run successfully when a task's final outcome is `SUCCESS` and no transition is eligible. | A successful task with no next edge is a successful terminal. | Approved minimal rule 7 | Later terminal-semantics test | The trace ends at that task and records a successful terminal run state. | `FR-008`, `FR-009` |
| `FR-012` | The system shall complete a run unsuccessfully when a task's final outcome is `FAILURE` and no transition is eligible. | A failed task with no next edge is an unsuccessful terminal. | Approved minimal rule 7 | Later terminal-semantics test | The trace ends at that task and records an unsuccessful terminal run state. | `FR-008`, `FR-009`, `FR-025` |
| `FR-013` | The system shall use one workflow-definition model for both orchestration and choreography. | Both modes must execute the same accepted definition. | CR-001 requested outcome; RK-004 | Later design review and cross-mode test | One accepted definition identifier is executed in either mode without conversion into a mode-specific definition. | `FR-001` |
| `FR-014` | The system shall apply one transition-resolution rule set in both orchestration and choreography. | Shared rules prevent mode-specific routing drift. | CR-001 requested outcome; RK-004 | Later design review and cross-mode trace comparison | For identical completed-task outcome and outgoing transitions, both modes select the same transition or terminal result. | `FR-007`–`FR-012`, `FR-013` |
| `FR-015` | The system shall execute an accepted workflow in orchestration mode under centralized control. | Centralized orchestration is one approved comparison mode. | CR-001 requested outcome; baseline `app/engine/orchestrator.py` artifact | Later orchestration acceptance tests | An orchestration run advances from the start task through only resolver-selected tasks and records mode `orchestration`. | `FR-006`, `FR-014` |
| `FR-016` | The system shall execute an accepted workflow in choreography mode through in-memory EventBus reactions. | Reactive execution is required without broker infrastructure. | CR-001 requested outcome and exclusion; baseline `app/engine/events.py` and `app/engine/choreography.py` artifacts | Later choreography acceptance tests | A choreography run advances through in-memory events, records mode `choreography`, and requires no broker process. | `FR-006`, `FR-014` |
| `FR-017` | The system shall produce semantic parity between orchestration and choreography for the same accepted definition and deterministic scenario. | The defense compares control style without changing business semantics. | Approved minimal rule 11; RK-004 | Later paired trace comparison across six acceptance cases | Paired runs have equivalent task outcomes, selected transitions, retry counts, trace ordering, and terminal state. | `FR-013`–`FR-016`, `FR-026`–`FR-029` |
| `FR-018` | The system shall create run-specific execution state for every workflow run. | Runtime observations belong to an execution instance, not the reusable definition. | CR-001 requested outcome; EV-020 and EV-021; RK-003 | Later persistence inspection | Every task attempt, retry count, selected transition, and terminal state is associated with one run identifier. | `FR-006` |
| `FR-019` | The system shall preserve the completed state and trace of an earlier run when a later sequential run executes the same workflow definition. | Repeated demonstrations must not overwrite history. | CR-001 requested outcome; RK-003 | Later sequential-run isolation test | After two sequential runs, each run retains its own outcomes, attempts, trace, and terminal state. | `FR-018`, `FR-026` |
| `FR-020` | The system shall prevent concurrent runs of the same workflow definition from reading or writing each other's runtime state. | Concurrent demonstrations must be isolated. | CR-001 requested outcome; RK-003 | Later controlled-concurrency isolation test | Interleaved runs retain distinct attempts, transitions, trace entries, and terminal states keyed to their own run identifiers. | `FR-018`, `FR-026` |
| `FR-021` | The system shall require every task in an accepted workflow definition to have a configured positive attempt bound that specifies its maximum total attempts. | Retry must be explicitly bounded without a separate retry-enabled flag. | Approved minimal rule 8; RK-005 | Later attempt-bound validation and boundary tests | A task with a missing, zero, or negative bound causes definition rejection before execution; a bound of one permits one total attempt and zero retries. | `FR-001` |
| `FR-022` | The system shall retry a failed task if and only if the number of completed attempts is less than its configured attempt bound. | The approved policy requires each permitted retry while preventing retries at or beyond the bound. | Approved minimal rule 8 | Later two-sided retry-boundary tests for bounds one and two, covering both required and prohibited retry decisions | With bound one, the first failed attempt produces zero retries and proceeds to exhaustion handling; with bound two, the first failed attempt produces exactly one retry, a second failure produces no further retry and proceeds to `FR-025`, and no retry occurs after the bound is reached. | `FR-021` |
| `FR-023` | The system shall persist the attempt number and outcome after every task attempt. | Retry state must survive inspection and restart. | Approved minimal rule 9; CR-001 requested outcome | Later persistence and restart test | After each attempt, stored run state and trace show its ordinal attempt number and deterministic outcome. | `FR-018`, `FR-022` |
| `FR-024` | The system shall retry the current task without selecting or traversing a workflow transition. | Retry is policy state, not a graph cycle. | Approved minimal rule 9; CR-001 exclusion; RK-005 | Later retry trace inspection | Between a failed retryable attempt and its next attempt, the trace contains a retry observation and no transition-selection observation. | `FR-022`, `FR-023` |
| `FR-025` | The system shall apply normal `FAILURE` then `ALWAYS` transition resolution after a task exhausts its attempt bound with a final `FAILURE` outcome. | Exhaustion returns control to the shared resolver. | Approved minimal rule 10 | Later retry-exhaustion resolver test | After the last failed attempt, a matching `FAILURE` transition is selected before `ALWAYS`; if neither is eligible, `FR-012` applies. | `FR-008`, `FR-009`, `FR-022`–`FR-024` |
| `FR-026` | The system shall persist an ordered execution trace for every run. | The defense requires observable, reviewable execution evidence. | CR-001 requested outcome; RK-004 and RK-011 | Later trace-content and restart test | The retrievable trace orders task attempts, attempt outcomes, retry observations, selected transitions, and the terminal run state for one run. | `FR-018`, `FR-023`–`FR-025` |
| `FR-027` | The system shall provide a deterministic success scenario in which every configured task outcome is repeatable. | The normal path must be demonstrable without randomness. | CR-001 requested outcome; RK-007 | Later paired acceptance cases | Repeated use of the success scenario produces the specified successful path and terminal state in each mode. | `FR-015`, `FR-016`, `FR-026` |
| `FR-028` | The system shall provide a deterministic retry-then-success scenario in which one designated task fails once and succeeds on its next allowed attempt. | Bounded retry must be visibly demonstrable. | CR-001 requested outcome; RK-005 and RK-007 | Later paired acceptance cases | The designated task records two attempts, one retry, no retry transition, then follows its `SUCCESS` route in each mode. | `FR-015`, `FR-016`, `FR-021`–`FR-026` |
| `FR-029` | The system shall provide a deterministic permanent-failure scenario in which one designated task exhausts its attempt bound. | Exhaustion and failure routing must be reproducible. | CR-001 requested outcome; RK-005 and RK-007 | Later paired acceptance cases | The designated task reaches its configured bound, records the expected retry count, applies `FAILURE`/`ALWAYS` resolution, and the run reaches the specified unsuccessful terminal state in each mode. | `FR-015`, `FR-016`, `FR-021`–`FR-026` |
| `FR-030` | The system shall provide one browser demonstration path through which an operator can select an accepted workflow, execution mode, and deterministic scenario, start a run, and inspect its persistent trace. | One bounded path makes the approved behavior observable without UI expansion. | CR-001 requested outcome; RK-013 | Later UI acceptance inspection | Without switching to a second application UI, the operator can complete the stated sequence and see mode, scenario, attempts, selected transitions, and terminal state. | `FR-015`–`FR-017`, `FR-026`–`FR-029` |

## 9. Non-functional requirements

| ID | Atomic normative statement | Rationale | Source | Verification method | Acceptance condition | Dependencies |
|---|---|---|---|---|---|---|
| `NFR-001` | The system shall produce identical task outcomes, transition selections, retry counts, trace ordering, and terminal state when the same accepted definition, execution mode, and deterministic scenario are repeated from equivalent initial state. | Repeatability is required for credible review evidence. | CR-001 deterministic scenarios; RK-007 | Later repeated-run comparison | Two repeated runs per mode and scenario have equivalent normalized traces, excluding run identifiers and timestamps. | `FR-017`, `FR-027`–`FR-029` |
| `NFR-002` | The system shall satisfy semantic parity for all six mode-by-scenario acceptance cases in the traceability matrix. | Both modes must differ in control style only. | Approved minimal rule 11; RK-004 | Later six-case paired comparison | Each orchestration trace has an equivalent choreography trace for outcomes, transitions, retries, ordering, and terminal state. | `FR-017` |
| `NFR-003` | The system shall retain accepted workflow definitions, run states, task-attempt state, retry counts, execution traces, and terminal states across a controlled application restart. | Persistent storage is part of the approved deployment objective. | CR-001 requested outcome; RK-011 | Later restart-retention test | Values recorded before shutdown are retrievable after restart and match their pre-restart values. | `FR-018`, `FR-023`, `FR-026` |
| `NFR-004` | The system shall make every persisted trace complete with respect to the executed run's attempts, outcomes, retry observations, transition selections, ordering, and terminal state. | Incomplete evidence would prevent behavioral review. | CR-001 persistent trace; RK-004 and RK-014 | Later trace completeness check | Expected observations derived from the deterministic scenario equal the observations retrieved for the run, with no missing or cross-run entry. | `FR-026`–`FR-029` |
| `NFR-005` | The system's pre-execution validation path shall cover every definition rule specified by `FR-002` through `FR-005`, `FR-007`, `FR-010`, and `FR-021`. | Validation must be objectively complete for the approved invalid classes. | CR-001 graph validation; approved minimal rules | Later inspection that every listed rule participates in the pre-execution validation path, combined with parameterized invalid-definition cases, valid boundary cases, and representative combined violations | Verification covers every listed validation class; every controlled invalid case is rejected without creating run, attempt, retry, transition-selection, or execution-trace state; and no valid boundary case is falsely rejected. | `FR-006` |
| `NFR-006` | The deployed system shall consist of one FastAPI application backed by persistent database storage. | The approved defense core has one bounded deployment unit. | CR-001 requested deployment; RK-011 | Later deployment configuration inspection and restart check | Deployment inventory contains one FastAPI application and persistent storage, and the restart check satisfies `NFR-003`. | `NFR-003`, `CON-001`, `CON-002` |
| `NFR-007` | The system shall preserve run isolation in every sequential and controlled-concurrency verification case. | Isolation is a system-wide quality property. | CR-001 run isolation; RK-003 | Later state-partition comparison | No retrieved state or trace entry for one run contains another run's identifier or overwrites another run's recorded values. | `FR-018`–`FR-020`, `NFR-004` |
| `NFR-008` | The system shall execute each of the six acceptance cases without random outcome generation, external business-service calls, or distributed-broker dependencies. | Verification must be reproducible in the bounded defense environment. | CR-001 exclusions; RK-007 and RK-010 | Later execution with named deterministic scenario inputs, combined with source and dependency inspection for external-service calls and Kafka, ZooKeeper, or another broker | Each case completes using its named deterministic inputs; the exercised path makes no external business-service call; and source and dependency inspection finds no random outcome generation or Kafka, ZooKeeper, or other broker dependency in that path. | `FR-027`–`FR-029`, `CON-003`, `CON-005`, `CON-008` |

## 10. System and process constraints

| ID | Normative constraint | Source | Verification and acceptance condition |
|---|---|---|---|
| `CON-001` | The target shall remain one FastAPI application rather than a microservice or distributed-execution system. | CR-001 requested outcome and exclusions | Later deployment inventory identifies one application service and no microservice claim. |
| `CON-002` | The target shall use persistent database storage without prescribing final tables or columns in this checkpoint. | CR-001 requested outcome | Requirements review finds persistence obligations but no final schema decision; later checkpoint 8 verifies restart retention. |
| `CON-003` | Choreography shall use an in-memory EventBus and shall not depend on Kafka, ZooKeeper, or another distributed broker. | CR-001 requested outcome and exclusions | Later dependency and deployment inspection finds no broker dependency or service. |
| `CON-004` | Workflow-definition tasks shall not store mutable run status, attempt count, start time, finish time, selected transition, or terminal state. | CR-001 exclusion; EV-021; RK-003 | Later model review locates all listed mutable values in run-specific state only. |
| `CON-005` | Task outcomes shall come from named deterministic scenarios and shall not be selected randomly. | CR-001 exclusion; RK-007 | Later source and test-fixture inspection finds no random outcome selection in the approved execution path. |
| `CON-006` | Retry shall not require or create a graph cycle. | CR-001 exclusion; RK-005 | Definition and trace inspection satisfy `FR-005` and `FR-024`. |
| `CON-007` | The target shall not include parallel fork/join execution. | CR-001 exclusion | Requirements, later design, and implementation reviews contain no fork/join behavior. |
| `CON-008` | The target shall not call an external business service as part of an acceptance scenario. | CR-001 exclusion | Scenario and dependency inspection finds no external service interaction. |
| `CON-009` | Authentication, authorization, billing, notification, analytics, and unrelated feature expansion shall remain outside the defense-core scope. | CR-001 unrelated-feature exclusion and Stage 3 authorization | Requirements review finds no requirement for these capabilities. |
| `CON-010` | Final endpoint paths, database tables or columns, classes, modules, ADRs, and UML shall not be selected in Requirements v2. | Requirements checkpoint boundary; lecture slide 25 | Requirements review finds observable behavior and constraints only; architecture checkpoint 4 remains the decision gate. |
| `CON-011` | Executable tests shall not be created or run until the separately authorized verification checkpoint. | Stage 3 authorization; process gate | Stage 3 evidence contains documentation validation only and no test execution result. |
| `CON-012` | Changes to controlled draft requirement identifiers shall record the reason and update forward and reverse traceability. | Lecture slide 76 and process change control | A later requirements diff that changes an identifier includes a change record and updated traceability entries. |

## 11. Explicit exclusions

The following are not requirements of the defense core:

- Kafka, ZooKeeper, or any distributed broker;
- microservices or distributed execution;
- arbitrary graph cycles or retry encoded as a cycle;
- parallel fork/join;
- random task outcomes;
- external business services;
- mutable run state on workflow-definition tasks;
- authentication, authorization, billing, notification, or analytics;
- final API endpoint paths;
- final database tables or columns;
- final class or module design;
- UML or ADR decisions;
- unrelated feature expansion.

## 12. Deterministic acceptance scenarios

The six review cases use one abstract accepted definition without prescribing final persisted entities or code structure:

- Tasks: `Start`, `Work`, `SuccessEnd`, and `FailureEnd`.
- Start task: `Start`.
- Transitions: `Start --ALWAYS--> Work`; `Work --SUCCESS--> SuccessEnd`; `Work --FAILURE--> FailureEnd`; `Work --ALWAYS--> FailureEnd`.
- Attempt bounds: `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1`.
- `SuccessEnd` and `FailureEnd` have no outgoing transition.
- A matching transition from `Work` takes precedence over its `ALWAYS` fallback.

| Scenario | Deterministic outcomes | Expected route and retries | Expected terminal state |
|---|---|---|---|
| Success | `Start: SUCCESS`; `Work: SUCCESS`; `SuccessEnd: SUCCESS` | `Start --ALWAYS--> Work --SUCCESS--> SuccessEnd`; zero retries | Successful |
| Retry then success | `Start: SUCCESS`; `Work: FAILURE, SUCCESS`; `SuccessEnd: SUCCESS` | Retry `Work` once without traversing an edge, then `Work --SUCCESS--> SuccessEnd` | Successful |
| Permanent failure | `Start: SUCCESS`; `Work: FAILURE, FAILURE`; `FailureEnd: FAILURE` | Retry `Work` once without an edge, then `Work --FAILURE--> FailureEnd`; no retry for bound-one `FailureEnd` | Unsuccessful |

Each scenario is required in both execution modes. The complete six-case matrix and persistent trace observations are in [requirements traceability](./requirements-traceability.md). These cases are specifications only; none has been executed or passed in this checkpoint.

## 13. Assumptions and review decisions

### Assumptions

- A deterministic scenario supplies a finite outcome sequence for every task it reaches.
- Every task in an accepted definition has a positive attempt bound.
- Attempt bound means maximum total attempts, not maximum retries; therefore a bound of one permits zero retries and a bound of two permits one retry.
- Timestamps and generated run identifiers may differ between equivalent runs and are excluded from normalized semantic-parity comparison.
- A workflow definition is accepted before it can be executed; editing-during-run behavior is outside this scope.

### Review decisions

- The approved minimal routing and retry rules do not conflict with the durable baseline or archive artifacts because they specify the controlled target rather than claim existing behavior.
- Archive fallback start selection for cyclic graphs in commit `5d18b469b77beb22e6721f769fbd1b39223955a3`, `app/engine/transitions.py`, is not transferred. `FR-002` and `FR-005` require one designated start and reject cycles.
- Archive loop counters in `app/engine/transitions.py`, `app/engine/orchestrator.py`, and `app/engine/choreography.py` are comparison evidence only. `FR-021` through `FR-025` specify bounded retry state without graph cycles.
- Archive writes to both definition-level and run-level state in `app/models.py` and `app/engine/task_runner.py` are not transferred. `CON-004` requires run-specific mutable state.
- Baseline and archive Kafka/ZooKeeper artifacts do not define the target. `FR-016` and `CON-003` require in-memory choreography without broker infrastructure; `NFR-008` requires all six acceptance cases to execute without distributed-broker dependencies.
- Baseline and archive test definitions do not prove runtime correctness. The archive execution attempt remains `INCONCLUSIVE — interrupted during initial collection`.
- Stage 3 r2 completes attempt-bound applicability, removes the `FR-006`/`FR-021` dependency cycle, aligns `NFR-005` verification with its system-wide claim, and clarifies `NFR-008`. All identifiers are preserved without renumbering, and the correction introduces no scope expansion, architecture decision, or implementation claim.
- Stage 3 r3 removes the remaining `FR-017`/`FR-027` dependency cycle, makes the `FR-022` retry decision obligatory on both sides of the attempt-bound boundary, and aligns the `NFR-008` dependencies with executable-test checkpoint `T6`. All identifiers and scenario behavior are preserved, and the correction introduces no scope expansion, approval, architecture decision, or implementation claim.
- Stage 3 r4 corrects the stale `NFR-006` brokerless-choreography cross-reference while preserving normative behavior, identifiers, dependencies, scenarios, checkpoints, and scope; it introduces no approval, architecture decision, or implementation claim.
- Stage 3 approval decision: r4 passed substantive project review. Its 30 functional requirements, 8 non-functional requirements, constraints, traceability, and six-case specification form the approved Stage 3 requirements baseline. This approval does not imply implementation or approval of any later checkpoint.

## 14. Validation checklist

- [x] Each `FR-*` and `NFR-*` identifier is unique and traceable.
- [x] Each functional and non-functional requirement is atomic, normative, sourced, and objectively checkable.
- [x] Start, reachability, terminal, DAG, transition-precedence, ambiguity, retry, and parity semantics are complete and non-contradictory.
- [x] Every CR-001 requested outcome has forward and reverse traceability.
- [x] Every CR-001 exclusion is preserved.
- [x] All six acceptance cases are specified and are not described as executed or passed.
- [x] No requirement selects a final endpoint, schema, class, module, ADR, or UML design.
- [x] No unsupported performance, availability, scale, security, or hardware threshold is stated.
- [x] Architecture/UML, implementation, executable tests, deployment work, and release remain outside this checkpoint.
- [x] Requirements v2 r4 is approved as the Stage 3 requirements baseline.

## 15. Course basis and source references

Course citations were verified directly against `6 - Requirement Engineering.pdf`:

- Slide 6 distinguishes user requirements from detailed, structured system requirements.
- Slide 9 distinguishes functional behavior from non-functional constraints and system-wide properties.
- Slides 14 and 19 cover non-functional properties and require objectively testable measures for verifiable NFRs.
- Slides 25 and 31 define the requirements document as a statement of what is required, combining user and system requirements without becoming a design document.
- Slides 33 and 39 support one-requirement natural-language statements and structured specification fields.
- Slides 67, 69, and 71 support requirements validation, manual review/test-case techniques, and checks for verifiability, comprehensibility, traceability, and adaptability.
- Slides 76–78 support unique requirement identification, traceability policy, impact analysis, and controlled requirements change.

Repository and process sources:

- [CR-001](../evolution/CR-001-defense-core-refactoring.md)
- [Product backlog](../process/product-backlog.md)
- [Evidence register](../process/evidence-register.md), especially EV-018 through EV-024
- [Risk register](../process/risk-register.md)
- Baseline commit `f5ea4d71ebb4082cebe4f7e7a8a5ad3fcdfbfbaa`: `README.md`, `docs/REPORT.md`, `app/models.py`, `app/routes.py`, `app/engine/orchestrator.py`, `app/engine/choreography.py`, `app/engine/events.py`, `app/engine/task_runner.py`, and `tests/*.py`
- Archive commit `5d18b469b77beb22e6721f769fbd1b39223955a3`: `app/models.py`, `app/engine/transitions.py`, `app/engine/orchestrator.py`, `app/engine/choreography.py`, `app/engine/events.py`, `app/engine/task_runner.py`, selected graph/run test definitions, `requirements.txt`, and `docker-compose.yml`

## 16. Related controlled documents

- [Requirements traceability](./requirements-traceability.md)
- [CR-001](../evolution/CR-001-defense-core-refactoring.md)
- [Product backlog](../process/product-backlog.md)
- [Evidence register](../process/evidence-register.md)
- [Risk register](../process/risk-register.md)
- [Development process](../process/development-process.md)
- [Sprint record](../process/sprint-record.md)
