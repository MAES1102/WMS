# Requirements v3 Traceability

| Field | Value |
|---|---|
| Status | `APPROVED — synchronized with Requirements v3 3.0` |
| Requirements source | [Requirements v3](./requirements-v3.md) |
| Change source | [CR-002](../evolution/CR-002-invoice-approval-reference-application.md) |
| Controlled implementation base | `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` |
| Implementation evidence | Focused foundation/E18/E19 evidence (`EV-032`–`EV-039`); no end-to-end v3 execution |

This document provides forward and reverse coverage for the approved project-level Requirements v3 baseline. Backlog references abbreviate `PBI-E17` as `E17` and follow the same pattern for the other evolution items. `A-v3` means the approved architecture/ADR/UML v3 baseline. `T-v3`, `U-v3`, and `D-v3` are future verification, UI, and deployment evidence checkpoints; none exists yet.

## 1. Forward traceability

### Definition, routing, execution, and state

| Requirement | Source | Backlog | Risks | Verification | Required next design/evidence | Current state |
|---|---|---|---|---|---|---|
| `FR-001` | CR-001 retained by CR-002 | E17, E22 | RK-005 | Definition inspection/test | `A-v3`: domain/activity; `T-v3` | Draft and immutable revision definitions pass application, persistence, and HTTP cases |
| `FR-002` | CR-001 retained | E17, E22 | RK-005 | Start-count cases | `A-v3`: validation activity; `T-v3` | Start-count validation is enforced before E22 activation |
| `FR-003` | CR-001 retained | E17, E22 | RK-005 | Reachable-terminal case | `A-v3`; `T-v3` | Reachable-terminal validation is enforced before E22 activation |
| `FR-004` | CR-001 retained | E17, E22 | RK-005 | Unreachable-task cases | `A-v3`; `T-v3` | Full reachability validation is enforced before E22 activation |
| `FR-005` | CR-001 retained | E17, E22 | RK-005 | Self-edge/cycle cases | `A-v3`; `T-v3` | Self-edges are rejected at draft storage and cycles before E22 activation |
| `FR-006` | CR-001 retained; CR-002 activation impact | E17, E22 | RK-005 | Validation/no-state test | `A-v3`: activation boundary; `T-v3` | Invalid activation returns issues without creating a revision or run |
| `FR-007` | CR-001 retained | E17, E22 | RK-005 | Condition cases | `A-v3`; `T-v3` | Closed transition conditions are enforced at API, storage, and activation boundaries |
| `FR-008` | CR-001 retained | E17 | RK-004, RK-018 | Resolver precedence test | `A-v3`: shared resolver; `T-v3` | Domain and shared-step cases pass |
| `FR-009` | CR-001 retained | E17 | RK-004, RK-018 | Fallback test | `A-v3`; `T-v3` | Focused resolver cases pass |
| `FR-010` | CR-001 retained | E17, E22 | RK-005 | Ambiguity cases | `A-v3`; `T-v3` | Equal-precedence ambiguity is rejected before draft persistence and activation |
| `FR-011` | CR-001 retained | E20, E21 | RK-018 | Successful terminal test | `A-v3`: run state/sequences; `T-v3` | All five scenarios in both modes reach the same persisted successful terminal state |
| `FR-012` | CR-001 retained | E20, E21 | RK-018 | Unsuccessful terminal test | `A-v3`; `T-v3` | C5A resolver concept present |
| `FR-013` | CR-001 retained | E17, E20, E21 | RK-004, RK-018 | Revision identity comparison | `A-v3`: domain/component; `T-v3` | Both strategies execute the same immutable reference-revision model |
| `FR-014` | CR-001 retained | E17, E20, E21 | RK-004, RK-018 | Paired resolver comparison | `A-v3`: component/sequences; `T-v3` | Both strategies delegate routing to the same resolver through the shared step and approval services |
| `FR-015` | Approved proposal; CR-002 retained | E20 | RK-004, RK-017 | Five orchestration cases | `A-v3`: orchestration sequence; `T-v3` | Five centralized orchestration scenarios pass over shared services |
| `FR-016` | Approved proposal; CR-002 retained | E21 | RK-004, RK-017, RK-018 | Five choreography cases | `A-v3`: choreography sequence/event lifecycle; `T-v3` | Five choreography scenarios pass through run-scoped events with zero retained subscribers |
| `FR-017` | CR-002 parity modification | E20, E21, E23 | RK-004, RK-018 | Ten-case normalized comparison | `A-v3`: shared services/trace; `T-v3` | Ten cross-mode executions and five normalized comparisons pass; E23 adds 20 repeatability executions |
| `FR-018` | CR-001 retained; CR-002 expanded | E17 | RK-003, RK-017 | Run association inspection | `A-v3`: domain/run state; `T-v3` | V3 schema and SQLAlchemy step adapter partition state by run |
| `FR-019` | CR-001 retained | E23 | RK-003 | Sequential isolation | `A-v3`; `T-v3` | Repeated isolated scenario executions preserve their own invoice/run/trace state |
| `FR-020` | CR-001 retained; invoice state added | E23 | RK-003, RK-017 | Concurrent isolation | `A-v3`; `T-v3` | Two file-backed runs per mode are driven and resumed in worker threads with exact state partitions |
| `FR-021` | CR-001 retained | E17, E22 | RK-005 | Bound validation | `A-v3`: executor policy; `T-v3` | Domain, schema, and defensive step checks pass |
| `FR-022` | CR-002 failure-classification modification | E17, E20, E21 | RK-005, RK-018 | Retry two-sided cases | `A-v3`: executor/result model; `T-v3` | Focused retry and shared-step cases pass |
| `FR-023` | CR-002 attempt-payload modification | E17, E23 | RK-005, RK-011 | Persistence/restart | `A-v3`: domain/persistence; `T-v3`, `D-v3` | Attempts/results/cursor survive file-backed engine/session and real Uvicorn process recreation in both modes |
| `FR-024` | CR-001 retained | E20, E21, E23 | RK-005 | No-edge retry trace | `A-v3`; `T-v3` | S4/S5 retries in both modes record no transition during the retry |
| `FR-025` | CR-001 retained | E20, E21, E23 | RK-005, RK-018 | Exhaustion routing | `A-v3`; `T-v3` | S5 in both modes routes failure only after the second bounded attempt |
| `FR-026` | CR-002 trace expansion | E17, E20, E21, E23 | RK-004, RK-011, RK-017 | Trace completeness/restart | `A-v3`: domain/state/sequences; `T-v3`, `D-v3` | Ten exact expected trace sequences pass and waiting traces survive real process recreation in both modes |

