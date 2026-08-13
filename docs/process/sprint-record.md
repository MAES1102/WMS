# Sprint Record

## Interpretation

The baseline and prototype reports describe three one-week delivery sprints and one evolution sprint. Git verifies final snapshots and artifact presence, but it does not provide a commit series mapped cleanly to each sprint. Intended objectives below come from historical documentation and are `RECONSTRUCTED`; outputs are `VERIFIED` only where the durable repository directly supports them.

No calendar dates, meeting attendance, daily Scrum record, approval event, velocity, story point total, or contemporaneous burndown is inferred here.

## Delivery Sprint 1

| Field | Record |
|---|---|
| Intended objective | Establish data models, database access, and CRUD API (`RECONSTRUCTED` from the report). |
| Verifiable output | Baseline contains FastAPI routes, SQLAlchemy models, SQLite configuration, and CRUD-oriented tests (`VERIFIED` as final artifact presence). |
| Reconstructed information | Backlog selection, internal task sequence, and claimed sprint review/retrospective. |
| Missing evidence | No durable sprint-start snapshot, dated Sprint Backlog, ceremony record, contemporaneous test result, or day-by-day progress record. |
| Review status | Historical review status is `UNVERIFIED`; final artifact exists. |
| Retrospective lesson | Future increments must produce verification evidence inside the same checkpoint rather than relying on later narrative. |

## Delivery Sprint 2

| Field | Record |
|---|---|
| Intended objective | Add linear orchestration, choreography, EventBus behavior, and run records (`RECONSTRUCTED`). |
| Verifiable output | Baseline contains orchestration, choreography, EventBus/Kafka adapter code, task runner, and workflow-run persistence (`VERIFIED` as final artifact presence). |
| Reconstructed information | The precise order of implementation, BUG-02 discovery timing, manual review activity, and retrospective actions. |
| Missing evidence | No sprint boundary commit, durable manual-test record, Kafka verification evidence, or contemporaneous review minutes. |
| Review status | Historical review status is `UNVERIFIED`; code presence does not prove the reported ceremony. |
| Retrospective lesson | Shared behavior needs deterministic tests and explicit transport scope before a feature is described as complete. |

## Delivery Sprint 3

| Field | Record |
|---|---|
| Intended objective | Add UI, broader tests, bug fixes, deployment material, UML, and consolidated reporting (`RECONSTRUCTED`). |
| Verifiable output | Baseline contains a dashboard, three test modules with 21 test functions, Docker Compose, README, and an embedded report/UML set (`VERIFIED` as artifact presence). |
| Reconstructed information | Claimed backlog commitment, review, retrospective, velocity, and burndown. |
| Missing evidence | No independent durable execution proving the historical 21-pass claim; no contemporaneous chart source or dated ceremony evidence. |
| Review status | Final submission commit exists; detailed sprint acceptance is `UNVERIFIED`. |
| Retrospective lesson | Test definitions and reports are not substitutes for reproducible test results, and process evidence must be captured when the work occurs. |

## Evolution Sprint

| Field | Record |
|---|---|
| Intended objective | Evolve the linear workflow toward conditional execution and stronger run isolation (`RECONSTRUCTED` for the historical prototype; `PLANNED` for defense core). |
| Verifiable output | The advanced prototype is preserved at `archive/advanced-prototype`; it contains transition, graph, task-execution, seed, UI, and additional test artifacts (`VERIFIED` as content). Stage 1 refs are preserved locally and remotely (`VERIFIED`). |
| Reconstructed information | The archive report’s Sprint 4 task sequence, points, burndown, reviews, and claimed 27-test result. |
| Missing evidence | No contemporaneous sprint record and no conclusive archive test run. The archive contains 34 test functions while its documentation claims 27. |
| Review status | Preservation is complete. At the historical Stage 2 approval boundary, [CR-001](../evolution/CR-001-defense-core-refactoring.md) was approved for progression to Requirements v2 only and Requirements v2 had not started. Requirements v2 was subsequently drafted; r4 passed final substantive review, and the approved Stage 3 baseline is established by the Stage 3 documentation commit. This row records that historical boundary; later C5A source presence is recorded separately below. |
| Retrospective lesson | Start from an immutable baseline, classify historical evidence, approve impact before requirements/design, and port only bounded capabilities. |

