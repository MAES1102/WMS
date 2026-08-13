# Architecture Traceability v3

| Field | Value |
|---|---|
| Status | `APPROVED — synchronized architecture v3 baseline` |
| Requirements baseline | [Requirements v3 3.0](../requirements/requirements-v3.md) |
| Architecture source | [Architecture overview v3](./architecture-overview-v3.md) |
| Decision source | [Architecture decisions v3](./architecture-decisions-v3.md) |
| Controlled implementation base | `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` |

This record maps requirements to the approved project-level architecture decisions and UML views. Its rows establish design coverage; focused implementation evidence is recorded separately in EV-032–EV-034.

## 1. Forward requirement coverage

| Requirements | Architectural responsibility | ADRs | UML v3 views | Later evidence |
|---|---|---|---|---|
| `FR-001`–`FR-006` | Draft/revision model and complete pre-activation graph validation | ADR-002, ADR-009 | domain, component, activity | Definition/revision validation tests |
| `FR-007`–`FR-014` | Shared closed conditions, resolver precedence, terminal meaning, one revision/resolver | ADR-003 | component, domain, activity, both sequences | Resolver and paired-mode tests |
| `FR-015` | Central loop until waiting/terminal; same-run resume | ADR-001, ADR-004, ADR-006 | orchestration sequence, component, run state | Five orchestration cases |
| `FR-016` | Temporary run-scoped handler over persistent cursor | ADR-001, ADR-005, ADR-006 | choreography sequence, component, run state | Five choreography cases plus cleanup checks |
| `FR-017` | Shared step/executor/retry/resolver/persistence vocabulary | ADR-003–ADR-007 | component, both sequences, activity | Five normalized paired comparisons |
| `FR-018`–`FR-020` | Run/invoice ownership, cursor version, unique state partitions | ADR-002, ADR-005, ADR-006 | domain, run state, both sequences | Sequential and threaded two-run isolation pass in E23 |
| `FR-021`–`FR-025` | Automatic-task attempt bound, classified retry, no retry edge, final resolver | ADR-003, ADR-006, ADR-007 | activity, domain, both sequences | Boundary/exhaustion/trace tests |
| `FR-026` | Transactionally ordered expanded trace | ADR-002, ADR-006 | domain, run state, both sequences | Completeness/restart checks |
| `FR-031`–`FR-035` | Submission service, raw input, PDF/metadata executors, invoice/run association | ADR-001, ADR-002, ADR-008 | use cases, component, domain, deployment | Submission/PDF/invalid scenario tests |
| `FR-036`–`FR-042` | Unique work item/decision, persistent waiting, idempotent same-run resume | ADR-002, ADR-004–ADR-006 | domain, run state, both sequences | Approval/duplicate/restart/isolation tests |
| `FR-043`, `FR-044` | Archive executor, archive record/state, manual-action result | ADR-002, ADR-003, ADR-006, ADR-008 | domain, component, activity | Approved/retry/exhaustion cases |
| `FR-045` | Stable deterministic executor adapter | ADR-003, ADR-007 | component, activity | Rename/fault-schedule tests |
| `FR-046`, `FR-047` | Notification executor and consistent query projection | ADR-001, ADR-002, ADR-006 | use cases, component, domain | Scenario/query consistency tests |
| `FR-048`–`FR-052` | Bounded draft CRUD, graph projection, closed catalog, immutable activation | ADR-002, ADR-009 | use cases, component, domain | Constructor/revision application, persistence, HTTP, and visible-runtime tests pass in E22 |
| `FR-053` | User-outcome-first connected presentation | ADR-001, ADR-009 | use cases, component | UI acceptance inspection |
| `NFR-001`, `NFR-002` | Deterministic adapter and shared semantics | ADR-003–ADR-007 | both sequences, activity | Repeated and paired trace comparisons pass in E23 |
| `NFR-003` | Persistent cursor/work/decision and recovery invocation | ADR-002, ADR-004–ADR-006 | run state, both sequences, deployment | File-backed engine/session restart/resume passes; deployed-process check remains E25 |
| `NFR-004` | Same-unit-of-work trace and state ordering | ADR-006 | domain, both sequences | Ten expected-versus-retrieved traces pass in E23 |
| `NFR-005` | Definition/revision validation boundary | ADR-003, ADR-009 | activity, component | Constructor activation rule-path coverage passes in E22/E23 |
| `NFR-006` | One process, database, controlled documents | ADR-001, ADR-007, ADR-008 | deployment, component | Deployment inventory/restart |
| `NFR-007` | Cursor version and unique work/decision/attempt/trace keys | ADR-002, ADR-005, ADR-006 | domain, run state, both sequences | Threaded partitions plus duplicate/conflict tests pass |
| `NFR-008` | No random/external/broker dependency | ADR-001, ADR-005, ADR-007, ADR-008 | component, deployment | V3 source/dependency inspection passes; deployment inventory remains E25 |
| `NFR-009` | Bounded stream/storage/PDF adapter | ADR-008 | component, deployment | Seven boundary classes in both modes create zero approval work |
| `NFR-010` | Query-only status/trace path over persistent projection | ADR-001, ADR-006 | component, deployment | E23 records 100/100 below 1 s, p95 1.172 ms |
| `NFR-011` | Business projection is primary; trace/mode is secondary | ADR-001, ADR-009 | use cases, component | Five-item UI inspection |