### Invoice, approval, constructor, and UI

| Requirement | Source | Backlog | Risks | Verification | Required next design/evidence | Current state |
|---|---|---|---|---|---|---|
| `FR-031` | CR-002 requested outcome | E18 | RK-015, RK-020 | Submission API/UI | `A-v3`: use case/domain/component; `T-v3`, `U-v3` | Integrated multipart submission and invoice-first Chromium path pass |
| `FR-032` | CR-002 bounded validation | E18, E23 | RK-020 | Metadata boundaries | `A-v3`: validation activity; `T-v3` | Complete field cases and persisted validation flow pass |
| `FR-033` | CR-002 PDF validation/exclusions | E18, E23 | RK-020 | PDF boundary suite | `A-v3`: executor/component; `T-v3` | Bounded storage/`pypdf` cases and persisted malformed-PDF flow pass |
| `FR-034` | CR-002 persistence/run impact | E17, E18 | RK-003, RK-017 | Association test | `A-v3`: domain/state; `T-v3` | Invoice/run/revision/cursor association integration case passes |
| `FR-035` | CR-002 invalid path | E18, E23 | RK-015, RK-018 | S3 paired cases | `A-v3`: state/sequence; `T-v3` | S3 in both modes completes validation-failure routing with zero approval work and one notification |
| `FR-036` | CR-002 human work item | E19 | RK-017 | Exactly-one creation | `A-v3`: domain/state/sequences; `T-v3` | Exactly-one pending creation and duplicate entry pass |
| `FR-037` | CR-002 wait lifecycle | E19 | RK-017 | Waiting/no-advance | `A-v3`: run state/sequences; `T-v3` | Invoice/run/cursor waiting transaction and session reconstruction pass |
| `FR-038` | CR-002 approver goal | E19, E24 | RK-015 | Pending list/detail | `A-v3`: use case/component; `T-v3`, `U-v3` | Query/list/detail and visible approve/reject action pass in both reference browser modes |
| `FR-039` | CR-002 approval path | E19, E23 | RK-017, RK-018 | Approve/boundary | `A-v3`: state/sequences; `T-v3` | Approve, optional-note, state, and success-route cases pass |
| `FR-040` | CR-002 rejection path | E19, E23 | RK-017, RK-018 | Reject/reason boundaries | `A-v3`; `T-v3` | Rejection boundaries, trimmed reason, state, and failure-route cases pass |
| `FR-041` | CR-002 idempotency control | E19, E23 | RK-017 | Duplicate/conflict | `A-v3`: state/concurrency decision; `T-v3` | Identical replay, conflict, uniqueness, stale/race rollback cases pass |
| `FR-042` | CR-002 same-run resume | E19, E20, E21, E23 | RK-003, RK-017, RK-018 | Resume/isolation | `A-v3`: both sequences/event lifecycle; `T-v3`, `D-v3` | Decision coordinator resumes the same run/cursor in both modes, including after real Uvicorn process recreation |
| `FR-043` | CR-002 approved archive | E20, E21 | RK-015, RK-018 | S1/S4 paired cases | `A-v3`: executor/state; `T-v3` | S1/S4 in both modes preserve document identity, create one archive record, and set `ARCHIVED` |
| `FR-044` | CR-002 manual-action result | E20, E21 | RK-005, RK-018 | S5 paired cases | `A-v3`; `T-v3` | S5 in both modes sets `NEEDS_MANUAL_ACTION` before failure routing after bound exhaustion |
| `FR-045` | CR-002 deterministic adapter | E17, E23 | RK-007, RK-019 | Adapter/rename test | `A-v3`: executor boundary; `T-v3` | Stable run/task/attempt adapter and rename-independent case pass |
| `FR-046` | CR-002 internal notification | E20, E21 | RK-015, RK-018 | Scenario notification check | `A-v3`: domain/component; `T-v3` | Every scenario in both modes persists one equivalent final-state notification |
| `FR-047` | CR-002 submitter visibility | E18, E24 | RK-015 | Status/history consistency | `A-v3`: use case/component; `T-v3`, `U-v3` | Integrated HTTP/UI preview returns consistent invoice/approval/archive/notification/run/trace state |
| `FR-048` | CR-002 bounded CRUD | E22 | RK-016 | Draft CRUD | `A-v3`: use case/domain/component; `T-v3`, `U-v3` | List/create/get/replace/delete pass through the bounded service and HTTP boundary; activated-history deletion is rejected |
| `FR-049` | CR-002 closed task catalog | E22 | RK-016, RK-021 | Unsupported-type cases | `A-v3`: domain/validation; `T-v3` | Closed catalog and complete executor registry pass focused cases |
| `FR-050` | CR-002 constructor fields | E22 | RK-016 | Form/API configuration | `A-v3`: use case/component; `T-v3`, `U-v3` | Name, key, task type, start flag, attempt bound, endpoints, and condition are form/API bounded and tested |
| `FR-051` | CR-002 graph/feedback | E22, E24 | RK-015, RK-016 | Visualization/UI inspection | `A-v3`: use case; `U-v3` | Compact graph and validation feedback remain available in an expandable advanced constructor verified in Chromium |
| `FR-052` | CR-002 revision immutability | E17, E22 | RK-003, RK-017 | Revision preservation | `A-v3`: domain/state; `T-v3` | Valid activation creates numbered snapshots; two-activation tests preserve the original revision after draft edits |
| `FR-053` | FB-004 and CR-002 UI correction | E24 | RK-013, RK-015 | End-to-end UI inspection | `A-v3`: use case/component; `U-v3` | Persisted invoice identity, state, next action, result, and mode pass DOM/HTTP and Chromium desktop/mobile inspection; trace/configuration are secondary |

