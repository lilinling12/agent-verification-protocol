# AEP-0001 — Oracle Evaluation Contract v0.1

- Status: Proposed
- Authors: AVP maintainers
- Created: 2026-08-13
- Target AVP version: 0.1

## Problem

The historical AVP design defines an Oracle as a privileged evaluator that consumes declared trusted evidence and whose execution failures invalidate evaluation rather than fail the Subject task. The current Python reference implementation already isolates Oracle execution and records detailed runner statuses, but it also exposes `ORACLE_TIMEOUT`, `ORACLE_CRASH`, `ORACLE_PROTOCOL_ERROR`, and `ORACLE_SECURITY_VIOLATION` as top-level `Validity` values.

That implementation detail is not a sound cross-language protocol commitment. It couples AVP's stable evaluation-validity taxonomy to one runner's failure vocabulary and makes implementation behavior appear normative before reconciliation.

## Motivation / interoperability case

Independent AVP implementations need to agree on two different questions:

1. whether an evaluation is valid enough to support a task verdict; and
2. why a particular Oracle execution failed.

The first is a stable protocol classification. The second is diagnostic detail that can evolve with execution technology. Keeping them separate allows a Python subprocess runner, a container runner, a microVM runner, or a remote verifier to report equivalent protocol outcomes without standardizing identical process mechanics.

## Existing standards analysis

AVP reuses JSON Schema for machine-readable resources and SHA-256 content identities already defined by the AVP Evidence contract. This AEP does not define a new sandbox format, package-signing format, RPC transport, or process protocol. Existing implementation-specific framing such as `avp.oracle/v2` remains reference-runtime behavior.

## Proposed semantics

1. Every Oracle evaluation is bound to an Oracle identity consisting of an identifier, semantic version, and immutable package/content digest.
2. An Oracle receives only declared evaluation inputs, state projections, and Evidence references required for its evaluation contract. Portable AVP semantics do not expose live Subject or privileged mutable runtime handles.
3. Evaluation inputs are integrity-bound so substitution can be detected.
4. Oracle execution failure never becomes Subject/task `FAIL`. If no valid task result can be produced, the task verdict is `INCONCLUSIVE`.
5. Oracle execution failures use the stable top-level evaluation validity `ORACLE_FAILURE`.
6. More specific failure causes are preserved in `validityDetail.code`. Initial standardized detail codes are `ORACLE_TIMEOUT`, `ORACLE_CRASH`, `ORACLE_PROTOCOL_ERROR`, and `ORACLE_SECURITY_VIOLATION`.
7. Verification results may reference only Evidence that is present and integrity-valid.
8. A verifier preserves an auditable Oracle execution record that binds Oracle/package identity, evaluation input identity, and execution outcome.

## Protocol/schema changes

This AEP introduces:

- `spec/oracle/oracle-evaluation-contract.md`;
- `spec/oracle/requirement-index.yaml`;
- `schemas/oracle-evaluation.schema.json`;
- the `avp-oracle-v0.1` conformance profile and Oracle TCK vectors.

A later implementation-alignment commit removes implementation-specific Oracle failure values from the Python top-level `Validity` enum and stores them as evaluation validity detail.

## Security considerations

This AEP preserves the Evaluator/Subject privilege boundary and intentionally does not standardize a particular subprocess/container/microVM mechanism. Oracle package identity and input integrity are security-relevant because an unbound evaluator or substituted input can make verification results unverifiable.

This slice does not complete the full AVP Security profile. Network isolation, evaluator credential inaccessibility, hidden fault schedules, answer-key secrecy, and adversarial Subject probes remain mandatory topics for the subsequent security reconciliation slice.

## Backward compatibility

The normative v0.1 protocol is pre-release. The Python reference implementation currently exposes four Oracle-specific top-level `Validity` values that are implementation drift. Runtime alignment will be intentionally breaking for callers that relied on those Python enum members:

- `ORACLE_TIMEOUT`
- `ORACLE_CRASH`
- `ORACLE_PROTOCOL_ERROR`
- `ORACLE_SECURITY_VIOLATION`

Their diagnostic information is retained under `ORACLE_FAILURE` through `validityDetail.code`; no diagnostic signal is discarded.

## Conformance tests

The Oracle profile tests:

- Oracle identity and execution binding;
- declared input scoping and digest integrity;
- failure separation and detail-code preservation;
- result/Evidence integrity.

## Reference implementation

The Python reference runtime already provides immutable `OraclePackage`, `OracleEvaluationContext`, `OracleExecutionArtifact`, bounded worker framing, subprocess isolation, and exact Evidence digest checks. These are implementation evidence. Only behavior promoted by this AEP and its normative specification is protocol authority.

## Alternatives

### Standardize every runner failure as a top-level Validity value

Rejected. It permanently couples protocol compatibility to implementation-specific process failure modes.

### Collapse all Oracle failures and discard the specific reason

Rejected. Operators need diagnostic detail for reliability analysis and incident review.

### Standardize the current Python subprocess framing

Rejected. AVP requires interoperable verification semantics, not one language/runtime's IPC mechanism.
