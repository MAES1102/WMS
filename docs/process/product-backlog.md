# Product Backlog

## Evidence policy

Backlog entries use evolution identifiers, not final requirement identifiers. No effort values or story points are assigned. Historical output is separated from current evolution work and excluded scope. Classifications follow the [development process](./development-process.md).

## Evidenced historical work

| ID | Historical objective/output | Evidence | Classification | Limitation |
|---|---|---|---|---|
| PBI-H01 | Create a FastAPI/SQLite workflow CRUD foundation | Baseline source at `v1-linear-baseline` | `VERIFIED` | Commit history does not isolate a sprint increment |
| PBI-H02 | Execute ordered tasks through centralized orchestration | Baseline engine source and tests | `VERIFIED` as implementation presence | Historical passing result is `UNVERIFIED` in this checkpoint |
| PBI-H03 | Execute ordered tasks through in-memory EventBus choreography | Baseline engine and EventBus source | `VERIFIED` as implementation presence | Kafka behavior and prior pass claims require revalidation |
| PBI-H04 | Provide dashboard, run history, logging, and documentation | Baseline UI, routes, models, README, and report | `VERIFIED` as artifact presence | Completeness and report accuracy are not implied |
| PBI-H05 | Explore transitions, branching, loops, and per-run task state | `archive/advanced-prototype` | `VERIFIED` as preserved prototype content | Verification is `INCONCLUSIVE`; architecture is not accepted wholesale |

## Current evolution backlog

| ID | Objective | Rationale | Priority | Status | Source/evidence | Acceptance condition | Dependency | Target checkpoint |
|---|---|---|---|---|---|---|---|---|
| PBI-E01 | Establish durable process and evidence records | Make work visible without fabricating history | Highest | Accepted | Stage 2 authorization and Stage 1 refs | Eight authorized documents pass validation and review | Stage 1 preservation | 2 |
| PBI-E02 | Review CR-001 scope and impact | Prevent uncontrolled transfer of prototype debt | Highest | Approved | [CR-001](../evolution/CR-001-defense-core-refactoring.md) | Reviewer accepts problem, scope, risks, alternatives, and impact analysis | PBI-E01 | 2 |
| PBI-E03 | Produce Requirements v2 | Define observable behavior and quality constraints before design | Highest | Approved and committed — checkpoint 3 complete | CR-001 requested outcome | Requirements are approved, testable, traced, and contain no excluded scope | Committed Stage 2 record and approved PBI-E02 | 3 |
| PBI-E04 | Draft architecture decisions and matching UML | Make design reviewable before implementation | High | Not started | Course process guidance and CR-001 | ADR/UML set represents the approved model and execution semantics | PBI-E03 | 4 |
| PBI-E05 | Introduce run-specific domain and persistence concepts | Prevent runtime state from leaking through workflow definitions | High | Not started | Prototype risk and CR-001 | Reviewed model separates definition, run, task execution, retry, and trace state | PBI-E04 | 5 |
| PBI-E06 | Implement conditional DAG transition resolution | Provide deterministic routing without arbitrary cycles | High | Not started | CR-001 | Shared resolver selects `SUCCESS`, `FAILURE`, or `ALWAYS` deterministically on an acyclic graph | PBI-E05 | 5 |
| PBI-E07 | Implement centralized orchestration on the shared model | Preserve explicit central control with common semantics | High | Not started | CR-001 | Orchestration uses the approved resolver and persistent run state | PBI-E06 | 5 |
| PBI-E08 | Implement in-memory EventBus choreography on the shared model | Demonstrate reactive control without broker infrastructure | High | Not started | CR-001 | Event-driven path uses the same transitions and terminal semantics as orchestration | PBI-E06 | 5 |
| PBI-E09 | Implement bounded retry and deterministic scenarios | Remove random outcomes and graph-cycle retries | High | Not started | CR-001 | Success, retry-then-success, and permanent-failure scenarios are repeatable and persist retry state | PBI-E05-PBI-E08 | 6 |
| PBI-E10 | Add six focused execution tests | Verify both modes and deterministic scenarios before UI work | Highest | Not started | Review-gate plan | Six approved tests pass in isolation with persistent trace assertions | PBI-E07-PBI-E09 | 6 |
| PBI-E11 | Provide one clear UI demonstration path | Make the approved behavior observable without feature sprawl | Medium | Not started | CR-001 | UI demonstrates one workflow and its persistent trace consistently | PBI-E10 | 7 |
| PBI-E12 | Simplify deployment to one FastAPI service with persistent storage | Remove broker dependencies and ensure retained data | High | Not started | CR-001 exclusions | Deployment restarts without losing approved persistent state | PBI-E10 | 8 |
| PBI-E13 | Reconcile final report, UML, traceability, and evidence | Prevent code/report drift at release decision | High | Not started | Instructor feedback and DoD | Final artifacts match the verified implementation and explicitly state limitations | PBI-E03-PBI-E12 | 9 |

## Excluded scope

| Excluded item | Reason |
|---|---|
| Kafka, ZooKeeper, and distributed brokers | Broker runtime behavior is `UNVERIFIED`, and broker infrastructure is unnecessary for the proposed defense-core scope |
| Microservice claims and distributed execution | The target is a single FastAPI application |
| Arbitrary graph cycles | Retry state must be bounded and explicit rather than encoded as cycles |
| Parallel fork/join | Outside the approved defense-core conditional-DAG scope |
| Random execution outcomes | Conflicts with deterministic verification and demonstration |
| External business services | Adds integration risk without supporting the core objective |
| Mutable runtime state on workflow-definition tasks | Violates run isolation |
| Unrelated feature expansion | Controlled scope is required for checkpoint review |

See the [risk register](./risk-register.md), [sprint record](./sprint-record.md), and [CR-001](../evolution/CR-001-defense-core-refactoring.md).
