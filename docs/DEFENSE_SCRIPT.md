# Defense Script — Event-Driven Workflow Management System

## 30-second opening

“This is not a simulator of green workflow nodes. It is an purchase-request-approval application. A user submits one purchase request structured purchase request data. The system validates it, pauses for a real human decision, resumes the same persisted run, authorizations an approved document or records another controlled outcome, creates an internal notification, and preserves the audit trace. I implemented that same business process with orchestration and choreography so their control-flow trade-off can be compared without changing the business rules.”

## Five-minute demonstration

### 1. Establish the product value — 40 seconds

Open `/ui`. Point to the purchase request form and say what the user receives: purchase request identity, current business state, required next action, final result, execution mode, and optional audit evidence.

Do not open the constructor or raw trace yet.

### 2. Approved orchestration path — 80 seconds

1. Select orchestration.
2. Submit the prepared valid structured purchase request data.
3. Show `PENDING_APPROVAL` and “Review and decide this purchase request.”
4. Explain that the HTTP request finished and the cursor/work item are persisted.
5. Approve the purchase request.
6. Show `AUTHORIZED`, “Approved and authorized,” and “No action required.”

Key sentence: “The green steps support the result; they are not the result.”

### 3. Failure with business meaning — 60 seconds

Use the visible **Demonstration scenario** selector.

- Select **Authorization fails once, then succeeds**, approve, and show two authorization attempts, one retry observation, then `AUTHORIZED`.
- If time permits, select **Authorization remains unavailable**, approve, and show `NEEDS_MANUAL_ACTION` after the bound is exhausted.

Key sentence: “A technical retry repeats the same task and selects no graph edge. Only after the bound is exhausted does normal failure routing continue.”

### 4. Choreography parity — 70 seconds

Run the equivalent approved case in choreography. Show the same final business state. Then open only the relevant trace observations.

Explain: “Choreography changes who triggers the next committed step. It does not own another copy of purchase request, retry, or routing policy. The handler is scoped to one active run and is removed while waiting.”

### 5. Architecture and evidence — 50 seconds

Show the shared activity diagram and the two sequence diagrams. Then state:

- five scenarios × two modes;
- five normalized mode comparisons;
- 205 passing repository tests after final product consolidation;
- both modes resume a waiting purchase request after real Uvicorn process recreation;
- one application service and no Kafka/ZooKeeper.

Finish with the limitation: the product is a bounded academic application, not an authenticated production accounting or payment system.

## Likely questions

### How does the system know whether a payment succeeded?

It does not process a bank payment. The bounded product is purchase request approval. Outcomes come from metadata/structured input validation, the human approve/reject decision, authorization behavior, and deterministic test faults. A real payment adapter is outside scope.

### Why have both orchestration and choreography?

To compare control placement under identical semantics. Orchestration is simpler to follow; choreography demonstrates event-triggered advancement but requires strict handler cleanup, persistent cursor state, and version checks.

### Why no Kafka?

The project is one application, and a distributed broker adds infrastructure without improving this bounded comparison. The EventBus is in-process and never authoritative for waiting state.

### What is custom here?

The graph validator, transition resolver integration, retry classification and bounds, persistent human lifecycle, idempotent decision, run isolation, cursor/version rules, two execution strategies, business projections, constructor boundary, and acceptance matrix. Framework/ORM/structured input/test libraries are disclosed reuse.

### Is the constructor a low-code platform?

No. It is an optional advanced form for four built-in task types and three transition conditions. It accepts no user code, scripts, expressions, or plugins.

### What survives restart?

Workflow revisions, purchase request/run state, cursor, attempts, work item, decision, notification, ordered trace, and stored document. EventBus subscriptions do not survive and do not need to.

### Why is the failure selectable?

The selector is a deterministic demonstration adapter for authorization availability. It is persisted with the run, produces repeatable evidence, and never decides whether the purchase request is approved. The actual business decision still comes from the approver; the adapter only demonstrates bounded technical failure handling.

### What would you do next?

Repeat container startup on the defense machine, perform external usability/accessibility testing, and add authentication if the application were moved beyond the academic boundary. I would not add another large feature before those steps.

## Closing sentence

“The project’s significance is controlled, explainable workflow behavior around failure and time: invalid input cannot reach approval, retries are bounded, a human decision can arrive after restart, duplicate decisions cannot advance twice, and both control strategies produce the same purchase request outcome.”
