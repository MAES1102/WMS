# Iteration Record

The dates are project-record dates. This is a concise reconstruction of the delivered increments, not a claim that a multi-person Scrum team held every formal ceremony.

## Iteration 1 — Workflow foundation

**Goal:** represent and validate directed workflows independently of UI and persistence details.

- Planning: define task/transition vocabulary, one start node, reachability, acyclicity, and transition precedence.
- Development: immutable domain types, deterministic validation, shared resolver, bounded retry vocabulary.
- Review: focused tests demonstrated valid/invalid graphs and terminal routing.
- Retrospective: technical correctness alone did not yet produce a useful end-user story.

## Iteration 2 — Persistent execution and two strategies

**Goal:** execute isolated runs through orchestration and choreography using shared semantics.

- Planning: separate definition state from run state; define attempt and trace ownership.
- Development: SQLAlchemy persistence, versioned cursor, automatic-step service, orchestration loop, run-scoped EventBus choreography.
- Review: paired tests showed both modes use the same retry and resolver policy.
- Retrospective: green task indicators and abstract failures were difficult to explain to the professor.

## Iteration 3 — Product-purpose correction

**Goal:** turn the workflow engine into an understandable Purchase Request Approval application.

- Planning: CR-002, bounded actors, five business scenarios, exclusions, and revised UML.
- Development: purchase request submission, safe document storage, metadata/structured input validation, persistent human work item, approve/reject continuation, authorization and notification records.
- Review: approved, rejected, and invalid paths produced business states rather than synthetic node colors.
- Retrospective: failure behavior needed to be directly selectable and repeatable in the dashboard.

## Iteration 4 — Configuration and quality matrix

**Goal:** show controlled configurability and verify recovery, isolation, and parity.

- Planning: closed constructor catalog, immutable activation, exact scenario evidence.
- Development: draft CRUD, graph validation feedback, revision snapshots, restart/resume, status projection, deterministic authorization fault adapter.
- Review: five scenarios in both modes, duplicate-decision protection, threaded isolation, structured input boundaries, exact traces, and restart checks.
- Retrospective: advanced configuration and technical trace must remain secondary to purchase request status.

## Iteration 5 — Product consolidation and submission

**Goal:** deliver one clean product, one startup path, and one coherent submission package.

- Planning: remove obsolete prototype files, reconcile documentation, preserve only defensible artifacts.
- Development: one `app.main` composition root, one `purchase request.db`, constrained launcher, five-scenario selector, concise README, synchronized report/UML/process records.
- Review: full automated suite, whitespace/reference scans, application smoke test, and final structured input visual inspection.
- Retrospective: reuse is disclosed, scope remains bounded, and production concerns such as authentication or external accounting are left as explicit future work.