## Requirements v2 approval checkpoint

| Field | Record |
|---|---|
| Entry state | Stage 2 is committed at `6a5e42c6fa5d4d71fd599d606d7c805e95177b2f`; CR-001 is approved for progression to Requirements v2 only. |
| Drafting activity | Requirements v2 and its traceability record were drafted from approved CR-001 and evidence-classified baseline/prototype inspection. |
| Review status | The r1 substantive review identified narrow corrections to attempt-bound applicability, the `FR-006`/`FR-021` dependency cycle, `NFR-005` verification alignment, and `NFR-008` clarity. The r2 substantive re-review then identified the remaining `FR-017`/`FR-027` dependency cycle, the incomplete retry obligation in `FR-022`, and the checkpoint-misaligned dependency in `NFR-008`. Final review of r3 identified the stale `NFR-006` brokerless-choreography cross-reference. The corrected r4 passed final substantive review, and the approved Requirements v2 baseline is established by the Stage 3 documentation commit. |
| Verification status | Documentation checks only; no executable test was created or run. |
| Later checkpoints | Architecture/UML and implementation remain not started. |
| Release status | `NOT SCHEDULED` |

## Burndown limitation

No contemporaneous source data has been found that can substantiate a burndown chart for any sprint. Historical charts in reports may be retrospective reconstructions and must not be presented as measured daily evidence. No replacement chart is fabricated in this checkpoint.

## Checkpoint-4 architecture/UML approval record

| Field | Record |
|---|---|
| Entry state | Requirements v2 remains the approved Stage 3 baseline at `6074fd7ef490ea3b08177e7a786035159f39a91c`; checkpoint-4 drafting starts from the post-push consistency correction `b5c7da9e51382bb418f017790ae944c8dff26a06`. |
| Authorized scope | Architecture decisions, architecture overview/traceability, and matching PlantUML sources only. |
| Artifact manifest | `docs/architecture/architecture-overview.md`; `docs/architecture/architecture-decisions.md`; `docs/architecture/architecture-traceability.md`; `docs/architecture/uml/system-context-use-cases.puml`; `docs/architecture/uml/component-view.puml`; `docs/architecture/uml/domain-model.puml`; `docs/architecture/uml/orchestration-sequence.puml`; `docs/architecture/uml/choreography-sequence.puml`; `docs/architecture/uml/routing-retry-activity.puml`; `docs/architecture/uml/run-state.puml`; `docs/architecture/uml/deployment-view.puml`. |
| Controlled record updates | Requirements traceability, development process, evidence register, feedback register, product backlog, and this sprint record. |
| Course sources inspected | `9 - sw architecture.pdf`, slides 24–26, 38, 41–43, 47–49, 92–93, 96, 100–106, 110–111, 129–130, and 143–145; `7 - modeling.pdf`, slides 67, 69–70, 86–87, 95–96, 109, 115–117, 146–147, and printed slide 161. |
| Review status | The r2 architecture review passed substantive project review; the architecture/ADR/UML set is the `APPROVED — checkpoint 4 architecture baseline`, and all seven ADRs are `ACCEPTED — checkpoint 4 architecture baseline`. Git durability of the accepted architecture baseline is established by commit f44f0d55349af4e7b1b19b49f5e3b26c67c96181 and the independently verified origin/refactor/defense-core ref. |
| Implementation and verification | No implementation or executable test was created or run; both remain `NOT STARTED`. |
| Later checkpoints | Checkpoint 5 remains `NOT STARTED`; no schema, endpoint, UI, configuration, deployment, or final-report work began. |
| Release status | `NOT SCHEDULED` |

## C5A foundation record

| Field | Record |
|---|---|
| Entry state | Checkpoint-4 architecture/ADR/UML is the approved design baseline. |
| Published increment | Commit `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0`, subject `feat(domain): add workflow definition and run-state foundation`. |
| Exact manifest | `app/domain/__init__.py`; `app/domain/types.py`; `app/domain/validation.py`; `app/domain/resolver.py`; `app/models.py`. |
| Durable source evidence | Five files changed, 491 insertions, 1 deletion; recorded by EV-027. |
| Verification limitation | No executable test, database migration, runtime behavior, deployment, release, or complete checkpoint-5 acceptance is established by source presence. |
| Later state | A separate unpublished C5B1 draft exists outside the controlled base and is not accepted progress or evidence. |