Coverage result: all active Requirements v3 identifier groups are assigned to at least one decision, UML view, and later evidence type.

## 2. Constraint coverage

| Constraint | Architectural preservation | Verification |
|---|---|---|
| CON-001 | ADR-001/ADR-007 and deployment view contain one FastAPI process. | Deployment inventory. |
| CON-002 | ADR-002/ADR-006/ADR-008 require database and document storage but defer physical schema/path. | Design/implementation review. |
| CON-003 | ADR-005 makes EventBus in-memory/run-scoped with no broker. | Dependency/deployment and subscriber-lifecycle tests. |
| CON-004 | ADR-002 keeps all mutable state outside revision tasks. | Domain/schema inspection. |
| CON-005 | ADR-003/ADR-007 separate real input/decision from deterministic fault adapter; no random outcome. | Source/fixture inspection. |
| CON-006 | ADR-003 applies retry before resolver and never creates an edge. | Activity and trace test. |
| CON-007 | No view or decision contains fork/join. | Architecture/source inspection. |
| CON-008 | ADR-001/ADR-007/ADR-008 use only local adapters in acceptance. | Isolated execution/dependency inspection. |
| CON-009 | Explicit exclusions omit auth/billing/analytics/external email/payment/accounting/OCR/AI. | Scope/dependency inspection. |
| CON-010 | v3 design stays conceptual; endpoint paths/tables/classes remain deferred. | Document inspection. |
| CON-011 | ADR-009 closed catalog accepts no scripts/plugins. | Negative constructor tests. |
| CON-012 | ADR-009 uses forms/graph projection, not full BPMN/general low-code. | UI/scope inspection. |
| CON-013 | ADR-003/ADR-004 exclude human decisions from automatic retry. | Decision/retry trace tests. |
| CON-014 | ADR-007 and explicit exclusions keep external products as references only. | Dependency/source/report inspection. |

## 3. Reverse ADR coverage

| ADR | Requirements | Primary views | Main risks controlled |
|---|---|---|---|
| ADR-001 | `FR-031`–`FR-053`, `NFR-006`, CON-001/002/008 | context, component, deployment | RK-002, RK-010, RK-016 |
| ADR-002 | `FR-018`–`FR-020`, `FR-034`–`FR-047`, `FR-052`, `NFR-003/007`, CON-004 | domain, run state | RK-003, RK-006, RK-017 |
| ADR-003 | `FR-007`–`FR-014`, `FR-021`–`FR-025`, `FR-032/033/045`, CON-005/006/013 | component, activity | RK-005, RK-018, RK-019 |
| ADR-004 | `FR-015`, `FR-036`–`FR-044`, `NFR-003/007` | orchestration sequence, run state | RK-017, RK-018 |
| ADR-005 | `FR-016/017/020`, `FR-036`–`FR-042`, `NFR-002/003/007`, CON-003 | choreography sequence, run state | RK-004, RK-017, RK-018 |
| ADR-006 | `FR-018`–`FR-020`, `FR-023/026/034`–`FR-047`, `NFR-003/004/007` | domain, run state, sequences | RK-003, RK-006, RK-011, RK-017 |
| ADR-007 | `FR-017/045`, `NFR-001/002/008`, CON-005/008/014 | component, deployment | RK-007, RK-019, RK-021 |
| ADR-008 | `FR-031`–`FR-035`, `FR-043`, `NFR-009`, CON-009 | component, domain, deployment | RK-020, RK-021 |
| ADR-009 | `FR-001`–`FR-010`, `FR-048`–`FR-053`, `NFR-005/011`, CON-011/012 | context, component, domain | RK-005, RK-015, RK-016 |

