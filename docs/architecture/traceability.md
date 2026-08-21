# Architecture Traceability

| Field | Value |
|---|---|
| Status | Synchronized with requirements and implementation |
| Requirements | [requirements.md](../requirements/requirements.md) |
| Overview | [overview.md](./overview.md) |
| Decisions | [decisions.md](./decisions.md) |

## Requirement-to-design coverage

| Requirements | Architectural responsibility | Decisions | UML views |
|---|---|---|---|
| `FR-001`–`FR-010`, `FR-048`–`FR-052` | Drafts, immutable revisions, graph validation, closed task catalog | ADR-002, ADR-003, ADR-009 | domain, component, routing activity |
| `FR-011`–`FR-017` | Shared terminal semantics and two control strategies | ADR-003–ADR-005 | component, both sequence views |
| `FR-018`–`FR-026` | Run ownership, cursor, retry, atomic step, ordered trace | ADR-002, ADR-003, ADR-006 | domain, run state, routing activity |
| `FR-031`–`FR-035` | Submission, bounded metadata/PDF validation | ADR-001, ADR-002, ADR-008 | context, component, domain, deployment |
| `FR-036`–`FR-042` | Persistent human waiting, decision, same-run resume | ADR-002, ADR-004–ADR-006 | domain, run state, both sequences |
| `FR-043`–`FR-047` | Archive, deterministic faults, notification, projection | ADR-002, ADR-003, ADR-006–ADR-008 | component, domain, routing activity |
| `FR-053`, `NFR-011` | Invoice-first browser experience | ADR-001, ADR-009 | context and component |
| `NFR-001`–`NFR-005`, `NFR-007` | Repeatability, parity, restart, completeness, validation, isolation | ADR-002–ADR-007, ADR-009 | run state, activity, both sequences |
| `NFR-006`, `NFR-008`, `NFR-009` | One service, local adapters, safe documents | ADR-001, ADR-005, ADR-007, ADR-008 | component and deployment |
| `NFR-010` | Query-only status projection | ADR-001, ADR-006 | component and deployment |

## Decision ownership

| Decision | Owns | Main verification |
|---|---|---|
| ADR-001 | Modular monolith and one deployment | dependency and deployment inventory tests |
| ADR-002 | Draft/revision/run/invoice ownership | model, constructor, run-state tests |
| ADR-003 | Executor result, retry, resolver order | domain and exact-trace tests |
| ADR-004 | Central orchestration | five orchestration scenarios |
| ADR-005 | Transient run-scoped choreography | five choreography scenarios and subscriber cleanup |
| ADR-006 | Persistent cursor and atomic step | restart, conflict, and trace tests |
| ADR-007 | Deterministic verification and local operation | paired-mode and dependency tests |
| ADR-008 | PDF/document boundary | storage and malformed-PDF tests |
| ADR-009 | Bounded constructor and immutable activation | CRUD, validation, and revision tests |

## UML register

| Source | Purpose |
|---|---|
| [system-context-use-cases.puml](./uml/system-context-use-cases.puml) | Actors and useful invoice goals |
| [component-view.puml](./uml/component-view.puml) | Module responsibilities and dependencies |
| [domain-model.puml](./uml/domain-model.puml) | Definition, run, invoice, approval, and trace ownership |
| [run-state.puml](./uml/run-state.puml) | Running, waiting, resume, and terminal behavior |
| [routing-retry-activity.puml](./uml/routing-retry-activity.puml) | Retry-before-routing algorithm |
| [orchestration-sequence.puml](./uml/orchestration-sequence.puml) | Centralized control sequence |
| [choreography-sequence.puml](./uml/choreography-sequence.puml) | Run-scoped event sequence |
| [deployment-view.puml](./uml/deployment-view.puml) | One service, SQLite, and document storage |

Every source has a matching SVG and PDF render under `docs/architecture/uml/rendered*`.

## Scope controls

The architecture deliberately excludes distributed brokers, microservices, external workflow engines, OCR/AI, payment/accounting integration, arbitrary user code, full BPMN, parallel fork/join, and retry cycles. These exclusions keep the implementation explainable and make the evidence reproducible on one laptop.
