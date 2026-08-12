# AVP Core — Episode Lifecycle

Status: Draft Normative Candidate for AVP v0.1.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in BCP 14 (RFC 2119 and RFC 8174) when, and only when, they appear in all capitals.

## 1. Scope

This specification defines the observable lifecycle semantics of an Agent Verification Protocol (AVP) Episode. Its purpose is to make execution ordering, termination, evidence boundaries, and replay interpretation comparable across independent AVP implementations without standardizing scheduler topology, worker processes, queues, deployment architecture, or Agent internals.

An implementation MAY use additional private states internally. Those states do not become AVP states. A conforming implementation MUST always be able to project the externally observable Episode onto the AVP Core lifecycle defined here.

## 2. Episode identity

An **Episode** is one bounded verification execution of one Scenario Instance against an identified Agent System configuration and an identified verification configuration.

The Episode identifier is stable for the lifetime of that Episode. Re-execution or replay creates another Episode identity and retains an explicit reference to the source Episode rather than reusing the original identifier.

## 3. Core state vocabulary

AVP Core defines the following lifecycle states.

| State | Requirement | Semantics |
|---|---|---|
| `CREATED` | required | Episode identity and verification scope exist; execution has not begun. |
| `PROVISIONING` | required | Required verification environment state and capabilities are being prepared or reset. |
| `READY` | required | Preconditions required to invoke the Subject are satisfied. |
| `RUNNING` | required | Subject execution is active and Subject-initiated side effects may occur. |
| `PAUSED` | optional capability | Subject execution is intentionally suspended while the Episode remains resumable. |
| `QUIESCING` | required | Subject execution is ending and externally visible side effects are being stabilized before verification. |
| `VERIFYING` | required | Evaluator-owned verification is executing against authorized evidence/state. |
| `COMPLETED` | required terminal | The verification lifecycle reached normal completion. This says nothing about task success. |
| `ABORTED` | required terminal | The Episode was intentionally terminated before normal completion. |
| `INVALID` | required terminal | The run cannot be interpreted as valid evaluation evidence about the Agent System. |
| `INFRA_FAILED` | required terminal | Verification infrastructure prevented the Episode from reaching a valid normal completion. |

`PAUSED` is the only optional AVP Core lifecycle state in v0.1. An implementation that does not advertise pause support MUST NOT emit `PAUSED`.

## 4. Lifecycle projection and observability

At every observable instant an Episode has exactly one AVP lifecycle state. Internal implementation substates MAY exist, but they MUST NOT make the AVP projection ambiguous.

Every observable state change is represented as a transition record. Transition records form an ordered sequence for an Episode. Wall-clock time MAY be included for correlation, but lifecycle ordering MUST NOT depend on synchronized wall clocks.

A transition record contains at least:

- the stable Episode identifier;
- a monotonically increasing Episode-local transition sequence number;
- the previous AVP state;
- the resulting AVP state; and
- a machine-readable transition cause code.

Implementations MAY add profile or vendor metadata under an extension field without changing Core state semantics.

## 5. Normative transition relation

The following transition relation is the AVP Core v0.1 state machine. A transition not present in this table is illegal unless a future negotiated AVP profile explicitly extends the lifecycle while preserving a valid Core projection.

| From | Allowed next states |
|---|---|
| `CREATED` | `PROVISIONING`, `ABORTED` |
| `PROVISIONING` | `READY`, `ABORTED`, `INVALID`, `INFRA_FAILED` |
| `READY` | `RUNNING`, `ABORTED`, `INVALID`, `INFRA_FAILED` |
| `RUNNING` | `QUIESCING`, `ABORTED`, `INVALID`, `INFRA_FAILED`, and `PAUSED` when pause is supported |
| `PAUSED` | `RUNNING`, `ABORTED`, `INVALID`, `INFRA_FAILED` |
| `QUIESCING` | `VERIFYING`, `ABORTED`, `INVALID`, `INFRA_FAILED` |
| `VERIFYING` | `COMPLETED`, `ABORTED`, `INVALID`, `INFRA_FAILED` |
| `COMPLETED` | none |
| `ABORTED` | none |
| `INVALID` | none |
| `INFRA_FAILED` | none |

The normal successful lifecycle path is:

