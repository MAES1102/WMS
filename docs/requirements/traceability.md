# Requirements Traceability

| Field | Value |
|---|---|
| Requirements source | [requirements.md](./requirements.md) |
| Change source | [CR-003](../evolution/CR-003-purchase-request-reference-workflow.md) |
| Architecture source | [overview.md](../architecture/overview.md) |
| Verification date | 2026-08-21 |
| Status | Implemented and covered by automated or inspection evidence |

This record maps requirement groups to product components and verification evidence. Exact test names are intentionally kept in the repository instead of duplicating hundreds of case descriptions here.

## Forward coverage

| Requirement group | Product responsibility | Main implementation | Verification evidence |
|---|---|---|---|
| `FR-001`–`FR-006` | Definition graph and complete validation before activation | `app/domain/validation.py`, constructor service/repository | `tests/domain/test_validation.py`, constructor tests |
| `FR-007`–`FR-014` | Transition conditions, precedence, terminal meaning, shared resolver | `app/domain/resolver.py`, `app/domain/types.py` | resolver and paired-mode tests |
| `FR-015` | Centralized orchestration | `app/application/orchestration.py` | orchestration and integrated persistence scenarios |
| `FR-016`, `FR-017` | Run-scoped choreography and mode parity | `app/application/choreography.py`, EventBus adapter | choreography, subscriber-cleanup, and paired-mode tests |
| `FR-018`–`FR-020` | Run-owned state and isolation | persistence models and unit-of-work adapters | sequential and threaded isolation tests |
| `FR-021`–`FR-025` | Positive attempt bounds, failure classes, retry-before-routing | retry policy and automatic-step service | retry boundary, exhaustion, and exact-trace tests |
| `FR-026` | Ordered persistent trace | persistence step and run-query services | trace completeness and restart tests |
| `FR-031`–`FR-035` | Structured JSON submission and Purchase Request field validation | submission API/service and domain validation executor | submission, domain, invalid-input, and connected journey tests |
| `FR-036`–`FR-042` | Persistent human work and idempotent same-run resume | approval service/repository and execution coordinator | approval boundary, duplicate/conflict, restart, and isolation tests |
| `FR-043`, `FR-044` | Authorization success and controlled manual action | authorization executor and business effect policy | approved, retry, and exhausted-failure scenarios |
| `FR-045` | Explicit deterministic authorization behaviors | `AuthorizationDemoFaultExecutor`, persisted run scenario | executor, HTTP, and both-mode scenario tests |
| `FR-046`, `FR-047` | Final notification and consistent status projection | notification executor and run-query service | all scenario and API projection tests |
| `FR-048`–`FR-052` | Bounded draft CRUD, closed catalog, immutable revision activation | constructor application/persistence/presentation modules | constructor service, persistence, API, and UI tests |
| `FR-053` | Connected Purchase Request-first browser demonstration | `app/static/index.html` and presentation APIs | UI structure and integrated HTTP paths |
| `NFR-001`, `NFR-002` | Repeatability and cross-mode semantic parity | shared services and normalized trace vocabulary | repeated five-scenario matrix in both modes |
| `NFR-003`, `NFR-004` | Restart survival and complete committed trace | SQLite persistence and versioned execution cursor | file-backed and OS-process restart tests; exact trace tests |
| `NFR-005` | Complete pre-activation validation | domain validator and constructor activation boundary | positive and negative rule-path tests |
| `NFR-006`, `NFR-008` | One local service with no broker or external business system | Docker inventory and local adapters | deployment/source/dependency inspections |
| `NFR-007` | Isolation and concurrency protection | run keys, unique constraints, state versions | threaded partitions and decision-conflict tests |
| `NFR-009` | Complete structured field validation before approval | Purchase Request domain validator | field-boundary and invalid-request cases |
| `NFR-010` | Responsive local status reads | query-only persistent projection | timed local query matrix |
| `NFR-011` | Business state is primary in the UI | purchase request status panel | UI content inspection |

## Five business scenarios

| Scenario | Expected outcome | Key requirements | Evidence |
|---|---|---|---|
| S1 Approved | `AUTHORIZED`, final notification, completed run | `FR-031`–`FR-039`, `FR-042`, `FR-043`, `FR-046` | Both execution modes |
| S2 Rejected | `REJECTED`, reason visible, authorization skipped | `FR-036`–`FR-042`, `FR-046` | Both execution modes |
| S3 Invalid | `VALIDATION_FAILED`, no approval work item | `FR-032`, `FR-033`, `FR-035` | Structured field boundary suites |
| S4 Retry then success | two authorization attempts, one retry, `AUTHORIZED` | `FR-022`–`FR-025`, `FR-043`, `FR-045` | Explicit UI/API scenario in both modes |
| S5 Manual action | bound exhausted, `NEEDS_MANUAL_ACTION` | `FR-022`–`FR-025`, `FR-044`, `FR-045` | Explicit UI/API scenario in both modes |

## Constraint coverage

| Constraint group | Evidence |
|---|---|
| `CON-001`–`CON-003` | One FastAPI service, one SQLite volume, run-scoped in-memory EventBus, no broker |
| `CON-004`–`CON-007` | Immutable definitions, run-specific state, deterministic outcomes, no retry edges or fork/join |
| `CON-008`–`CON-010` | No external business calls; excluded integrations absent; requirements remain solution-independent |
| `CON-011`–`CON-013` | Closed constructor, no executable user input, human decisions never retried |
| `CON-014` | Reference products disclosed; no external workflow engine included |

## Reverse coverage

The implementation contains no feature without a product or quality justification:

- purchase request submission, approval, authorization, notification, and status satisfy the business requirements;
- graph validation, retry, resolver, cursor, and trace satisfy correctness and recoverability requirements;
- two coordination strategies satisfy the course comparison objective;
- the constructor satisfies bounded configurability without becoming a general low-code platform;
- deployment and tests support repeatable academic demonstration.
