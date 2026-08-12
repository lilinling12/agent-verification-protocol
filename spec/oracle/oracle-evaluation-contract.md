# AVP Oracle Evaluation Contract v0.1

Status: Draft normative candidate.

This specification defines portable Oracle verification semantics. It intentionally does **not** standardize Python APIs, subprocess/container/microVM selection, IPC framing, operating-system limits, filesystem layout, or network-sandbox implementation.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as BCP 14 requirement levels.

## Model

An **Oracle** is a privileged evaluator that computes verification results from declared evaluation inputs and Evidence. An Oracle is not the Subject Agent. Evaluator malfunction is therefore not evidence that the Subject failed its task.

Portable Oracle evaluation has three orthogonal outcome layers:

- task verdict: whether available verification supports task success;
- evaluation validity: whether the evaluation is trustworthy enough to support that verdict;
- validity detail: diagnostic information explaining an invalid evaluation.

For Oracle execution failure, the stable evaluation validity is `ORACLE_FAILURE`; runner-specific causes are represented by `validityDetail.code`.

## Normative requirements

### AVP-ORACLE-001 Oracle identity binding

A verifier **MUST** bind each Oracle evaluation to a non-empty Oracle identifier, version, and immutable SHA-256 package/content digest. The bound identity **MUST** be available in the Episode manifest, evaluation record, or equivalent auditable record.

### AVP-ORACLE-002 Declared input scope

An Oracle **MUST** receive only evaluation inputs, projections, and Evidence capabilities declared for that Oracle evaluation. A portable Oracle input contract **MUST NOT** expose live mutable Subject handles or unrestricted privileged evaluator/runtime handles.

This requirement constrains the observable capability boundary, not the implementation technology used to enforce it.

### AVP-ORACLE-003 Evaluation input integrity

A verifier **MUST** integrity-bind the Oracle evaluation inputs to the relevant Episode context so that substitution can be detected. The binding **MUST** cover the Oracle/package identity and the evaluated scenario/manifest/projection input identities or an equivalent cryptographic representation.

### AVP-ORACLE-004 Oracle failure is not task failure

An Oracle execution failure **MUST NOT** by itself produce task verdict `FAIL`. When Oracle failure prevents a valid task evaluation, the task verdict **MUST** be `INCONCLUSIVE` and the Episode evaluation **MUST** be invalid.

### AVP-ORACLE-005 Stable Oracle failure validity

An Oracle execution failure **MUST** use top-level evaluation validity `ORACLE_FAILURE`. A verifier **MUST** preserve a non-empty `validityDetail.code` sufficient to distinguish the failure cause when the cause is known.

AVP v0.1 defines these interoperable Oracle detail codes:

- `ORACLE_TIMEOUT`
- `ORACLE_CRASH`
- `ORACLE_PROTOCOL_ERROR`
- `ORACLE_SECURITY_VIOLATION`

Implementations **MAY** add implementation-specific detail codes through extension mechanisms, but those codes do not create new top-level evaluation-validity classes.

### AVP-ORACLE-006 Oracle result Evidence integrity

A verification result produced by an Oracle **MUST NOT** be accepted if it references Evidence that is absent from the evaluation output/registry or whose Artifact bytes fail the declared Evidence integrity contract. Such a condition invalidates the Oracle evaluation; it does not establish Subject task failure.

### AVP-ORACLE-007 Auditable Oracle execution record

A verifier **MUST** preserve an auditable record that binds the Oracle/package identity, evaluation input identity, execution outcome, and any verification results accepted from that execution. The record **MUST** be immutable from the completed/invalid Episode's verification perspective.

## Validity detail

`validityDetail` is diagnostic metadata attached to evaluation validity. It is not a second task verdict and MUST NOT override task-verdict semantics.

A portable validity detail contains:

- `code`: a stable non-empty token;
- optional human-readable `message`;
- optional Evidence references supporting the invalidity diagnosis.

Sensitive evaluator internals, credentials, raw secrets, stack traces, or hidden benchmark answers MUST NOT be exposed merely to populate a validity detail.

## Oracle execution technology

A conforming implementation may execute an Oracle in a subprocess, container, microVM, remote service, WebAssembly sandbox, or another mechanism provided the observable requirements above are satisfied.

The reference implementation's `avp.oracle/v2` worker framing, resource-limit values, module allowlist, and process-launch strategy are implementation details and do not define AVP conformance.

## Relationship to Security profile

This contract preserves the evaluator privilege boundary but does not complete AVP Security conformance. Subject inability to reach evaluator endpoints, evaluator secret isolation, future-fault secrecy, answer-key secrecy, and Judge mutation controls are specified/tested by the separate Security profile.
