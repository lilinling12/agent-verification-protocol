# AVP Core — Episode Lifecycle

Status: Draft Normative Candidate for AVP v0.1.

The normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY follow BCP 14.

## 1. Scope

This specification defines the observable lifecycle semantics of an Agent Verification Protocol (AVP) Episode. It defines interoperability requirements for lifecycle observation and verification evidence.

This specification does not define scheduler topology, worker models, queues, deployment architecture, or runtime implementation details.

## 2. Episode

An Episode is one bounded verification execution of a Scenario Instance against an identified Agent System configuration.

An Episode MUST have exactly one lifecycle state at any point in time.

## 3. Lifecycle States

The following states are defined by AVP Core:

| State | Meaning |
|---|---|
| CREATED | Episode identity exists and verification scope is established. |
| PROVISIONING | Verification environment is being prepared. |
| READY | Required execution prerequisites are satisfied. |
| RUNNING | Subject execution is active. |
| PAUSED | Execution is intentionally suspended. Optional state. |
| QUIESCING | Execution is stopping and side effects are being stabilized. |
| VERIFYING | Evaluator is producing verification evidence and results. |
| COMPLETED | Lifecycle execution reached normal completion. |
| ABORTED | Execution was intentionally terminated before completion. |
| INVALID | Evidence cannot represent a valid evaluation. |
| INFRA_FAILED | Evaluation infrastructure prevented valid execution. |

Implementations MUST NOT expose internal runtime states as AVP states unless their semantics match this specification.

## 4. Transition Semantics

A lifecycle transition MUST record:

- previous state;
- resulting state;
- transition timestamp;
- transition cause or reference.

The normal lifecycle ordering is:

CREATED -> PROVISIONING -> READY -> RUNNING -> QUIESCING -> VERIFYING -> COMPLETED

PAUSED MAY occur from RUNNING and MUST resume only according to the implementation profile.

## 5. Terminal States

COMPLETED, ABORTED, INVALID, and INFRA_FAILED are terminal lifecycle classifications.

A terminal Episode MUST NOT transition back into an executable state.

## 6. Result Separation

Lifecycle completion MUST NOT imply task success.

Implementations MUST distinguish:

- execution outcome;
- task verdict;
- verification validity.

A COMPLETED Episode MAY have a failed task verdict.

An INVALID or INFRA_FAILED Episode MUST NOT automatically be interpreted as an Agent task failure.

## 7. Replay

A replayed Episode MUST preserve reference identity metadata required to identify the original verification scope.

## 8. Non Goals

AVP Core does not standardize:

- Agent architecture;
- model providers;
- orchestration frameworks;
- infrastructure platforms;
- benchmark scoring algorithms.

## 9. Requirements

- AVP-CORE-001
- AVP-CORE-002
- AVP-CORE-003
- AVP-CORE-004
- AVP-CORE-005
- AVP-CORE-006
- AVP-CORE-007
