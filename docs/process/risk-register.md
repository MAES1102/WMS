# Risk Register

| ID | Risk | Probability | Impact | Mitigation and evidence | Residual state |
|---|---|---:|---:|---|---|
| R-01 | Evaluator sees only technical nodes and cannot identify product value | Medium | High | Request-first UI, five-minute script, business states, real approval decision | Low |
| R-02 | Orchestration and choreography diverge semantically | Medium | High | Shared step/retry/resolver services and paired normalized scenario tests | Low |
| R-03 | Duplicate approval advances a run twice | Medium | High | Unique decision/work-item rules, idempotent replay, conflict tests | Low |
| R-04 | In-memory events are mistaken for durable state | Medium | High | Persistent cursor is authoritative; handlers removed at waiting/terminal; restart tests | Low |
| R-05 | Retry selects an edge too early or loops forever | Medium | High | Positive attempt bounds, retry-before-resolver policy, exact trace tests | Low |
| R-06 | Two runs contaminate each other's data | Low | High | Run/purchase request keys, unique constraints, version checks, threaded isolation tests | Low |
| R-07 | Uploaded file escapes storage or invalid structured input reaches approval | Medium | High | Generated identity, bounded size, structured validation adapter, traversal and malformed-file tests | Low |
| R-08 | Constructor becomes an unsafe low-code platform | Medium | Medium | Closed four-task catalog, three conditions, no scripts/plugins, negative tests | Low |
| R-09 | Repository bloat slows startup or hides the final product | High | Medium | External virtual environment recommendation, no default reload, one runtime, minimal tracked artifacts | Low |
| R-10 | Report overclaims reuse, deployment, or production readiness | Medium | High | Reuse disclosure, evidence ledger, explicit limitations, final consistency review | Low |
| R-11 | Local database schema is stale after pulling a new version | Medium | Medium | Runtime DB is ignored and disposable for demonstration; startup instructions use a clean `purchase request.db` | Low |
| R-12 | Professor does not accept the clarified direction | Medium | High | Send concise approval email and explain that the engine objective remains while the business application clarifies it | Open until instructor response |
