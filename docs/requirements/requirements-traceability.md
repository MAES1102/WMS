# Requirements v2 Traceability

| Field | Value |
|---|---|
| Document status | `APPROVED — Stage 3 requirements baseline` |
| Requirements version | `2.0` |
| Source change request | `CR-001` |
| Source checkpoint | `6a5e42c6fa5d4d71fd599d606d7c805e95177b2f` |
| Draft date | `2026-08-11` |
| Approval date | `2026-08-11` |
| Implementation status | `NOT STARTED` |
| Release status | `NOT SCHEDULED` |

This document traces the approved Stage 3 requirements baseline in [Requirements v2](./requirements-v2.md). Approval establishes the requirements baseline only; it makes no implementation, execution, pass, deployment, or release claim.

## 1. Traceability policy

- Every controlled `FR-*` and `NFR-*` identifier has one forward-trace row.
- Every approved CR-001 outcome and exclusion has reverse coverage.
- Requirement identifiers are not renumbered or reused without a recorded reason and corresponding traceability change.
- Source presence is not runtime evidence. Baseline and archive paths are classified according to [EV-018 through EV-024](../process/evidence-register.md).
- Future evidence is named by checkpoint without inventing a file, design, class, endpoint, schema, or executable test.
- Every traceability cell contains a concrete value or a controlled future-evidence statement.

Controlled future-evidence wording:

- `A4`: Not yet assigned — architecture checkpoint 4 has not started.
- `T6`: Not yet available — executable test checkpoint 6 has not started.
- `U7`: Not yet available — UI checkpoint 7 has not started.
- `D8`: Not yet available — deployment checkpoint 8 has not started.

## 2. Forward traceability