## CR-002 review checkpoint

| Field | Record |
|---|---|
| Trigger | FB-004 reports that the earlier abstract live demonstration did not communicate the project's useful function. |
| Entry state | C5A is the latest published implementation foundation at `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0`; Requirements v2 and checkpoint-4 architecture remain the latest approved specification/design baselines. |
| Authorized activity | Draft CR-002, impact analysis, feedback/evidence links, backlog entry, and risk registration only. |
| Proposed outcome | Apply the existing workflow engine to one bounded invoice-approval reference application without replacing the independently implemented orchestration/choreography core. |
| Review status | `APPROVED FOR REQUIREMENTS V3 — project-level review` on `2026-08-13`; no instructor approval claimed. |
| Implementation and verification | No CR-002-derived implementation or executable verification is authorized or claimed. |
| Release status | `NOT SCHEDULED`. |

## Requirements v3 approval checkpoint

| Field | Record |
|---|---|
| Entry state | CR-002 passed project-level review for requirements drafting; Requirements v2 and checkpoint-4 architecture remain the latest approved baselines. |
| Authorized activity | Draft Requirements v3, v3 traceability, backlog refinement, and related process consistency updates. |
| Output | `docs/requirements/requirements-v3.md` and `docs/requirements/requirements-traceability-v3.md`. |
| Scenario boundary | Five invoice scenarios paired across orchestration and choreography: approved, rejected, invalid, retry-then-archive, and exhausted-to-manual-action. |
| Review status | Substantive project review passed on `2026-08-13`; 49 active FRs and 11 NFRs match forward traceability, 14 constraints are covered, and no instructor approval is claimed. |
| Implementation and verification | No source implementation, executable test, database, migration, deployment, or release action is authorized or claimed. |
| Next gate | Affected architecture/ADR/UML correction; implementation remains paused until that gate passes. |

## Architecture v3 approval checkpoint

| Field | Record |
|---|---|
| Entry state | Requirements v3 3.0 is the current project-level specification baseline; C5A at `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` is the latest published implementation foundation. |
| Authorized activity | Correct the affected architecture, amend ADR-001–ADR-007, add necessary decisions, replace affected UML views, and synchronize architecture traceability/process records. |
| Output | `docs/architecture/architecture-overview-v3.md`; `docs/architecture/architecture-decisions-v3.md`; `docs/architecture/architecture-traceability-v3.md`; eight PlantUML sources under `docs/architecture/uml-v3/`. |
| C5A decision | Retain and extend the immutable definition, validation, resolver, transition, attempt, trace, and run concepts; replace mutable definition-task runtime state, name-based scenarios, and incompatible runtime paths through vertical increments. |
| Review status | Project-level review passed on `2026-08-13`; nine ADRs are accepted, eight of eight PlantUML sources parsed/rendered, and all rendered views passed visual inspection after correcting the run-state label layout. No instructor approval is claimed. |
| Implementation and verification | No v3 source implementation, executable test, database, migration, deployment, or release action is established. Git durability of this documentation bundle is pending. |
| Next gate | PBI-E17 focused C5A compatibility implementation plan; broad code replacement is not authorized by this design record. |

## PBI-E17 compatibility planning checkpoint

| Field | Record |
|---|---|
| Entry state | Architecture v3 is the approved project-level design baseline; C5A remains the controlled implementation base. |
| Source inspected | `app/domain/`; `app/models.py`; `app/engine/`; `app/routes.py`; current tests; README; dependency manifest. |
| Output | `docs/implementation/checkpoint-5a-v3-implementation-plan.md`. |
| Decision | Continue in the existing repository; retain/extend C5A, replace incompatible runtime paths through vertical increments, prohibit dual writes, and exclude the unpublished C5B1 draft. |
| Review status | Plan passed project-level review on `2026-08-13`; no instructor approval is claimed. |
| Implementation and verification | No v3 source implementation, executable test, database, migration, runtime, commit, push, deployment, or release action occurred. |
| Next gate | 5A.1 pure domain execution contracts and focused tests only. |

## Checkpoint 5A.1 implementation record

