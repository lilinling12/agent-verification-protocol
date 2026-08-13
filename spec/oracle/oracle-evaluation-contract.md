# AVP Oracle Evaluation Contract v0.1

Status: Draft normative candidate.

This specification defines portable Oracle verification semantics. It intentionally does **not** standardize Python APIs, subprocess/container/microVM selection, IPC framing, operating-system limits, filesystem layout, network-sandbox implementation, or one portable Oracle package archive format.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as BCP 14 requirement levels.

## Model

An **Oracle** is a privileged evaluator that computes verification results from declared evaluation inputs and Evidence. An Oracle is not the Subject Agent. Evaluator malfunction is therefore not evidence that the Subject failed its task.

Portable Oracle evaluation has three orthogonal outcome layers:

- task verdict: whether available verification supports task success;
- evaluation validity: whether the Oracle evaluation is trustworthy enough to support that verdict;
- validity detail: diagnostic information explaining an invalid Oracle evaluation.

For Oracle execution failure, the stable evaluation validity is `ORACLE_FAILURE`; runner-specific causes are represented by `validityDetail.code`.

An **Oracle Execution Record** is the immutable runner-side record of what was executed. It binds the Oracle package identity, evaluation input identity, execution status, and Oracle output identity.

An **Oracle Evaluation Record** is the verifier-side record of what was accepted. It binds the Oracle identity and inputs to the execution record, the Oracle evaluation validity, the task verdict produced by that Oracle evaluation, the accepted verification results, and the Evidence identities supporting those results.

Oracle evaluation validity is not the same as final Episode validity. For example, an Oracle Evaluation Record can be `VALID` while the Episode later becomes `INFRA_CONFOUND` because a required telemetry or persistence gate fails.

## Oracle package identity

`packageDigest` is an opaque SHA-256 identity for the immutable Oracle package representation actually selected for evaluation. The package representation **MUST** cover the executable content and the evaluation-contract metadata necessary to interpret that package, or those declarations **MUST** be separately integrity-bound by the verifier.

AVP Oracle v0.1 deliberately does not prescribe one package archive format or one canonical package serialization. A consumer **MUST** compare `packageDigest` as an identity and **MUST NOT** recompute it from `oracleId`, `version`, or language-specific descriptor fields unless another packaging profile defines the exact digest preimage.

A reference implementation MAY derive `packageDigest` from its own immutable package descriptor. Such derivation is implementation behavior, not a cross-language AVP canonicalization rule.

## Normative requirements

### AVP-ORACLE-001 Oracle identity binding

A verifier **MUST** bind each Oracle evaluation to a non-empty Oracle identifier, version identifier, and immutable SHA-256 package digest. The bound identity **MUST** be available in the Episode manifest, Oracle Evaluation Record, or equivalent auditable record.

### AVP-ORACLE-002 Declared input scope

An Oracle **MUST** receive only evaluation inputs, projections, and Evidence capabilities declared for that Oracle evaluation. A portable Oracle input contract **MUST NOT** expose live mutable Subject handles or unrestricted privileged evaluator/runtime handles.

This requirement constrains the observable capability boundary, not the implementation technology used to enforce it.

### AVP-ORACLE-003 Evaluation input integrity

A verifier **MUST** integrity-bind the Oracle evaluation inputs to the relevant Episode context so that substitution can be detected. The binding **MUST** cover the Oracle/package identity and the evaluated scenario/manifest/projection input identities or an equivalent cryptographic representation.

### AVP-ORACLE-004 Oracle failure is not task failure

An Oracle execution failure **MUST NOT** by itself produce task verdict `FAIL`. When Oracle failure prevents a valid task evaluation, the task verdict **MUST** be `INCONCLUSIVE` and the Oracle evaluation **MUST** be invalid.

### AVP-ORACLE-005 Stable Oracle failure validity

An Oracle execution failure **MUST** use top-level Oracle evaluation validity `ORACLE_FAILURE`. A verifier **MUST** preserve a non-empty `validityDetail.code` sufficient to distinguish the failure cause when the cause is known.

AVP v0.1 defines these interoperable Oracle detail codes:

- `ORACLE_TIMEOUT`
- `ORACLE_CRASH`
- `ORACLE_PROTOCOL_ERROR`
- `ORACLE_SECURITY_VIOLATION`

Implementations **MAY** add implementation-specific detail codes through extension mechanisms, but those codes do not create new top-level evaluation-validity classes.

A `VALID` Oracle Evaluation Record **MUST NOT** contain `validityDetail`.

### AVP-ORACLE-006 Oracle result Evidence integrity

A verification result produced by an Oracle **MUST NOT** be accepted if it references Evidence that is absent from the evaluation output/registry or whose Artifact bytes fail the declared Evidence integrity contract. Such a condition invalidates the Oracle evaluation; it does not establish Subject task failure.

### AVP-ORACLE-007 Auditable Oracle execution and acceptance record

A verifier **MUST** preserve an immutable auditable record that binds the Oracle/package identity, evaluation input identity, execution outcome, and Oracle output identity.

When verification results are accepted from that output, the verifier **MUST** additionally preserve which result values were accepted. The accepted result set **MUST** remain bound to the same Oracle/package, input, and execution identities. If the verifier transforms, filters, enriches, or otherwise changes runner output before acceptance, the accepted representation **MUST** be preserved separately rather than being implied from the raw runner output.

For a successful Oracle evaluation, the Oracle Evaluation Record **MUST** reference an immutable execution record. For a failure that occurs before a runner can produce an execution record, `executionRecordDigest` MAY be absent, but the failure remains subject to the other audit and lifecycle requirements.

## Oracle Evaluation Record

The portable `schemas/oracle-evaluation.schema.json` resource represents verifier acceptance state. It contains:

- `oracle`: `oracleId`, `version`, and opaque `packageDigest`;
- `inputDigest`: identity of the evaluated input context;
- optional `executionRecordDigest`: immutable execution-record identity;
- `evaluationValidity`: `VALID` or `ORACLE_FAILURE`;
- optional `validityDetail`, required for `ORACLE_FAILURE` and forbidden for `VALID`;
- `taskVerdict`;
- `acceptedResults`: the exact verification-result values accepted by the verifier;
- `evidenceIds`: Evidence identities referenced by the accepted result set and/or execution audit chain.

A record with `evaluationValidity: ORACLE_FAILURE` **MUST** use `taskVerdict: INCONCLUSIVE` and **MUST NOT** contain accepted results.

## Validity detail

`validityDetail` is diagnostic metadata attached to invalid Oracle evaluation validity. It is not a second task verdict and MUST NOT override task-verdict semantics.

A portable validity detail contains:

- `code`: a stable non-empty token;
- optional human-readable `message`;
- optional Evidence references supporting the invalidity diagnosis.

Sensitive evaluator internals, credentials, raw secrets, stack traces, or hidden benchmark answers MUST NOT be exposed merely to populate a validity detail.

## Oracle execution technology

A conforming implementation may execute an Oracle in a subprocess, container, microVM, remote service, WebAssembly sandbox, or another mechanism provided the observable requirements above are satisfied.

The reference implementation's worker framing, resource-limit values, module allowlist, package-descriptor canonicalization, and process-launch strategy are implementation details and do not define AVP conformance.

## Relationship to Security profile

This contract preserves the evaluator privilege boundary but does not complete AVP Security conformance. Subject inability to reach evaluator endpoints, evaluator secret isolation, future-fault secrecy, answer-key secrecy, and Judge mutation controls are specified/tested by the separate Security profile.