### Quality and constraints

| Requirement | Source | Backlog | Risks | Verification | Required evidence | Current state |
|---|---|---|---|---|---|---|
| `NFR-001` | CR-001 repeatability, v3 scenarios | E23 | RK-007, RK-014 | Repeated normalized traces | `T-v3` | All five scenarios repeat twice per mode with equal normalized business and trace results |
| `NFR-002` | Shared-mode semantics | E23 | RK-004, RK-018 | Ten-case parity | `T-v3` | Five orchestration/choreography result and trace pairs match exactly after mode normalization |
| `NFR-003` | Persistence plus CR-002 waiting state | E19, E23, E25 | RK-011, RK-017 | Restart/resume | `T-v3`, `D-v3` | Both modes restore and decide a waiting run after real Uvicorn process recreation against the same database/document directory |
| `NFR-004` | Persistent trace | E23 | RK-004, RK-014 | Trace completeness | `T-v3` | Ten retrieved traces match exact expected ordered observations with no missing or duplicate position |
| `NFR-005` | Definition validation | E17, E22, E23 | RK-005, RK-016 | Rule-path coverage | `T-v3` | Every approved graph class is covered before activation; invalid activation creates no revision and valid boundaries activate |
| `NFR-006` | Single-service deployment | E25 | RK-010, RK-011 | Inventory/restart | `D-v3` | Compose parses to one FastAPI service and one persistent volume with no broker; OS-process restart passes; container build unexecuted because no engine was available |
| `NFR-007` | Isolation/idempotency | E19, E23 | RK-003, RK-017 | State partition | `T-v3` | Sequential, threaded, duplicate-decision, conflict, and restart/resume cases preserve run partitions |
| `NFR-008` | Self-contained acceptance | E23, E25 | RK-007, RK-010, RK-016 | Dependency/isolation inspection | `T-v3`, `D-v3` | Application acceptance and restart run locally; source, dependencies, and deployment inventory contain no required broker, payment/OCR, or external HTTP integration |
| `NFR-009` | Bounded PDF handling | E18, E23 | RK-020 | File boundary suite | `T-v3` | Seven PDF boundary classes in both modes produce controlled rejection and zero approval work |
| `NFR-010` | Measurable status-read responsiveness | E23 | RK-014 | 100-read timing run | `T-v3` | Reference Linux/Python/SQLAlchemy/SQLite run: 100/100 below 1 s; p95 1.172 ms, maximum 2.676 ms |
| `NFR-011` | FB-004 understandability response | E24, E26 | RK-013, RK-015 | Five-item UI inspection | `U-v3`, final report | Six persisted status items are primary; technical trace and advanced constructor are collapsed; Chromium desktop/mobile inspection passes |
| `CON-001`–`CON-004` | Retained architecture/scope constraints | E16, E17, E25 | RK-003, RK-010, RK-017 | Design/dependency/deployment inspection | `A-v3`, `D-v3` | One-service/no-broker inventory and persistent run/document ownership pass; container build remains an explicit environmental limitation |
| `CON-005`–`CON-010` | CR-002-adjusted execution and scope boundary | E16, E17, E23 | RK-007, RK-010, RK-016, RK-019 | Requirements/source/dependency inspection | `A-v3`, `T-v3` | Deterministic/no-cycle retry, local EventBus, excluded-integration checks, and no-broker deployment inventory pass |
| `CON-011`–`CON-012` | CR-002 constructor and human-task boundary | E22 | RK-016, RK-017 | Negative/source inspection | `A-v3`, `T-v3` | Extra executable fields and unsupported task types are rejected; human approval has no automatic retry field |
| `CON-013`–`CON-014` | CR-002 reference-product and disclosure boundary | E23, E26 | RK-021 | Source/report inspection | `A-v3`, `T-v3`, final report | Final review pending |

