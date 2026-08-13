# PBI-E25 — Persistent Single-Service Deployment Verification

| Field | Value |
|---|---|
| Status | `ACCEPTED — deployment inventory and OS-process restart` |
| Date | `2026-08-13` |
| Requirements | `NFR-003`, `NFR-006`, CON-001–CON-003 |
| Entry evidence | PBI-E23 and PBI-E24 accepted; `EV-044`, `EV-045` |
| Instructor approval | `NOT CLAIMED` |

## 1. Deployment correction and inventory

The preserved prototype compose file still declared application, Kafka, and ZooKeeper services, installed dependencies at container start, and bind-mounted the repository. E25 replaces that obsolete topology with:

- one built FastAPI application service;
- no broker or coordination service;
- one named `invoice_data` volume mounted at `/data`;
- legacy compatibility SQLite at `/data/workflow.db`;
- current invoice SQLite at `/data/invoice_v3.db`;
- controlled invoice documents at `/data/documents`;
- a non-root image user and local HTTP healthcheck.

The compose YAML parses to one service (`app`) and one volume (`invoice_data`). Source inventory tests also reject Kafka, ZooKeeper, runtime `pip install`, and source-tree bind mounting.

## 2. Controlled process restart

For each execution mode, the deployment test starts a real Uvicorn OS process against a disposable persistent directory, submits a readable invoice, and reaches persistent `PENDING_APPROVAL`. It then terminates the process and verifies that both SQLite files and the stored document exist.

A new Uvicorn process starts against the same directory and port configuration. It retrieves the original invoice/run/work item, accepts an approval decision using the restored state version, and resumes the original run to `ARCHIVED`/`COMPLETED` with the expected archive identity. Both orchestration and choreography pass this sequence.

This demonstrates that the in-memory EventBus is not authoritative and that waiting work, run state, trace, and document storage survive process recreation.

## 3. Verification result and limits

Focused deployment checks report `4 passed in 4.05s`. The complete isolated repository suite reports `220 passed in 10.05s`. Compose YAML parsing, Python compilation, JavaScript syntax, layer/dependency checks, and `git diff --check` pass.

No Docker, Podman, or compatible container engine is available in the verification environment. Therefore the Dockerfile was inspected and the topology parsed, but the image was not built and a container/volume restart was not executed. The OS-process restart exercises the same environment-variable paths and persistent resources using disposable storage. Production migration, external deployment, commit, push, release, and instructor approval are not claimed.

Next gate: PBI-E26 final report, UML, reuse disclosure, and defense-script reconciliation.
