---
title: "Event-Driven Workflow Management System"
subtitle: "Software Engineering Project report"
course: "Software Engineering"
student: "Yermek Aubayev(551098)"
stack: "Python 3.13 · FastAPI · SQLAlchemy 2.0 · SQLite · Apache Kafka (optional)"
---

<!-- ═══════════════════════════════════════════════════════════
     ACADEMIC COVER PAGE — styled by docs/report-style.css
     Rendered as a full first page; no page number printed.
     ═══════════════════════════════════════════════════════════ -->
<div class="cover-page">

  <div>
    <div class="cover-institution">University of Messina</div>
    <div class="cover-department"></div>
    <hr class="cover-rule">
  </div>

  <div class="cover-title-block">
    <div class="cover-type">Software Engineering Project Report</div>
    <div class="cover-title">Event-Driven Workflow Management System</div>
    <div class="cover-subtitle">Graph-Based Workflow Engine with<br>Orchestration and Choreography</div>
  </div>

  <div>
    <table class="cover-meta-table">
      <tbody>
        <tr>
          <td class="label">Student:</td>
          <td class="value">Yermek Aubayev &nbsp;(ID 551098)</td>
        </tr>
        <tr>
          <td class="label">Course:</td>
          <td class="value">Software Engineering</td>
        </tr>
        <tr>
          <td class="label">Methodology:</td>
          <td class="value">Scrum — 3 one-week sprints + 1 evolution sprint</td>
        </tr>
        <tr>
          <td class="label">Test Suite:</td>
          <td class="value">27 automated tests, all passing</td>
        </tr>
        <tr>
          <td class="label">Academic Year:</td>
          <td class="value">2025 / 2026</td>
        </tr>
      </tbody>
    </table>
    <div class="cover-tech-stack">FastAPI &nbsp;·&nbsp; SQLAlchemy &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; EventBus &nbsp;·&nbsp; Apache Kafka &nbsp;·&nbsp; Docker</div>
    <hr class="cover-rule-bottom">
    <div class="cover-year">University of Messina &nbsp;—&nbsp; Academic Year 2025/2026</div>
  </div>

</div>

# Event-Driven Workflow Management System
 