| Field | Record |
|---|---|
| Authorized scope | Pure task catalog/result/failure/retry policy, v3 definition-bound validation, resolver non-regression tests, and no ORM/API/runtime changes. |
| Working-tree output | Modified `app/domain/types.py` and `app/domain/validation.py`; new `app/domain/retry.py` and four focused modules under `tests/domain/`. |
| Static verification | Syntax compilation, forbidden-import scan, direct eight-assertion domain smoke run, and `git diff --check` passed. |
| Executable-test status | Focused pytest 8.3.4 suite passed: `29 passed in 0.03s`. The run reused dependencies from an existing isolated audit environment; no package was installed. |
| Scope confirmation | No model, route, engine, UI, dependency, database, migration, runtime, commit, push, deployment, or release change occurred. |
| Next gate | 5A.1 is accepted at project level; 5A.2 persistence ownership is authorized next, while invoice/API/runtime increments remain blocked. |

## Checkpoint 5A.2 implementation record

| Field | Record |
|---|---|
| Authorized scope | Isolated v3 draft/revision/invoice/run/cursor/attempt/approval/archive/notification/trace persistence ownership and fresh-schema invariant tests. |
| Working-tree output | New `app/persistence/` package and `tests/persistence/`; no changes to prototype models, routes, engines, UI, or dependencies. |
| Schema boundary | Fifteen new v3 tables use distinct names; tests create/drop them only in in-memory SQLite. `create_all()` is not represented as a migration. |
| Executable-test status | Focused persistence suite passed: `8 passed in 0.07s`; domain suite recheck passed: `29 passed in 0.02s`. |
| Scope confirmation | No developer database, old runtime, endpoint, application startup, package installation, migration, commit, push, deployment, or release action occurred. |
| Next gate | 5A.3 shared executor and transaction-bounded one-step service; PBI-E18 and later remain blocked. |

## Checkpoint 5A.3 implementation record

| Field | Record |
|---|---|
| Authorized scope | Closed automatic-executor port/registry, stable deterministic fault adapter, optimistic unit-of-work command, and one shared automatic-step service; no HTTP or human-decision path. |
| Working-tree output | New `app/application/` package and `tests/application/test_step_service.py`; no changes to prototype models, routes, engines, UI, or dependencies. |
| Policy ownership | `AutomaticStepService` is the only application module importing the retry policy and resolver. It commits attempt/result/resolution/trace before returning a versioned result that a later controller may trigger from. |
| Executable-test status | Final focused application suite passed: `8 passed in 0.02s`; domain and persistence rechecks passed: `29 passed in 0.02s` and `8 passed in 0.07s`. |
| Static verification | Syntax compilation, application forbidden-import/single-policy-owner checks, line-length inspection, and `git diff --check` passed. |
| Scope confirmation | Fake unit of work only. No real repository adapter, invoice endpoint, PDF processing, human lifecycle, developer database, old runtime, migration, application startup, package installation, commit, push, deployment, or release action occurred. |
| Next gate | PBI-E17 is accepted at project level; PBI-E18 bounded invoice submission and document validation is authorized next. |

## PBI-E18.1 validation/document-adapter record

| Field | Record |
|---|---|
| Entry correction | The isolated invoice schema could not retain invalid raw date/amount/currency before validation. It now separates bounded raw values and nullable normalized values and records original filename, declared media type, and byte size. |
| Working-tree output | New pure invoice validation, `DOCUMENT_VALIDATION` executor, generated-identity storage, `pypdf` adapter, focused tests, and one explicit PDF dependency range. |
| Reuse boundary | Environment-provided `pypdf 6.10.0` is used only behind `PdfInspector` for openability, encryption status, and page count; no extraction/OCR or external workflow engine is used. |
| Executable-test status | Final combined recheck after the submission slice passed: domain `42 passed in 0.06s`; application `12 passed in 0.06s`; infrastructure `9 passed in 0.22s`; persistence `13 passed in 0.25s`. |
| Safety evidence | Empty/oversize partial files are removed; UUID identity validation prevents traversal; original filename is retained only as database metadata; PDF errors become controlled business failures. |
| Scope confirmation | No submission transaction, real SQLAlchemy step adapter, endpoint, approval work, old runtime, developer database, migration, application startup, package installation, commit, push, deployment, or release action occurred. |
| Next gate | E18.2 submission transaction and validation persistence. |

## PBI-E18.2 submission and validation-persistence record

