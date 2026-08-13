# PBI-E18 — Bounded Invoice Submission and Validation Plan

| Field | Value |
|---|---|
| Status | `APPROVED — project-level implementation plan` |
| Date | `2026-08-13` |
| Requirements | `FR-031`–`FR-035`, section 6, `NFR-009` |
| Entry evidence | `EV-034`; PBI-E17 foundation accepted at project level |
| Implementation | `PBI-E18 ACCEPTED — E19 NEXT` |
| Instructor approval | `NOT CLAIMED` |

## 1. User-visible outcome

The increment starts the first real invoice case. A submitter supplies one bounded PDF and raw invoice metadata. The application creates a generated document identity, invoice, run, initial cursor, and trace. `DOCUMENT_VALIDATION` then produces a controlled success or a visible field/file-specific business failure. Invalid input must never create approval work.

This replaces abstract task lights with an explainable statement: the system received invoice X and either accepted it for review or rejected it for a concrete validation reason.

## 2. Entry correction

The 5A.2 `Invoice` columns used parsed `Date`/`Numeric` values only. That cannot satisfy `FR-031`, which requires raw business-invalid values to remain available to `DOCUMENT_VALIDATION`. Before a submission adapter is connected, persistence must retain bounded raw date/amount/currency strings and make normalized values nullable until validation succeeds. Original filename, declared media type, and byte size are also required as controlled metadata; the original filename never selects a path.

This correction is confined to the still-isolated v3 schema. No migration or existing database is implied.

## 3. Selected reuse boundary

Use [`pypdf`](https://pypi.org/project/pypdf/) behind a local `PdfInspector` adapter for openability, encryption status, and page count. The [official `PdfReader` documentation](https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html) exposes page reading and encryption status. The project owns the size/media boundary, metadata rules, storage identity, executor result, workflow routing, persistence, and trace. It does not copy another workflow product or perform text extraction/OCR.

Selected dependency range: `pypdf>=6.10,<7`. The initial focused adapter tests run with 6.10.0 already available in the controlled environment. Before a locked release, the exact version and license notice must be recorded and the full PDF boundary suite rerun.

## 4. Controlled increments

### E18.1 — Validation and document adapters

- add pure raw-metadata validation with complete field-specific issues;
- add controlled local storage using generated UUID identities and a 10 MiB streaming limit;
- add `pypdf` inspection for non-PDF, malformed, encrypted, unreadable, and zero-page rejection;
- add `DOCUMENT_VALIDATION` executor over ports, returning `TaskResult` only;
- correct the isolated invoice schema to preserve raw submission values;
- use disposable directories and in-memory databases only.

### E18.2 — Submission transaction and validation persistence

- add a submission service and SQLAlchemy adapter that atomically creates invoice, run, cursor, and `RUN_STARTED` trace after document storage succeeds;
- delete the newly stored document if the database transaction fails;
- implement the 5A.3 SQLAlchemy unit-of-work adapter so validation attempt/result/cursor/trace and `VALIDATION_FAILED` state commit together;
- verify valid and invalid cases and zero approval work for failure.

### E18.3 — Separate v3 HTTP boundary

- add one multipart v3 submission endpoint with bounded structural parsing;
- keep it separate from old prototype endpoints and tables;
- do not start the server or switch startup schema until migration/fresh-database strategy is reviewed;
- return invoice/run identities and business status, not abstract executor indicators.

## 5. Acceptance and stop conditions

PBI-E18 is complete only when valid and invalid submissions persist mutually linked invoice/run/revision/cursor/trace state, failure creates no approval item, and the focused boundary suite covers every section 6 class. E18.1 alone is not an endpoint or a completed user flow.

Stop and review if implementation requires OCR, executable user input, an external service, original-filename paths, unbounded reads, writes to the developer database, dual writes to prototype models, or a hidden migration.

## 6. E18.1 execution record

E18.1 adds raw-metadata validation, a generated-identity local storage adapter, a `pypdf` structural inspector, and a port-based `DOCUMENT_VALIDATION` executor. The isolated invoice schema now retains raw date/amount/currency plus controlled file metadata while normalized values remain nullable before validation. The final focused runs reported 42 domain, 12 application, 9 infrastructure, and 9 in-memory persistence passes. The environment supplied `pypdf 6.10.0`; no package installation occurred.

This record establishes no SQLAlchemy validation-step adapter, endpoint, approval work, old-runtime cutover, migration, developer-database compatibility, deployment, or release. E18.2 is in progress.

## 7. E18.2 initial-submission execution record

The first E18.2 slice adds an application submission service and SQLAlchemy adapter. It stores the bounded document first, then transactionally creates the raw invoice, selected-revision run, version-1 `READY` cursor, and position-1 `RUN_STARTED` trace. Explicit flush ordering preserves foreign keys inside one transaction. Database failure rolls back all four records and compensates by deleting the newly stored document. Missing active revision fails before storage.

Four integration cases raised the persistence suite from 9 to 13 passes. This slice satisfies initial association/atomicity evidence for `FR-031` and `FR-034`, but E18.2 remains incomplete until the real 5A.3 SQLAlchemy step adapter persists normalized validation success or `VALIDATION_FAILED` together with attempt/cursor/trace.

## 8. E18.2 validation-step execution record

The SQLAlchemy automatic-step adapter now loads the authoritative run cursor and activated-revision task/transition data, supplies stored invoice input to `DOCUMENT_VALIDATION`, and commits the attempt, business effects, optimistic cursor update, and ordered trace in one transaction. A successful validation stores normalized metadata and selects the human-review task. A metadata or structural-PDF business failure stores `VALIDATION_FAILED`, selects the notification task, records the state change, and creates no approval work.

The application service owns explicit business effects; the persistence adapter applies them without reimplementing validation or routing rules. A conditional `state_version` update rejects stale commits, and the rollback case leaves normalized metadata, attempts, and trace unchanged. The final isolated run reported 82 passes: 42 domain, 14 application, 9 infrastructure, and 17 persistence tests.

E18.2 is accepted at project level. This is not the complete S3 scenario: notification execution and terminal run completion remain future controller/executor work. E18.3 is the next gate and is limited to a separate bounded v3 HTTP submission boundary; no old-runtime switch or database migration is implied.

## 9. E18.3 HTTP-boundary execution record

A separate `/api/v3/invoices` router now translates one bounded multipart request into `InvoiceSubmissionService`. The boundary requires the six controlled text fields and exactly one document part, rejects unknown/duplicate/nested parts, bounds the complete request before parsing, and leaves business validation to `DOCUMENT_VALIDATION`. Its response leads with invoice/run identities and business status rather than executor indicators.

The adapter uses the standard-library MIME parser inside the explicit body bound, so it adds no second multipart dependency and does not implement delimiter splitting itself. Presentation code depends only on application/domain exceptions and contracts; SQLAlchemy and local-storage errors are translated below that boundary.

Four HTTP acceptance cases pass for successful submission, preservation of business-invalid raw values, structural request failures including oversize input, and missing active revision. The final isolated combined suite reports 86 passes across domain, application, infrastructure, persistence, and presentation layers.

PBI-E18 is accepted at project level. The router is deliberately not registered in the prototype `main.py`: doing so before a reviewed fresh-database or migration composition would create a hidden runtime/schema dependency. E19 persistent human approval is the next vertical increment.