**Methodology:** Scrum (3 one-week sprints + 1 evolution sprint)  
**Test Suite:** 27 automated tests — all passing (`pytest tests/ -v`)

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#1-introduction)
3. [Problem Statement](#2-problem-statement)
4. [Motivation](#3-motivation)
5. [Objectives](#4-objectives)
6. [Scrum Methodology — Justification and Process](#5-scrum-methodology--justification-and-process)
7. [Requirements Engineering](#6-requirements-engineering)
8. [Product Backlog](#7-product-backlog)
9. [Sprint 1 — Foundation: Data Models and CRUD API](#8-sprint-1--foundation-data-models-and-crud-api)
10. [Sprint 2 — Execution Engine: Orchestration and Choreography](#9-sprint-2--execution-engine-orchestration-and-choreography)
11. [Sprint 3 — Dashboard, Testing, Bug Fixes, and Documentation](#10-sprint-3--dashboard-testing-bug-fixes-and-documentation)
12. [Sprint 4 — Evolution Sprint: Graph-Based Workflow Engine](#11-sprint-4--evolution-sprint-graph-based-workflow-engine)
13. [Backlog Refinement](#12-backlog-refinement)
14. [Requirements Traceability Matrix](#13-requirements-traceability-matrix)
15. [System Architecture](#14-system-architecture)
16. [UML Modeling — Complete Embedded Diagram Set](#15-uml-modeling--complete-embedded-diagram-set)
17. [Complex Custom Logic](#16-complex-custom-logic)
18. [Execution Models — Comparative Analysis](#17-execution-models--comparative-analysis)
19. [Design Patterns](#18-design-patterns)
20. [Testing](#19-testing)
21. [NFR Implementation and Verification Evidence](#20-nfr-implementation-and-verification-evidence)
22. [Limitations](#21-limitations)
23. [Future Work](#22-future-work)
24. [Conclusion](#23-conclusion)
25. [References](#24-references)
26. [Appendix A — Modification Log](#appendix-a--modification-log)
27. [Appendix B — Professor Comment Mapping](#appendix-b--professor-comment-mapping)
28. [Appendix C — Self-Assessment](#appendix-c--self-assessment)

---

## Abstract

This report documents the design, implementation, and evaluation of an **Event-Driven Workflow Management System (WMS)** developed as a Software Engineering semester project. The final system models workflows as **directed graphs**: tasks are nodes, and `WorkflowTransition` edges connect them with conditional routing (`SUCCESS`, `FAILURE`, or `ALWAYS`). The execution path is resolved dynamically at runtime by a `TransitionResolver`, enabling **conditional branching**, **decision gateways**, and **retry loops** — not merely a fixed ordered sequence of steps.

The system executes these graphs under two architecturally distinct patterns: **orchestration** (a central controller traverses the workflow graph as a state machine, consulting the `TransitionResolver` after each task) and **choreography** (task-completion events trigger the `TransitionResolver` reactively through an `EventBus` Observer chain, with no central loop). A `MAX_LOOP_ITERATIONS` safety valve prevents infinite execution on cyclic graphs.

The system evolved through **evolutionary prototyping**: an initial working prototype confirmed the technical foundation (CRUD API, event infrastructure, orchestration/choreography engines) and was validated against stakeholder requirements. This validation revealed that the linear, order-based execution model was insufficient for real business workflow semantics. A structured evolution sprint produced the graph-based architecture that is the primary contribution of this project.

The system is built with Python 3.13, FastAPI, SQLAlchemy 2.0, SQLite, and optional Apache Kafka. Development followed the Scrum framework across three delivery sprints plus one evolution sprint, producing a full artefact set: 20 user stories with Given/When/Then acceptance criteria, four Sprint Backlogs, burndown charts, a Definition of Done, and 15 embedded UML diagrams. The test suite consists of **27 automated integration tests, all passing**.

---

## 1. Introduction

### 1.1 Background

Workflow automation underpins modern enterprise software. Applications ranging from CI/CD pipelines and business process engines to microservice orchestration all require a mechanism to define, execute, monitor, and recover from multi-step computational processes. Two fundamentally different approaches have emerged in the literature and industry: **orchestration** (a central coordinator explicitly drives every step) and **choreography** (each service reacts autonomously to events, with no coordinator).

While both patterns are documented in *Enterprise Integration Patterns* (Hohpe & Woolf, 2003) and *Microservices Patterns* (Richardson, 2018), their practical trade-offs — coupling, resilience, auditability, failure isolation — are rarely explored through a running implementation in academic settings. This project makes those trade-offs concrete by implementing both patterns in a single, testable system with a shared data model.

### 1.2 System Overview

The WMS exposes a REST API for full workflow lifecycle management: users register accounts, create named workflows, compose workflow **graphs** from tasks and conditional transitions, and execute the workflow in one of two modes. A workflow is not a flat ordered list — it is a directed graph where each `WorkflowTransition` edge connects a source task to a target task and carries a condition (`SUCCESS`, `FAILURE`, or `ALWAYS`). After each task executes, the `TransitionResolver` reads the matching edge and determines the next node dynamically. This enables decision gateways, conditional branches, and retry loops.

Every execution is persisted as a `WorkflowRun` audit record with per-task `TaskExecution` instances. A browser dashboard (`GET /ui`) provides real-time execution visualisation including graph rendering. The event transport layer supports both an in-memory `EventBus` and optional Apache Kafka with graceful fallback.

### 1.3 Evolutionary Prototype Approach

This project applies **evolutionary prototyping** as described by Sommerville (2016): a working system is built incrementally, validated with stakeholders, and evolved based on the feedback received. This approach is appropriate when requirements cannot be fully specified upfront — as is the case for workflow semantics, where the limitations of a simple execution model only become apparent when stakeholders observe the running system.

**Initial prototype (Sprints 1–3):** The first deliverable established a complete technical foundation: REST API, SQLAlchemy data layer, `EventBus` pub/sub infrastructure, and both execution engines (orchestration and choreography). Tasks were executed in a fixed integer `order` sequence — a simple, correct, and testable starting point.

**Stakeholder validation:** The working prototype was presented for evaluation. The feedback was direct: *"This workflow just executes tasks one after another."* Real business processes require conditional routing — a fraud check that branches to capture or cancel, a payment retry loop, a document review cycle. The linear model could not express these semantics.

**Requirement refinement:** Stakeholder feedback translated into new requirements (UR-10, UR-11, FR-18–FR-21 in §6) that the initial prototype did not satisfy. This is a textbook example of how prototype validation reveals incomplete requirements — the gap between what users specified ("ordered steps") and what they actually needed ("conditional graph execution") was invisible until they saw the system run.

**Architecture evolution (Sprint 4):** A targeted evolution sprint introduced `WorkflowTransition` (directed, conditional graph edges), `TransitionResolver` (dynamic next-node selection), `MAX_LOOP_ITERATIONS` (loop protection), and `TaskExecution` (per-run instance tracking). Both execution engines were extended to use the graph model while preserving full backward compatibility with linear workflows through a `workflow_has_transitions()` detection function.

The result is a system whose architecture reflects not the requirements as first written, but the requirements as understood after validation — which is precisely the value of evolutionary prototyping.

### 1.4 Scope and Constraints

The system is an academic prototype. Authentication, production-grade security, and horizontal scalability are explicitly out of scope (see Section 6.3).

---

## 2. Problem Statement

University Software Engineering curricula describe orchestration and choreography conceptually, but rarely provide hands-on experience implementing them in a real system. Students can read about the patterns but cannot directly observe how they fail differently, what code differences they impose, or how their coupling properties manifest in practice.

A concrete, runnable, tested system implementing both patterns with the same domain model and the same test infrastructure is needed to make these trade-offs empirically observable. Additionally, such a system must demonstrate professional software engineering practices — automated tests, a traceable Scrum process, complete UML documentation, and measurable non-functional requirements — to serve as a credible academic artefact.

---

## 3. Motivation

**Architectural duality.** Most educational projects implement a single architectural pattern. Implementing both within one system forces the developer to understand each deeply enough to compare them, not just describe them.

**Industrial relevance.** Apache Kafka is used at LinkedIn, Uber, Netflix, and Airbnb at billions-of-events-per-day scale. Understanding event-driven workflow execution is a transferable engineering skill.

**Non-obvious failure behaviour (BUG-02).** The choreography chain continuing to execute downstream tasks after an upstream failure is a bug class unique to event-driven systems — it cannot occur in orchestration. Identifying it, fixing it with a one-line guard, and writing a named regression test is itself a learning outcome not available from textbook reading.

**Scrum process compliance.** Prior assessment feedback identified the project report as incomplete. This project was designed from the first sprint to produce a complete Scrum artefact set with traceable requirements, measurable NFRs, and honest retrospectives.

---

## 4. Objectives

1. Implement a **REST API** (20 endpoints) supporting the full workflow lifecycle: user management, workflow/task CRUD, conditional transition CRUD, execution in both modes, monitoring, and deletion.
2. Implement the **orchestration pattern**: `app/engine/orchestrator.py` — a central controller that manages workflow state and **dynamically traverses the workflow graph**, consulting the `TransitionResolver` after each task execution to select the next node. For workflows with no transitions defined, a sequential fallback preserves backward compatibility.
3. Implement the **choreography pattern**: `app/engine/choreography.py` — a reactive event-driven execution model where `TaskCompletedEvent` messages trigger the `TransitionResolver`, which determines the next task without any central loop. For workflows with no transitions, the original handler-chain mechanism is preserved.
4. Implement the **graph workflow engine**: `WorkflowTransition` directed edges with `SUCCESS`/`FAILURE`/`ALWAYS` conditions, `TransitionResolver` for dynamic next-node selection, `MAX_LOOP_ITERATIONS` loop protection, and `TaskExecution` per-run instance tracking.
5. Support **conditional branching** (decision gateways where task outcome selects the outgoing edge), **retry loops** (back-edges revisiting earlier tasks), and **loop limit protection** (`MAX_LOOP_ITERATIONS = 10`).
6. Support **Apache Kafka** as optional distributed event transport for the legacy choreography path, with in-memory `EventBus` fallback when Kafka is unreachable. The graph choreography path uses the `EventBus` abstraction directly.
7. Provide a **browser dashboard** (`app/static/index.html`, served at `GET /ui`) with real-time task status polling and a Canvas-rendered workflow graph.
8. Produce a **27-test automated suite** covering all 21 functional requirements, including graph branching, FAILURE path execution, retry loops, loop limit enforcement, and choreography graph traversal.
9. Follow the **Scrum framework** with documented Product Backlog, Sprint Backlogs, burndown charts, sprint reviews, retrospectives, and a Definition of Done across four sprints (three delivery sprints + one evolution sprint).
10. Produce a complete embedded **UML documentation set**: Use Case, Class, ER, Component, Deployment, Package, State (×2), Sequence (×3), Activity (×4).

---

## 5. Scrum Methodology — Justification and Process

### 5.1 Why Scrum Was Selected

Scrum was chosen as the development methodology after evaluating three candidate frameworks. The decision was driven by four criteria specific to this project: predictable academic milestones, solo team size, an iteratively evolving architecture, and the need to produce a documentable process.

**Fitness for this project:**
The system has a natural three-layer decomposition (data → engine → UI/testing) that maps directly to three Scrum sprints. Scrum's sprint-end review ceremony provides a built-in checkpoint to validate that each layer is stable before the next is built on top of it. Without this structure, the risk of building the execution engine on a flawed data model would have been significant.

**Academic artefact production:**
Scrum mandates Product Backlog, Sprint Backlogs, sprint reviews, and retrospectives — precisely the artefacts required by the Software Engineering course rubric. Kanban and Lean do not prescribe these ceremonies, so switching to them would have sacrificed academic documentation without any compensating benefit.

### 5.2 Alternatives Considered

| Framework | Evaluated | Reason Not Selected |
|---|---|---|
| **Kanban** | Yes | No sprint boundaries — continuous flow does not produce dated review evidence or burndown charts required by the course rubric |
| **XP (Extreme Programming)** | Yes | Pair programming and test-driven development are excellent practices, but XP's engineering-heavy ceremonies (pair rotations, continuous integration releases) are designed for teams of 3+; applying them solo would produce ceremony overhead without benefit |
| **Lean Software Development** | Yes | Lean's "eliminate waste" focus is a mindset, not a process with defined events; it does not generate the Sprint Retrospective or burndown artefacts required |
| **Crystal** | Yes | Crystal adapts to team size, but the adaptation itself requires process design effort; for a three-sprint academic project, the time cost of designing the process exceeds the benefit of flexibility |
| **Plan-Driven (Waterfall)** | Yes | A fixed requirements → design → implementation → test sequence would have required complete requirements knowledge in Week 1; the choreography engine design was not fully understood until Sprint 2 Day 1 — a Scrum impediment that a Waterfall plan would have been unable to accommodate |

### 5.3 Benefits Obtained from Scrum

| Benefit | Evidence in This Project |
|---|---|
| **Incremental delivery** | Sprint 1 delivered a fully tested CRUD API; Sprint 2 delivered execution engines on top of a verified foundation |
| **Early defect detection** | BUG-02 was identified at Sprint 2 end via Sprint Review manual testing, not in production |
| **Honest process reflection** | All three Sprint Retrospectives candidly document deferred testing as a process failure, with concrete improvement actions |
| **Scope management** | Sprint 3's 28-point commitment was identified as 30% over the Sprint 1/2 average; the risk was consciously accepted and documented |
| **Traceability** | Every user story links to a requirement, a sprint task, and at least one automated test |

### 5.4 Scrum Roles (Solo Adaptation)

| Role | Responsibility in This Project |
|---|---|
| Product Owner | Prioritise Product Backlog; define acceptance criteria; accept/reject sprint deliverables at Sprint Review |
| Scrum Master | Enforce Definition of Done; facilitate ceremonies; remove technical impediments |
| Developer | Implement stories; write tests; maintain UML documentation |

### 5.5 Definition of Done

A user story is **Done** when all of the following are verified:

- [ ] Code implemented and passes self-review checklist
- [ ] All existing tests pass (`pytest tests/ -v` — zero failures)
- [ ] New tests written to cover the story's acceptance criteria
- [ ] No `datetime.utcnow()` deprecation warnings (replaced with `datetime.now(UTC)`)
- [ ] Affected UML diagrams updated in `docs/`
- [ ] `README.md` endpoint table updated if a new HTTP endpoint was added
- [ ] Application starts cleanly (`uvicorn app.main:app --reload`)
- [ ] `docker-compose up` completes without errors

Full checklist: `docs/definition_of_done.md`

---

## 6. Requirements Engineering

> **Note on requirement style:** User Requirements describe *what users need* (problem level, technology-agnostic). System Requirements describe *what the system shall do* (behavioural constraints). Implementation technology is not a requirement — it is an architectural decision.

### 6.1 User Requirements

User Requirements capture the needs of the primary user (a developer or system administrator using the WMS) without prescribing implementation.

| UR-ID | User Requirement | Priority | Origin |
|---|---|---|---|
| UR-01 | Users need to register and manage personal accounts with exclusive ownership of their workflows | High | Initial |
| UR-02 | Users need to define and manage multi-step automated processes composed of named steps | High | Initial |
| UR-03 | Users need to execute automated processes and have the system carry out each step reliably | High | Initial |
| UR-04 | Users need the system to stop processing when a step fails, so that subsequent steps are not executed on invalid state | High | Initial |
| UR-05 | Users need to observe the progress and outcome of an executing process in real time | Medium | Initial |
| UR-06 | Users need a complete audit history of all past executions, including which steps succeeded or failed | Medium | Initial |
| UR-07 | Users need the system to be resilient to infrastructure failures; if the messaging infrastructure is unavailable, processes should still run | Medium | Initial |
| UR-08 | Users need the system to prevent conflicting step definitions (e.g., two steps with the same position in a workflow) | High | Initial |
| UR-09 | Users need different reliability and coupling trade-offs for process execution — some use cases demand a single auditable control point, others demand that no single component failure can halt the entire process | Low | Initial |
| UR-10 | Users need workflows whose execution path can change depending on task outcomes, so that a single workflow definition can model real business decision points (e.g. approve/reject, charge/retry) | High | **Evolved** — discovered via prototype validation |
| UR-11 | Users need workflows to support automatic recovery paths (retry loops, compensating actions) so that temporary failures do not require manual re-execution of the entire workflow | High | **Evolved** — discovered via prototype validation |

> **Note on UR-10 and UR-11:** These requirements were not identified upfront. They emerged from stakeholder validation of the initial prototype (§1.3). The prototype demonstrated that the system executed tasks sequentially without any notion of branching or recovery. User observation of this behaviour immediately surfaced the gap. This is a concrete example of evolutionary prototyping revealing incomplete requirements.

### 6.2 System Requirements — Functional

System functional requirements specify the observable behaviour the system must exhibit. They are derived directly from User Requirements and are verified by automated tests.

| FR-ID | System Requirement | Derived From | Test |
|---|---|---|---|
| FR-01 | The system shall create a user account and return HTTP 200 when given a unique email and password | UR-01 | `test_create_user_success` |
| FR-02 | The system shall return HTTP 409 when a user account is created with an email that already exists | UR-01 | `test_duplicate_email_returns_409` |
| FR-03 | The system shall create a named workflow associated with a valid user and return its identifier | UR-02 | `test_create_workflow` |
| FR-04 | The system shall add a task to a workflow with a non-negative integer execution order | UR-02 | `test_list_tasks_returns_only_existing` |
| FR-05 | The system shall return HTTP 409 when a task is added with an execution order that already exists in the same workflow | UR-08 | `test_duplicate_task_order_returns_409` |
| FR-06 | The system shall renumber remaining tasks with consecutive integers after a task is deleted | UR-02 | `test_delete_task_reorders_remaining` |
| FR-07 | The system shall delete all tasks belonging to a workflow when that workflow is deleted | UR-02 | `test_delete_workflow_cascades_tasks` |
| FR-08 | The system shall execute all tasks of a workflow sequentially in ascending order and return a completed status when all tasks succeed (orchestration mode) | UR-03 | `test_orchestrated_workflow_success` |
| FR-09 | The system shall stop executing remaining tasks and return a failed status after the first task failure (orchestration mode) | UR-04 | `test_orchestrated_workflow_halts_on_failure` |
| FR-10 | The system shall execute all tasks of a workflow reactively via events and return a completed status when all tasks succeed (choreography mode) | UR-03, UR-09 | `test_choreography_success` |
| FR-11 | The system shall not emit a continuation event after a task failure; all downstream tasks shall remain PENDING (choreography mode) | UR-04 | `test_choreography_stops_on_failure` |
| FR-12 | The system shall return HTTP 404 when an execution is requested for a workflow identifier that does not exist | UR-03 | `test_execute_nonexistent_workflow_returns_404` |
| FR-13 | The system shall record every workflow execution as a persistent audit record with start/end timestamps and outcome status | UR-06 | `test_workflow_run_history_recorded` |
| FR-14 | The system shall expose structured execution logs for all task state transitions | UR-05 | `GET /logs` |
| FR-15 | The system shall serve a browser dashboard displaying workflow state and supporting execution controls | UR-05 | `GET /ui` |
| FR-16 | The system shall complete execution of a workflow that contains no tasks without error | UR-03 | `test_execute_empty_workflow_completes` |
| FR-17 | The system shall return HTTP 404 when a resource that does not exist is accessed or modified | UR-08 | `test_delete_workflow_not_found`, `test_get_task_not_found`, `test_delete_task_not_found`, `test_workflow_status_not_found` |
| FR-18 | The system shall allow workflow tasks to be connected via conditional `WorkflowTransition` edges carrying a `condition` value of `SUCCESS`, `FAILURE`, or `ALWAYS`, managed through a REST CRUD API | UR-10 | `test_conditional_success_path` |
| FR-19 | The system shall support alternative execution paths (branching): when a task finishes, the engine shall follow the outgoing edge whose condition matches the task result, enabling decision gateways | UR-10 | `test_failure_branch_execution` |
| FR-20 | The system shall support controlled workflow cycles (retry loops): a `WorkflowTransition` edge may point to an earlier task, allowing the graph to revisit a node | UR-11 | `test_workflow_loop_retry` |
| FR-21 | The system shall prevent infinite execution on cyclic workflows: if any single task is visited more than `MAX_LOOP_ITERATIONS` times within one run, the engine shall terminate the run with status `FAILED` | UR-11 | `test_loop_limit_prevents_infinite_execution` |

### 6.3 System Requirements — Non-Functional (Measurable)

Each NFR includes a measurable metric, target value, acceptance criterion, and validation method.

| NFR-ID | Category | Requirement | Metric | Target | Acceptance Criterion | Validation |
|---|---|---|---|---|---|---|
| NFR-01 | **Reliability** | Kafka unavailability shall not prevent workflow execution | Execution success rate without Kafka | 100% | System executes orchestration and choreography correctly when `KAFKA_BOOTSTRAP_SERVERS` is unreachable | Run `pytest tests/test_execution.py` with no Kafka broker; all 9 tests pass |
| NFR-02 | **Failure Isolation** | A choreography chain shall halt after a task failure; no downstream task shall execute | Downstream task status after upstream failure | 0 downstream tasks change from PENDING | `tasks[1]["status"] == "PENDING"` after task[0] fails | `test_choreography_stops_on_failure` |
| NFR-03 | **Auditability** | Every workflow execution shall produce a persistent audit record | Audit records created per execution | 1 per `POST /execute*` | `GET /workflow_runs/{id}` returns ≥ 1 record after any execution | `test_workflow_run_history_recorded` |
| NFR-04 | **Data Integrity** | No two tasks in the same workflow shall have the same execution order | Duplicate task order rejection rate | 100% | HTTP 409 returned on every duplicate order attempt | `test_duplicate_task_order_returns_409` |
| NFR-05 | **Data Integrity** | Database-level foreign key constraints shall be enforced | Orphaned record creation rate | 0 | Deleting a workflow cascades to its tasks | `test_delete_workflow_cascades_tasks` |
| NFR-06 | **Portability** | The system shall start from source with a single command | Start-up commands required | 1 (`docker-compose up`) | System accepts HTTP requests within 60 seconds of `docker-compose up` | Manual: time `docker-compose up`; `curl localhost:8000/` returns 200 |
| NFR-07 | **Maintainability** | All runtime dependencies shall have pinned exact versions | Unpinned dependencies | 0 | `requirements.txt` contains only `==` version specifiers | `grep -v "==" requirements.txt` returns nothing |
| NFR-08 | **Correctness** | Deprecated APIs shall not be used | `DeprecationWarning` count | 0 | `pytest tests/ -W error::DeprecationWarning` passes | `pytest tests/ -v` (27 tests pass with 0 warnings) |
| NFR-09 | **Testability** | The test suite shall run in complete isolation without file-system or network dependencies | External dependencies during test run | 0 | Tests pass with no database file and no Kafka broker | `pytest tests/ -v` on a clean machine with only `pip install -r requirements.txt` — 27 passed |

### 6.4 Constraints

| C-ID | Constraint | Rationale |
|---|---|---|
| C-01 | Implementation language: Python 3.13 | Course requirement |
| C-02 | Persistence: SQLite | Sufficient for academic prototype; eliminates PostgreSQL setup complexity |
| C-03 | Team size: 1–2 developers; 3 × 1-week sprints | Academic timeline |
| C-04 | Authentication and production security: out of scope | Documented limitation; plaintext passwords acceptable only in prototype |
| C-05 | Kafka must be optional | System must function in a development environment without a running broker |
| C-06 | Execution is synchronous | `POST /execute*` blocks until completion; async execution is Future Work |

---

## 7. Product Backlog

The Product Backlog is the single source of truth for all planned work. It was created before Sprint 1 and refined at the start of each sprint. Full Given/When/Then acceptance criteria for every story are embedded in §7.2 below.

| ID | User Story | Priority | SP | Sprint | AC Summary | Status |
|---|---|---|---|---|---|---|
| US-01 | As a user I want to register an account so that I can own workflows | High | 2 | 1 | Given unique email → 200 + id; Given duplicate email → 409 | ✅ |
| US-02 | As a user I want to create named workflows so that I can organise automated processes | High | 2 | 1 | Given valid user_id → 200 + workflow id | ✅ |
| US-03 | As a user I want to add tasks with execution order so that the system knows the step sequence | High | 3 | 1 | Given valid workflow → 200 + task PENDING; Given duplicate order → 409 | ✅ |
| US-04 | As a user I want to delete a task and have remaining tasks renumbered so that the sequence stays gapless | Medium | 3 | 1 | Given 3 tasks, delete order=1 → remaining at orders 1,2 | ✅ |
| US-05 | As a user I want to delete a workflow and have its tasks removed so that no orphaned data remains | Medium | 2 | 1 | Given workflow with tasks → delete → tasks count = 0 | ✅ |
| US-06 | As a user I want to execute a workflow in orchestration mode so that tasks run in order with fail-fast | High | 5 | 2 | All succeed → COMPLETED; first fails → FAILED + remaining PENDING | ✅ |
| US-07 | As a user I want to execute a workflow in choreography mode so that tasks trigger each other reactively | High | 8 | 2 | All succeed → COMPLETED; first fails → FAILED + next stays PENDING | ✅ |
| US-08 | As a user I want to see structured execution logs so that I can audit what happened | Medium | 3 | 2 | GET /logs returns list with timestamp, run_id, status | ✅ |
| US-09 | As a user I want a browser dashboard that shows task status in real time | Medium | 5 | 3 | Dashboard polls and updates colours every 1 second | ✅ |
| US-10 | As a user I want to see a visual workflow graph on the dashboard | Low | 3 | 3 | Canvas renders nodes coloured by PENDING/RUNNING/DONE/FAILED | ✅ |
| US-11 | As a developer I want Kafka to work as optional transport so the system degrades gracefully | Low | 5 | 3 | System runs fully without Kafka; uses EventBus fallback | ✅ |
| US-12 | As a developer I want an automated test suite so that regressions are caught immediately | High | 8 | 3 | `pytest tests/ -v` → 21 passed (Sprint 3 baseline; 27 after Sprint 4) | ✅ |
| US-13 | As a developer I want duplicate emails to return 409 not 500 | High | 1 | 3 | POST /users with duplicate email → 409 | ✅ |
| US-14 | As a developer I want executing a missing workflow to return 404 | High | 1 | 3 | POST /execute/99999 → 404 | ✅ |
| US-15 | As a developer I want UML diagrams so that architecture is documented | Medium | 5 | 3 | 13 diagrams embedded in report | ✅ |
| US-16 | As a developer I want task execution order to be unique within a workflow at the database level | High | 2 | 3 | UniqueConstraint on (workflow_id, order) enforced in DB and API layer | ✅ |
| US-17 | As a developer I want FK constraints enforced at SQLite level | Medium | 1 | 3 | PRAGMA foreign_keys=ON on every connection | ✅ |
| US-18 | As a workflow designer I want to define conditional transitions between tasks so that workflows can follow different paths depending on outcome | High | 5 | 4 | Given two tasks and a SUCCESS transition → execute → SUCCESS path followed; Given FAILURE transition → FAILURE path followed | ✅ |
| US-19 | As a workflow designer I want failed tasks to trigger recovery paths so that workflows can model real business processes | High | 3 | 4 | Given ChargeCard fails with FAILURE transition to RetryPayment → RetryPayment executes; recovery path reachable | ✅ |
| US-20 | As a workflow designer I want retry loops so that temporary failures can be handled automatically without restarting the entire workflow | Medium | 3 | 4 | Given A –FAILURE→ B –SUCCESS→ A loop → B executes on failure, loop exits on A success; loop bounded by MAX_LOOP_ITERATIONS | ✅ |

**Total story points:** 70 across 4 sprints (59 delivery + 11 evolution).

### 7.1 Backlog Prioritisation Rationale

The backlog was prioritised using MoSCoW (Must/Should/Could/Won't):

- **Must Have:** US-01–06, US-12–14 — core functionality without which the system cannot demonstrate its purpose
- **Should Have:** US-07–08, US-16–17 — required for correctness and data integrity
- **Could Have:** US-09–11 — dashboard and infrastructure enhancements; deferrable
- **Won't Have (this project):** Authentication, password hashing, async execution

### 7.2 Acceptance Criteria — Key Stories

Full Given/When/Then acceptance criteria for CRUD stories (US-01–US-05, US-08–US-17) are embedded within each Sprint's backlog section (§8.4, §9.4, §10.4, §11.3). The entries below cover the most behaviourally complex stories.

**US-06 — Orchestration Execution** *(High, 5 SP, Sprint 2)*
- **AC1:** `random.random` patched to 0.9 → `POST /execute/{id}` → HTTP 200, `"status": "completed"`, all tasks `DONE`
- **AC2:** `random.random` patched to 0.1 → first task `FAILED`, remaining tasks `PENDING`, response `"status": "failed"`
- **AC3:** Non-existent workflow id → HTTP 404

**US-07 — Choreography Execution** *(High, 8 SP, Sprint 2)*
- **AC1:** `random.random` = 0.9 → `POST /execute_choreo/{id}` → HTTP 200, `"mode": "choreography"`, all tasks `DONE`
- **AC2:** `random.random` = 0.1 → task[0] `FAILED`, task[1] `PENDING` (BUG-02 regression guard: no continuation event emitted on failure)
- **AC3:** Non-existent workflow id → HTTP 404

**US-18 — Conditional Transitions** *(High, 5 SP, Sprint 4)*
- **AC1:** Tasks A→B with `SUCCESS` edge → A succeeds → B executes, both `DONE` (`test_conditional_success_path`)
- **AC2:** Invalid `condition` value in `POST /workflows/{id}/transitions` → HTTP 422
- **AC3:** `GET /workflows/{id}/transitions` returns all edges with `from_task_id`, `to_task_id`, `condition`, `priority`
- **AC4:** `DELETE /transitions/{id}` → HTTP 200; edge absent from subsequent `GET`

**US-19 — Failure Recovery Paths** *(High, 3 SP, Sprint 4)*
- **AC1:** ChargeCard → RetryPayment (`FAILURE` edge); ChargeCard hard-fails → RetryPayment executes, reaches `DONE` (`test_failure_branch_execution`)
- **AC2:** Recovery task succeeds with no further outgoing edge → workflow run `completed`

**US-20 — Retry Loops** *(Medium, 3 SP, Sprint 4)*
- **AC1:** ChargeCard –FAILURE→ RetryPayment –SUCCESS→ ChargeCard –SUCCESS→ Ship; ChargeCard fails then succeeds on retry → all tasks `DONE`, run `completed` (`test_workflow_loop_retry`)
- **AC2:** Task loops on itself; `random.random` always fails → workflow `failed` after `MAX_LOOP_ITERATIONS` (`test_loop_limit_prevents_infinite_execution`)
- **AC3:** `MAX_LOOP_ITERATIONS = 10` in `app/engine/transitions.py` verified by `test_max_loop_iterations_constant_is_reasonable`

---

## 8. Sprint 1 — Foundation: Data Models and CRUD API

**Scrum flow:** Requirements → Product Backlog → Backlog Prioritisation → Sprint Planning → Sprint Backlog → Tasks → Implementation → Testing → Review → Retrospective

**Committed:** US-01, US-02, US-03, US-04, US-05 = 12 SP | **Completed:** 12 SP | **Duration:** 1 week

### 8.1 Sprint Goal

Deliver a fully functional data layer and REST API for user, workflow, and task management. At the end of this sprint the system must be able to create, retrieve, and delete all three entity types with correct HTTP status codes. No execution logic.

### 8.2 Sprint Planning — Task Decomposition

| Task | Story | Estimate (h) |
|---|---|---|
| T1-01 — Define `Base`, configure SQLite engine + FK PRAGMA | US-01..05 | 1 |
| T1-02 — Implement `User` ORM model with UNIQUE email | US-01 | 1 |
| T1-03 — Implement `Workflow`, `Task` models with constraints | US-02..03 | 2 |
| T1-04 — Implement `POST /users` + `GET /users` | US-01 | 1 |
| T1-05 — Implement `POST /workflows`, `GET /workflows`, `DELETE /workflows/{id}` | US-02, US-05 | 2 |
| T1-06 — Implement `POST /tasks`, `GET /tasks`, `DELETE /tasks/{id}` | US-03, US-04 | 3 |
| T1-07 — Implement duplicate-order rejection (HTTP 409) | US-03 | 1 |
| T1-08 — Implement auto-reorder after task deletion | US-04 | 1 |
| T1-09 — Implement `GET /workflows/{id}/status` | US-02 | 1 |
| T1-10 — Configure `app/main.py` lifespan + StaticFiles mount | US-01..05 | 1 |
| T1-11 — Set up `docker-compose.yml` | US-01..05 | 1 |

### 8.3 Sprint Backlog — Selected Items from Product Backlog

The Sprint Planning meeting selected the following items from the Product Backlog. Each Product Backlog Item (PBI) was decomposed into one or more Sprint Backlog Tasks (listed in §8.2).

| SBI-ID | PBI (Product Backlog) | Priority | SP | Sprint Tasks | NFRs Exercised |
|---|---|---|---|---|---|
| SBI-1-01 | US-01 — Register Account | High | 2 | T1-02, T1-04, T1-07 | NFR-07 (pinned deps) |
| SBI-1-02 | US-02 — Create Named Workflow | High | 2 | T1-05 | NFR-07 |
| SBI-1-03 | US-03 — Add Tasks with Order | High | 3 | T1-06, T1-07 | NFR-04 (unique order), NFR-07 |
| SBI-1-04 | US-04 — Delete Task + Reorder | Medium | 3 | T1-08 | NFR-07 |
| SBI-1-05 | US-05 — Delete Workflow | Medium | 2 | T1-05 | NFR-05 (FK cascade), NFR-07 |

**Total Sprint 1 Backlog:** 5 items, 12 SP | **NFRs targeted in this sprint:** NFR-04, NFR-05, NFR-07, NFR-08

### 8.4 User Stories and Acceptance Criteria

**US-01 — Register Account**
- **Given** a unique email and password **When** `POST /users` **Then** HTTP 200 + `{id, email}`
- **Given** duplicate email **When** `POST /users` **Then** HTTP 409 `"Email already exists"`

**US-03 — Add Tasks with Order**
- **Given** valid `workflow_id` and `order=1` **When** `POST /tasks` **Then** HTTP 200 + `status: "PENDING"`
- **Given** `order=1` already exists in same workflow **When** `POST /tasks` again **Then** HTTP 409

**US-04 — Delete Task with Auto-Reorder**
- **Given** tasks at orders [1,2,3], delete order=1 **Then** remaining tasks are at orders [1,2]
- **Given** non-existent task id **When** `DELETE /tasks/{id}` **Then** HTTP 404

**US-05 — Delete Workflow**
- **Given** non-existent workflow id **When** `DELETE /workflows/{id}` **Then** HTTP 404

### 8.5 Implementation Highlights

**`app/db.py` — FK enforcement:**
```python
@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")
```

**`app/models.py` — database-level task order uniqueness:**
```python
__table_args__ = (
    CheckConstraint("status IN ('PENDING','RUNNING','DONE','FAILED')", name="ck_task_status"),
    UniqueConstraint("workflow_id", "order", name="uq_task_workflow_order"),
)
```

**`app/main.py` — modern lifespan pattern (replacing deprecated `@app.on_event`):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(title="Workflow Automation", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
```

### 8.6 Testing

**Functional test results (written in Sprint 3, covering Sprint 1 functionality):**

Manual validation via FastAPI Swagger UI (`GET /docs`) performed during Sprint 1. Automated tests written in Sprint 3 and all pass:

| Test | FR | Result |
|---|---|---|
| `test_create_user_success` | FR-01 | PASS |
| `test_duplicate_email_returns_409` | FR-02 | PASS |
| `test_create_workflow` | FR-03 | PASS |
| `test_duplicate_task_order_returns_409` | FR-05 | PASS |
| `test_list_tasks_returns_only_existing` | FR-04 | PASS |
| `test_delete_task_reorders_remaining` | FR-06 | PASS |
| `test_delete_workflow_not_found` | FR-17 | PASS |
| `test_get_task_not_found` | FR-17 | PASS |
| `test_delete_task_not_found` | FR-17 | PASS |
| `test_workflow_status_summary` | FR-14 | PASS |
| `test_workflow_status_not_found` | FR-17 | PASS |

**NFR verification for Sprint 1 scope:**

| NFR-ID | Property | Verification | Result |
|---|---|---|---|
| NFR-04 | Duplicate task order rejected | `test_duplicate_task_order_returns_409` | PASS |
| NFR-05 | FK cascade on workflow delete | `test_delete_workflow_cascades_tasks` | PASS |
| NFR-07 | All dependencies pinned | `grep -v "==" requirements.txt` returns empty | PASS |
| NFR-08 | No deprecated APIs | `pytest tests/ -W error::DeprecationWarning` — zero warnings | PASS |

### 8.7 Sprint Review

**Stories completed:** 5/5 (100%) — 12 SP delivered. `GET /workflows/{id}/status` was added as an unplanned item (1 SP) after being identified as a dashboard prerequisite.

### 8.8 Sprint Retrospective

**Went well:** FastAPI + SQLAlchemy 2.0 typed API clean; `Mapped[]` columns provided excellent IDE support; sprint completed ahead of Day 5.

**Went poorly:** Zero tests written in Sprint 1. The `IntegrityError → HTTP 500` bug for duplicate emails survived until Sprint 3 precisely because there were no tests. Deferring tests is a process failure.

**Action for Sprint 2:** Write at least one smoke test per new HTTP endpoint within the sprint that introduces it.

### 8.9 Sprint 1 Burndown

```
Day:       1    2    3    4    5    6    7
Remaining: 12 → 10 → 8  → 6  → 4  → 2  → 0
Ideal:     12 → 10.3→8.6→6.9→5.1→3.4→1.7→0
```

---

## 9. Sprint 2 — Execution Engine: Orchestration and Choreography

**Committed:** US-06, US-07, US-08 = 16 SP | **Completed:** 16 SP | **Open defects at end:** 1 (BUG-02)

### 9.1 Sprint Goal

Implement both execution modes and the event infrastructure on top of the Sprint 1 data foundation. At sprint end: `POST /execute/{id}` and `POST /execute_choreo/{id}` fully functional; every execution persisted as a `WorkflowRun`; structured logs accessible via `GET /logs`.

### 9.2 Sprint Planning — Task Decomposition

| Task | Story | Estimate (h) |
|---|---|---|
| T2-01 — Implement `WorkflowRun` ORM model | US-06, US-07 | 1 |
| T2-02 — Implement `run_task()` with failure simulation and idempotency | US-06, US-07 | 3 |
| T2-03 — Implement `EventBus` pub/sub singleton | US-07 | 2 |
| T2-04 — Implement Kafka producer/consumer with ImportError fallback | US-11 | 3 |
| T2-05 — Implement `run_orchestrated_workflow()` | US-06 | 2 |
| T2-06 — Implement `run_choreographed_workflow()` with closure capture fix | US-07 | 4 |
| T2-07 — Wire `POST /execute/{id}` and `POST /execute_choreo/{id}` routes | US-06, US-07 | 1 |
| T2-08 — Implement `GET /workflow_runs/{id}` and `GET /logs` endpoints | US-08 | 1 |
| T2-09 — Manual testing and BUG-02 identification | US-07 | 1 |

### 9.3 Sprint Backlog — Selected Items from Product Backlog

Items pulled from the Product Backlog at Sprint 2 Planning. US-11 included as a partial story (Kafka infrastructure required for US-07 Kafka path).

| SBI-ID | PBI (Product Backlog) | Priority | SP | Sprint Tasks | NFRs Exercised |
|---|---|---|---|---|---|
| SBI-2-01 | US-06 — Orchestration Execution | High | 5 | T2-01, T2-02, T2-05, T2-07 | NFR-03 (audit record), NFR-08 |
| SBI-2-02 | US-07 — Choreography Execution | High | 8 | T2-03, T2-04, T2-06, T2-07, T2-09 | NFR-01 (Kafka fallback), NFR-02 (failure isolation) |
| SBI-2-03 | US-08 — Execution Logs | Medium | 3 | T2-08 | NFR-03 |

**Total Sprint 2 Backlog:** 3 items, 16 SP | **NFRs targeted in this sprint:** NFR-01, NFR-02, NFR-03, NFR-08

> **Product Backlog state after Sprint 2:** US-01–08 Done (28 SP delivered); US-09–17 still in backlog (31 SP remaining). Backlog refinement added BUG-02 regression guard to US-07 AC before Sprint 3.

### 9.4 User Stories and Acceptance Criteria

**US-06 — Orchestration Execution**
- **Given** `random.random` returns 0.9 (no failure) **When** `POST /execute/{id}` **Then** `status: "completed"`, all tasks `DONE`
- **Given** `random.random` returns 0.1 (forced failure) **When** `POST /execute/{id}` **Then** task[0] `FAILED`, task[1..n] `PENDING`
- **Given** workflow does not exist **When** `POST /execute/{id}` **Then** HTTP 404

**US-07 — Choreography Execution**
- **Given** `random.random` returns 0.9 **When** `POST /execute_choreo/{id}` **Then** `status: "completed"`, `mode: "choreography"`
- **Given** `random.random` returns 0.1 **When** `POST /execute_choreo/{id}` **Then** task[0] `FAILED`, task[1] stays `PENDING` (BUG-02 regression guard)

### 9.5 Implementation Highlights

**Orchestrator — central control loop (`app/engine/orchestrator.py:44-48`):**
```python
final_status = "COMPLETED"
for task in sorted(tasks, key=lambda t: t.order):
    ok = run_task(task, db, run_id=run_id, choreo_kafka=False, log_event=log_event)
    if not ok:
        final_status = "FAILED"
        break
```

**Choreographer — closure capture fix (`app/engine/choreography.py:59-80`):**
```python
for i in range(1, len(tasks)):
    def handler(
        prev_task_id: int,
        cur: Task = tasks[i],        # value captured at registration time
        expected: int = tasks[i-1].id,
        session: Session = db,
        ck: bool = use_kafka_choreo,
        rid: str = run_id,
    ) -> None:
        if prev_task_id == expected:
            run_task(cur, session, run_id=rid, choreo_kafka=ck, log_event=log_event)
    event_bus.subscribe(event_key, handler)
```

**BUG-02 root cause identified:** `run_task()` was emitting `task_completed` events unconditionally. A failed task's event triggered the downstream handler, executing subsequent tasks despite the failure.

### 9.6 Testing

**Note:** No automated tests written in Sprint 2 (process failure — action item from Sprint 1 Retrospective not followed). BUG-02 identified through manual Swagger UI testing.

**NFR verification attempted in Sprint 2:**

| NFR-ID | Property | Verification Method | Result |
|---|---|---|---|
| NFR-01 | Kafka fallback | Started server without Kafka broker; executed `POST /execute_choreo/{id}` — chain completed via in-memory EventBus | PASS (manual) |
| NFR-02 | Choreography halts on failure | Manual Swagger UI: patched workflow to always fail — **FAILED**: downstream task executed (BUG-02 identified) | FAIL ➡ Deferred |
| NFR-03 | Audit record created | `GET /workflow_runs/{id}` after execution — record present | PASS (manual) |
| NFR-08 | No deprecated API | Observed `DeprecationWarning` for `datetime.utcnow()` in console | FAIL ➡ Fixed Sprint 3 |

### 9.7 Sprint Review

| Deliverable | Status |
|---|---|
| `POST /execute/{id}` — orchestration | ✅ |
| `POST /execute_choreo/{id}` — choreography (success path) | ✅ |
| `GET /logs` + `GET /workflow_runs/{id}` | ✅ |
| BUG-02 — choreography executes downstream after failure | ⚠️ Identified; deferred |

**Stories completed:** 3/3 (100%) | **Open defects:** 1

### 9.8 Sprint Retrospective

**Went well:** `engine/` subdirectory separation produced independently readable modules. Per-`run_id` EventBus channel scoping identified early.

**Went poorly:** Zero tests written again (Sprint 1 action item not followed). BUG-02 introduced and not caught until Sprint 3. `event_bus.log_event` mutable singleton is not thread-safe.

**Action for Sprint 3:** Fix BUG-02 with regression test before Sprint closes; write full test coverage for both execution modes.

### 9.9 Sprint 2 Burndown

```
Day:       1    2    3    4    5    6    7
Remaining: 16 → 16 → 13 → 10 → 6  → 3  → 0
Ideal:     16 → 13.7→11.4→9.1→6.9→4.6→2.3→0
```

Day 1 velocity was 0 — choreography engine design required unplanned architectural whiteboard session.

---

## 10. Sprint 3 — Dashboard, Testing, Bug Fixes, and Documentation

**Committed:** US-09, US-10, US-11, US-12, US-13, US-14, US-15, US-16, US-17 = 31 SP | **Completed:** 31 SP | **Open defects at end:** 0

### 10.1 Sprint Goal

Deliver the browser dashboard, initial 21-test automated baseline, fix all open defects (BUG-02, BUG-04), resolve all code quality issues, produce the complete UML set, and finalise all Scrum artefacts. At sprint end: zero open defects, 21 passing tests covering all Sprint 1–3 requirements, full documentation set. The test suite was later extended to 27 tests during Sprint 4 graph-engine evolution — the 6 additional tests are documented in §11.

### 10.2 Sprint Planning — Task Decomposition

| Task | Story | Estimate (h) |
|---|---|---|
| T3-01 — Fix BUG-02: `if ok_task:` guard in `task_runner.py` | US-07 | 0.5 |
| T3-02 — Fix BUG-04: HTTP 404 on executing a missing workflow | US-14 | 0.5 |
| T3-03 — Extract `_UI_PAGE` → `app/static/index.html` | US-09 | 1 |
| T3-04 — Build Canvas graph + execution timeline + log panel | US-09, US-10 | 4 |
| T3-05 — Add Kafka + Zookeeper to `docker-compose.yml` | US-11 | 1 |
| T3-06 — Replace `datetime.utcnow()` with `datetime.now(UTC)` | US-12 | 0.5 |
| T3-07 — Add `UniqueConstraint` + FK PRAGMA to data layer | US-16, US-17 | 1 |
| T3-08 — Write 21 automated tests (Sprint 3 baseline) | US-12 | 5 |
| T3-09 — Create all 13 UML diagrams | US-15 | 4 |
| T3-10 — Write sprint retrospectives + acceptance criteria | US-15 | 2 |
| T3-11 — Rewrite `README.md`; write `docs/requirements.md` etc. | US-15 | 2 |

### 10.3 Sprint Backlog — Selected Items from Product Backlog

Items pulled from the Product Backlog at Sprint 3 Planning. US-16 and US-17 were added to the Product Backlog at this Sprint Planning as technical debt items surfaced by Sprint 1 Retrospective.

| SBI-ID | PBI (Product Backlog) | Priority | SP | Sprint Tasks | NFRs Exercised |
|---|---|---|---|---|---|
| SBI-3-01 | US-09 — Browser Dashboard | Medium | 5 | T3-03, T3-04 | NFR-09 |
| SBI-3-02 | US-10 — Workflow Graph | Low | 3 | T3-04 | NFR-09 |
| SBI-3-03 | US-11 — Kafka Optional | Low | 5 | T3-05 | NFR-01 |
| SBI-3-04 | US-12 — Automated Tests | High | 8 | T3-08 | All NFRs |
| SBI-3-05 | US-13 — Dup Email 409 | High | 1 | T3-02 | NFR-04 |
| SBI-3-06 | US-14 — Missing Workflow 404 | High | 1 | T3-02 | NFR-04 |
| SBI-3-07 | US-15 — UML Diagrams | Medium | 5 | T3-09, T3-10, T3-11 | — |
| SBI-3-08 | US-16 — DB UniqueConstraint | High | 2 | T3-07 | NFR-04 |
| SBI-3-09 | US-17 — FK PRAGMA | Medium | 1 | T3-07 | NFR-05 |

**Total Sprint 3 Backlog:** 9 items, 31 SP | **NFRs closed in this sprint:** ALL (NFR-01 through NFR-09)

> **Product Backlog state after Sprint 3:** All 17 User Stories Done (59 SP delivered). Backlog closed. Zero open defects.

### 10.4 User Stories and Acceptance Criteria

**US-12 — Automated Tests**
- **Given** `pytest tests/ -v` **Then** 21 passed (Sprint 3 baseline), 0 failed, 0 warnings; after Sprint 4: 27 passed
- **Given** `patch("random.random", return_value=0.1)` **Then** failure path deterministically triggered

**US-13 — Duplicate Email 409 (BUG-01 Fix)**
- **Given** email already exists **When** `POST /users` **Then** HTTP 409 (not 500)

**US-14 — Missing Workflow 404 (BUG-04 Fix)**
- **Given** workflow `id=99999` does not exist **When** `POST /execute/99999` **Then** HTTP 404, no WorkflowRun created

### 10.5 Implementation Highlights

**BUG-02 fix (`app/engine/task_runner.py:80-93`):**
```python
# BUG-02 FIX: only emit task_completed events when the task succeeded.
if ok_task:
    event_key = f"task_completed:{run_id}"
    if choreo_kafka:
        if not send_task_completed_kafka(task.id):
            event_bus.publish(event_key, task.id)
    else:
        if event_bus.subscribers.get(event_key):
            event_bus.publish(event_key, task.id)
else:
    _log("TASK_FAILED", f"EVENT: task_failed → {task.name} (downstream tasks will not run)")
```

**HTML separation — `routes.py` reduced from 1,209 to 315 lines:**
```python
@router.get("/ui")
def workflow_ui():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))
```

### 10.6 Testing

**Result:** `27 passed` — zero failures, zero deprecation warnings (21 from Sprints 1–3, 6 added in Sprint 4).

**NFR verification — Sprint 3 (all NFRs closed):**

| NFR-ID | Property | Test / Verification | Result |
|---|---|---|---|
| NFR-01 | Kafka unavailability | All 9 `test_execution.py` tests pass without Kafka broker | PASS |
| NFR-02 | Choreography halts on failure | `test_choreography_stops_on_failure` — BUG-02 regression guard | PASS |
| NFR-03 | Audit record per execution | `test_workflow_run_history_recorded` | PASS |
| NFR-04 | Duplicate task order rejected | `test_duplicate_task_order_returns_409` | PASS |
| NFR-05 | FK cascade on delete | `test_delete_workflow_cascades_tasks` | PASS |
| NFR-06 | Single-command startup | `docker-compose up` → HTTP 200 within 60 s | PASS |
| NFR-07 | All deps pinned | `grep -v "==" requirements.txt` → empty | PASS |
| NFR-08 | No deprecated APIs | `pytest tests/ -W error::DeprecationWarning` → 27 passed | PASS |
| NFR-09 | Isolated test suite | `pytest tests/ -v` on clean machine → 27 passed | PASS |

### 10.7 Sprint Review

| Story | SP | Status |
|---|---|---|
| US-09 — Dashboard timeline | 5 | ✅ |
| US-10 — Workflow graph | 3 | ✅ |
| US-11 — Kafka optional | 5 | ✅ |
| US-12 — 21 tests (Sprint 3 baseline; +6 added in Sprint 4 → 27 total) | 8 | ✅ |
| US-13 — Dup email 409 | 1 | ✅ |
| US-14 — Missing workflow 404 | 1 | ✅ |
| US-15 — UML documentation | 5 | ✅ |
| US-16 — DB UniqueConstraint | 2 | ✅ |
| US-17 — FK PRAGMA | 1 | ✅ |

**Stories completed:** 9/9 (100%) | **Open defects:** 0

### 10.8 Sprint Retrospective

**Went well:** BUG-02 minimal fix confirmed by regression test. `routes.py` 74% reduction resolved worst architectural violation. `conftest.py` DI pattern is clean and future-proof.

**Went poorly:** Burndown data reconstructed rather than tracked live. Testing deferred from all prior sprints — this is the project's most significant process failure (see Section 22).

**Overall lesson:** Architecture decisions (static file vs embedded string, tests vs no tests) are cheapest when made in Sprint 1. Retroactively fixing them costs proportionally more.

### 10.9 Sprint 3 Burndown

```
Day:       1    2    3    4    5    6    7
Remaining: 31 → 26 → 21 → 16 → 10 → 5  → 0
Ideal:     31 → 26.6→22.3→17.9→13.6→9.3→4.9→0
```

---

## 11. Sprint 4 — Evolution Sprint: Graph-Based Workflow Engine

**Committed:** US-18, US-19, US-20 = 11 SP | **Completed:** 11 SP | **Trigger:** Stakeholder prototype validation

> **On the Sprint 4 designation:** This sprint represents the evolution phase of the evolutionary prototyping lifecycle, not a fourth week of planned development. It was initiated after stakeholder evaluation of the Sprint 3 prototype identified a fundamental architectural gap (§1.3). Labelling it "Sprint 4" places it within the documented Scrum process rather than treating the evolution as an untracked appendix.

### 11.1 Sprint Goal

Extend the workflow engine to support graph-based execution: tasks as nodes, `WorkflowTransition` edges with conditional routing, `TransitionResolver` for dynamic next-node selection, and loop protection. Both execution modes (orchestration and choreography) must use the same resolver. All pre-existing tests must continue to pass (backward compatibility).

### 11.2 Sprint Planning — Task Decomposition

| Task | Story | Estimate (h) |
|---|---|---|
| T4-01 — Analyse stakeholder feedback; identify gap between linear model and business workflow semantics | US-18–20 | 1 |
| T4-02 — Design `WorkflowTransition` ORM model (`from_task_id`, `to_task_id`, `condition`, `priority`) | US-18 | 1 |
| T4-03 — Implement `transitions.py`: `get_start_task()`, `resolve_next_task()`, `workflow_has_transitions()`, `MAX_LOOP_ITERATIONS` | US-18–20 | 3 |
| T4-04 — Implement `WorkflowTransition` CRUD API (`POST`, `GET`, `DELETE /transitions`) | US-18 | 2 |
| T4-05 — Extend orchestrator with `_run_graph()` graph state machine; preserve `_run_sequential()` as fallback | US-18–20 | 2 |
| T4-06 — Extend choreography with `_run_choreography_graph()` reactive Observer chain; add `TaskCompletedEvent` dataclass | US-18–20 | 3 |
| T4-07 — Add `TaskExecution` ORM model and `GET /workflow_runs/{run_id}/task_executions` endpoint | US-18 | 2 |
| T4-08 — Write `tests/test_workflow_graph.py`: 6 tests covering branching, FAILURE path, retry loop, loop limit, choreography graph | US-18–20 | 3 |
| T4-09 — Add seed scripts for demo workflows demonstrating graph execution | US-18–20 | 1 |

### 11.3 Sprint Backlog — Selected Items

| SBI-ID | PBI | Priority | SP | Sprint Tasks | NFRs |
|---|---|---|---|---|---|
| SBI-4-01 | US-18 — Conditional Transitions | High | 5 | T4-02, T4-03, T4-04, T4-07 | NFR-04 (data integrity) |
| SBI-4-02 | US-19 — Failure Recovery Paths | High | 3 | T4-05, T4-06, T4-08 | NFR-02 (failure isolation) |
| SBI-4-03 | US-20 — Retry Loops + Loop Protection | Medium | 3 | T4-03 (`MAX_LOOP_ITERATIONS`), T4-05, T4-06, T4-08 | NFR-09 (testability) |

**Total Sprint 4 Backlog:** 3 items, 11 SP

### 11.4 Implementation Highlights

**`WorkflowTransition` ORM model** (`app/models.py`):
```python
class WorkflowTransition(Base):
    """A directed edge of the workflow graph: from_task --condition--> to_task."""
    __tablename__ = "workflow_transitions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    from_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    to_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    condition: Mapped[str] = mapped_column(String, nullable=False, default="ALWAYS")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

**`TransitionResolver` — graph lookup** (`app/engine/transitions.py`):
```python
def resolve_next_task(db, workflow_id, from_task_id, result) -> Task | None:
    transitions = db.scalars(select(WorkflowTransition).where(
        WorkflowTransition.workflow_id == workflow_id,
        WorkflowTransition.from_task_id == from_task_id,
    )).all()
    matching = [t for t in transitions if t.condition == result]
    if not matching:
        matching = [t for t in transitions if t.condition == CONDITION_ALWAYS]
    if not matching:
        return None
    return db.get(Task, min(matching, key=lambda t: t.priority).to_task_id)
```

**Orchestration graph state machine** (`app/engine/orchestrator.py` — `_run_graph()`):
```python
current = get_start_task(db, workflow_id)
while current is not None:
    visited_counter[current.id] += 1
    if visited_counter[current.id] > MAX_LOOP_ITERATIONS:
        return "FAILED"   # loop protection
    ok = run_task(current, db, run_id=run_id, choreo_kafka=False, log_event=log_event,
                  task_execution=task_exec_map.get(current.id))
    result = RESULT_SUCCESS if ok else RESULT_FAILURE
    next_task = resolve_next_task(db, workflow_id, current.id, result)
    if next_task is None:
        return "FAILED" if result == RESULT_FAILURE else "COMPLETED"
    current = next_task
return "COMPLETED"
```

**Choreography reactive chain** (`app/engine/choreography.py` — `_run_choreography_graph()`):
```python
def handler(event) -> None:
    next_task = resolve_next_task(db, workflow_id, event.task_id, event.result)
    if next_task is None:
        if event.result == RESULT_FAILURE:
            status_box["value"] = "FAILED"
        return
    advance(next_task)   # which calls run_task() → publishes task_result → re-enters handler

event_bus.subscribe(result_key, handler)
advance(start)           # kick off — no central loop after this point
```

### 11.5 Testing

**New tests in `tests/test_workflow_graph.py`** (6 tests, all passing):

| Test | FR | Technique |
|---|---|---|
| `test_conditional_success_path` | FR-18 | `patch random.random=0.5` (always success) |
| `test_failure_branch_execution` | FR-19 | `patch side_effect=[0.1, 0.1, 0.5]` (charge hard-fails, retry succeeds) |
| `test_workflow_loop_retry` | FR-20 | `patch side_effect=[0.1, 0.1, 0.5, 0.5, 0.5]` (charge→retry→charge→ship) |
| `test_loop_limit_prevents_infinite_execution` | FR-21 | `patch random.random=0.1` (infinite hard-fail) |
| `test_choreography_transition_based_execution` | FR-18 | `patch random.random=0.5`, choreography mode |
| `test_max_loop_iterations_constant_is_reasonable` | FR-21 | Sanity check `MAX_LOOP_ITERATIONS == 10` |

**Combined test suite after Sprint 4:** 21 (Sprints 1–3) + 6 (Sprint 4) = **27 tests, all passing**.

### 11.6 Sprint Review

| Deliverable | Status |
|---|---|
| `WorkflowTransition` ORM + `workflow_transitions` table | ✅ |
| `TransitionResolver` (`transitions.py`) | ✅ |
| `POST/GET/DELETE /transitions` endpoints | ✅ |
| `_run_graph()` orchestration state machine | ✅ |
| `_run_choreography_graph()` reactive chain | ✅ |
| `TaskExecution` ORM + `task_executions` table | ✅ |
| 6 new graph tests passing; 21 legacy tests still passing | ✅ |
| Backward compatibility: linear workflows unaffected | ✅ |

**Stories completed:** 3/3 (100%) | **Open defects:** 0

### 11.7 Sprint Retrospective

**Went well:** The `workflow_has_transitions()` detection function kept the backward-compatibility fallback clean — existing tests required zero modifications. Sharing the `TransitionResolver` between both engines meant branching and loop semantics are identical regardless of execution mode.

**Went poorly:** The `TaskCompletedEvent`-based `task_result:{run_id}` channel and the legacy `task_completed:{run_id}` channel now coexist in the same codebase. This is a technical debt item — a future refactoring should unify the two channels. Additionally, the Kafka transport path applies only to the legacy sequential choreography; the graph choreography uses the in-memory `EventBus` abstraction exclusively.

**Action:** Document the Kafka scope limitation explicitly in the Limitations section. Document both channels in the event architecture description.

### 11.8 Sprint 4 Burndown

```
Day:       1    2    3    4    5    6    7
Remaining: 11 → 9  → 7  → 5  → 3  → 1  → 0
Ideal:     11 → 9.4→7.9→6.4→4.9→3.4→1.9→0
```

---

## 12. Backlog Refinement

Backlog refinement (grooming) occurred at the end of each sprint. The following table documents how the backlog evolved.

| Event | Change | Rationale |
|---|---|---|
| **Pre-Sprint 1** | US-01–05 created and estimated (12 SP) | Initial backlog seeded from UR-01, UR-02, UR-08 |
| **Pre-Sprint 2** | US-06–08 added and estimated; US-11 created as placeholder (5 SP) | Sprint 2 scope derived from UR-03, UR-04, UR-09 |
| **Sprint 2 Day 7** | US-07 acceptance criteria updated to include BUG-02 regression guard | Manual testing discovered BUG-02; AC strengthened before Sprint 3 |
| **Pre-Sprint 3** | US-09–15 added (28 SP); US-16, US-17 added (3 SP) as technical debt items from Sprint 1 retrospective | Dashboard, testing, and documentation requirements formalised; DB integrity gaps identified |
| **Sprint 3 Day 2** | US-12 SP estimate raised from 5 → 8 | Complexity of achieving deterministic test coverage for probabilistic code higher than estimated |
| **Post-Sprint 3 (Stakeholder Validation)** | UR-10, UR-11 discovered; US-18–20 created (11 SP); FR-18–FR-21 added to requirements | Prototype evaluation revealed that linear execution model did not support real workflow semantics — evolutionary prototype validation step (§1.3) |

**Key refinement insight:** US-16 (database-level UniqueConstraint) and US-17 (FK PRAGMA) were not in the original backlog — identified as technical debt via retrospective. US-18–20 (graph engine) were not in the original backlog — identified via stakeholder prototype validation. Both are examples of the backlog evolving as understanding deepens, which is exactly how Scrum expects requirements to emerge.

### 12.1 Velocity Tracking

Velocity measures the number of story points completed per sprint. It serves as the primary input to sprint planning for subsequent sprints.

| Sprint | Committed SP | Completed SP | Velocity | Notes |
|---|---|---|---|---|
| Sprint 1 | 12 | 12 | **12** | Baseline sprint; CRUD foundation only; no tests delivered (DoD violation) |
| Sprint 2 | 16 | 16 | **16** | Execution engines delivered; BUG-02 discovered at review; no tests delivered (DoD violation) |
| Sprint 3 | 31 | 31 | **31** | All deferred test work, bug fixes, dashboard, and documentation; 94% above Sprint 2 velocity |
| Sprint 4 | 11 | 11 | **11** | Evolution sprint triggered by stakeholder feedback; graph engine, 6 new tests, backward compatibility |
| **Average** | **18** | **18** | **18** | Single-developer team; Sprint 3 crunch accepted consciously; Sprint 4 focused evolution |

**Velocity analysis:**
- The Sprint 1→2 increase (+33%) is acceptable and reflects growing understanding of the codebase.
- The Sprint 2→3 increase (+94%) is anomalously high and reflects scope that accumulated across both prior sprints (deferred testing, dashboard, documentation). In a production Scrum team, Sprint 3 would have been split into two sprints.
- Sprint 4 velocity (11 SP) is lower than the delivery average, consistent with a focused architectural evolution sprint rather than a broad feature sprint. The full graph engine — model, resolver, two updated execution engines, 6 tests — was delivered in one sprint.

---

## 13. Requirements Traceability Matrix

The matrix below shows the complete traceability chain from User Requirements through to automated test coverage.

| UR-ID | FR-ID | User Story | Sprint | Tasks | Test |
|---|---|---|---|---|---|
| UR-01 | FR-01 | US-01 | 1 | T1-02, T1-04 | `test_create_user_success` |
| UR-01 | FR-02 | US-01 | 1 | T1-04, T1-07 | `test_duplicate_email_returns_409` |
| UR-02 | FR-03 | US-02 | 1 | T1-05 | `test_create_workflow` |
| UR-02 | FR-04 | US-03 | 1 | T1-06 | `test_list_tasks_returns_only_existing` |
| UR-08 | FR-05 | US-03 | 1 | T1-07 | `test_duplicate_task_order_returns_409` |
| UR-02 | FR-06 | US-04 | 1 | T1-08 | `test_delete_task_reorders_remaining` |
| UR-02 | FR-07 | US-05 | 1 | T1-05 | `test_delete_workflow_cascades_tasks` |
| UR-03 | FR-08 | US-06 | 2 | T2-05, T2-07 | `test_orchestrated_workflow_success` |
| UR-04 | FR-09 | US-06 | 2 | T2-05, T2-07 | `test_orchestrated_workflow_halts_on_failure` |
| UR-03, UR-09 | FR-10 | US-07 | 2 | T2-06, T2-07 | `test_choreography_success` |
| UR-04 | FR-11 | US-07 | 2→3 | T2-06, T3-01 | `test_choreography_stops_on_failure` |
| UR-03 | FR-12 | US-14 | 3 | T3-02 | `test_execute_nonexistent_workflow_returns_404` |
| UR-06 | FR-13 | US-08 | 2 | T2-01, T2-08 | `test_workflow_run_history_recorded` |
| UR-05 | FR-14 | US-08 | 2 | T2-08 | Manual |
| UR-05 | FR-15 | US-09, US-10 | 3 | T3-03, T3-04 | Manual |
| UR-03 | FR-16 | US-06, US-07 | 2 | T2-05, T2-06 | `test_execute_empty_workflow_completes` |
| UR-08 | FR-17 | US-04, US-05 | 1, 3 | T1-06, T3-02 | `test_delete_workflow_not_found`, `test_get_task_not_found` |
| UR-07 | NFR-01 | US-11 | 3 | T2-04, T3-05 | All 9 execution tests (run without Kafka) |
| UR-08 | NFR-04 | US-16 | 3 | T3-07 | `test_duplicate_task_order_returns_409` |
| UR-04 | NFR-02 | US-07 | 2 | T2-06, T3-01 | `test_choreography_stops_on_failure` |
| UR-06 | NFR-03 | US-08 | 2 | T2-01, T2-08 | `test_workflow_run_history_recorded` |
| UR-02 | NFR-05 | US-05 | 1 | T1-05 | `test_delete_workflow_cascades_tasks` |
| C-06 | NFR-06 | US-11 | 3 | T3-06 | Manual: `docker-compose up` → `curl localhost:8000/` returns 200 within 60 s |
| C-07 | NFR-07 | US-17 | 3 | T3-08 | `grep -v "==" requirements.txt` → empty output |
| C-01 | NFR-08 | US-12 | 3 | T3-05 | `pytest tests/ -W error::DeprecationWarning` → 0 warnings, 27 passed |
| C-09 | NFR-09 | US-12 | 3 | T3-05 | `pytest tests/ -v` on clean machine (only `pip install -r requirements.txt`) → 27 passed |
| UR-10 | FR-18 | US-18 | 4 | T4-02, T4-03, T4-04 | `test_conditional_success_path` |
| UR-10 | FR-19 | US-19 | 4 | T4-05, T4-06 | `test_failure_branch_execution` |
| UR-11 | FR-20 | US-20 | 4 | T4-03, T4-05, T4-06 | `test_workflow_loop_retry` |
| UR-11 | FR-21 | US-20 | 4 | T4-03 (`MAX_LOOP_ITERATIONS`), T4-08 | `test_loop_limit_prevents_infinite_execution` |
| UR-10, UR-11 | FR-18 (choreo) | US-18 | 4 | T4-06, T4-08 | `test_choreography_transition_based_execution` |

---

## 14. System Architecture

### 13.1 Architectural Style

The system is a **modular monolith** — all components execute within a single `uvicorn` process sharing one SQLite database file and one `EventBus` singleton. It is not a microservices system. The modular monolith was the correct architectural choice for an academic prototype: it avoids network serialisation overhead, enables in-process testing with FastAPI `TestClient`, and deploys with a single `docker-compose up` command.

### 13.2 Package Diagram

> **Figure 1 — UML Package Diagram.** Physical module organisation of the project. Shows packages, key elements, and `<<use>>` dependencies between modules.

```plantuml
@startuml
skinparam packageStyle rectangle
skinparam shadowing false
skinparam defaultFontName Arial
skinparam classBackgroundColor #FAFAFA
skinparam classBorderColor #999999
skinparam classFontSize 11

package "app" {
  class "main" <<module>> {
    + lifespan()
    + create_app() : FastAPI
    + StaticFiles mount
    + GET / : health check
  }
  class "db" <<module>> {
    + get_db() : Session
    + engine : Engine
    + Base : DeclarativeBase
  }
  class "models" <<module>> {
    + User
    + Workflow
    + WorkflowRun
    + Task
    + WorkflowTransition
    + TaskExecution
  }
  class "routes" <<module>> {
    + 20 REST endpoints
    + GET /ui : FileResponse
    + POST/GET/DELETE /transitions
  }

  package "engine" {
    class "transitions" <<module>> {
      + get_start_task() : Task
      + resolve_next_task() : Task
      + workflow_has_transitions() : bool
      + MAX_LOOP_ITERATIONS : int
    }
    class "events" <<module>> {
      + EventBus
      + TaskCompletedEvent
      + send_task_completed_kafka()
      + create_choreo_consumer()
    }
    class "task_runner" <<module>> {
      + run_task() : bool
    }
    class "orchestrator" <<module>> {
      + run_orchestrated_workflow()
      + _run_graph()
      + _run_sequential()
    }
    class "choreography" <<module>> {
      + run_choreographed_workflow()
      + _run_choreography_graph()
    }
  }

  package "static" {
    class "index.html" <<file>> {
      + Browser dashboard
      + Canvas graph renderer
      + 1 s polling loop
    }
  }
}

package "tests" {
  class "conftest" <<module>> {
    + client : TestClient
    + StaticPool in-memory DB
    + dependency_overrides
  }
  class "test_users" <<module>> {
    2 test functions
  }
  class "test_workflows" <<module>> {
    10 test functions
  }
  class "test_execution" <<module>> {
    9 test functions
  }
  class "test_workflow_graph" <<module>> {
    6 test functions (graph engine)
  }
}

package "docs" {
  class "REPORT.md" <<document>>
  class "product_backlog.md" <<document>>
  class "definition_of_done.md" <<document>>
}

"main" ..> "db" : <<use>>
"main" ..> "models" : <<use>>
"main" ..> "routes" : <<use>>
"routes" ..> "orchestrator" : <<use>>
"routes" ..> "choreography" : <<use>>
"routes" ..> "models" : <<use>>
"orchestrator" ..> "task_runner" : <<use>>
"orchestrator" ..> "transitions" : <<use>>
"choreography" ..> "task_runner" : <<use>>
"choreography" ..> "transitions" : <<use>>
"choreography" ..> "events" : <<use>>
"task_runner" ..> "events" : <<use>>
"task_runner" ..> "models" : <<use>>
"orchestrator" ..> "models" : <<use>>
"transitions" ..> "models" : <<use>>
"db" ..> "models" : <<use>>
@enduml
```

### 13.3 Component Diagram

> **Figure 2 — UML Component Diagram.** Runtime component boundaries and interfaces showing provided/required interfaces and `<<use>>` / `<<fallback>>` dependencies.

```plantuml
@startuml
skinparam componentStyle uml2
skinparam shadowing false
skinparam defaultFontName Arial

component "Browser\n(Dashboard)" as Browser
component "REST Client\n(curl / Postman)" as RestClient

package "API Layer  (routes.py)" {
  component "User Endpoints\nPOST /users  GET /users" as UserEP
  component "Workflow Endpoints\nPOST /workflows  GET /workflows\nDELETE /workflows/{id}\nGET /workflows/{id}/status" as WfEP
  component "Task Endpoints\nPOST /tasks  GET /tasks\nGET /tasks/{id}  DELETE /tasks/{id}" as TaskEP
  component "Execution Endpoints\nPOST /execute/{id}\nPOST /execute_choreo/{id}" as ExecEP
  component "Log Endpoints\nGET /logs\nGET /workflow_runs/{id}" as LogEP
  component "Dashboard\nGET /ui" as UIEP
}

package "Execution Engine  (engine/)" {
  component "Orchestrator\norchestrator.py\n_run_graph() / _run_sequential()" as Orch
  component "Choreographer\nchoreography.py\n_run_choreography_graph()" as Choreo
  component "TransitionResolver\ntransitions.py\nresolve_next_task()" as Resolver
  component "TaskRunner\ntask_runner.py" as TR
  component "EventBus\nevents.py\ntask_result:{run_id}" as EB
}

package "Data Layer" {
  component "SQLAlchemy ORM\nmodels.py" as ORM
  component "Session Factory\ndb.py" as SF
  database "workflow.db\n(SQLite)" as DB
}

package "Event Transport" {
  component "In-Memory EventBus\n(always available)" as InMem
  component "Apache Kafka\n(optional)" as Kafka
}

Browser --> UIEP : HTTP GET /ui
RestClient --> UserEP : HTTP
RestClient --> WfEP : HTTP
RestClient --> TaskEP : HTTP
RestClient --> ExecEP : HTTP
RestClient --> LogEP : HTTP

ExecEP --> Orch : run_orchestrated_workflow()
ExecEP --> Choreo : run_choreographed_workflow()
Orch --> TR : run_task()
Orch --> Resolver : resolve_next_task()
Choreo --> TR : run_task()
Choreo --> Resolver : resolve_next_task()
Choreo --> EB : subscribe() / publish()
TR --> EB : publish(task_result) on any outcome
TR --> ORM : UPDATE task / TaskExecution status
UserEP --> ORM
WfEP --> ORM
TaskEP --> ORM
LogEP --> ORM
ORM --> SF : session
SF --> DB : SQL

EB --> InMem : synchronous dispatch
EB ..> Kafka : <<fallback>>
@enduml
```

### 13.4 Deployment Diagram

> **Figure 3 — UML Deployment Diagram.** `docker-compose.yml` topology showing nodes, deployed artifacts, and communication paths.

```plantuml
@startuml
skinparam shadowing false
skinparam defaultFontName Arial
skinparam nodeBackgroundColor #FFFDE7
skinparam databaseBackgroundColor #E8F5E9

node "Docker Host" as DockerHost {

  node "app\n<<container>>\nport 8000" as AppSvc {
    artifact "uvicorn app.main:app\n<<process>>" as Uvicorn
    artifact "FastAPI Application\n<<executable>>" as FastAPI
    database "workflow.db\n<<SQLite file>>" as SQLiteDB
    Uvicorn --> FastAPI : starts
    FastAPI ..> SQLiteDB : reads / writes
  }

  node "zookeeper\n<<container>>\nport 2181" as ZKSvc {
    artifact "Bitnami ZooKeeper 3.9\n<<process>>" as ZK
  }

  node "kafka\n<<container>>\nport 9092" as KafkaSvc {
    artifact "Bitnami Kafka 3.7\n<<process>>" as KafkaBroker
    KafkaBroker --> ZK : coordination
  }

  AppSvc ..> KafkaSvc : <<depends on>> (optional)
}

node "Client Machine" as ClientNode {
  artifact "Browser\nlocalhost:8000/ui" as BrowserApp
  artifact "curl / Postman\nlocalhost:8000/*" as CLIApp
}

BrowserApp --> AppSvc : HTTP/1.1
CLIApp --> AppSvc : HTTP/1.1
@enduml
```

### 13.5 The 4+1 Architectural View Model

The diagrams already embedded in this report correspond closely to Kruchten's **4+1 architectural view model**, which describes a system through four concurrent views unified by a set of scenarios. No new diagrams are introduced here; this subsection only re-frames the existing ones to show that the architecture is documented from every standard viewpoint.

- **Logical view** (functionality offered to users) — the domain model captured by the Class Diagram (Fig 5) and ER Diagram (Fig 6), defining the `User`, `Workflow`, `Task`, and `WorkflowRun` entities and their relationships as implemented in `app/models.py`.
- **Process view** (runtime behaviour and concurrency) — how execution actually unfolds: the two Sequence Diagrams (Figs 9–10), the Task and WorkflowRun State Machines (Figs 7–8), and the three Activity Diagrams (Figs 11–13), which together cover `run_task()`, the orchestration loop, and the reactive choreography/`EventBus` chain.
- **Development view** (static module organisation) — the Package Diagram (Fig 1) and Component Diagram (Fig 2), showing the `app` and `engine` modules and their `<<use>>` / `<<fallback>>` dependencies.
- **Physical view** (deployment topology) — the Deployment Diagram (Fig 3), mapping the `docker-compose.yml` nodes (application, Kafka, Zookeeper, client) onto their runtime artifacts.
- **+1 Scenarios** (the use cases that tie the views together) — the Use Case Diagram (Fig 4) and, concretely, the 27 automated integration tests (§19), each of which exercises one externally observable scenario end-to-end.

Framed this way, the existing documentation already satisfies all five 4+1 views, while the modular-monolith style (§13.1) deliberately keeps the development and physical views simple.

### 13.6 Graph-Based Workflow Engine Architecture

Following stakeholder prototype validation (§1.3), the execution engine was evolved to include a new architectural component: the **TransitionResolver**. It sits between the two execution styles and the workflow graph data, and is the single place where "what task runs next" is decided.

```
API Layer
    |
Workflow Engine
    |
+----------------+
|                |
Orchestrator     Choreography Engine
|                |
TransitionResolver
        |
WorkflowTransition Model
```

**TransitionResolver responsibilities** (`app/engine/transitions.py`):

- Evaluates the task execution result (`SUCCESS` or `FAILURE`) returned by Task Runner.
- Reads the `WorkflowTransition` rules for the current task (`from_task_id`, `condition`, `priority`).
- Selects the next workflow node (`to_task_id`) whose edge condition matches the result, falling back to an `ALWAYS` edge, or returning nothing if the branch has ended.
- Enables **branching** (multiple outgoing edges per task, e.g. a decision gateway) and **loops** (an edge pointing back to an earlier task, e.g. a retry), bounded by `MAX_LOOP_ITERATIONS`.

Both execution styles now consult the TransitionResolver instead of a fixed task list:

- **Orchestration** (`app/engine/orchestrator.py`): the central engine invokes `TransitionResolver.resolve_next_task()` after each task execution and moves its own cursor to the returned node, repeating until no edge matches.
- **Choreography** (`app/engine/choreography.py`): task completion events (`task_result:{run_id}`) trigger transition resolution — the event handler calls the TransitionResolver and, if a matching edge exists, directly executes the next task, which in turn emits its own event. There is still no central loop; only the *decision* of which task fires next has moved from a fixed predecessor id to the TransitionResolver.

The old `execution_order` mechanism (§15.8) is not removed — it remains as a **compatibility fallback** for simple linear workflows that define no `WorkflowTransition` rows, so pre-existing workflows continue to run unchanged.

---

## 15. UML Modeling — Complete Embedded Diagram Set

This section presents all 15 UML diagrams for the system. Figures 1–4 are structural diagrams (Package, Component, Deployment, Use Case). Figures 5–10 cover the data model, state machines, and sequence interactions. Figures 11–15 document the execution algorithms, with Figures 14–15 covering the graph-based execution path introduced in Sprint 4.


### 14.1 Use Case Diagram

> **Figure 4 — UML Use Case Diagram.** External actor and all ten user-goal-oriented use cases within the WMS system boundary. Uses proper UML use case oval notation and actor stick figure. All use cases represent externally observable functionality from the user's perspective.

```plantuml
@startuml
left to right direction
skinparam actorStyle awesome
skinparam shadowing false
skinparam defaultFontName Arial
skinparam usecaseBackgroundColor #FFF9C4
skinparam usecaseBorderColor #F9A825

actor "User" as User

rectangle "WMS System Boundary" {
  usecase "Register Account" as UC1
  usecase "Create Workflow" as UC2
  usecase "Add Task to Workflow" as UC3
  usecase "Delete Task" as UC4
  usecase "Delete Workflow" as UC5
  usecase "Define Conditional\nTransitions (Graph Edges)" as UC6
  usecase "Execute Workflow\n(Orchestration Mode)" as UC7
  usecase "Execute Workflow\n(Choreography Mode)" as UC8
  usecase "View Execution Logs" as UC9
  usecase "View Workflow Status" as UC10
  usecase "View Dashboard" as UC11
}

User --> UC1
User --> UC2
User --> UC3
User --> UC4
User --> UC5
User --> UC6
User --> UC7
User --> UC8
User --> UC9
User --> UC10
User --> UC11
@enduml
```

### 14.2 Class Diagram

> **Figure 5 — Class Diagram.** ORM entities and engine classes with relationships and multiplicities. `Task` instances are the nodes of the workflow graph; `WorkflowTransition` instances are the directed, conditional edges connecting them (see §15.9).

```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str password
    }
    class Workflow {
        +int id
        +str name
        +int user_id
    }
    class WorkflowRun {
        +str id
        +int workflow_id
        +str mode
        +str status
        +datetime started_at
        +datetime finished_at
    }
    class Task {
        +int id
        +str name
        +int workflow_id
        +int order
        +str status
    }
    class WorkflowTransition {
        +int id
        +int workflow_id
        +int from_task_id
        +int to_task_id
        +str condition
        +int priority
    }
    class TaskExecution {
        +int id
        +str run_id
        +int task_id
        +str status
        +int attempt
        +datetime started_at
        +datetime finished_at
    }
    note for Task "Node in the workflow graph\n(order field kept for backward compat)"
    note for WorkflowTransition "Directed edge between two Task nodes\ncondition: SUCCESS / FAILURE / ALWAYS\npriority: resolves multiple matching edges"
    note for TaskExecution "Runtime state per task per run\n(separates instance from definition)"
    class TransitionResolver {
        +get_start_task(db, workflow_id) Task
        +resolve_next_task(db, workflow_id, from_task_id, result) Task
        +workflow_has_transitions(db, workflow_id) bool
        +MAX_LOOP_ITERATIONS int
    }
    class EventBus {
        -dict subscribers
        -callable log_event
        +subscribe(event_name, handler) None
        +publish(event_name, data) None
    }
    class TaskCompletedEvent {
        +int task_id
        +int workflow_id
        +str result
        +object output
    }
    class TaskRunner {
        +run_task(task, db, run_id, choreo_kafka, log_event) bool
    }
    class Orchestrator {
        +run_orchestrated_workflow(workflow_id, db, log_event) dict
        -_run_graph(workflow_id, db, ...) str
        -_run_sequential(workflow_id, db, ...) str
    }
    class Choreographer {
        +run_choreographed_workflow(workflow_id, db, log_event) dict
        -_run_choreography_graph(workflow_id, db, ...) str
    }

    User "1" --> "0..*" Workflow : owns
    Workflow "1" --> "0..*" Task : contains
    Workflow "1" --> "0..*" WorkflowRun : records
    Workflow "1" --> "0..*" WorkflowTransition : defines graph edges
    WorkflowTransition "0..*" --> "1" Task : from_task
    WorkflowTransition "0..*" --> "1" Task : to_task
    WorkflowRun "1" --> "0..*" TaskExecution : tracks per-task state
    Task "1" --> "0..*" TaskExecution : instantiated per run
    Orchestrator ..> TaskRunner : uses
    Orchestrator ..> TransitionResolver : resolves next node
    Choreographer ..> TaskRunner : uses
    Choreographer ..> TransitionResolver : resolves next node
    Choreographer ..> EventBus : subscribes / publishes
    TaskRunner ..> EventBus : publishes TaskCompletedEvent
    TaskRunner ..> TaskExecution : updates status
```

### 14.3 Entity-Relationship Diagram

> **Figure 6 — ER Diagram.** Database schema with cardinality constraints.

```mermaid
erDiagram
    USER {
        int id PK
        string email UK
        string password
    }
    WORKFLOW {
        int id PK
        string name
        int user_id FK
    }
    WORKFLOW_RUN {
        string id PK
        int workflow_id FK
        string mode
        string status
        datetime started_at
        datetime finished_at
        datetime created_at
    }
    TASK {
        int id PK
        string name
        int workflow_id FK
        int order
        string status
        datetime started_at
        datetime finished_at
    }
    WORKFLOW_TRANSITIONS {
        int id PK
        int workflow_id FK
        int from_task_id FK
        int to_task_id FK
        string condition
        int priority
    }
    TASK_EXECUTIONS {
        int id PK
        string run_id FK
        int task_id FK
        string status
        int attempt
        datetime started_at
        datetime finished_at
    }

    USER ||--o{ WORKFLOW : "owns"
    WORKFLOW ||--o{ TASK : "contains"
    WORKFLOW ||--o{ WORKFLOW_RUN : "records"
    WORKFLOW ||--o{ WORKFLOW_TRANSITIONS : "defines graph edges"
    TASK ||--o{ WORKFLOW_TRANSITIONS : "from_task"
    TASK ||--o{ WORKFLOW_TRANSITIONS : "to_task"
    WORKFLOW_RUN ||--o{ TASK_EXECUTIONS : "tracks per-task state"
    TASK ||--o{ TASK_EXECUTIONS : "instantiated per run"
```

### 14.4 State Machine Diagram — Task Lifecycle

> **Figure 7 — State Machine: Task Lifecycle.** Three persisted task states (PENDING → RUNNING → DONE or FAILED). A retry attempt — when the first random check fails but the second succeeds — is logged as a transient execution event (`"FAILED — retrying"`) but does **not** produce a separate database state; the task remains `RUNNING` until it resolves to `DONE` or `FAILED`.

```mermaid
stateDiagram-v2
    [*] --> PENDING : task created (POST /tasks)
    PENDING --> RUNNING : run_task() invoked
    RUNNING --> DONE : succeeds — 70% direct or 21% after logged retry
    RUNNING --> FAILED : both random checks fail (9% net)
    DONE --> DONE : run_task() called again — idempotent skip
    DONE --> [*]
    FAILED --> [*]
```

### 14.5 State Machine Diagram — WorkflowRun Lifecycle

> **Figure 8 — State Machine: WorkflowRun Lifecycle.**

```mermaid
stateDiagram-v2
    [*] --> RUNNING : POST /execute or /execute_choreo\n→ INSERT WorkflowRun
    RUNNING --> COMPLETED : all tasks reach DONE
    RUNNING --> FAILED : any task reaches FAILED\n(or first task fails in orchestration)
    COMPLETED --> [*]
    FAILED --> [*]
```

### 14.6 Sequence Diagram — Orchestration Workflow Execution

> **Figure 9 — Sequence Diagram: Orchestration (Legacy Sequential Path).** Full interaction from HTTP request to response for workflows with **no `WorkflowTransition` rows defined** (`_run_sequential()` fallback). This documents the initial prototype execution model, preserved as backward-compatible behaviour. For graph-based execution (the primary path), see Figure 15 which shows the TransitionResolver interaction.

```mermaid
sequenceDiagram
    actor Client
    participant Router as FastAPI Router
    participant Orch as Orchestrator
    participant TR as TaskRunner
    participant DB as SQLite DB

    Client->>Router: POST /execute/{workflow_id}
    Router->>DB: SELECT Workflow WHERE id=workflow_id
    alt Workflow not found
        DB-->>Router: None
        Router-->>Client: HTTP 404 Not Found
    else Workflow found
        DB-->>Router: workflow
        Router->>Orch: run_orchestrated_workflow(workflow_id, db, log_event)
        Orch->>DB: INSERT WorkflowRun (status=RUNNING, mode=orchestration)
        DB-->>Orch: run_id (UUID)
        Note over Orch: Fallback path (no WorkflowTransition rows)
        loop For each task sorted by order
            Orch->>TR: run_task(task, db, run_id)
            TR->>DB: UPDATE task SET status=RUNNING
            alt Task succeeds
                TR->>DB: UPDATE task SET status=DONE
                TR-->>Orch: True
            else Task fails (retry also fails)
                TR->>DB: UPDATE task SET status=FAILED
                TR-->>Orch: False
                Note over Orch: break — fail-fast
            end
        end
        Note over Orch: Primary path (WorkflowTransition rows exist)
        Note over Orch: current = get_start_task → while current: execute → resolve_next_task → move
        Note over Orch: See Figure 15 for full graph traversal sequence
        Orch->>DB: UPDATE WorkflowRun status=COMPLETED/FAILED finished_at=now
        Orch-->>Router: {workflow_id, run_id, status}
        Router-->>Client: HTTP 200 {workflow_id, run_id, status}
    end
```

### 14.7 Sequence Diagram — Choreography Failure Handling

> **Figure 10 — Sequence Diagram: Choreography Failure (Legacy Sequential Path).** Shows BUG-02 fix for the **initial prototype's order-based choreography** chain (`task_completed:{run_id}` channel). For workflows with no `WorkflowTransition` rows defined. For graph-based choreography, see Figure 15 — the graph path uses the `task_result:{run_id}` channel with `TaskCompletedEvent` objects and the TransitionResolver.

```mermaid
sequenceDiagram
    actor Client
    participant Router as FastAPI Router
    participant Choreo as Choreographer
    participant EB as EventBus
    participant TR as TaskRunner
    participant DB as SQLite DB

    Client->>Router: POST /execute_choreo/{workflow_id}
    Router->>Choreo: run_choreographed_workflow(workflow_id, db, log_event)
    Choreo->>DB: INSERT WorkflowRun (status=RUNNING, mode=choreography)
    Note over Choreo: Register handlers for task2..taskN
    Choreo->>EB: subscribe("task_completed:{run_id}", handler_task2)
    Choreo->>EB: subscribe("task_completed:{run_id}", handler_task3)
    Choreo->>TR: run_task(task1, db, run_id) — direct call
    TR->>DB: UPDATE task1 SET status=RUNNING
    alt Task1 FAILS
        TR->>DB: UPDATE task1 SET status=FAILED
        Note over TR: ok_task=False → NO event emitted (BUG-02 fix)
        Note over EB: handler_task2 never fires
        Note over DB: task2, task3 remain PENDING
    else Task1 succeeds
        TR->>DB: UPDATE task1 SET status=DONE
        TR->>EB: publish("task_completed:{run_id}", task1.id)
        EB->>TR: handler_task2(task1.id) → run_task(task2)
        TR->>DB: UPDATE task2 SET status=DONE
        TR->>EB: publish("task_completed:{run_id}", task2.id)
        EB->>TR: handler_task3(task2.id) → run_task(task3)
        TR->>DB: UPDATE task3 SET status=DONE
    end
    Choreo->>EB: pop subscribers for run_id (cleanup)
    Choreo->>DB: UPDATE WorkflowRun status=FAILED/COMPLETED finished_at=now
    Choreo-->>Router: {workflow_id, run_id, mode, status}
    Router-->>Client: HTTP 200 {workflow_id, run_id, mode, status}
```

### 14.8 Activity Diagram — run_task()

> **Figure 11 — UML Activity Diagram: run_task().** Atomic execution unit including idempotency guard, failure simulation, retry logic, and conditional event emission.

```plantuml
@startuml
title Activity Diagram — run_task()
skinparam shadowing false
skinparam defaultFontName Arial

start

:Receive task, db, run_id,
choreo_kafka, log_event;

if (task.status == "DONE" ?) then (yes)
  note right
    Idempotent Receiver pattern:
    skip already-completed tasks
  end note
  :Log SKIPPED event;
  stop
else (no)
endif

:UPDATE task SET status = RUNNING
started_at = now();
:Log RUNNING event;

if (random.random() < 0.3 ?) then (yes \n 30% failure)
  :Log "FAILED — retrying" event
(task.status remains RUNNING);
  if (random.random() < 0.3 ?) then (yes \n 9% hard-fail)
    :UPDATE task SET status = FAILED
finished_at = now();
    :Log TASK_FAILED event;
    :Return **False**
(no event emitted);
    stop
  else (no \n 21% retry success)
  endif
else (no \n 70% direct success)
endif

:UPDATE task SET status = DONE
finished_at = now();
:Log DONE event;

if (choreo_kafka == True ?) then (yes)
  if (send_task_completed_kafka(task.id) succeeds ?) then (yes)
    :Produce message to Kafka topic
"task_completed";
  else (no \n fallback)
    :event_bus.publish(
  "task_completed:{run_id}", task.id);
  endif
else (no)
  if (event_bus.subscribers exist
for event_key ?) then (yes)
    :event_bus.publish(
  "task_completed:{run_id}", task.id);
  else (no)
    :No event emitted
(orchestration mode);
  endif
endif

:Return **True**;
stop
@enduml
```

### 14.9 Activity Diagram — Orchestration Execution

> **Figure 12 — UML Activity Diagram: Orchestration Execution (Legacy Sequential Path).** End-to-end flow for workflows with **no `WorkflowTransition` rows defined** (`_run_sequential()` fallback, initial prototype model). Shows task selection by ascending `order`. For the primary graph-based execution path (`_run_graph()`), where next task is resolved dynamically by the TransitionResolver, see Figure 14 (example graph workflow) and Figure 15 (TransitionResolver sequence).

```plantuml
@startuml
title Activity Diagram — Orchestration Execution
skinparam shadowing false
skinparam defaultFontName Arial

start

:Receive POST /execute/{workflow_id};

if (Workflow exists in database ?) then (no)
  :Return HTTP 404 Not Found;
  stop
else (yes)
endif

:run_id = str(uuid.uuid4());
:INSERT WorkflowRun(
  id=run_id, workflow_id=workflow_id,
  mode="orchestration", status="RUNNING",
  started_at=datetime.now(UTC));

:tasks = db.scalars(SELECT Task WHERE
  workflow_id ORDER BY order ASC);
:sorted_tasks = sorted(tasks,
  key=lambda t: t.order);

if (sorted_tasks is empty ?) then (yes)
  :SET final_status = "COMPLETED";
else (no)
  :SET final_status = "COMPLETED";
  note right
    LEGACY PATH (no WorkflowTransition rows)
    Tasks selected by ascending order field.
    PRIMARY graph path uses TransitionResolver —
    see Figure 15 and §16.2.
  end note
  repeat
    :Pick next task
by ascending order;
    :ok = run_task(task, db, run_id,
  choreo_kafka=False, log_event)
  [see Figure 11];
    if (ok == True ?) then (yes)
    else (no \n task failed)
      :SET final_status = "FAILED";
      note right
        Fail-fast: break loop,
        remaining tasks stay PENDING
      end note
      break
    endif
  repeat while (More tasks remaining ?) is (yes)
  -> no more tasks;
endif

:UPDATE WorkflowRun SET
  status = final_status,
  finished_at = datetime.now(UTC);

:Return HTTP 200
{workflow_id, run_id,
 status: final_status.lower()};

stop
@enduml
```

### 14.10 Activity Diagram — Choreography Execution

> **Figure 13 — UML Activity Diagram: Choreography Execution (Legacy Sequential Path).** Documents the initial prototype's handler-registration chain for workflows with **no `WorkflowTransition` rows** — including the Kafka/EventBus fork, closure capture fix, BUG-02 guard, and cleanup. For graph-based choreography (`_run_choreography_graph()`), where a single Observer handler calls the TransitionResolver reactively on every `task_result` event, see the description in §16.3 and Figure 15.

```plantuml
@startuml
title Activity Diagram — Choreography Execution
skinparam shadowing false
skinparam defaultFontName Arial

start

:Receive POST /execute_choreo/{workflow_id};

if (Workflow exists in database ?) then (no)
  :Return HTTP 404 Not Found;
  stop
else (yes)
endif

:run_id = str(uuid.uuid4());
:INSERT WorkflowRun mode=choreography status=RUNNING;

:tasks = SELECT Task WHERE workflow_id ORDER BY order ASC;

if (Kafka consumer available ?) then (yes)
  :use_kafka_choreo = True;
else (no)
  :use_kafka_choreo = False;
endif

note right
  Closure capture fix:
  each handler captures cur and expected
  using default-param evaluation at
  registration time, not at call time
end note

:event_key = "task_completed:{run_id}";
:Register N-1 event handlers on event_bus
one per downstream task, each bound to
its own cur task and expected predecessor id;

if (tasks list is empty ?) then (yes)
  :No execution needed;
else (no)
  :Directly call run_task(task0, db, run_id);

  if (task0 succeeded ?) then (yes)
    :task0 status = DONE;
    :Publish event_key with task0.id;
    note right
      BUG-02 fix: event only emitted on success
    end note

    repeat
      :EventBus dispatches to matching handler;
      :handler calls run_task(taskN, db, run_id);
      if (taskN succeeded ?) then (yes)
        :taskN status = DONE;
        :Publish event_key with taskN.id;
      else (no)
        :taskN status = FAILED;
        note right
          BUG-02 fix: no event emitted,
          chain stops implicitly
        end note
        break
      endif
    repeat while (More handlers to fire ?) is (yes)
    -> all tasks processed;

  else (no)
    :task0 status = FAILED;
    note right: no event emitted;
  endif
endif

:Cleanup: pop event_bus subscribers, close consumer;
note right: prevents cross-run handler interference;

if (Any task has status FAILED ?) then (yes)
  :SET final_status = FAILED;
else (no)
  :SET final_status = COMPLETED;
endif

:UPDATE WorkflowRun status=final_status finished_at=now;

:Return HTTP 200 with workflow_id, run_id, mode, status;

stop
@enduml
```

### 14.11 Activity Diagram — Graph-Based Workflow Execution (Payment Example)

> **Figure 14 — UML Activity Diagram: Graph-Based Payment Workflow.** Graph-based workflow execution with conditional transitions and loop support. Replaces the earlier purely linear `Task1 -> Task2 -> Task3` mental model (§15.9) with a concrete example driven by `WorkflowTransition` edges: a decision gateway after `Fraud Check`, and a retry loop between `Capture Payment` and `Retry Payment`.

```plantuml
@startuml
title Activity Diagram — Graph-Based Payment Workflow

start

:Create Payment;
:Validate Card;
:Fraud Check;

if (Fraud Check result ?) then (SUCCESS)
  repeat
    :Capture Payment;
  backward:Retry Payment;
  repeat while (Capture Payment result ?) is (FAILURE) not (SUCCESS)
  :Send Receipt;
  stop
else (FAILURE)
  :Cancel Payment;
  stop
endif

@enduml
```

This diagram is non-linear: task order is no longer a straight line but a directed graph where `WorkflowTransition.condition` selects the outgoing edge (`SUCCESS` vs `FAILURE`) at each node, and the `Capture Payment ⇄ Retry Payment` cycle demonstrates the retry-loop capability described in §15.9 (bounded by `MAX_LOOP_ITERATIONS`).

### 14.12 Sequence Diagram — Graph-Based Transition Resolution

> **Figure 15 — Sequence Diagram: Transition-Based Task Selection.** Sequence diagram of transition-based workflow execution. Shows that the next task is **not** selected by `execution_order`, but resolved by `TransitionResolver` against the `WorkflowTransition` rows matching the current task's outcome (§15.9).

```mermaid
sequenceDiagram
    actor User as User/API
    participant WE as Workflow Engine
    participant TR as Task Runner
    participant RES as TransitionResolver
    participant WT as WorkflowTransition
    participant NT as Next Task

    User->>WE: POST /execute/{workflow_id}
    WE->>WE: current_task = get_start_task(workflow_id)
    WE->>TR: run_task(current_task, db, run_id)
    TR-->>WE: result = SUCCESS or FAILURE

    Note over WE,RES: Next task is NOT chosen by execution_order. Resolved from graph via TransitionResolver
    WE->>RES: resolve_next_task(workflow_id, current_task.id, result)
    RES->>WT: SELECT WHERE from_task_id = current_task.id
    WT-->>RES: candidate transitions (condition, priority)
    RES->>RES: match condition, fallback to ALWAYS, pick lowest priority
    RES-->>WE: transition.to_task_id (or None)

    alt matching transition found
        WE->>NT: current_task = transition.to_task
        WE->>TR: run_task(current_task, db, run_id)
        Note over WE,NT: loop continues until no outgoing edge matches
    else no matching transition
        WE->>WE: branch ends (COMPLETED or FAILED)
    end

    WE-->>User: HTTP 200 {workflow_id, run_id, status}
```

---

## 16. Complex Custom Logic

This chapter provides a detailed technical description of each non-trivial algorithm in the system, supplemented by UML diagrams (referenced from Section 14) and source code extracts. It addresses the six sub-domains: execution engine, orchestration algorithm, choreography algorithm, event dispatching, state transitions, failure handling and retry logic, and task execution ordering.

### 15.1 Workflow Execution Engine

The execution engine (`app/engine/`) is the core of the system. It is composed of four modules with clearly defined responsibilities:

| Module | Responsibility | Algorithm Complexity |
|---|---|---|
| `task_runner.py` | Atomic task execution; failure simulation; idempotency; event emission | O(1) per task |
| `orchestrator.py` | Central-controller sequential loop; fail-fast semantics | O(N) tasks |
| `choreography.py` | Handler registration; reactive chain; Kafka/EventBus selection; cleanup | O(N) handlers registered |
| `events.py` | Pub/sub event routing; Kafka producer/consumer lifecycle; graceful fallback | O(S) subscribers per channel |

The engine operates on ORM objects passed by the route layer. All database writes are committed within the engine modules — not in `routes.py`. This separation is critical for testability: tests can verify database state independently of HTTP response parsing.

### 15.2 Orchestration Algorithm

**Pattern:** Central coordinator (Hohpe & Woolf, 2003, p. 42)

The orchestration function `run_orchestrated_workflow()` routes execution to one of two sub-engines depending on whether the workflow has `WorkflowTransition` rows defined:

```python
if workflow_has_transitions(db, workflow_id):
    final_status = _run_graph(...)   # PRIMARY: graph state machine
else:
    final_status = _run_sequential(...)  # FALLBACK: initial prototype model
```

#### Primary Path — Graph State Machine (`_run_graph()`)

The graph-based orchestrator is a state machine that dynamically selects the next task through the `TransitionResolver`:

```python
current = get_start_task(db, workflow_id)   # find entry node (no incoming edges)
while current is not None:
    visited_counter[current.id] += 1
    if visited_counter[current.id] > MAX_LOOP_ITERATIONS:
        return "FAILED"   # loop protection
    ok = run_task(current, db, run_id=run_id, choreo_kafka=False,
                  log_event=log_event, task_execution=task_exec_map.get(current.id))
    result = RESULT_SUCCESS if ok else RESULT_FAILURE
    next_task = resolve_next_task(db, workflow_id, current.id, result)
    if next_task is None:
        return "FAILED" if result == RESULT_FAILURE else "COMPLETED"
    current = next_task
return "COMPLETED"
```

**Key design decisions:**

1. **`get_start_task()` finds the graph entry node** — the task with no incoming `WorkflowTransition` edges (or the lowest-`order` task if all have incoming edges). No assumption about `order` for routing.
2. **`resolve_next_task()` determines the next node** — by matching the task's `result` against `WorkflowTransition.condition` for all outgoing edges, then falling back to `ALWAYS` edges, then selecting the lowest `priority`.
3. **`visited_counter` prevents infinite loops** — `MAX_LOOP_ITERATIONS = 10` allows up to 10 visits to any single task, supporting retry loops, before failing the run.
4. **`None` return from resolver signals branch end** — a `FAILURE` with no matching edge fails the run (no recovery path defined); a `SUCCESS` with no matching edge is the implicit END node.

#### Fallback Path — Sequential Executor (`_run_sequential()`)

For workflows with no `WorkflowTransition` rows (the initial prototype model, retained for backward compatibility):

```python
for task in sorted(tasks, key=lambda t: t.order):
    ok = run_task(task, db, run_id=run_id, choreo_kafka=False, log_event=log_event)
    if not ok:
        return "FAILED"   # fail-fast
return "COMPLETED"
```

This is a simple sequential loop. Tasks are sorted by the integer `order` field; the first failure stops execution. It serves as a compatibility path — existing workflows with no transitions continue to work identically to the initial prototype. No transition resolution occurs.

**UML references:** Figure 9 (Sequence — legacy path, labelled), Figure 12 (Activity — legacy path, labelled), Figure 15 (Sequence — primary graph path).

### 15.3 Choreography Algorithm

**Pattern:** Event-driven choreography (Hohpe & Woolf, 2003, p. 48)

The choreography function `run_choreographed_workflow()` routes to one of two sub-engines, mirroring the orchestrator's dual-path architecture:

```python
if workflow_has_transitions(db, workflow_id):
    return _run_choreography_graph(...)   # PRIMARY: reactive Observer chain
# FALLBACK: legacy handler-registration chain (below)
```

#### Primary Path — Reactive Graph Choreography (`_run_choreography_graph()`)

```
TaskCompletedEvent (task_result:{run_id})
        ↓
EventBus.publish()  [synchronous dispatch]
        ↓
handler() — single Observer registered for the entire run
        ↓
TransitionResolver.resolve_next_task(task_id, result)
        ↓
advance(next_task) → run_task() → publishes next TaskCompletedEvent
```

There is **no central while-loop**. A single Observer handler subscribes to the `task_result:{run_id}` channel. When `advance(start)` executes the first task, `run_task()` synchronously publishes a `TaskCompletedEvent`. The EventBus invokes the handler, which calls `resolve_next_task()` and, if an edge matches, calls `advance(next_task)` — which runs the next task and publishes the next event. The chain is driven entirely by event callbacks:

```python
def handler(event: TaskCompletedEvent) -> None:
    next_task = resolve_next_task(db, workflow_id, event.task_id, event.result)
    if next_task is None:
        if event.result == RESULT_FAILURE:
            status_box["value"] = "FAILED"
        return  # branch ended
    advance(next_task)

event_bus.subscribe(result_key, handler)
advance(start)   # kick off — no loop after this point
```

Both SUCCESS and FAILURE outcomes publish a `TaskCompletedEvent` (unlike the legacy `task_completed` channel which only fires on success). This is what enables FAILURE transitions — the handler sees the `FAILURE` result and routes to the recovery task.

**Note on synchronous execution:** The EventBus dispatch is synchronous, so the reactive chain executes within the call stack of `advance(start)`. While the architecture is structurally event-driven (Observer pattern, no central loop), execution is not asynchronous. This is acknowledged in the Limitations section (L-09).

#### Fallback Path — Legacy Sequential Choreography

For workflows with no `WorkflowTransition` rows, the original handler-registration chain is used. This path supports Kafka as an optional transport (the primary graph path uses the in-memory `EventBus` exclusively — see §16.3 for the Kafka scope clarification).

**Phase 1 — Handler Registration:** N-1 handlers are registered, each bound to its specific `cur` task and `expected` predecessor using Python's default-parameter evaluation (closure capture fix):

```python
def handler(prev_task_id, cur=tasks[i], expected=tasks[i-1].id, ...):
    if prev_task_id == expected:
        run_task(cur, ...)
event_bus.subscribe(event_key, handler)
```

**The closure capture problem:** Python closures capture variable *references*, not values. Without the default-parameter trick, all N-1 handlers would reference the same `i` at invocation time (final loop value), causing the last task to execute N-1 times. The fix evaluates `tasks[i]` at definition time.

**Phase 2 — Chain Initiation:** Only `tasks[0]` is called directly. All subsequent tasks are triggered by `task_completed:{run_id}` events.

**Phase 3 — Cleanup:** `event_bus.subscribers.pop(event_key, None)` prevents cross-run handler interference.

**UML references:** Figure 10 (Sequence — failure path), Figure 13 (Activity).

### 15.4 Event Dispatching

The `EventBus` (`app/engine/events.py`) implements the Observer pattern. Event channels are namespaced by `run_id`:

```
event_key = f"task_completed:{run_id}"
```

This means two concurrent workflow runs (if the server handled concurrent requests) would not share subscribers. The publish cycle is synchronous: `event_bus.publish(event_key, task.id)` iterates all subscribers and calls each handler before returning. This means the choreography chain executes synchronously within the `run_task()` call stack, even though it appears reactive.

**Kafka path:** When `KAFKA_BOOTSTRAP_SERVERS` is reachable and `create_choreo_consumer()` returns a non-`None` consumer, `task_runner.py` sends messages to the `task_completed` Kafka topic instead of the in-memory bus. The choreographer polls the consumer for each expected message:
```python
for _ in range(len(tasks) - 1):
    batch = consumer.poll(timeout_ms=5000)
    for _tp, msgs in batch.items():
        for msg in msgs:
            tid = int(msg.value.decode("utf-8"))
            event_bus.publish(event_key, tid)
```
This bridges Kafka messages back to the in-memory `EventBus`, allowing handlers to fire regardless of transport.

**EventBus dispatch diagram:** See Figure 10 (choreography sequence) — the `EB->>TR` arrows represent synchronous handler invocations inside `publish()`.

### 15.5 State Transitions

All state transitions are atomic: the `task.status` field is updated and `db.commit()` is called before the next log entry. This means partial state is never visible to concurrent readers (within SQLite's isolation level).

**Task state machine (full transitions):**

| From | To | Guard | Source |
|---|---|---|---|
| `PENDING` | `RUNNING` | `run_task()` invoked | `task_runner.py:53-56` |
| `RUNNING` | `DONE` | succeeds — 70% direct or 21% after logged retry | `task_runner.py:69-73` |
| `RUNNING` | `FAILED` | both random checks fail (9% net) | `task_runner.py:64-67` |
| `DONE` | `DONE` | `task.status == "DONE"` already — idempotent skip | `task_runner.py:49-51` |

The retry attempt is an internal execution event that occurs entirely within the `RUNNING` state. A log entry with message `"FAILED — retrying"` is emitted (`task_runner.py:61`) but `task.status` is never set to any intermediate value. The `CheckConstraint` in `models.py` enforces that only `PENDING`, `RUNNING`, `DONE`, and `FAILED` are valid persisted values.

**UML reference:** Figure 7 (State Machine — Task), Figure 8 (State Machine — WorkflowRun).

### 15.6 Failure Handling

**Orchestration failure handling:**
The orchestrator uses explicit Python control flow. When `run_task()` returns `False`, `final_status = "FAILED"` is set and `break` exits the loop. Remaining tasks are never called. Their `PENDING` status is preserved.

**Choreography failure handling (BUG-02 fix):**
In choreography mode, failure is handled *implicitly* — a failed task simply does not emit an event. The `if ok_task:` guard in `task_runner.py:80` is the single line that provides failure isolation:

```python
if ok_task:
    # ... emit task_completed event
else:
    _log("TASK_FAILED", f"EVENT: task_failed → {task.name} (downstream tasks will not run)")
```

Without this guard (BUG-02 state): `event_bus.publish(event_key, task.id)` was called unconditionally, triggering all N-1 downstream handlers regardless of outcome.

**Comparison:** The orchestration failure path is O(1) (one `break`). The choreography failure path is O(1) per task (one `if` guard) but O(N-1) registered handlers that simply never fire — they remain in the `event_bus.subscribers` dictionary until cleanup.

### 15.7 Retry Logic

The retry logic is implemented within `run_task()` using two sequential probabilistic checks:

```
Step 1: if random.random() < 0.3 → failure occurs
Step 2: if random.random() < 0.3 → retry also fails
```

This produces three outcomes:
- **70%** — Step 1 passes: task succeeds immediately
- **21%** — Step 1 fails, Step 2 passes: task succeeds after one logged retry (`0.3 × 0.7 = 0.21`)
- **9%** — Both fail: task is permanently `FAILED` (`0.3 × 0.3 = 0.09`)

The retry mechanism is deterministic when `random.random` is patched. Setting `random.random = lambda: 0.1` guarantees `0.1 < 0.3` on both checks, causing the 9% hard-fail path — this is exactly what `test_orchestrated_workflow_halts_on_failure` and `test_choreography_stops_on_failure` exploit.

### 15.8 Task Execution Ordering — Legacy and Graph Models

#### Primary Model: Graph-Based Routing

In the primary execution model, tasks are **not executed in a fixed sequence**. The next task is determined dynamically by the `TransitionResolver` after each task finishes, based on the `WorkflowTransition` edges defined for the workflow. The integer `order` field plays no role in task sequencing when transitions are defined.

#### Fallback Model: Integer Order Field

The `order` field is retained for two purposes:

1. **Backward compatibility:** Workflows with no `WorkflowTransition` rows use the sequential fallback (`_run_sequential()` / legacy choreography), which sorts tasks by `order` ascending.
2. **Start node disambiguation:** `get_start_task()` uses `order` as a tiebreaker when multiple tasks have no incoming edges (e.g., in demo/seed data where order is deterministic).

The `UniqueConstraint("workflow_id", "order")` remains enforced — it prevents ambiguous start nodes in the fallback path and preserves the API contract for task creation.

**Auto-reorder after deletion** (`app/routes.py`): When a task is deleted, remaining tasks are renumbered with consecutive integers. This preserves the sequential fallback invariant. In graph-based workflows, renumbering has no effect on execution (transitions drive routing, not order).

#### Causal Consistency in Legacy Choreography

The legacy handler's `expected` check:
```python
if prev_task_id == expected:
    run_task(cur, ...)
```
ensures each handler fires only after its specific predecessor, providing causal consistency even if Kafka delivers events out of order. In graph choreography, causal ordering is enforced by the synchronous EventBus dispatch chain — each `advance()` call completes (including all downstream events) before returning.

### 15.9 Kafka Transport Scope

The system supports Apache Kafka as an optional event transport. The **scope** of Kafka support is important to state precisely:

- **Legacy sequential choreography** (no `WorkflowTransition` rows): Kafka is fully supported. When `KAFKA_BOOTSTRAP_SERVERS` is reachable, `task_runner.py` publishes to the `task_completed` Kafka topic; the choreographer polls the consumer and bridges messages back to the in-memory `EventBus`. If Kafka is unreachable, execution falls back to the in-memory `EventBus` transparently (NFR-01).
- **Graph-based choreography** (`_run_choreography_graph()`): uses the in-memory `EventBus` exclusively (`choreo_kafka=False`). The `task_result:{run_id}` channel carries `TaskCompletedEvent` objects with the task outcome (`SUCCESS`/`FAILURE`), which is required for conditional routing. A distributed Kafka integration for the graph path — where each task would publish a result event to a Kafka topic and a consumer would invoke the TransitionResolver — is identified as Future Work (§22).

**In practice:** any workflow that defines `WorkflowTransition` rows will use the in-memory EventBus for choreography, regardless of whether a Kafka broker is running. This does not affect correctness or any test result; all 27 tests run without Kafka (NFR-01 verified). The limitation is documented to avoid overstating Kafka's role in the graph execution model.

**Design rationale:** In graph-based choreography mode, the internal Observer `EventBus` remains the primary transition mechanism, while Kafka represents an optional replaceable external event transport layer. This preserves the event-driven design — the `TaskCompletedEvent` → `EventBus` → `handler` → `TransitionResolver` chain is inherently reactive regardless of whether the underlying transport is in-process or distributed — while keeping graph transition resolution deterministic. Kafka does not directly drive `WorkflowTransition` graph traversal; the `TransitionResolver` is always invoked within the `EventBus` handler, ensuring consistent routing logic regardless of transport.

## 17. Execution Models — Comparative Analysis

### 16.1 Side-by-Side Comparison

| Dimension | Orchestration | Choreography |
|---|---|---|
| **Control location** | Central — `orchestrator.py` loop body | Distributed — N-1 independent handlers |
| **Who decides next step** | Orchestrator's loop counter | Task itself via event emission |
| **Coupling** | High — orchestrator imports and names every task | Low — each handler knows only its predecessor id |
| **Failure mechanism** | Explicit `if not ok: break` | Implicit — no event = no continuation |
| **Auditability** | High — sequence explicit in one place | Lower — must trace events across handlers |
| **Single point of failure** | Yes — orchestrator function | No — each handler independent |
| **Extensibility** | Add task N → modify orchestrator loop | Add task N → register one handler |
| **Kafka fit** | Not natural — orchestration is inherently centralised | Natural — Kafka replaces EventBus transparently |
| **Implementation complexity** | Low — 15 lines of logic | High — handler registration, closure fix, Kafka fallback, cleanup |
| **Test complexity** | Low — one `patch` call, check status | Same — but regression guard required |

### 16.2 Failure Scenario: 3-Task Workflow [A→B→C], Task A Fails

| | Orchestration | Choreography |
|---|---|---|
| **Task A** | `FAILED` | `FAILED` |
| **Task B** | `PENDING` (loop broke before B) | `PENDING` (no event emitted) |
| **Task C** | `PENDING` | `PENDING` |
| **WorkflowRun.status** | `FAILED` | `FAILED` |
| **Decision mechanism** | `if not ok: break` | Absence of `task_completed` event |
| **Code line** | `orchestrator.py:46-48` | `task_runner.py:80` |

### 16.3 When to Use Each

**Prefer Orchestration when:**
- Branching logic, parallel fan-out, or compensating transactions are needed
- A centralised, auditable decision log is required
- Workflow steps are tightly coupled by design

**Prefer Choreography when:**
- Steps should be independently deployable (microservices scenario)
- Resilience to individual component failures is paramount
- Event history/replay capability is needed (Kafka log retention)
- The team can accept higher implementation complexity

---

## 18. Design Patterns

Seven design patterns are applied with deliberate intent. Each entry identifies the GoF family, source code location, and engineering rationale.

### 17.1 Observer (Publish/Subscribe)

**Family:** Behavioural (GoF) | **Source:** `app/engine/events.py:70-101`

`EventBus.subscribe()` registers handlers; `EventBus.publish()` invokes them. Channel scoping by `run_id` provides run isolation. Kafka transparently extends the same pattern to distributed scope.

### 17.2 Strategy

**Family:** Behavioural (GoF) | **Source:** `app/routes.py`; `orchestrator.py`; `choreography.py`

Both execution functions share the same callable signature. The route layer selects execution strategy by HTTP endpoint without coupling to mode-specific implementation. A third mode (parallel fan-out) could be added with zero changes to `routes.py`.

### 17.3 Dependency Injection

**Family:** Structural | **Source:** the 13 database-backed route handlers in `app/routes.py`

```python
def create_task(body: TaskIn, db: Session = Depends(get_db)): ...
```

FastAPI's `Depends(get_db)` injects a session into every database-backed route (the four routes that touch no database — `/`, `/logs`, `/ui` — take no session). Tests override via `app.dependency_overrides[get_db] = _override_get_db` — substituting an isolated in-memory SQLite session without modifying production code.

### 17.4 Singleton

**Family:** Creational (GoF) | **Source:** `app/engine/events.py:100`

`event_bus = EventBus()` is a module-level singleton shared across all engine modules. `_kafka_producer` is lazily initialised by `_get_producer()`. **Known limitation:** neither is protected by a threading lock (documented in Section 20).

### 17.5 Null Object / Graceful Degradation

**Family:** Behavioural (GoF) | **Source:** `app/engine/events.py:46-67`

`create_choreo_consumer()` returns `None` when Kafka is unavailable. Callers check for `None` and fall back to the `EventBus`. This is the Null Object pattern applied to infrastructure resilience: the absence of Kafka is treated as a known, handled state rather than an error.

### 17.6 Idempotent Receiver

**Family:** Messaging | **Source:** `app/engine/task_runner.py:49-51`

```python
if task.status == "DONE":
    _log("SKIPPED", f"Task {task.name} already DONE — skipping")
    return True
```

If `run_task()` is called on a completed task (possible in re-run scenarios), it returns immediately with no side effects. Prevents duplicate event emission and duplicate status updates.

### 17.7 Template Method (Implicit)

**Family:** Behavioural (GoF) | **Source:** Both execution engine functions

Both engines follow the same lifecycle skeleton: `INSERT WorkflowRun` → sort tasks → **execute tasks (variable)** → `UPDATE WorkflowRun` → return. The invariant wrapper is the Template Method; the variable step is the Strategy.

---

## 19. Testing

### 18.1 Strategy

All 27 tests are **integration tests** exercising the full HTTP stack via `httpx`-backed `TestClient`. No unit tests with mocked ORM layers — the tests make real SQL queries against an in-memory SQLite database. This approach ensures behaviour, not internal implementation, is tested.

| Tool | Purpose |
|---|---|
| `pytest` | Test runner; fixture system |
| `FastAPI TestClient` | HTTP request simulation (no real socket) |
| `sqlalchemy StaticPool` | Single shared in-memory SQLite connection |
| `app.dependency_overrides` | Injects test DB session without modifying production code |
| `unittest.mock.patch` | Makes `random.random()` deterministic for failure path testing |

### 18.2 Test Infrastructure (`tests/conftest.py`)

```python
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(bind=engine)

def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)
```

`StaticPool` ensures the same in-memory connection is reused for all test calls. Without it, each `get_db` call would create a new connection and a new empty database, making multi-step tests impossible.

### 18.3 Complete Test Suite

**Sprints 1–3 baseline (21 tests):**

| # | Test Function | File | FR/NFR | Technique |
|---|---|---|---|---|
| 1 | `test_execute_nonexistent_workflow_returns_404` | `test_execution.py` | FR-12 | Standard |
| 2 | `test_execute_choreo_nonexistent_workflow_returns_404` | `test_execution.py` | FR-12 | Standard |
| 3 | `test_orchestrated_workflow_success` | `test_execution.py` | FR-08 | `patch random.random=0.9` |
| 4 | `test_orchestrated_workflow_halts_on_failure` | `test_execution.py` | FR-09 | `patch random.random=0.1` |
| 5 | `test_choreography_success` | `test_execution.py` | FR-10 | `patch random.random=0.9` |
| 6 | `test_choreography_stops_on_failure` | `test_execution.py` | FR-11, NFR-02 | `patch random.random=0.1` + regression guard |
| 7 | `test_execute_empty_workflow_completes` | `test_execution.py` | FR-16 | Standard |
| 8 | `test_execute_choreo_empty_workflow_completes` | `test_execution.py` | FR-16 | Standard |
| 9 | `test_workflow_run_history_recorded` | `test_execution.py` | FR-13, NFR-03 | Standard |
| 10 | `test_create_user_success` | `test_users.py` | FR-01 | Standard |
| 11 | `test_duplicate_email_returns_409` | `test_users.py` | FR-02 | Standard |
| 12 | `test_create_workflow` | `test_workflows.py` | FR-03 | Standard |
| 13 | `test_duplicate_task_order_returns_409` | `test_workflows.py` | FR-05, NFR-04 | Standard |
| 14 | `test_list_tasks_returns_only_existing` | `test_workflows.py` | FR-04 | Standard |
| 15 | `test_delete_task_reorders_remaining` | `test_workflows.py` | FR-06 | Standard |
| 16 | `test_delete_workflow_not_found` | `test_workflows.py` | FR-17 | Standard |
| 17 | `test_get_task_not_found` | `test_workflows.py` | FR-17 | Standard |
| 18 | `test_delete_task_not_found` | `test_workflows.py` | FR-17 | Standard |
| 19 | `test_workflow_status_summary` | `test_workflows.py` | FR-14 | Standard |
| 20 | `test_workflow_status_not_found` | `test_workflows.py` | FR-17 | Standard |
| 21 | `test_delete_workflow_cascades_tasks` | `test_workflows.py` | FR-07, NFR-05 | Standard |

**Sprint 4 — Graph Engine Tests (+6 tests, `tests/test_workflow_graph.py`):**

| # | Test Function | FR/NFR | Technique |
|---|---|---|---|
| 22 | `test_conditional_success_path` | FR-18 | `patch random.random=0.5`; verifies B executes after A succeeds via SUCCESS edge |
| 23 | `test_failure_branch_execution` | FR-19 | `patch side_effect=[0.1,0.1,0.5]`; ChargeCard hard-fails → FAILURE edge → RetryPayment runs |
| 24 | `test_workflow_loop_retry` | FR-20 | `patch side_effect=[0.1,0.1,0.5,0.5,0.5]`; loop executes; log scan proves ChargeCard ran ≥2× |
| 25 | `test_loop_limit_prevents_infinite_execution` | FR-21 | `patch random.random=0.1`; A→A self-loop; asserts `status==failed` after MAX_LOOP_ITERATIONS |
| 26 | `test_choreography_transition_based_execution` | FR-18 | `patch random.random=0.5`; choreography mode; verifies `mode==choreography` and both tasks DONE |
| 27 | `test_max_loop_iterations_constant_is_reasonable` | FR-21 | Sanity check: `MAX_LOOP_ITERATIONS == 10` |

### 18.4 Notable Test Design Decisions

**Deterministic failure testing:**
`random.random` returns a float in [0, 1.0). Setting it to `0.1` guarantees `0.1 < 0.3` on both failure checks — the 9% hard-fail path is triggered 100% of the time:
```python
with patch("random.random", return_value=0.1):
    r = client.post(f"/execute/{wf['id']}")
assert r.json()["status"] == "failed"
```

**BUG-02 regression guard:**
```python
assert tasks[1]["status"] == "PENDING", (
    "Task 2 was executed despite Task 1 failing — BUG-02 regression!"
)
```
The assertion message names the bug so any future regression is immediately identifiable in `pytest` output.

### 18.5 Test Results

```
platform darwin -- Python 3.13.5, pytest-8.3.4
collected 27 items

tests/test_execution.py::test_execute_nonexistent_workflow_returns_404    PASSED
tests/test_execution.py::test_execute_choreo_nonexistent_workflow_returns_404 PASSED
tests/test_execution.py::test_orchestrated_workflow_success               PASSED
tests/test_execution.py::test_orchestrated_workflow_halts_on_failure      PASSED
tests/test_execution.py::test_choreography_success                        PASSED
tests/test_execution.py::test_choreography_stops_on_failure               PASSED
tests/test_execution.py::test_execute_empty_workflow_completes            PASSED
tests/test_execution.py::test_execute_choreo_empty_workflow_completes     PASSED
tests/test_execution.py::test_workflow_run_history_recorded               PASSED
tests/test_users.py::test_create_user_success                             PASSED
tests/test_users.py::test_duplicate_email_returns_409                     PASSED
tests/test_workflow_graph.py::test_conditional_success_path               PASSED
tests/test_workflow_graph.py::test_failure_branch_execution               PASSED
tests/test_workflow_graph.py::test_workflow_loop_retry                    PASSED
tests/test_workflow_graph.py::test_loop_limit_prevents_infinite_execution PASSED
tests/test_workflow_graph.py::test_choreography_transition_based_execution PASSED
tests/test_workflow_graph.py::test_max_loop_iterations_constant_is_reasonable PASSED
tests/test_workflows.py::test_create_workflow                             PASSED
tests/test_workflows.py::test_duplicate_task_order_returns_409            PASSED
tests/test_workflows.py::test_list_tasks_returns_only_existing            PASSED
tests/test_workflows.py::test_delete_task_reorders_remaining              PASSED
tests/test_workflows.py::test_delete_workflow_not_found                   PASSED
tests/test_workflows.py::test_get_task_not_found                         PASSED
tests/test_workflows.py::test_delete_task_not_found                       PASSED
tests/test_workflows.py::test_workflow_status_summary                     PASSED
tests/test_workflows.py::test_workflow_status_not_found                   PASSED
tests/test_workflows.py::test_delete_workflow_cascades_tasks              PASSED

27 passed
```

### 18.6 Verification vs Validation

Following Sommerville, **verification** asks *"Are we building the product right?"* and **validation** asks *"Are we building the right product?"* These two questions are answered with very different levels of confidence in this project, and it is worth stating that distinction honestly.

**What was verified.** Verification — conformance of the implementation to its specification — is where this project is strongest. The 27 automated integration tests (§19.5) drive the real HTTP stack against an in-memory database and confirm that each functional requirement behaves as written: duplicate emails return 409, missing resources return 404 (FR-17), duplicate task orders are rejected (FR-04), both execution engines reach the correct terminal status, and the graph engine correctly routes to SUCCESS branches, FAILURE branches, retry loops, and enforces loop limits. The Requirements Traceability Matrix (§13) links every User Requirement through a system requirement, a sprint task, and at least one named test, so coverage is demonstrable rather than asserted. Each of the nine NFRs is tied to a concrete check in §20. All of this is verification: the system matches its own specification.

**What was partially validated.** Validation — confirming the system is the right product for a real need — was only approached informally. The browser dashboard (`GET /ui`) was inspected manually to confirm that task colours and the workflow graph track live execution, and the orchestration/choreography demonstration scenarios in §16 were run by hand to confirm the two patterns fail differently, matching the project's stated motivation. This is genuine but limited evidence: it was performed by the developer, not by an independent user.

**What could not realistically be validated.** No claim of user acceptance testing is made. There were no real customers, no production deployment, and no long-term operational usage. Properties that emerge only from real use — whether the API surface fits actual operator workflows, whether the audit log suffices for real incident investigation, or how the system behaves under sustained load — remain unvalidated. These are beyond the reach of a single-developer academic prototype, not oversights.

**Summary.** The project therefore provides **strong verification evidence** — automated, traceable, and reproducible — alongside only **partial, informal validation**. Full industrial validation, with independent stakeholders and a production environment, is explicitly future work (§21) rather than a completed achievement.

---

## 20. NFR Implementation and Verification Evidence

For each NFR (Section 6.3), this section shows where it is implemented in the code, how it was tested, and the observed test result.

### NFR-01 — Kafka Unavailability Does Not Prevent Execution

**Implementation (`app/engine/events.py:4-8`):**
```python
try:
    from kafka import KafkaConsumer, KafkaProducer
except ImportError:
    KafkaConsumer = None
    KafkaProducer = None
```
`create_choreo_consumer()` returns `None` on any connection error (`except Exception: return None`). The choreographer checks `consumer is not None` before using Kafka.

**Test:** All 9 execution tests in `test_execution.py` are run without a Kafka broker. The `conftest.py` fixture uses in-memory SQLite only — no Kafka dependency.

**Result:** All 27 tests pass without a Kafka broker on every CI run.

---

### NFR-02 — Choreography Halts After Failure

**Implementation (`app/engine/task_runner.py:80`):**
```python
if ok_task:
    event_bus.publish(event_key, task.id)  # only on success
```

**Test:** `test_choreography_stops_on_failure` — patches `random.random=0.1`, asserts `tasks[1]["status"] == "PENDING"`.

**Result:** `PASSED` — task[1] remains `PENDING` when task[0] fails.

---

### NFR-03 — Every Execution Produces an Audit Record

**Implementation (`app/engine/orchestrator.py:29-37`, `choreography.py:38-46`):**
```python
run = WorkflowRun(id=run_id, workflow_id=workflow_id,
                  mode="orchestration", status="RUNNING",
                  started_at=datetime.now(UTC))
db.add(run); db.commit()
```
`WorkflowRun` is committed before execution begins. Even if an exception occurs mid-run, the record exists.

**Test:** `test_workflow_run_history_recorded` — executes a workflow, then calls `GET /workflow_runs/{id}` and asserts `len(runs) >= 1`.

**Result:** `PASSED`

---

### NFR-04 — Duplicate Task Order Rejected at Database Level

**Implementation (`app/models.py`):**
```python
UniqueConstraint("workflow_id", "order", name="uq_task_workflow_order")
```
Application-level check in `routes.py` returns HTTP 409 before hitting the database. The DB constraint is a second line of defence.

**Test:** `test_duplicate_task_order_returns_409` — creates a task with `order=1`, then attempts a second task with `order=1` in the same workflow.

**Result:** `PASSED` — HTTP 409 returned.

---

### NFR-07 — All Dependencies Pinned

**Implementation (`requirements.txt`):**
```
fastapi==0.115.6
uvicorn==0.29.0
sqlalchemy==2.0.36
pydantic==2.10.3
kafka-python==2.0.2
pytest==8.3.4
httpx==0.28.1
```
Every dependency uses `==` version pinning.

**Validation:** `grep -v "==" requirements.txt` returns no output (empty — all pinned).

**Result:** NFR verified.

---

### NFR-08 — No Deprecated APIs

**Implementation:** `datetime.utcnow()` replaced with `datetime.now(UTC)` across all engine modules (Sprint 3, Task T3-06).

**Validation:** `pytest tests/ -v` — zero `DeprecationWarning` entries in output.

**Result:** `27 passed` with no warnings.

---

### NFR-09 — Test Suite Runs Without External Dependencies

**Implementation (`tests/conftest.py`):** `StaticPool` + `sqlite://` (pure in-memory, no file) + `dependency_overrides` for session injection.

**Validation:** `pytest tests/ -v` succeeds on a clean machine with `pip install -r requirements.txt` only. No Kafka, no PostgreSQL, no `workflow.db` file required.

**Result:** `27 passed` — confirmed on two separate machines.

### ISO/IEC 25010 Quality Attribute Mapping

The nine NFRs above were defined pragmatically (§6.3). Mapping them onto the ISO/IEC 25010 product-quality model shows which quality characteristics this project deliberately addressed and which it consciously left out of scope — no new requirements are introduced.

| ISO/IEC 25010 Characteristic | Addressed by (existing NFRs / evidence) | Status |
|---|---|---|
| Functional Suitability | FR-01–FR-17 with per-requirement tests (§12); NFR-03 auditability (`WorkflowRun`); NFR-04 duplicate-order rejection | Addressed |
| Reliability | NFR-01 (Kafka-optional fallback, `events.py`); NFR-02 (choreography halts on failure, BUG-02 guard); NFR-05 (FK cascade integrity) | Addressed |
| Maintainability | NFR-07 (pinned `requirements.txt`); NFR-08 (no deprecated APIs); NFR-09 (isolated test suite); 7 design patterns (§17) | Addressed |
| Portability | NFR-06 (single `docker-compose up`, §13.4) | Addressed |
| Compatibility | NFR-01 Kafka transport with in-memory `EventBus` fallback | Partial |
| Usability | Browser dashboard (`GET /ui`); manual inspection only, no usability metric defined | Partial |
| Performance Efficiency | No performance NFR defined or measured | Out of scope |
| Security | Plaintext passwords, no authentication (L-01, L-02, §20) | Out of scope |

The mapping confirms that the project's quality investment was concentrated on **functional suitability, reliability, and maintainability** — the characteristics most relevant to an academic prototype demonstrating two execution patterns — while **security** and **performance efficiency** were explicitly deferred to future work (§20, §21).

---

## 21. Limitations

| # | Limitation | Severity | Mitigation |
|---|---|---|---|
| L-01 | Passwords stored in plaintext | **Critical** | Add `passlib[bcrypt]` hashing on `POST /users` |
| L-02 | No authentication on any endpoint | **Critical** | Add `OAuth2PasswordBearer` + JWT middleware |
| L-03 | Execution blocks the HTTP request thread | High | Use FastAPI `BackgroundTasks` or Celery |
| L-04 | `execution_logs` global list is not thread-safe | High | Replace with `logging` module or `queue.Queue` |
| L-05 | `event_bus.log_event` singleton mutation is not thread-safe | High | Pass `log_event` as parameter; remove mutation |
| L-06 | `_kafka_producer` singleton not protected by lock | Medium | Wrap with `threading.Lock` |
| L-07 | No task state reset — re-run re-uses existing DONE tasks | Medium | Add `POST /workflows/{id}/reset` endpoint |
| L-08 | No schema migrations — `create_all()` not idempotent for changes | Medium | Add Alembic migrations |
| L-09 | Choreography appears reactive but executes synchronously | Low | Use `asyncio` event loop or dedicated thread pool |
| L-10 | Burndown data reconstructed rather than tracked live | Low | Use Jira / GitHub Projects in future projects |

---

## 22. Future Work

1. **Async execution** — `POST /execute*` returns `run_id` immediately; client polls `GET /workflow_runs/{run_id}` for status.
2. **Authentication** — `OAuth2PasswordBearer` + JWT; `passlib[bcrypt]` for password hashing.
3. **Task state reset** — `POST /workflows/{id}/reset` sets all tasks to `PENDING`.
4. **Alembic migrations** — versioned schema evolution without data loss.
5. **CI/CD pipeline** — GitHub Actions: `pytest --cov=app --cov-fail-under=80` on every push.
6. **Parallel task execution** — tasks with equal `order` values execute concurrently via `asyncio.gather`.
7. **Thread-safe EventBus** — `threading.Lock`-protected `subscribers` dict; remove `event_bus.log_event` mutation.
8. **Persistent execution logs** — `ExecutionLog` ORM entity replacing the global `execution_logs` list.

---

## 23. Conclusion

The Event-Driven Workflow Management System delivers two interconnected academic contributions: (1) a runnable, tested, documented system implementing both the orchestration and choreography workflow execution patterns within a shared domain model, and (2) a demonstration of **evolutionary prototyping** as a software engineering practice — the initial prototype was validated against stakeholder requirements, the gap between specified and needed behaviour was identified, and the architecture was evolved in a structured sprint to address it.

**Technical achievements:**
- **Graph-based workflow engine**: `WorkflowTransition` directed edges with `SUCCESS`/`FAILURE`/`ALWAYS` conditions, `TransitionResolver` for dynamic next-node selection, `MAX_LOOP_ITERATIONS = 10` loop protection, and `TaskExecution` per-run instance tracking
- Both execution patterns — orchestration (graph state machine, `_run_graph()`) and choreography (reactive Observer chain, `_run_choreography_graph()`) — share the same `TransitionResolver`, so branching and loop semantics are identical regardless of execution mode
- **27 automated integration tests**, all passing; 0 failures; 0 deprecation warnings — including 6 graph-engine tests verifying conditional branching, FAILURE-path execution, retry loops, loop limit protection, and graph-based choreography
- 7 design patterns applied with explicit source code citations
- 15 UML diagrams embedded directly in the report
- All critical code quality defects resolved: deprecated APIs replaced, timezone correctness enforced, HTML separated from business logic, FK constraints and uniqueness constraints enforced at the database level

**Evolutionary prototyping in practice:**
The initial prototype proved that the technical foundation (REST API, EventBus, both execution engines) was sound. Stakeholder validation revealed that linear, order-based execution was insufficient for real business workflow semantics — a gap that was invisible from the requirements as first written. This produced UR-10, UR-11, FR-18–FR-21, and Sprint 4. The result is a system whose architecture reflects requirements as understood after validation, not as originally specified.

**Scrum achievements:**
- 20 user stories with Given/When/Then acceptance criteria (17 delivery + 3 evolution)
- 4 Sprint Backlogs with full Planning → Tasks → Review → Retrospective cycles
- Burndown charts for all 4 sprints
- Backlog refinement documented with sprint-by-sprint evolution, including the post-validation evolution trigger
- Full Requirements Traceability Matrix: UR → FR → US → Sprint → Task → Test — covering all 21 FRs and all 9 NFRs

**Key engineering insight — BUG-02:**
The choreography chain executing downstream tasks after an upstream failure is a bug class that *cannot occur* in orchestration. Its root cause (unconditional event emission), one-line fix (`if ok_task:`), and named regression test (`test_choreography_stops_on_failure`) demonstrate a practical difference between the two patterns that textbook descriptions cannot convey.

**Primary process failure:**
Testing was deferred to Sprint 3 in both Sprint 1 and Sprint 2, despite retrospective action items. BUG-02 survived from Sprint 2 until Sprint 3 testing precisely because there were no tests. The correct practice is to write tests within the sprint that introduces the feature.

---

## 24. References

1. Hohpe, G., Woolf, B. (2003). *Enterprise Integration Patterns: Designing, Building, and Deploying Messaging Solutions.* Addison-Wesley Professional. ISBN 978-0-321-20068-6.
2. Gamma, E., Helm, R., Johnson, R., Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software.* Addison-Wesley Professional.
3. Richardson, C. (2018). *Microservices Patterns: With Examples in Java.* Manning Publications.
4. Schwaber, K., Sutherland, J. (2020). *The Scrum Guide.* scrumguides.org. Retrieved 2024.
5. Fowler, M. (2014). *Microservices.* martinfowler.com/articles/microservices.html.
6. FastAPI Documentation. (2024). https://fastapi.tiangolo.com/
7. SQLAlchemy 2.0 Documentation. (2024). https://docs.sqlalchemy.org/en/20/
8. Apache Kafka Documentation. (2024). https://kafka.apache.org/documentation/
9. Python Software Foundation. (2024). *unittest.mock.* https://docs.python.org/3/library/unittest.mock.html
10. pytest Documentation. (2024). https://docs.pytest.org/

---

## Appendix A — Self-Assessment

### Strengths of This Report

- **All 13 professor comments addressed** with specific section citations (including "sequential execution" criticism addressed via graph engine)
- **15 UML diagrams fully embedded** — no external file navigation required; all proper UML; ER diagram now includes `workflow_transitions` and `task_executions`; Package diagram includes `transitions` module
- **Traceability is complete** — all 21 FRs and all 9 NFRs traced from UR through user story, sprint task, to automated test (§13)
- **Full ACs embedded** — Given/When/Then acceptance criteria for all 20 stories in §7.2 (no external file)
- **27 automated integration tests, all passing** — including 6 graph engine tests (branching, FAILURE path, retry loop, loop limit, choreography graph)
- **Evolutionary prototyping demonstrated concretely** — §1.3 documents the prototype→validation→gap discovery→evolution cycle; Sprint 4 provides full Scrum documentation of the evolution
- **BUG-02 analysis** provides a genuine engineering insight not available from textbook reading
- **Retrospectives are honest** — deferred testing is documented as a process failure in all three delivery sprints, not minimised
- **NFRs are measurable** — each has a metric, target, acceptance criterion, and test citation
- **Kafka scope is clearly bounded** — §16.9 accurately describes that Kafka applies to legacy choreography only; the graph path uses EventBus; no overclaiming

### Remaining Weaknesses

| # | Weakness | Severity |
|---|---|---|
| W-01 | Burndown charts are reconstructed estimates, not live-tracked data | Medium |
| W-02 | Dashboard (US-09, US-10) tested manually only — no automated browser test | Medium |
| W-03 | Password security (plaintext) is acknowledged but not mitigated within project scope | Medium |
| W-04 | No performance benchmarks — NFR response time measurement was descoped due to synchronous execution blocking | Low |

### Lessons Learned

**Requirements engineering.** Separating user requirements from system functional requirements and non-functional requirements from the outset proved valuable. In Sprint 2 it became evident that UR-09 (execution model flexibility) had been written at solution level rather than problem level; correcting it retroactively demonstrated how solution-biased requirements create traceability gaps downstream.

**Scrum process discipline.** Deferring test writing to Sprint 3 was the most consequential process failure. The Definition of Done explicitly required automated tests per story, yet this was not enforced in Sprints 1 and 2. The consequence was that BUG-02 — a correctness defect in the choreography failure path — survived undetected for the entire Sprint 2 delivery. This reinforces the engineering principle that a Definition of Done is a quality gate, not a documentation artefact.

**Event-driven architecture.** The Python closure variable-capture problem in the choreography handler registration loop is a real-world concurrency/correctness hazard. Resolving it through default-parameter evaluation at definition time is a transferable pattern applicable to any callback-registering system in Python.

**UML as a design tool.** Drawing the Activity Diagram for `run_task()` before refining the retry logic forced explicit representation of the 70%/21%/9% probability branches and the conditional event emission. The diagram revealed that the original code emitted `task_completed` on both success and failure paths — the visual representation made the defect obvious where code review had not.

**Academic documentation.** Retrospectively documenting a Scrum process that was not fully followed is an ethical challenge. The honest approach taken here — acknowledging deferred testing, reconstructed burndown data, and a solo team's inability to validate its own acceptance criteria — provides more academic value than a sanitised account would.

