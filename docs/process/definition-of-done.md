# Definition of Done

A product increment is done only when all applicable checks pass.

## Requirement and design

- User-visible behavior is linked to an active requirement.
- Architecture decisions and UML agree with the implemented responsibility.
- Scope exclusions are respected; no hidden external dependency is introduced.
- New persistence state has an owner, lifecycle, and invariant.

## Implementation

- Presentation, application, domain, persistence, and infrastructure boundaries remain explicit.
- Both modes share task execution, retry, routing, and business effects.
- Failure paths return controlled states and reasons.
- No mutable definition field stores run state.
- No arbitrary user code or random outcome controls business behavior.

## Verification

- Focused tests pass for the changed behavior.
- The complete suite passes.
- `git diff --check` passes.
- Startup and `/ui` smoke checks pass with a disposable database/storage directory.
- Runtime data, caches, and virtual environments are not tracked.

## Submission artifact

- README gives one correct startup and demonstration path.
- Requirements, traceability, ADRs, UML, process record, report, and defense script agree.
- The generated structured input builds reproducibly and has been visually inspected.
- Reused libraries and behavioral references are disclosed.
- Limitations and unverified claims are explicit.
- The repository contains one final product and no obsolete parallel runtime.
