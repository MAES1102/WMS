# PBI-E21 — Invoice Choreography Record

| Field | Value |
|---|---|
| Status | `ACCEPTED — project-level implementation` |
| Date | `2026-08-13` |
| Requirements | `FR-013`–`FR-017`, `FR-024`–`FR-026`, `FR-035`, `FR-042`–`FR-047`, `NFR-002`, CON-003 |
| Entry evidence | PBI-E20 accepted; `EV-040`, `EV-041` |
| Instructor approval | `NOT CLAIMED` |

## 1. Implemented control strategy

`InvoiceChoreographer` opens one temporary processing scope for a persisted choreography run. It registers exactly one handler keyed by run identity and publishes synchronous `AdvanceRun(run_id, expected_state_version)` triggers. The event contains no invoice, task result, transition, or mutable business state.

Every handler invocation reloads the authoritative cursor and delegates to the same `AutomaticStepService` or `HumanApprovalService` used by orchestration. A committed step publishes the next committed version. Waiting and terminal state stop dispatch, and a `finally` block removes the run handler after success or any controlled error.

## 2. Persistence and waiting behavior

The EventBus is transient and is not a queue or state store. No subscriber survives human waiting. An approval decision commits the same waiting run and cursor, after which the coordinator inspects the persisted mode and creates a new temporary choreography scope. Missing handlers, duplicate subscriptions, mismatched versions, wrong-run events, and safety-bound exhaustion are controlled errors.

## 3. Shared semantics and visible runtime

The execution coordinator now selects orchestration or choreography from the persisted run mode. Both strategies use the same immutable revision, executor registry, retry policy, resolver, approval lifecycle, transaction adapters, business effects, notification behavior, query projection, and trace vocabulary.

The invoice UI exposes both modes with a short explanation. The run projection and screen show the selected mode so the evaluator can first observe the invoice result and then compare how it was coordinated.

## 4. Verification

- Five business scenarios execute in orchestration and choreography, producing ten concrete cases.
- Five paired comparisons assert equal normalized business state, approval result, archive presence, notification, terminal result, attempts, retries, selected transitions, waiting/resume observations, and trace order.
- EventBus tests verify run-keyed dispatch, duplicate/missing-handler errors, exact unsubscription, and zero retained subscribers after waiting, terminal state, version conflict, or safety error.
- Integrated HTTP tests execute the approved invoice path through both selectable modes and confirm the selected mode in the returned status.
- The final complete isolated repository suite reports `155 passed in 2.54s`.

## 5. Explicit limits and next gate

This increment does not establish process-restart recovery, controlled concurrent-run acceptance, production migration, final cross-browser visual acceptance, constructor behavior, deployment, commit, push, release, or instructor approval. The exact five-pair comparison covers E21 semantic parity but does not close the broader E23 quality matrix.

Next gate: PBI-E22 bounded workflow constructor and immutable activation flow.
