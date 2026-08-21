# Evidence Register

## Final evidence ledger

| ID | Claim | Evidence | State |
|---|---|---|---|
| EV-01 | Definition validation rejects invalid graphs before activation | Domain and constructor rule-path tests | Verified |
| EV-02 | Resolver precedence and terminal decisions are deterministic | Resolver tests | Verified |
| EV-03 | Retry repeats the current task and is bounded | Retry, step-service, and exact-trace tests | Verified |
| EV-04 | Both modes implement the same five business scenarios | Orchestration/choreography integration matrix | Verified |
| EV-05 | Human approval waits persistently and resumes the same run once | Approval, idempotency, and restart tests | Verified |
| EV-06 | Runs remain isolated under sequential and threaded execution | Quality-matrix isolation tests | Verified |
| EV-07 | PDF input is bounded and cannot choose its storage path | Document/PDF and submission API tests | Verified |
| EV-08 | Constructor accepts only bounded task types and immutable activation | Constructor service, persistence, API, and UI tests | Verified |
| EV-09 | Invoice status, decision, archive, notification, and trace agree | Integrated visible-runtime tests | Verified |
| EV-10 | Deployment is one service with no broker | Dockerfile/Compose inventory tests | Verified by inspection |
| EV-11 | Normal local launcher avoids repository-wide file watching | Launcher and deployment-hygiene test | Verified |
| EV-12 | Repository contains one invoice application, not a parallel legacy runtime | Repository inventory test | Verified |
| EV-13 | Report and UML sources are versioned and the final PDF is generated | Build script, artifact register, visual PDF review | Verified at final build |
| EV-14 | Professor approved the clarified Invoice Approval direction | No preserved approval response | Not claimed |
| EV-15 | Production security, scale, availability, and accounting correctness | Outside bounded academic verification | Not claimed |

## Evidence interpretation

Automated tests are strong evidence for deterministic behavior in the recorded local environment. They do not by themselves establish production certification. The final demonstration should show one successful case, one controlled failure, the second execution mode, and the constructor while explaining the shared policy underneath.