| Field | Record |
|---|---|
| Authorized scope | Initial submission and one automatic validation-step transaction; no HTTP route or human approval lifecycle. |
| Transaction output | Raw invoice, run linked to latest activated revision, version-1 `READY` cursor at the single start task, and position-1 `RUN_STARTED` trace. |
| File compensation | Database failure rolls back all records and deletes only the document created for that failed command; missing active revision stores nothing. |
| Review correction | Integration testing exposed cursor-before-run flush ordering under enabled SQLite foreign keys. The adapter now explicitly flushes invoice, then run, then cursor/trace within the same commit. |
| Validation transaction | The SQLAlchemy step adapter loads run/revision state and atomically commits attempt, explicit invoice effect, optimistic cursor decision, and continued trace positions. Success stores normalized fields and routes to review; business failure stores `VALIDATION_FAILED`, routes to notification, and creates no approval item. |
| Concurrency correction | A conditional cursor update rejects stale `state_version`; the verified rollback leaves metadata, attempts, and trace unchanged. |
| Executable-test status | Final isolated combined suite passed: domain `42`, application `14`, infrastructure `9`, and persistence `17` tests (`82 passed in 0.56s`). |
| Scope confirmation | No endpoint, approval work creation, notification execution, old runtime, developer database, migration, application startup, package installation, commit, push, deployment, or release action occurred. |
| Next gate | E18.3 separate bounded v3 HTTP submission boundary. |

## PBI-E18.3 separate HTTP-boundary record

| Field | Record |
|---|---|
| Authorized scope | One separate bounded v3 multipart submission router and isolated HTTP tests; no prototype `main.py` registration. |
| Boundary output | `/api/v3/invoices` requires six controlled UTF-8 text fields and exactly one document part, returns invoice/run identities plus `SUBMITTED`/`RUNNING`, and delegates persistence to `InvoiceSubmissionService`. |
| Layer correction | Presentation initially exposed infrastructure/persistence exception types. Application-owned storage/submission exceptions now preserve one-way presentation-to-application dependencies. |
| Boundary controls | Complete request and stored document sizes are bounded; duplicate, missing, unknown, nested, non-multipart, invalid-mode, and missing-revision conditions become controlled HTTP responses. |
| Executable-test status | Four presentation acceptance cases passed; final isolated combined run reported `86 passed`. |
| Scope confirmation | No prototype route/startup modification, developer database, migration, application startup, package installation, commit, push, deployment, or release action occurred. |
| Next gate | PBI-E19 persistent human approval and idempotent same-run continuation. |

## PBI-E19 persistent human-approval record

| Field | Record |
|---|---|
| Authorized scope | Persistent waiting work, approve/reject decision, idempotent replay/conflict, same-cursor resume, query projection, and separate approval HTTP boundary. |
| Waiting transaction | One work item, invoice `PENDING_APPROVAL`, run/cursor `WAITING_FOR_APPROVAL`, state version, and trace commit together; duplicate entry returns the same item without another write. |
| Decision transaction | One authoritative decision, work-item/invoice state, same cursor/run resume, shared-resolver result, and ordered trace commit together. |
| Concurrency/isolation | Conditional version updates and unique rows reject stale/racing writes; identical replay changes nothing; a selected run does not affect another waiting run. |
| HTTP/query output | Pending list/detail expose invoice/document/run context; decision responses distinguish accepted continuation from replay. |
| Executable-test status | Final isolated combined suite passed: `104 passed in 1.09s`. |
| Scope confirmation | No mode-specific controller, notification/archive executor, prototype runtime registration, process restart, developer database, migration, application startup, package installation, commit, push, deployment, or release action occurred. |
| Next gate | PBI-E20 centralized invoice orchestration over shared services. |

## PBI-E20 centralized invoice-orchestration record

| Field | Record |
|---|---|
| Authorized scope | One centralized controller over the shared automatic-step and human-approval services, plus archive/notification effects and a run status/history query. |
| Control behavior | The controller repeatedly reads committed cursor state, executes one shared automatic step at a time, atomically enters human waiting, and stops at waiting or terminal. A decision coordinator resumes the same run. |
| Business output | Approved documents retain their generated identity in one archive record; exhausted archive failure sets `NEEDS_MANUAL_ACTION`; every reference path creates one final-state notification. |
| Scenario evidence | `S1` approved, `S2` rejected, `S3` invalid, `S4` retry then archive, and `S5` exhausted-to-manual-action pass in orchestration mode. |
| Executable-test status | Focused E20 cases passed; final isolated repository suite reported `138 passed in 1.85s`. |
| Scope confirmation | No choreography, paired parity, prototype runtime registration, process restart, developer database, migration, application startup, package installation, commit, push, deployment, or release action occurred. |
| Next gate | PBI-E21 run-scoped in-memory choreography over the same shared services. |