```text
CREATED -> PROVISIONING -> READY -> RUNNING -> QUIESCING -> VERIFYING -> COMPLETED
```

The table defines semantic phase ordering, not the number of threads, workers, services, processes, containers, or scheduling steps used to implement a phase.

## 6. Quiescing boundary

`QUIESCING` is the protocol boundary between Subject execution and evaluator-owned verification preparation. After entry into `QUIESCING`, an implementation MUST NOT initiate a new Subject-requested side effect for that Episode. Operations already accepted before the transition MAY be allowed to settle according to the applicable Environment/Profile contract, and their effects remain evidence.

This rule prevents verification from racing with newly initiated Subject actions while allowing an implementation to stabilize in-flight work.

## 7. Terminal semantics

`COMPLETED`, `ABORTED`, `INVALID`, and `INFRA_FAILED` are terminal. No terminal Episode may re-enter an executable or verification state.

Terminal lifecycle state is not a Task Verdict:

- `COMPLETED` does **not** mean `PASS`;
- `ABORTED` does not establish Agent failure;
- `INVALID` does not establish Agent failure; and
- `INFRA_FAILED` does not establish Agent failure.

Detailed validity and failure taxonomies are specified separately. A lifecycle implementation MUST preserve the distinction between lifecycle state, Task Verdict, and Validity even when a product UI chooses to summarize them together.

## 8. Replay

Replay is a new Episode, not mutation of a completed Episode. A replay preserves reference identity sufficient to identify the source Episode and the verification inputs selected for replay. Reproducibility semantics for Scenario Instance, seeds, artifacts, Environment state, and Agent configuration are defined by their respective AVP specifications.

## 9. Extension rule

Profiles MAY define additional internal or externally reported substates only when:

1. every reported moment still has exactly one unambiguous AVP Core state projection;
2. Core transition ordering is not bypassed;
3. terminal immutability is preserved; and
4. an implementation that understands only AVP Core can still interpret the Episode lifecycle safely.

Extensions MUST NOT redefine the semantics of a Core state.

## 10. Normative requirements

### AVP-CORE-001 — Single active state

An Episode **MUST** have exactly one AVP lifecycle state at every observable instant.

### AVP-CORE-002 — Ordered observable transitions

Every observable lifecycle state change **MUST** produce an Episode-local ordered transition record.

### AVP-CORE-003 — Stable Episode identity

An Episode **MUST** retain one stable Episode identifier for its lifetime.

### AVP-CORE-004 — Transition record minimum

A transition record **MUST** contain the Episode identifier, a monotonically increasing Episode-local sequence number, the previous state, the resulting state, and a machine-readable cause code.

### AVP-CORE-005 — Terminal immutability

A terminal Episode **MUST NOT** transition to any other lifecycle state.

### AVP-CORE-006 — Result-dimension separation

An implementation **MUST** represent lifecycle state, Task Verdict, and Validity as distinct protocol dimensions.

### AVP-CORE-007 — Replay reference identity

A replayed Episode **MUST** have a new Episode identifier and **MUST** preserve an explicit reference to its source Episode.

### AVP-CORE-008 — Core state projection

A conforming AVP Core implementation **MUST** support an unambiguous projection onto all required Core states defined in Section 3.

### AVP-CORE-009 — Transition relation enforcement

An implementation **MUST** reject or classify as protocol-invalid any lifecycle transition not permitted by Section 5 for the negotiated profile.

### AVP-CORE-010 — Lifecycle is not Task Verdict

`COMPLETED`, `ABORTED`, `INVALID`, and `INFRA_FAILED` **MUST NOT** be interpreted as Task Verdict values.

### AVP-CORE-011 — Quiescing side-effect boundary

After entering `QUIESCING`, an implementation **MUST NOT** initiate a new Subject-requested side effect for that Episode.

### AVP-CORE-012 — Conditional pause semantics

If an implementation advertises pause support, it **MUST** enter `PAUSED` only from `RUNNING`, and it **MUST** leave `PAUSED` only for `RUNNING` or a terminal state permitted by Section 5.

## 11. Non-goals

This lifecycle specification does not standardize Agent architecture, model providers, orchestration frameworks, infrastructure platforms, benchmark scoring algorithms, UI status labels, or commercial control-plane scheduling states.
