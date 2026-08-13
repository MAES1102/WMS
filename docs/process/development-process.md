# Development Process Record

## Purpose and evidence policy

This document records the development process for the University of Messina Software Engineering project developed by Yermek Aubayev. The instructor is the stakeholder and reviewer; private contact details are intentionally excluded. Because this is a solo academic project, the student performs the product, development, testing, configuration-management, and documentation responsibilities. Review and approval authority remains with the instructor or the explicitly authorized reviewer.

Historical statements use these classifications:

- `VERIFIED`: supported directly by durable Git, repository, or remote-ref evidence.
- `RECONSTRUCTED`: inferred retrospectively from code, commits, or documents, but not supported by contemporaneous process evidence.
- `PLANNED`: proposed or otherwise identified future work that has not been implemented; the classification does not imply approval.
- `UNVERIFIED`: asserted historically but not supported by available durable evidence.
- `INCONCLUSIVE`: verification was attempted but produced no result.

These classifications apply throughout the linked [evidence register](./evidence-register.md), [sprint record](./sprint-record.md), and [feedback register](./feedback-register.md).

## Selected and tailored process

The recorded methodology is three one-week delivery sprints followed by one evolution sprint. It is described as a tailored, incremental Scrum process for a solo academic project. The baseline report contains Product Backlog, Sprint Backlog, review, retrospective, and burndown narratives, but the available Git history does not independently establish when ceremonies occurred or whether all artifacts were maintained contemporaneously. Those detailed historical process claims are therefore `RECONSTRUCTED` or `UNVERIFIED`, not proof of full Scrum compliance.

Solo tailoring assigns responsibilities as follows:

| Responsibility | Responsible role | Independent gate |
|---|---|---|
| Backlog preparation, implementation, tests, UML, and documentation | Student developer | Review at the applicable checkpoint |
| Configuration and evidence capture | Student developer | Exact Git/ref and validation evidence |
| Stakeholder feedback | Instructor as stakeholder/reviewer | Feedback record without private correspondence |
| Change approval, commit approval, and push approval | Explicit reviewer/approver | Explicit approval required |

This project does not claim to follow RUP. Selected RUP change-control practices are used only as useful control techniques.

## Core process activities

The activity model follows the four common software-process activities in `4 - SwProc.pdf`, slide 3. Product, role, precondition, and post-condition fields follow slide 5.

| Activity | Inputs | Outputs/products | Responsible role | Preconditions | Completion evidence | Current classification |
|---|---|---|---|---|---|---|
| Specification | Stakeholder need, feedback, approved change request | Requirements, acceptance conditions, scope boundaries, traceability | Student developer; reviewer approves | Problem and scope recorded | Reviewed requirements and links to source evidence | Requirements v3 3.0 and synchronized traceability are the current project-level approved specification baseline; no instructor approval or implementation evidence is claimed |
| Design and implementation | Approved requirements and architecture decisions | Domain model, persistence, resolver, execution modes, UI, deployment increment | Student developer | Relevant checkpoint approved | Reviewable diff, matching UML, deterministic verification | C5A foundation source is published at `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0`; executable verification and complete checkpoint-5 acceptance are absent; affected implementation is paused for CR-002 review |
| Verification and validation | Implemented increment and acceptance conditions | Test results, trace, review findings, release recommendation | Student developer; reviewer decides gate | Clean isolated environment and known baseline | Reproducible results and unchanged repository/runtime evidence | `PLANNED`; archive attempt is `INCONCLUSIVE` |
| Evolution | Change proposal, preserved baseline, impact analysis, risk register | Controlled increments and updated traceability | Student developer; reviewer controls gates | Baseline and historical prototype preserved | Approved change artifacts and checkpoint evidence | CR-001 is approved; its implementation progressed through the published C5A foundation without executable verification or full acceptance. CR-002 and Requirements v3 passed project-level review; no instructor or implementation approval is claimed. |

