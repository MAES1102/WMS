# Risk Register

| ID | Risk | Probability | Impact | Mitigation and evidence | Residual state |
|---|---|---:|---:|---|---|
| R-01 | Evaluator sees only technical nodes and cannot identify product value | Medium | High | Request-first UI, five-minute script, business states, real approval decision | Low |
| R-02 | Orchestration and choreography diverge semantically | Medium | High | Shared step/retry/resolver services and paired normalized scenario tests | Low |
| R-03 | Duplicate approval advances a run twice | Medium | High | Unique decision/work-item rules, idempotent replay, conflict tests | Low |
| R-04 | In-memory events are mistaken for durable state | Medium | High | Persistent cursor is authoritative; handlers removed at waiting/terminal; restart tests | Low |
| R-05 | Retry selects an edge too early or loops forever | Medium | High | Positive attempt bounds, retry-before-resolver policy, exact trace tests | Low |
| R-06 | Two runs contaminate each other's data | Low | High | Run/purchase request keys, unique constraints, version checks, threaded isolation tests | Low |
| R-07 | Invalid structured request reaches approval | Medium | High | Domain validation before work-item creation and invalid-request journey tests | Low |
| R-08 | Constructor becomes an unsafe low-code platform | Medium | Medium | Closed four-task catalog, three conditions, no scripts/plugins, negative tests | Low |
| R-09 | Repository bloat slows startup or hides the final product | High | Medium | External virtual environment recommendation, no default reload, one runtime, minimal tracked artifacts | Low |
| R-10 | Report overclaims reuse, deployment, or production readiness | Medium | High | Reuse disclosure, evidence ledger, explicit limitations, final consistency review | Low |
| R-11 | Local database schema is stale after pulling a new version | Medium | Medium | Runtime DB is ignored and disposable for demonstration; startup instructions use a clean `workflow.db` | Low |
| R-12 | Professor does not accept the final reference scenario | Medium | High | Explain that Purchase Request Approval clarifies the already approved WMS direction without claiming separate scenario approval | Open until academic acceptance |
