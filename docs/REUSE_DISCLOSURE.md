# Reuse and Reference Disclosure

## Purpose

This record distinguishes reused general-purpose components, product references, and independently implemented project logic. Reuse is part of the engineering approach and is not presented as original library work.

## Runtime and test dependencies

| Dependency | Use in the project | Not supplied by the dependency |
|---|---|---|
| FastAPI 0.115.6 | HTTP routing and request/response boundary | Invoice lifecycle, workflow execution, retry, waiting, idempotency |
| Uvicorn 0.29.0 | ASGI process | Application recovery or business semantics |
| SQLAlchemy 2.0.36 | ORM and transaction primitives | Persistence model decisions, constraints, run ownership, trace vocabulary |
| Pydantic 2.10.3 | Boundary data validation | Domain graph validation or invoice process policy |
| pypdf 6.x | Structural PDF opening, encryption and page checks | OCR, invoice interpretation, business validation |
| pytest 8.3.4 | Automated test runner | Scenario design or expected results |
| HTTPX 0.28.1 | HTTP test client | Application behavior |
| SQLite | Local persistent database | Schema and state-machine design |

Browser acceptance temporarily used Playwright and Chromium outside project dependencies. They are verification tools, not runtime product components.

## Behavioral references

Camunda, n8n, and Temporal were reviewed as examples of established workflow products. The project retained three broad ideas that are common in such systems:

- a process can pause for durable human work;
- a workflow definition can be configured and versioned;
- execution history should be inspectable independently of the current UI request.

No engine, source file, workflow definition, diagram, UI implementation, or branded asset from these products is included. The project’s bounded DAG validator, resolver, retry policy, run-scoped EventBus strategy, persistence model, invoice services, constructor, tests, and UI were implemented for Requirements v3 in this repository.

## Course and literature sources

The project structure and report use concepts from the supplied Software Engineering course material, including requirements traceability, architecture views, quality attributes, component reuse, and evolution/change control. Enterprise integration and microservice pattern literature provided general terminology for orchestration and choreography.

## Scope statement

The project is not claimed as a new general workflow-engine product. Its academic contribution is an independently implemented, evidence-backed comparison of two execution strategies inside one bounded invoice-approval application.
