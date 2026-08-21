# Development Process

## Process choice

The project used a lightweight iterative process with Scrum-style checkpoints. It was a solo academic project, so formal team ceremonies were replaced by short planning, implementation, review, and retrospective records. Requirements, risks, architecture, code, tests, and report evidence were kept under Git configuration management.

The process was deliberately adapted after instructor feedback. The first prototype demonstrated technical execution but did not communicate useful product behavior. CR-003 records the final return to requirements and architecture, preservation of the reusable workflow core, and application to one bounded Purchase Request Approval product.

## Iteration cycle

Every iteration used the same control loop:

1. **Plan** — select a product goal, requirement group, risks, and acceptance evidence.
2. **Design** — update affected decisions, UML, and data ownership before changing behavior.
3. **Implement** — deliver a small vertical slice across the required layers.
4. **Verify** — run focused tests first, then the complete suite; inspect user-visible behavior.
5. **Review** — compare the result with requirements and evidence limits.
6. **Retrospect** — record what to simplify or correct in the next iteration.

## Change control

Material scope changes follow this path:

```text
feedback → change request → requirements → architecture → backlog → code/tests → report
```

CR-003 is the main change record. It did not discard the graph validator, transition resolver, retry policy, run isolation, or trace model. It changed how those capabilities are presented and extended them with Purchase Request data, structured validation, persistent approval, authorization/notification effects, and a user-outcome-first dashboard.

## Evidence policy

Claims are classified as:

- **verified** — supported by executable tests, source inspection, or a generated artifact;
- **reconstructed** — based on project history or student-reported feedback without a preserved original record;
- **excluded/not verified** — intentionally outside scope or not executed in the recorded environment.

The final report states limitations instead of converting missing evidence into positive claims.

## Configuration management

- The Git repository is the source of truth.
- Requirements, ADRs, UML sources, code, tests, and report source are versioned together.
- Runtime databases, caches, virtual environments, and local tools are excluded.
- Activated workflow revisions are immutable in the product; earlier runs remain linked to their original revision.
- The final repository exposes one application and one local deployment topology.

See [sprint-record.md](./sprint-record.md) for the iteration outcomes and [evidence-register.md](./evidence-register.md) for the claim ledger.
