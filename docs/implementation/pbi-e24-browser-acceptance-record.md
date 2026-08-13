# PBI-E24 — User-Outcome-First Browser Acceptance Record

| Field | Value |
|---|---|
| Status | `ACCEPTED — Chromium desktop/mobile reference acceptance` |
| Date | `2026-08-13` |
| Requirements | `FR-038`, `FR-047`, `FR-051`, `FR-053`, `NFR-011` |
| Entry evidence | PBI-E23 accepted; `EV-044` |
| Instructor approval | `NOT CLAIMED` |

## 1. User outcome and information hierarchy

The primary `/ui` path now identifies a concrete invoice and supplier, shows its current business state, states the next required human action, reports the final business result, and identifies the selected execution mode. These fields use the persisted run projection rather than the current form values.

The page leads with invoice submission and status. Technical observations remain available in a collapsed audit-trace disclosure. The workflow constructor remains available but is collapsed by default and labelled as optional advanced configuration, so configuration mechanics no longer dominate the initial business demonstration.

## 2. Automated structure and accessibility checks

The focused UI acceptance suite verifies:

- one main landmark and one level-one heading;
- no duplicate element identifiers, nested forms, or misnested tags;
- every static `label[for]` target exists;
- the six required status elements are present;
- business result precedes the collapsed technical trace;
- the advanced constructor is collapsed by default;
- skip navigation, visible focus rules, live status, alert regions, and a table caption are present.

The integrated HTTP test executes submission, persistent waiting, approval, archive, notification, and status retrieval in orchestration and choreography. It verifies that supplier and invoice identity survive into the run projection.

## 3. Headless Chromium acceptance

A disposable local FastAPI process, SQLite databases, document directory, one-page PDF, Playwright, and Chromium `149.0.7827.0` were used outside project dependencies. The test performed both complete paths:

1. submit an invoice;
2. observe `PENDING_APPROVAL` and the explicit review action;
3. approve it;
4. observe `ARCHIVED`, `Approved and archived`, and `No action required`.

The orchestration and choreography paths both completed. The final projection identified the supplier, business state, next action, final result, and execution mode. The technical trace was collapsed by default. A 390 × 844 viewport had zero horizontal overflow. No page or console error was observed. Desktop waiting/final and mobile initial screenshots were inspected during the acceptance run; no clipping, overlap, or misleading status was observed.

The constructor was separately expanded in Chromium and its heading became visible, establishing that collapsing it did not remove the E22 controls.

## 4. Verification result and limits

The complete isolated repository suite reports `216 passed in 6.73s`. Python compilation, JavaScript syntax, layer-boundary scans, prohibited-dependency checks, and `git diff --check` pass.

This is one reference Chromium engine, desktop/mobile viewport, source/DOM, HTTP, and visual-inspection record. It does not claim Firefox, Safari, assistive-technology, or external human usability testing. It also does not establish production migration, deployed-process restart, persistent-volume configuration, deployment, commit, push, release, or instructor approval.

Next gate: PBI-E25 persistent single-service deployment verification.