Forward coverage result: every active v3 functional requirement, non-functional requirement, and constraint is mapped to a source, backlog work, verification method, and next evidence checkpoint.

## 2. Reverse coverage of CR-002 outcomes

| CR-002 outcome | Requirement coverage | Backlog | Main risk | Evidence state |
|---|---|---|---|---|
| Understandable invoice-processing purpose | `FR-031`–`FR-047`, `FR-053`, `NFR-011` | E18–E21, E24 | RK-015 | Submission, approval, five outcomes, persisted identity/status/next-action/result/mode projection, and dual-mode Chromium path pass |
| Bounded PDF and metadata validation | `FR-032`, `FR-033`, section 6, `NFR-009` | E18, E23 | RK-020 | Storage, media-type, structural PDF, persisted failure, HTTP oversize, and zero-approval boundaries pass |
| Persistent human approval and same-run continuation | `FR-036`–`FR-042`, `NFR-003`, `NFR-007` | E19, E23, E25 | RK-017 | Both modes restore and resume the same waiting run after real Uvicorn process recreation |
| Approved archive, rejection, invalid, retry, and manual-action paths | `FR-035`, `FR-039`, `FR-040`, `FR-043`–`FR-046`, section 9 | E18–E21, E23 | RK-018 | All five complete scenarios pass in both modes with normalized parity |
| Shared orchestration/choreography semantics | `FR-013`–`FR-017`, `NFR-002`, CON-003 | E20, E21, E23 | RK-004, RK-018 | Both strategies use shared services; ten cases and five normalized pair comparisons pass |
| Run isolation and persistent trace | `FR-018`–`FR-020`, `FR-023`, `FR-026`, `FR-047`, `NFR-003`, `NFR-004`, `NFR-007` | E17, E19, E23, E25 | RK-003, RK-011, RK-017 | Exact traces, threaded partitions, and both-mode waiting/resume across real process recreation pass |
| Bounded constructor | `FR-048`–`FR-052`, `NFR-005`, CON-011, CON-012 | E22 | RK-016 | CRUD, closed catalog, field bounds, graph feedback, invalid-activation rejection, executable-field rejection, and immutable revision preservation pass |
| Deterministic adapters remain secondary verification tools | `FR-017`, `FR-022`–`FR-025`, `FR-045`, `NFR-001`, CON-005 | E17, E23 | RK-007, RK-019 | Stable adapter, retry routes, paired comparisons, and all repeated normalized traces pass |
| Independent student core with disclosed behavioral references | CON-014 | E16, E26 | RK-021 | CR-002 source references recorded; final disclosure pending |

