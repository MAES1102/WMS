# PBI-E22 — Bounded Workflow Constructor Record

| Field | Value |
|---|---|
| Status | `ACCEPTED — project-level implementation` |
| Date | `2026-08-13` |
| Requirements | `FR-002`–`FR-007`, `FR-010`, `FR-021`, `FR-048`–`FR-052`, `NFR-005`, CON-011, CON-012 |
| Entry evidence | PBI-E21 accepted; `EV-042` |
| Instructor approval | `NOT CLAIMED` |

## 1. Implemented constructor boundary

The constructor manages editable workflow drafts through a form-bounded application service and a separate HTTP adapter. A user can list, create, retrieve, replace, validate, and delete drafts. The accepted catalog is deliberately closed to four invoice task types: document validation, human approval, document archiving, and notification creation. Transition conditions are limited to `SUCCESS`, `FAILURE`, and `ALWAYS`.

The API rejects additional executable fields, unsupported task types, scripts, and plugins. It is not a general low-code platform and does not import another workflow engine.

## 2. Validation and immutable activation

Incomplete graph drafts may be saved so the user can build incrementally, but malformed field values, duplicate task keys, invalid endpoints, self-edges, unsupported conditions or task types, ambiguous equal-precedence transitions, and invalid retry bounds are rejected at the storage boundary. Full graph validation covers the designated start, reachability, a reachable terminal, acyclicity, supported conditions, transition ambiguity, and bounded automatic attempts.

Activation is permitted only for a fully valid draft. Each activation copies the current draft into a new numbered immutable revision with its own task and transition snapshots. Later draft edits and activations do not mutate earlier revisions. A draft with activated history cannot be deleted through the constructor.

## 3. Visible operator flow

The invoice UI keeps submission and the business result as its primary content. A separate lower constructor panel provides task and transition forms, a compact read-only graph projection, complete validation feedback, and explicit save, validate, activate, and delete actions. The interface states that scripts and plugins are not accepted.

The runtime bootstraps an editable reference draft and backfills it from the current reference revision when needed. Activating a valid revision changes the persisted workflow used by new runs; already created runs remain linked to their original revision.

## 4. Verification

- Application tests cover bounded draft validation, incomplete draft storage, closed task catalog, and activation rejection.
- Persistence tests cover CRUD, immutable revision snapshots, revision numbering, edit-after-activation preservation, and deletion conflict.
- HTTP tests cover the full constructor lifecycle, arbitrary-spec validation, executable-field rejection, unsupported task-type rejection, and retrieval of unchanged historical revisions.
- Integrated visible-runtime tests verify that the constructor controls are present while both execution modes still complete the approved invoice path.
- The complete isolated repository suite reports `165 passed in 2.55s`; compilation, JavaScript syntax, architecture-boundary scans, and `git diff --check` pass.

## 5. Explicit limits and next gate

This increment does not establish manual cross-browser acceptance, process-restart recovery, controlled concurrent-run acceptance, production migration, deployment, commit, push, release, or instructor approval. Graph projection is intentionally a compact form-derived view rather than a drag-and-drop BPMN editor.

Next gate: PBI-E23 remaining acceptance and quality matrix.
