# Definition of Done

This is a normative quality gate. It does not claim that future work is complete. A criterion is applicable only to the artifact or checkpoint under review, and completion requires evidence rather than assertion.

## Documentation Definition of Done

- Purpose, scope, owner role, status, and evidence basis are explicit.
- Historical claims are classified as `VERIFIED`, `RECONSTRUCTED`, `PLANNED`, `UNVERIFIED`, or `INCONCLUSIVE`.
- Private correspondence and personal data are excluded.
- Requirements, architecture, UML, tests, and implementation are not described as approved or complete without their gate evidence.
- Relative links resolve and terminology/statuses are consistent.
- Traceability links every decision to evidence, backlog, risk, and next artifact where applicable.
- No placeholders, unsupported dates, fabricated ceremonies, points, velocity, approvals, or burndown data remain.
- The diff contains only authorized documentation paths and passes Markdown/Git checks.
- Explicit user approval is obtained before staging, committing, or pushing.

## Implementation increment Definition of Done

- Applicable requirements and acceptance conditions are approved before coding.
- The implementation scope matches the approved checkpoint and contains no undocumented expansion.
- The code is reviewable through a focused diff from a known clean baseline.
- Workflow definitions do not store mutable per-run state.
- Behavior is deterministic for the approved scenarios.
- Tests cover success, retry-then-success, and permanent failure where applicable.
- Retry is bounded and its state is persistent where required.
- Orchestration and choreography use the approved shared semantics.
- Persistent execution evidence is observable and traceable.
- UML and technical documentation match the implementation.
- Isolated verification records exact counts and failures without modifying repository runtime data.
- Git worktree/index are clean after the reviewed checkpoint.
- Explicit user approval is obtained before commit or push.

## Checkpoint Definition of Done

- The previous checkpoint is reviewed before work on the next begins.
- Entry criteria, output manifest, acceptance conditions, risks, and exclusions are recorded.
- Only authorized files changed.
- Validation commands and their exact results are reported.
- New or changed risks are registered with a later verification gate.
- Evidence classification and traceability are updated.
- No unresolved contradiction is represented as complete.
- Commit/push decisions are separate explicit approvals.

## Final project Definition of Done

- Requirements v2 is approved and traced to implementation and tests.
- Architecture decisions and UML match the delivered system.
- The conditional DAG, shared transition semantics, run isolation, bounded persistent retries, both execution modes, and persistent trace meet approved acceptance conditions.
- Deterministic verification completes with reproducible evidence.
- The UI demonstrates one clear approved workflow path.
- The single-service deployment retains persistent data through the approved restart check.
- Excluded scope is absent or explicitly documented as excluded.
- The risk register contains no unreviewed release-blocking risk.
- The final report accurately reflects verified evidence and limitations.
- Git refs, status, release decision, commit, and push are explicitly approved and recorded.

Stages 2 and 3 passed substantive documentation review, and their durability is established by their respective documentation commits; implementation, checkpoint 4+, and final-project criteria remain incomplete.

Related records: [development process](./development-process.md), [evidence register](./evidence-register.md), [risk register](./risk-register.md), and [CR-001](../evolution/CR-001-defense-core-refactoring.md).