## 4. Reverse UML coverage

| UML source | Concern | Requirements/ADRs |
|---|---|---|
| [system-context-use-cases.puml](./uml-v3/system-context-use-cases.puml) | Actors, useful invoice goals, configuration, comparison | `FR-031`–`FR-053`, `NFR-011`; ADR-001/009 |
| [component-view.puml](./uml-v3/component-view.puml) | Layered modules, shared semantics, executors, adapters | Broad functional set; ADR-001/003/005/007/008/009 |
| [domain-model.puml](./uml-v3/domain-model.puml) | Draft/revision/run/invoice/cursor/approval ownership | `FR-018`–`FR-052`; ADR-002/006/009 |
| [run-state.puml](./uml-v3/run-state.puml) | Ready/waiting/resume/terminal and idempotent decision | `FR-036`–`FR-044`, `NFR-003/007`; ADR-004–ADR-006 |
| [routing-retry-activity.puml](./uml-v3/routing-retry-activity.puml) | Human branch, failure class, retry, resolver, terminal | `FR-007`–`FR-025`, `FR-032/033/045`; ADR-003 |
| [orchestration-sequence.puml](./uml-v3/orchestration-sequence.puml) | Central submission, waiting, decision, resume | `FR-015`, invoice/approval paths; ADR-004/006 |
| [choreography-sequence.puml](./uml-v3/choreography-sequence.puml) | Transient event scope over persistent cursor | `FR-016/017`, invoice/approval paths; ADR-005/006 |
| [deployment-view.puml](./uml-v3/deployment-view.puml) | One process, database, controlled files, PDF library | `NFR-003/006/008/009`; ADR-001/007/008 |

## 5. Five-scenario design coverage

| Scenario | Architecture path | Key invariant |
|---|---|---|
| S1 Approved | submit → validate → wait → approve/resume → archive → notify | Same run/revision; archive/notification committed. |
| S2 Rejected | submit → validate → wait → reject/resume → notify | Rejection is business `FAILURE`, never retry. |
| S3 Invalid | submit → validation business failure → notify | No work item or waiting subscriber. |
| S4 Retry then archive | approved path; archive retryable failure → same-task retry → success | Retry selects no edge; both modes share fault schedule. |
| S5 Manual action | approved path; archive failures exhaust bound → failure route → notify | Invoice `NEEDS_MANUAL_ACTION`; failure routing after exhaustion. |

Each path is represented in both control sequences through the shared step service. The diagrams do not claim that ten executions passed.

## 6. C5A compatibility coverage

| Disposition | Elements | Control |
|---|---|---|
| Retain | immutable definition/result types, graph validation, transition resolver, transition concept | ADR-002/003/009 and focused compatibility tests. |
| Extend | task type/config, attempt result, trace vocabulary, run association/status | ADR-002/003/006 and migration/schema review. |
| Replace after vertical cutover | mutable task runtime fields, named task scenario lookup, incompatible routes/engines | PBI-E17–PBI-E21; no old/new dual writes. |
| Exclude | unpublished C5B1 draft | Not evidence and not a merge source. |

## 7. Review gate

Architecture approval requires:

- all nine ADRs and eight UML sources agree with Requirements v3 terminology;
- every PlantUML source passes syntax/render review and visual inspection;
- C5A retain/extend/replace decisions remain explicit;
- no diagram introduces a broker, external engine/service, full BPMN, OCR/AI, or arbitrary code;
- the architecture-approval result itself claims no source implementation, test pass, migration, deployment, or instructor approval.

Result on `2026-08-13`: all conditions passed. Eight of eight PlantUML sources parsed and rendered, all rendered views passed visual inspection, and the C5A compatibility dispositions remain explicit. Subsequent focused foundation evidence is recorded in EV-032–EV-034; Git durability is still pending.

## 8. Related records

- [Architecture overview v3](./architecture-overview-v3.md)
- [Architecture decisions v3](./architecture-decisions-v3.md)
- [Requirements traceability v3](../requirements/requirements-traceability-v3.md)
- [Product backlog](../process/product-backlog.md)
- [Risk register](../process/risk-register.md)