The incremental approach is supported by `4 - SwProc.pdf`, slides 34-39: change creates rework; prototypes and increments can reduce change cost; incremental development supports feedback; and visibility and structural degradation require regular deliverables and refactoring. Plan-driven and agile elements may coexist (slide 6). The process therefore combines an explicit gate plan with incremental implementation.

## Change-control workflow

The controlled workflow is:

1. Change identification.
2. Change request.
3. Impact analysis.
4. Review and approval.
5. Requirements update.
6. Architecture and UML update.
7. Controlled implementation.
8. Verification and validation.
9. Release decision.
10. Documentation and traceability update.

Stage 2 created and committed [CR-001](../evolution/CR-001-defense-core-refactoring.md) and its approved impact analysis. Stage 3 established Requirements v2, and checkpoint 4 established the approved architecture/ADR/UML baseline. C5A later published definition, validation, resolver, and persistence-foundation source at `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0`; source presence is recorded by EV-027, not as executable verification or complete checkpoint-5 acceptance.

FB-004 triggered [CR-002](../evolution/CR-002-invoice-approval-reference-application.md) at change-control steps 1-3. Project-level CR review, [Requirements v3](../requirements/requirements-v3.md), and the affected [architecture v3](../architecture/architecture-overview-v3.md) review passed on `2026-08-13`. Requirements v3 3.0 and architecture v3 are the current project-level specification/design baselines while Requirements v2 and checkpoint 4 remain historical. V3 implementation, executable testing, reference-browser acceptance, and OS-process restart verification have since completed at project level; external deployment and release have not started.

The workflow is consistent with `11 - sw evolmaintenance.pdf`, slides 8-12: change proposals drive evolution, affected components support cost and impact estimation, and implementation follows requirements analysis and updating. Slides 17 and 24 frame useful-system change and functional enhancement; slides 33-34 and 55 support maintainability evidence, re-documentation, and continuous refactoring.

## Configuration management

| Controlled item | Meaning | Evidence classification |
|---|---|---|
| `v1-linear-baseline` | Immutable annotated baseline tag peeling to `f5ea4d71ebb4082cebe4f7e7a8a5ad3fcdfbfbaa` | `VERIFIED` locally and remotely |
| `archive/advanced-prototype` | Preserved historical prototype at `5d18b469b77beb22e6721f769fbd1b39223955a3` | `VERIFIED` locally and remotely |
| `refactor/defense-core` | Preserves the staged evolution from the linear baseline through process, requirements, architecture, and the C5A foundation. The controlled CR-002 base is commit `958d4f7f2b8b58dfb3cef2c3242082fa5a018ab0` on `origin/refactor/defense-core`. | `VERIFIED` by the checkpoint records, EV-027, local Git, and the remote ref |
| `main` | Unchanged baseline branch | `VERIFIED` locally and remotely |

Commits and pushes require explicit approval. The controlled workflow prohibits reset, force push, and history rewriting. Branches and tags are not replaced or deleted as an implicit recovery action. This configuration-control approach is supported by `4 - SwProc.pdf`, slides 74-76, which discuss change/configuration management, iterative development, managed requirements, visual modeling, quality verification, and controlled software changes.

## Review gates

Only one checkpoint may advance at a time:

1. Version preservation - complete and durably verified.
2. Process documentation and change request - substantively reviewed and approved; durability established by the Stage 2 documentation commit.
3. Requirements v2 - complete; substantively reviewed, approved, and committed by the Stage 3 documentation commit.
4. Architecture, ADR, and UML baseline - substantively reviewed and `APPROVED — checkpoint 4 architecture baseline`; Git durability of the accepted architecture baseline is established by commit f44f0d55349af4e7b1b19b49f5e3b26c67c96181 and the independently verified origin/refactor/defense-core ref.
5. Backend domain-model foundation - C5A source published; executable verification and full acceptance incomplete.
6. Execution verification - accepted at project application level by PBI-E23.
7. UI - accepted for the reference Chromium desktop/mobile boundary by PBI-E24.
8. Deployment - accepted for inventory and OS-process restart; container build was unavailable and is not claimed.
9. Final report - reconciled and accepted at project level by PBI-E26; Git durability and instructor approval remain separate gates.