| Requirement | Source and approved coverage | Backlog | Evidence basis | Verification method | Later checkpoint evidence | Current evidence state |
|---|---|---|---|---|---|---|
| `FR-001` | CR-001 conditional graph and explicit nodes/transitions | PBI-E06 | EV-018, EV-019 | Definition inspection and graph test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-002` | Minimal rule 1: exactly one designated start | PBI-E06 | EV-019; CR-001 transition impact | Invalid-definition test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-003` | Minimal rule 1: reachable terminal exists | PBI-E06 | EV-019; CR-001 transition impact | Invalid-definition test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-004` | Minimal rule 2: every task reachable | PBI-E06 | EV-019 | Graph-reachability test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-005` | Minimal rule 3; arbitrary-cycle exclusion | PBI-E06, PBI-E09 | EV-022, RK-005 | Self-edge and directed-cycle rejection tests | `A4`; `T6` | Approved baseline requirement; archive cycle artifacts remain comparison evidence; implementation and verification have not started |
| `FR-006` | CR-001 complete definition validation before execution, including attempt bounds | PBI-E06 | CR-001 impact analysis, RK-005 | Validation-path inspection and rejection-with-no-execution-state tests | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-007` | CR-001 `SUCCESS`/`FAILURE`/`ALWAYS` conditions | PBI-E06 | EV-019 | Condition-domain validation test | `A4`; `T6` | Approved baseline requirement; archive source presence is not runtime proof; implementation and verification have not started |
| `FR-008` | Minimal rule 4: outcome-specific precedence | PBI-E06 | EV-019 | Resolver and trace-selection test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-009` | Minimal rule 5: `ALWAYS` fallback | PBI-E06 | EV-019 | Resolver fallback test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-010` | Minimal rule 6: reject equal-precedence ambiguity | PBI-E06 | CR-001 transition impact | Duplicate-eligibility rejection test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-011` | Minimal rule 7: successful terminal | PBI-E06 | CR-001 transition impact | Terminal-semantics test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-012` | Minimal rule 7: unsuccessful terminal | PBI-E06 | CR-001 transition impact | Terminal-semantics test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-013` | CR-001 one shared workflow model | PBI-E05, PBI-E06 | EV-019, EV-020, RK-004 | Design review and cross-mode definition identity check | `A4`; `T6` | Approved baseline requirement; architecture and implementation have not started |
| `FR-014` | CR-001 shared transition-resolution rule set | PBI-E06 | EV-019, RK-004 | Paired resolver and trace comparison | `A4`; `T6` | Approved baseline requirement; no final resolver design is assigned, and architecture has not started |
| `FR-015` | CR-001 centralized orchestration | PBI-E07 | EV-018, EV-019 | Orchestration acceptance cases | `A4`; `T6` | Approved baseline requirement; baseline source presence is not current runtime proof, and implementation has not started |
| `FR-016` | CR-001 in-memory EventBus choreography | PBI-E08 | EV-018, EV-019, EV-023, EV-024 | Choreography acceptance cases without broker | `A4`; `T6` | Approved baseline requirement; Kafka runtime remains `UNVERIFIED` and excluded, and implementation has not started |
| `FR-017` | Minimal rule 11; semantic parity | PBI-E07, PBI-E08, PBI-E10 | RK-004 | Paired normalized-trace comparison | `A4`; `T6` | Approved baseline requirement; the six cases have not been executed |
| `FR-018` | CR-001 run-specific execution state | PBI-E05 | EV-020, EV-021, RK-003 | Run-state association inspection | `A4`; `T6` | Approved baseline requirement; archive artifacts remain comparison evidence, and implementation has not started |
| `FR-019` | CR-001 sequential run isolation | PBI-E05 | EV-020, RK-003 | Repeated-run isolation test | `A4`; `T6` | Approved baseline requirement; archive test definitions are not pass evidence, and verification has not started |
| `FR-020` | CR-001 concurrent run isolation | PBI-E05 | EV-020, RK-003 | Controlled-concurrency isolation test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-021` | Minimal rule 8: positive maximum-total-attempt bound for every task | PBI-E09 | RK-005 | Attempt-bound validation and boundary tests | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-022` | Minimal rule 8: retry if and only if the bound remains | PBI-E09 | EV-022, RK-005 | Two-sided boundary tests proving the required retry below the bound and prohibited retry at the bound for bounds one and two | `A4`; `T6` | Approved baseline retry rule; the archive loop counter is not accepted behavior, and implementation has not started |
| `FR-023` | Minimal rule 9: persistent attempt state | PBI-E05, PBI-E09 | EV-020, RK-005 | Attempt-state persistence inspection | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-024` | Minimal rule 9: retry without graph edge | PBI-E09 | EV-022, RK-005 | Retry trace inspection | `A4`; `T6` | Approved baseline retry rule; cycle-capable prototype behavior is excluded, and implementation has not started |
| `FR-025` | Minimal rule 10: resolution after exhaustion | PBI-E09 | EV-019, EV-022, RK-005 | Exhaustion resolver test | `A4`; `T6` | Approved baseline requirement; implementation and verification have not started |
| `FR-026` | CR-001 persistent execution trace | PBI-E05, PBI-E10 | CR-001 impact analysis, RK-004, RK-011 | Trace-content and restart test | `A4`; `T6`; `D8` | Approved baseline requirement; no trace execution evidence exists, and implementation has not started |
| `FR-027` | CR-001 deterministic success scenario | PBI-E09, PBI-E10 | RK-007 | Orchestration/choreography success cases | `T6` | Approved baseline scenario; it has not been executed or passed |
| `FR-028` | CR-001 deterministic retry-then-success scenario | PBI-E09, PBI-E10 | RK-005, RK-007 | Orchestration/choreography retry-success cases | `T6` | Approved baseline scenario; it has not been executed or passed |
| `FR-029` | CR-001 deterministic permanent-failure scenario | PBI-E09, PBI-E10 | RK-005, RK-007 | Orchestration/choreography failure cases | `T6` | Approved baseline scenario; it has not been executed or passed |
| `FR-030` | CR-001 one clear UI demonstration path | PBI-E11 | RK-013; baseline UI artifact presence | UI acceptance inspection | `U7` | Approved baseline requirement; UI checkpoint 7 has not started |
| `NFR-001` | CR-001 deterministic repeatability | PBI-E09, PBI-E10 | RK-007 | Repeated normalized-trace comparison | `T6` | Approved baseline quality requirement; verification has not started and no result exists |
| `NFR-002` | Minimal rule 11 cross-mode parity | PBI-E10 | RK-004 | Six paired-case comparisons | `T6` | Approved baseline quality requirement; the cases have not been executed |
| `NFR-003` | CR-001 persistent storage and restart retention | PBI-E12 | RK-011 | Controlled restart-retention test | `D8` | Approved baseline quality requirement; deployment has not started |
| `NFR-004` | CR-001 trace completeness | PBI-E10 | RK-004, RK-014 | Expected-versus-retrieved trace comparison | `T6` | Approved baseline quality requirement; verification has not started and no trace result exists |
| `NFR-005` | CR-001 system-wide completeness of pre-execution validation | PBI-E06, PBI-E10 | RK-005 | Validation-path inspection plus parameterized invalid, valid-boundary, and combined-violation cases | `A4`; `T6` | Approved baseline quality requirement; implementation and verification have not started |
| `NFR-006` | CR-001 single FastAPI deployment with persistent storage | PBI-E12 | RK-011 | Deployment inventory and restart check | `D8` | Approved baseline deployment constraint; deployment checkpoint 8 has not started |
| `NFR-007` | CR-001 sequential and concurrent isolation | PBI-E05, PBI-E10 | EV-020, EV-021, RK-003 | State-partition comparison | `A4`; `T6` | Approved baseline quality requirement; implementation and verification have not started |
| `NFR-008` | CR-001 deterministic, self-contained execution without external services or brokers | PBI-E10 | RK-007, RK-010 | Named-scenario execution plus source and dependency inspection against `CON-003`, `CON-005`, and `CON-008` | `T6` | Approved baseline system/dependency constraint; no deployment-checkpoint dependency exists, and the cases have not been executed |

Coverage result: all 30 functional requirements and all 8 non-functional requirements have one forward-trace row.

## 3. Reverse coverage of CR-001 requested outcomes

| Approved requested outcome | Requirement coverage | Backlog | Evidence and current state |
|---|---|---|---|
| Conditional directed acyclic workflow graph | `FR-001`–`FR-006`, `NFR-005` | PBI-E06 | EV-018, EV-019, EV-022; approved baseline target, not implemented |
| Deterministic `SUCCESS`, `FAILURE`, and `ALWAYS` selection | `FR-007`–`FR-012`, `FR-025` | PBI-E06 | EV-019; approved baseline rules, not executed |
| One shared workflow model | `FR-013` | PBI-E05, PBI-E06 | EV-019, EV-020; architecture not assigned |
| Run-specific execution state | `FR-018`, `FR-023`, `CON-004` | PBI-E05 | EV-020, EV-021; approved baseline separation requirement, not implemented |
| Isolated concurrent and sequential runs | `FR-019`, `FR-020`, `NFR-007` | PBI-E05, PBI-E10 | EV-020, RK-003; not executed |
| Bounded retry with persistent retry state | `FR-006`, `FR-021`–`FR-025`, `NFR-005` | PBI-E09 | EV-020, EV-022, RK-005; all-task bound validation and the required/prohibited retry boundary are approved baseline targets, not implemented |
| Shared `TransitionResolver` concept | `FR-014` | PBI-E06 | EV-019, RK-004; shared rule requirement only, no final class/module design |
| Centralized orchestration | `FR-015` | PBI-E07 | EV-018, EV-019; source artifacts do not prove target behavior |
| In-memory EventBus choreography | `FR-016`, `CON-003` | PBI-E08 | EV-018, EV-023, EV-024; broker excluded, target not executed |
| Persistent execution trace | `FR-026`, `NFR-004` | PBI-E05, PBI-E10 | RK-004, RK-011; approved baseline target, no execution evidence |
| Deterministic success scenario | `FR-027`, `NFR-001`, `NFR-008` | PBI-E09, PBI-E10 | RK-007; two specified cases, not executed |
| Deterministic retry-then-success scenario | `FR-028`, `NFR-001`, `NFR-008` | PBI-E09, PBI-E10 | RK-005, RK-007; two specified cases, not executed |
| Deterministic permanent-failure scenario | `FR-029`, `NFR-001`, `NFR-008` | PBI-E09, PBI-E10 | RK-005, RK-007; two specified cases, not executed |
| One clear UI demonstration path | `FR-030` | PBI-E11 | RK-013; UI checkpoint 7 not started |
| One FastAPI deployment with persistent database storage | `NFR-003`, `NFR-006`, `CON-001`, `CON-002` | PBI-E12 | RK-011; deployment checkpoint 8 not started |

Reverse outcome coverage result: every CR-001 requested outcome is mapped to at least one approved baseline requirement and one later checkpoint.

## 4. Reverse coverage of exclusions

| Approved exclusion | Normative preservation | Verification | Current state |
|---|---|---|---|
| Kafka and ZooKeeper | `NFR-008`, `CON-003` | Later source, dependency, and deployment inventory | Preserved; no broker requirement introduced |
| Distributed-broker dependencies | `NFR-008`, `CON-003` | Later source and dependency inspection | Preserved |
| Unsupported microservice claims | `CON-001` | Requirements and later deployment review | Preserved; one FastAPI application required |
| Distributed execution | `CON-001` | Requirements and later deployment review | Preserved |
| Arbitrary graph cycles | `FR-005`, `FR-024`, `CON-006` | Invalid-graph and retry-trace checks | Preserved |
| Parallel fork/join | `CON-007` | Requirements and later design review | Preserved |
| Random outcomes | `FR-027`–`FR-029`, `NFR-008`, `CON-005` | Scenario and later source inspection | Preserved |
| External business services | `NFR-008`, `CON-008` | Scenario dependency inspection | Preserved |
| Mutable runtime state on workflow-definition tasks | `FR-018`, `CON-004` | Later model and state-location review | Preserved |
| Unrelated feature expansion | `CON-009` | Requirements scope review | Preserved |
| Final API endpoint paths | `CON-010` | Requirements content inspection | Preserved checkpoint boundary |
| Final schema or class/module design | `CON-002`, `CON-010` | Requirements content inspection | Preserved checkpoint boundary |
| UML or ADR decisions | `CON-010` | Requirements content inspection | Preserved; checkpoint 4 not started |

Reverse exclusion coverage result: every CR-001 exclusion and every Stage 3 prohibited design expansion is explicitly preserved.

## 5. Six-case acceptance-scenario matrix

All cases use the abstract accepted definition specified in Requirements v2: `Start`, `Work`, `SuccessEnd`, and `FailureEnd`; transitions `Start --ALWAYS--> Work`, `Work --SUCCESS--> SuccessEnd`, `Work --FAILURE--> FailureEnd`, and `Work --ALWAYS--> FailureEnd`; attempt bounds `Start: 1`, `Work: 2`, `SuccessEnd: 1`, and `FailureEnd: 1`. Each case starts with a new run-specific state and no attempt or trace entry for that run.

| Case | Initial state | Configured attempt bounds | Deterministic task outcomes | Expected retry count | Expected transition path | Expected terminal state | Required persistent trace observations | Related requirements |
|---|---|---|---|---|---|---|---|---|
| Orchestration × success | Accepted definition; mode `orchestration`; success scenario; new isolated run | `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1` | `Start: SUCCESS`; `Work: SUCCESS`; `SuccessEnd: SUCCESS` | Zero | `Start --ALWAYS--> Work --SUCCESS--> SuccessEnd` | Successful | Ordered attempts for all three reached tasks; `ALWAYS` fallback from `Start`; outcome-specific `SUCCESS` selection from `Work`; zero retry observations; successful terminal record | `FR-008`, `FR-009`, `FR-011`, `FR-015`, `FR-021`, `FR-026`, `FR-027`, `NFR-001`, `NFR-004`, `NFR-008` |
| Orchestration × retry-then-success | Accepted definition; mode `orchestration`; retry-success scenario; new isolated run | `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1` | `Start: SUCCESS`; `Work: FAILURE, SUCCESS`; `SuccessEnd: SUCCESS` | One retry for `Work` | `Start --ALWAYS--> Work`; retry `Work` without edge; `Work --SUCCESS--> SuccessEnd` | Successful | `Work` attempt one failure; persistent retry observation; no transition during retry; `Work` attempt two success; `SUCCESS` selection; successful terminal record | `FR-015`, `FR-021`–`FR-028`, `NFR-001`, `NFR-004`, `NFR-008` |
| Orchestration × permanent failure | Accepted definition; mode `orchestration`; permanent-failure scenario; new isolated run | `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1` | `Start: SUCCESS`; `Work: FAILURE, FAILURE`; `FailureEnd: FAILURE` | One retry for `Work`; zero for bound-one `FailureEnd` | `Start --ALWAYS--> Work`; retry `Work` without edge; `Work --FAILURE--> FailureEnd`; no eligible edge after `FailureEnd` | Unsuccessful | Two ordered `Work` attempts; one retry observation; no retry edge; outcome-specific `FAILURE` selection before `ALWAYS`; one failed `FailureEnd` attempt; unsuccessful terminal record | `FR-012`, `FR-015`, `FR-021`–`FR-026`, `FR-029`, `NFR-001`, `NFR-004`, `NFR-008` |
| Choreography × success | Accepted definition; mode `choreography`; success scenario; new isolated run; in-memory EventBus available | `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1` | `Start: SUCCESS`; `Work: SUCCESS`; `SuccessEnd: SUCCESS` | Zero | `Start --ALWAYS--> Work --SUCCESS--> SuccessEnd` | Successful | Ordered event-driven attempts for all three reached tasks; same selections and terminal record as orchestration success; no broker observation; zero retries | `FR-008`, `FR-009`, `FR-011`, `FR-016`, `FR-017`, `FR-021`, `FR-026`, `FR-027`, `NFR-002`, `NFR-004`, `NFR-008` |
| Choreography × retry-then-success | Accepted definition; mode `choreography`; retry-success scenario; new isolated run; in-memory EventBus available | `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1` | `Start: SUCCESS`; `Work: FAILURE, SUCCESS`; `SuccessEnd: SUCCESS` | One retry for `Work` | `Start --ALWAYS--> Work`; retry `Work` without edge; `Work --SUCCESS--> SuccessEnd` | Successful | Same normalized attempt, retry, transition, ordering, and terminal observations as orchestration retry-success; no broker observation | `FR-016`, `FR-017`, `FR-021`–`FR-028`, `NFR-002`, `NFR-004`, `NFR-008` |
| Choreography × permanent failure | Accepted definition; mode `choreography`; permanent-failure scenario; new isolated run; in-memory EventBus available | `Start: 1`; `Work: 2`; `SuccessEnd: 1`; `FailureEnd: 1` | `Start: SUCCESS`; `Work: FAILURE, FAILURE`; `FailureEnd: FAILURE` | One retry for `Work`; zero for bound-one `FailureEnd` | `Start --ALWAYS--> Work`; retry `Work` without edge; `Work --FAILURE--> FailureEnd`; no eligible edge after `FailureEnd` | Unsuccessful | Same normalized attempt, retry, transition, ordering, and terminal observations as orchestration permanent failure; no broker observation | `FR-012`, `FR-016`, `FR-017`, `FR-021`–`FR-026`, `FR-029`, `NFR-002`, `NFR-004`, `NFR-008` |

Matrix status: specification only. No case has been executed or passed. `T6` remains not yet available because executable test checkpoint 6 has not started.

## 6. Review and change controls

- Requirements v2 is `APPROVED — Stage 3 requirements baseline` at version `2.0`.
- The Stage 3 documentation commit establishes the approved baseline and continuing change control; later changes require recorded impact analysis and explicit approval.
- Architecture/UML, implementation, executable tests, deployment, and release remain not started.
- A proposed requirement change must identify affected forward rows, reverse coverage, acceptance cases, backlog items, risks, and later evidence checkpoints before approval.

## 7. Related records

- [Requirements v2](./requirements-v2.md)
- [CR-001](../evolution/CR-001-defense-core-refactoring.md)
- [Product backlog](../process/product-backlog.md)
- [Evidence register](../process/evidence-register.md)
- [Risk register](../process/risk-register.md)
- [Development process](../process/development-process.md)
- [Sprint record](../process/sprint-record.md)
