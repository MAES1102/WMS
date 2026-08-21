# Architecture Traceability

| Field | Value |
|---|---|
| Status | Reconciled with implementation and verification |
| Requirements | [requirements.md](../requirements/requirements.md) |
| Overview | [overview.md](./overview.md) |
| Decisions | [decisions.md](./decisions.md) |

## Requirement-to-design coverage

| Concern | Architectural responsibility | UML/evidence |
|---|---|---|
| Drafts, immutable revisions, graph validation | Constructor service, domain validator, revision repository | Domain, component, activity views; constructor tests |
| Shared routing and terminal semantics | Domain resolver used by the shared automatic step service | Activity view; resolver tests |
| Retry before routing | Retry policy, attempt persistence, step service | Activity view; retry and exact-trace tests |
| Run ownership and isolation | Revision/request references, cursor, run-scoped repositories | Domain/run-state views; sequential and concurrent isolation tests |
| Structured request validation | Purchase Request domain validation and executor | Context/component views; domain and journey tests |
| Persistent approval and same-run resume | Approval service, work item/decision persistence, coordinator | Domain/run-state/sequence views; decision and restart tests |
| Purchase Authorization and Internal Notification | Controlled effect policies and persistence records | Domain/component views; business journey tests |
| Orchestration | Central strategy over shared step service | Orchestration sequence; paired scenario tests |
| Choreography | Temporary synchronous run-scoped EventBus handler | Choreography sequence; parity and cleanup tests |
| Four-view browser experience | Static UI and presentation APIs | Context view; UI structure and connected API tests |
| One-service local deployment | FastAPI, SQLite, optional Docker Compose volume | Deployment view; Compose validation |

## Decision ownership

| Decision | Owns | Main verification |
|---|---|---|
| ADR-001 | Modular monolith and single-service deployment | dependency/deployment inspection |
| ADR-002 | Draft, revision, run, cursor, and request ownership | persistence and constructor tests |
| ADR-003 | Executor result, retry, and resolver order | domain/step-service tests |
| ADR-004 | Central orchestration | orchestration scenarios and restart |
| ADR-005 | Transient run-scoped choreography | choreography scenarios, cleanup, restart |
| ADR-006 | Persistent cursor and atomic observable step | conflict, isolation, trace, recovery tests |
| ADR-007 | Deterministic demonstration failures | paired-mode retry/exhaustion tests |
| ADR-008 | Structured Purchase Request boundary | domain validation and submission journey tests |
| ADR-009 | Closed designer and immutable activation | CRUD, validation, and revision tests |

## UML register

| Source | Purpose |
|---|---|
| [system-context-use-cases.puml](./uml/system-context-use-cases.puml) | Actors, system boundary, and useful outcomes |
| [component-view.puml](./uml/component-view.puml) | Modules, ports, database, and internal EventBus |
| [domain-model.puml](./uml/domain-model.puml) | Definition/revision, request/run, approval, effects, and trace ownership |
| [run-state.puml](./uml/run-state.puml) | Ready, waiting, resume, and terminal lifecycle |
| [routing-retry-activity.puml](./uml/routing-retry-activity.puml) | Retry-before-routing algorithm |
| [orchestration-sequence.puml](./uml/orchestration-sequence.puml) | Central control sequence |
| [choreography-sequence.puml](./uml/choreography-sequence.puml) | Synchronous run-scoped event sequence |
| [deployment-view.puml](./uml/deployment-view.puml) | Browser, one FastAPI service, SQLite volume |

Every PlantUML source has a corresponding SVG under `docs/architecture/uml/rendered/`.

## Scope controls

The architecture excludes authentication/RBAC, external procurement/accounting/payment/email integration, distributed brokers, microservices, arbitrary user code, general BPMN, parallel fork/join, production scalability claims, and high-availability claims.