Reverse coverage result: every requested CR-002 capability and boundary has active requirement and backlog coverage.

## 3. Reverse coverage of the five scenarios

| Scenario | Functional coverage | Quality coverage | Verification cases |
|---|---|---|---|
| S1 Approved | `FR-031`–`FR-034`, `FR-036`–`FR-039`, `FR-042`, `FR-043`, `FR-046`, `FR-047` | `NFR-001`–`NFR-004`, `NFR-007`, `NFR-011` | Orchestration S1; choreography S1 |
| S2 Rejected | `FR-031`–`FR-034`, `FR-036`–`FR-038`, `FR-040`–`FR-042`, `FR-046`, `FR-047` | `NFR-001`–`NFR-004`, `NFR-007`, `NFR-011` | Orchestration S2; choreography S2 |
| S3 Invalid | `FR-031`–`FR-035`, `FR-046`, `FR-047` | `NFR-001`, `NFR-002`, `NFR-004`, `NFR-009`, `NFR-011` | Orchestration S3; choreography S3 |
| S4 Retry then archive | `FR-022`–`FR-026`, `FR-031`–`FR-034`, `FR-036`–`FR-039`, `FR-042`, `FR-043`, `FR-045`–`FR-047` | `NFR-001`–`NFR-004`, `NFR-007` | Orchestration S4; choreography S4 |
| S5 Manual action | `FR-022`–`FR-026`, `FR-031`–`FR-034`, `FR-036`–`FR-039`, `FR-042`, `FR-044`–`FR-047` | `NFR-001`–`NFR-004`, `NFR-007` | Orchestration S5; choreography S5 |

Scenario coverage result: all ten paired-mode cases execute, all five normalized cross-mode comparisons pass, and all scenarios repeat twice per mode with equal normalized traces. E23 closes application-level restart, concurrency, PDF, exact-trace, dependency, and timing evidence. E24 closes the reference Chromium desktop/mobile UI boundary. E25 closes the one-service/no-broker inventory and OS-process restart boundary; container image build remains an explicit environmental limitation.

## 4. Review controls

- Requirements v2 and its traceability remain the historical approved baseline.
- Requirements v3 and this synchronized traceability record passed project-level substantive review on `2026-08-13`; no instructor approval is claimed.
- Architecture-v3 mappings are impact targets, not accepted design evidence.
- C5A is classified only as source presence; the unpublished C5B1 draft is excluded from evidence.
- Approval of Requirements v3 requires simultaneous consistency review of this document and the requirements source.

## 5. Related records

- [Requirements v3](./requirements-v3.md)
- [Requirements v2 traceability](./requirements-traceability.md)
- [CR-002](../evolution/CR-002-invoice-approval-reference-application.md)
- [Product backlog](../process/product-backlog.md)
- [Risk register](../process/risk-register.md)
- [Evidence register](../process/evidence-register.md)
