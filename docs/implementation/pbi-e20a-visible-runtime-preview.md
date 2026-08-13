# PBI-E20A — Visible Invoice Runtime Preview

| Field | Value |
|---|---|
| Status | `VERIFIED PREVIEW — not final UI acceptance` |
| Date | `2026-08-13` |
| Motivation | Make the useful function observable before more control-strategy work |
| Requirements touched | `FR-031`, `FR-038`, `FR-047`, `FR-053`, `NFR-011` |
| Instructor approval | `NOT CLAIMED` |

## Outcome

The FastAPI composition root now registers the separate v3 submission, approval, orchestration-resume, and run-status boundaries. `/ui` serves an invoice-first browser screen; the preserved prototype remains at `/legacy-ui`.

The visible path accepts invoice metadata and a PDF, executes validation under centralized orchestration, returns persistent waiting, accepts approve/reject, resumes the same run, and displays the final invoice state, notification, and ordered technical trace.

## Runtime isolation

The invoice path owns `invoice_v3.db` and `invoice_documents/` separately from legacy `workflow.db`. Startup creates only the 15 v3 tables in the invoice engine and seeds the bounded four-task reference workflow when no revision exists. It does not reinterpret or migrate legacy rows.

Tests override both database URLs with in-memory SQLite and use a temporary document root. The integrated HTTP case verifies the actual `/ui`, submission, waiting, approval, archive, notification, and status endpoints without accessing developer data.

## Verification and limits

The integrated runtime case passes and the final repository suite reports `139 passed in 1.85s`. The browser JavaScript parses successfully. No manual cross-browser visual inspection, choreography, mode selector, constructor, process-restart retention, production migration, developer-database write, external deployment, commit, push, release, or final UI acceptance is claimed.

The controlled next implementation gate remains PBI-E21 choreography. PBI-E24 will later complete visual inspection, configuration/mode presentation, accessibility, and defense-oriented usability after paired execution evidence exists.