The PBI-E17 [compatibility plan](../implementation/checkpoint-5a-v3-implementation-plan.md) and increments 5A.1–5A.3 passed project-level review. PBI-E18 provides bounded submission/validation. PBI-E19 provides persistent human waiting, one authoritative decision, same-cursor resume, and query projection. PBI-E20 provides centralized same-run execution, archive/manual-action effects, one final notification, and five passing orchestration scenarios. The E20A preview registers the invoice path through a separate database and makes it visible at `/ui` while preserving `/legacy-ui`. PBI-E21 adds run-scoped choreography, dual-mode runtime selection, ten scenario executions, five normalized pair comparisons, and subscriber cleanup. PBI-E22 adds bounded draft CRUD, closed-catalog configuration, full graph feedback, and immutable revision activation. PBI-E23 adds repeated normalized runs, exact trace expectations, file-backed restart/resume, threaded run isolation, complete PDF-to-no-approval boundaries, dependency inspection, and recorded status-read timing. PBI-E24 makes the persisted business result and next action explicit, defers trace/configuration details, and passes the reference Chromium desktop/mobile acceptance path in both modes. PBI-E25 replaces the broker compose topology with one persistent FastAPI target and verifies both modes across real process recreation. PBI-E26 reconciles the product-first report, vector UML, reuse disclosure, defense script, and final claim ledger. The next controlled action is configuration-management review, not another feature increment.

A later stage may begin only after the previous checkpoint is reviewed. The applicable quality criteria are defined in the [Definition of Done](./definition-of-done.md), and current threats are tracked in the [risk register](./risk-register.md).

## Course basis

- `4 - SwProc.pdf`, slides 3 and 5-6: process activities, process products/roles/conditions, and mixed incremental planning.
- `4 - SwProc.pdf`, slides 34-39: change, rework, prototyping, incremental development, visibility, and structural degradation.
- `4 - SwProc.pdf`, slides 74-76: configuration/change management, iterative delivery, requirements management, UML, quality verification, and change control. These are referenced practices, not a claim that the project uses RUP.
- `11 - sw evolmaintenance.pdf`, slides 8-12 and 17: change proposals, impact analysis, release planning, requirements updating, implementation, and continuing evolution.
- `11 - sw evolmaintenance.pdf`, slides 24, 33-34, and 55: enhancement maintenance, maintainability indicators, re-documentation/restructuring, and continuous refactoring.
- `6 - Requirement Engineering.pdf`, slides 6, 9, 14, and 19: user/system requirements, functional/non-functional requirements, and objectively verifiable NFRs.
- `6 - Requirement Engineering.pdf`, slides 25, 31, 33, and 39: requirements-document purpose, user/system specification, atomic natural-language statements, and structured specification.
- `6 - Requirement Engineering.pdf`, slides 67, 69, 71, and 76-78: validation, review techniques/checks, unique identification, traceability, impact analysis, and controlled requirements change.

## Related records

- [Product backlog](./product-backlog.md)
- [Sprint record](./sprint-record.md)
- [Feedback register](./feedback-register.md)
- [Evidence register](./evidence-register.md)
- [Risk register](./risk-register.md)
- [Definition of Done](./definition-of-done.md)
- [CR-001](../evolution/CR-001-defense-core-refactoring.md)
- [CR-002](../evolution/CR-002-invoice-approval-reference-application.md)
- [Requirements v3](../requirements/requirements-v3.md)
- [Requirements v3 traceability](../requirements/requirements-traceability-v3.md)
