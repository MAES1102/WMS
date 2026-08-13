# PBI-E23 — Acceptance and Quality Matrix Record

| Field | Value |
|---|---|
| Status | `ACCEPTED — project-level application verification` |
| Date | `2026-08-13` |
| Requirements | Requirements v3 section 9; `NFR-001`–`NFR-005`, `NFR-007`–`NFR-010`; CON-003, CON-005, CON-008, CON-009 |
| Entry evidence | PBI-E18–PBI-E22 accepted; `EV-038`–`EV-043` |
| Instructor approval | `NOT CLAIMED` |

## 1. Scenario, parity, repeatability, and trace evidence

The five approved invoice scenarios pass in orchestration and choreography. Five normalized cross-mode comparisons establish semantic parity. E23 repeats each scenario twice in each mode from equivalent isolated state, adding 20 executions whose normalized business result and trace match exactly.

Ten expected-versus-retrieved trace checks assert the exact ordered observation sequence for every scenario and mode. Retry scenarios contain one retry observation and no transition during the retry. Approval scenarios contain one waiting/resume pair; invalid input creates no approval observation.

## 2. Restart and isolation evidence

A file-backed SQLite test executes each mode to persistent human waiting, closes the session, disposes the engine, creates a new engine and service composition, reloads the original revision/invoice/run/cursor/attempt/work item/trace, decides the waiting item, and resumes the same run to archive and notification. This is application persistence-boundary restart evidence; deployed process restart remains PBI-E25.

For each mode, two runs sharing one revision and file-backed database are driven to waiting in two worker threads and then decided/resumed in two worker threads. The resulting invoice, work-item, archive, notification, and trace partitions remain associated with their own run. The two threaded cases passed three additional repeated executions without a lock, version, or cross-run failure.

## 3. Validation, dependency, and PDF boundaries

Constructor cases cover every approved graph-validation class before activation and prove that invalid activation creates no revision. Unsupported conditions, task types, attempt bounds, ambiguous transitions, malformed constructor fields, and executable payload fields are rejected.

The v3 dependency/source inspection finds no random outcome import, Kafka/broker client, payment provider, external HTTP client, OCR/AI integration, or external notification dependency. The obsolete optional `kafka-python` requirement was removed; the preserved legacy prototype may still contain compatibility code, but the installed target and v3 path require no broker.

Seven PDF boundary classes—empty, oversized, wrong declared media type, non-PDF, malformed, zero-page, and encrypted—are checked in both modes. Storage-boundary failures create no run; readable-boundary failures reach controlled `VALIDATION_FAILED`; all 14 cases create zero approval work items.

## 4. Status-read measurement

Reference environment:

- Linux `6.18.35`, `x86_64`;
- Python `3.12.13`;
- SQLAlchemy `2.0.36`;
- SQLite `3.50.4`;
- completed approved reference run in isolated in-memory SQLite with local disposable PDF storage;
- 100 consecutive `SqlAlchemyInvoiceRunQueryService.get()` reads, including ordered trace projection.

Result: `100/100` reads completed below one second; p95 `1.172 ms`, median `0.832 ms`, maximum `2.676 ms`. This exceeds the `95/100 < 1 s` threshold. The value is reference-environment evidence, not a production latency guarantee.

## 5. Verification result and limits

The complete isolated repository suite reports `213 passed in 6.76s`. Python compilation, JavaScript syntax, layer-boundary scans, prohibited-dependency checks, and `git diff --check` pass.

This record does not establish production migration, deployed-process restart, persistent-volume configuration, manual cross-browser acceptance, accessibility acceptance, deployment, commit, push, release, or instructor approval.

Next gate: PBI-E24 final user-outcome-first browser acceptance.