## PBI-E20A visible-runtime preview

| Field | Record |
|---|---|
| Motivation | Respond immediately to the visibility gap: substantial backend behavior existed but `/ui` and `main.py` still exposed only the preserved prototype. |
| Runtime output | A separate invoice engine/schema and generated-identity document root, one seeded reference revision, registered submission/approval/status routes, and same-run orchestration continuation. |
| Browser output | `/ui` leads with invoice submission, business-state progress, a real approve/reject action, final notification, and collapsible audit trace; `/legacy-ui` preserves the old screen. |
| Executable-test status | The integrated visible approval path passes; final isolated repository run reported `139 passed in 1.85s`; browser script syntax check passed. |
| Limit | This is an early preview, not final PBI-E24 acceptance; no manual browser matrix, choreography/parity, constructor, restart, production migration, deployment, commit, push, or release is claimed. |
| Next gate | PBI-E21 remains the next controlled implementation increment. |

## PBI-E21 run-scoped invoice-choreography record

| Field | Record |
|---|---|
| Authorized scope | One temporary run-keyed EventBus strategy over the accepted shared step/approval services, coordinator mode selection, visible mode choice, and paired scenario verification. |
| Control behavior | Each active scope subscribes one handler, publishes only run identity plus committed version, reloads persistent state on every reaction, and unsubscribes at waiting, terminal, or error. |
| Shared semantics | Both strategies use the same revision, retry policy, resolver, automatic executors, approval lifecycle, persistence effects, query projection, and normalized trace vocabulary. |
| Scenario evidence | Five orchestration plus five choreography executions pass; five exact normalized business/trace pair comparisons match. |
| Executable-test status | Focused E21 tests passed; final isolated repository suite reported `155 passed in 2.54s`; browser script syntax and architecture-boundary scans passed. |
| Scope confirmation | No process-restart recovery, controlled concurrent-run matrix, constructor, production migration, developer database, deployment, commit, push, release, or instructor approval is claimed. |
| Next gate | PBI-E22 bounded workflow constructor and immutable revision activation. |

## PBI-E22 bounded workflow-constructor record

| Field | Record |
|---|---|
| Authorized scope | Form-bounded invoice workflow drafts, full definition feedback, closed executor catalog, immutable revision activation, and a compact constructor UI. |
| Safety boundary | Four built-in task types and three transition conditions only; additional executable fields, scripts, plugins, and unsupported task types are rejected. |
| Revision behavior | A valid activation creates a new numbered task/transition snapshot; later draft edits and activations preserve prior revisions. |
| Visible behavior | Operators can save, validate, inspect a graph projection, activate, and conditionally delete drafts below the primary invoice demonstration. |
| Executable-test status | Constructor application, persistence, HTTP, and visible-runtime cases pass; final isolated repository suite reported `165 passed in 2.55s`; compilation, JavaScript syntax, architecture-boundary scans, and whitespace checks passed. |
| Scope confirmation | No manual cross-browser acceptance, process restart, controlled concurrent-run matrix, production migration, deployment, commit, push, release, or instructor approval is claimed. |
| Next gate | PBI-E23 remaining acceptance and quality matrix. |

## PBI-E23 acceptance and quality-matrix record

| Field | Record |
|---|---|
| Authorized scope | Repeatability, paired semantics, exact trace completeness, persistence-boundary restart, run isolation, constructor rule coverage, complete PDF gating, prohibited-dependency inspection, and 100-read timing. |
| Repeatability and trace | Every scenario repeats twice in each mode with an equal normalized result; every scenario/mode pair matches its exact ordered trace vocabulary. |
| Restart and isolation | Both modes restore a waiting run from a recreated file-backed engine/session and resume its original cursor; two runs are driven and decided in worker threads without cross-run state. |
| Boundary evidence | Seven PDF rejection classes in both modes produce zero approval work; the v3 target requires no broker, random outcome, payment/OCR, or external HTTP integration. |
| Timing evidence | Linux x86_64, Python 3.12.13, SQLAlchemy 2.0.36, SQLite 3.50.4: 100/100 completed-run status+trace reads below 1 second; p95 1.172 ms, maximum 2.676 ms. |
| Executable-test status | Final isolated repository suite reported `213 passed in 6.76s`; compilation, JavaScript syntax, layer/dependency scans, and whitespace checks passed. |
| Scope confirmation | No production migration, deployed-process restart, persistent-volume inventory, manual cross-browser acceptance, deployment, commit, push, release, or instructor approval is claimed. |
| Next gate | PBI-E24 final user-outcome-first browser acceptance. |

## PBI-E24 user-outcome-first browser record

| Field | Record |
|---|---|
| Authorized scope | Persisted invoice identity, explicit business state/next action/final result/mode, secondary trace, optional advanced constructor, DOM/accessibility hooks, and reference browser acceptance. |
| Information hierarchy | Submission and invoice outcome remain primary; technical trace and workflow construction are collapsed by default. |
| Browser evidence | Chromium 149 completed waiting-to-approval-to-archive in orchestration and choreography; desktop and 390 px mobile views were captured and inspected; no horizontal overflow or page/console error occurred. |
| Structure evidence | HTML parser checks one main/H1, unique IDs, valid static labels, no nested/misnested form structure, business-result ordering, and accessibility hooks. |
| Executable-test status | Focused UI/persistence checks passed; final isolated repository suite reported `216 passed in 6.73s`; compilation, JavaScript syntax, layer/dependency scans, and whitespace checks passed. |
| Scope confirmation | No Firefox/Safari, assistive-technology, external human-usability, production migration, deployed restart, deployment, commit, push, release, or instructor approval is claimed. |
| Next gate | PBI-E25 persistent single-service deployment verification. |

## PBI-E25 persistent single-service deployment record

| Field | Record |
|---|---|
| Authorized scope | Remove the obsolete broker topology, define one built FastAPI service with persistent database/document paths, and exercise recovery across a real process restart. |
| Deployment inventory | One `app` service, one `invoice_data` volume, two SQLite files plus document storage under `/data`, non-root image user, and HTTP healthcheck; no Kafka/ZooKeeper/source bind mount/runtime dependency installation. |
| Restart evidence | Orchestration and choreography each reach waiting in one Uvicorn process, survive termination, reload in a new process, and resume the same run to archive. |
| Executable-test status | Focused deployment suite reported `4 passed in 4.05s`; final isolated repository suite reported `220 passed in 10.05s`; YAML parsing, compilation, JavaScript syntax, layer/dependency scans, and whitespace checks passed. |
| Scope confirmation | Docker/Podman was unavailable, so image build/container-volume restart, production migration, external deployment, commit, push, release, and instructor approval are not claimed. |
| Next gate | PBI-E26 final report, UML, reuse disclosure, and defense-script reconciliation. |

## PBI-E26 final-reconciliation record

| Field | Record |
|---|---|
| Authorized scope | Replace the obsolete prototype narrative with a product-first final invoice report, clean UML renders, explicit reuse disclosure, and a defense script without changing runtime behavior. |
| Report output | A separate 39-page final report embeds the business case, acceptance matrix, architecture/custom logic, eight UML views, verification results, deployment limits, reuse statement, and final claim ledger. |
| UML output | Eight PlantUML sources have matching vector SVG/PDF renders; error-page scans and visual inspection passed; both long sequence diagrams use landscape pages. |
| Defense output | The script opens with invoice value, demonstrates approved/failure/parity paths, and delays trace/constructor details until the product result is clear. |
| Reuse output | Dependencies and behavioral references are disclosed; no external workflow engine, source, diagrams, definitions, or UI are claimed as original work. |
| Scope confirmation | No runtime feature, production migration, container build, external deployment, commit, push, release, or instructor approval is claimed. |
| Next gate | Intentional configuration-management review, then instructor submission/defense decision. |

Related records: [development process](./development-process.md), [product backlog](./product-backlog.md), [evidence register](./evidence-register.md), [feedback register](./feedback-register.md), and [CR-002](../evolution/CR-002-invoice-approval-reference-application.md).
