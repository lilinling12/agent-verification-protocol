# AEP-0001 — Oracle Evaluation Contract v0.1

- Status: Final
- Authors: AVP maintainers
- Created: 2026-08-13
- Accepted: 2026-08-13
- Acceptance decision: Accepted by the protocol maintainer on 2026-08-13 as the approved Oracle protocol direction; this historical acceptance preceded the Alpha 2 Final-eligibility evidence review.
- Finalized: 2026-08-17
- Final decision: Explicitly approved by the protocol maintainer for `Accepted` → `Final` on 2026-08-17, based on the merged Alpha 2 Final-eligibility audit and released evidence at `v0.3.0-rc.1` / `ef199124017b0dcc8c4a966d00c4f407760f9a06`; the published release bytes passed external-consumer and full TCK validation, no post-release protocol-semantic drift invalidated that evidence, and this Finalization does not authorize stable `v0.3.0` publication.
- Target AVP version: 0.1

## Problem

The historical AVP design defines an Oracle as a privileged evaluator that consumes declared trusted evidence and whose execution failures invalidate evaluation rather than fail the Subject task. The current Python reference implementation already isolates Oracle execution and records detailed runner statuses, but it also exposed runner-specific failure vocabulary as top-level evaluation validity before reconciliation.

That implementation detail is not a sound cross-language protocol commitment. It couples AVP's stable evaluation-validity taxonomy to one runner and makes implementation behavior appear normative before reconciliation.

The acceptance audit also identified two interoperability gaps in the first draft of this AEP: `packageDigest` was not explicit enough about its digest preimage, and the audit requirement did not yet have a portable verifier-side representation of the exact result set accepted from an Oracle execution.

## Motivation / interoperability case

Independent AVP implementations need to agree on three different questions:

1. whether an Oracle evaluation is valid enough to support a task verdict;
2. why a particular Oracle execution failed; and
3. which verification-result values the verifier actually accepted from the execution.

The first is a stable protocol classification. The second is diagnostic detail that can evolve with execution technology. The third is acceptance provenance and must not be inferred from mutable implementation state.

Keeping these concerns separate allows a Python subprocess runner, a container runner, a microVM runner, a WASM evaluator, or a remote verifier to report equivalent protocol outcomes without standardizing identical process mechanics.

## Existing standards analysis

AVP reuses JSON Schema for machine-readable resources and SHA-256 content identities already defined by the AVP Evidence contract. This AEP does not define a new sandbox format, package-signing format, RPC transport, or process protocol.

`packageDigest` is intentionally an opaque SHA-256 identity of the immutable Oracle package representation selected by the implementation. AVP Oracle v0.1 does not invent a package canonicalization format. Consumers compare the digest as identity; an implementation-specific package descriptor may be used as the digest preimage only within that implementation unless a later packaging profile standardizes the representation.

Existing implementation-specific framing such as the reference worker protocol remains reference-runtime behavior.

## Proposed semantics

1. Every Oracle evaluation is bound to an Oracle identity consisting of an identifier, version identifier, and immutable package/content digest.
2. An Oracle receives only declared evaluation inputs, state projections, and Evidence capabilities required for its evaluation contract. Portable AVP semantics do not expose live Subject or privileged mutable runtime handles.
3. Evaluation inputs are integrity-bound so substitution can be detected.
4. Oracle execution failure never becomes Subject/task `FAIL`. If no valid task result can be produced, the task verdict is `INCONCLUSIVE`.
5. Oracle execution failures use the stable top-level Oracle evaluation validity `ORACLE_FAILURE`.
6. More specific failure causes are preserved in `validityDetail.code`. Initial standardized detail codes are `ORACLE_TIMEOUT`, `ORACLE_CRASH`, `ORACLE_PROTOCOL_ERROR`, and `ORACLE_SECURITY_VIOLATION`.
7. Verification results may reference only Evidence that is present and integrity-valid.
8. A verifier preserves an immutable Oracle execution record that binds package identity, input identity, execution outcome, and runner output identity.
9. A verifier separately preserves an Oracle Evaluation Record containing the exact verification-result values it accepted. Successful records reference the execution record; Oracle failures contain no accepted results.
10. Oracle evaluation validity remains distinct from later Episode-wide validity gates such as telemetry completeness or infrastructure persistence.

## Protocol/schema changes

This AEP introduces:

- `spec/oracle/oracle-evaluation-contract.md`;
- `spec/oracle/requirement-index.yaml`;
- `schemas/oracle-evaluation.schema.json`;
- the `avp-oracle-v0.1` conformance profile and Oracle TCK vectors.

The schema defines a verifier-side Oracle Evaluation Record with `acceptedResults`. A `VALID` record requires an immutable `executionRecordDigest` and forbids `validityDetail`. An `ORACLE_FAILURE` record requires `validityDetail`, forces task verdict `INCONCLUSIVE`, and accepts no results.

Reference-runtime alignment removes implementation-specific Oracle failure values from the Python top-level `Validity` enum and stores runner cause as structured validity detail.

## Security considerations

This AEP preserves the Evaluator/Subject privilege boundary and intentionally does not standardize a particular subprocess/container/microVM mechanism. Oracle package identity and input integrity are security-relevant because an unbound evaluator or substituted input can make verification results unverifiable.

The verifier must not trust a runner-provided execution record blindly. Identity fields and output identity must be checked at the trusted parent boundary before results are accepted.

This slice does not complete the full AVP Security profile. Network isolation, evaluator credential inaccessibility, hidden fault schedules, answer-key secrecy, and adversarial Subject probes remain mandatory topics for the subsequent security reconciliation slice.

## Backward compatibility

The normative v0.1 protocol is pre-release. The Python reference implementation previously exposed four Oracle-specific top-level `Validity` values that were implementation drift:

- `ORACLE_TIMEOUT`
- `ORACLE_CRASH`
- `ORACLE_PROTOCOL_ERROR`
- `ORACLE_SECURITY_VIOLATION`

Their diagnostic information is retained under `ORACLE_FAILURE` through `validityDetail.code`; no diagnostic signal is discarded.

The reference `OraclePackage.identity_digest` is also clarified as one implementation's package identity mechanism, not a cross-language package canonicalization algorithm. The reference model may accept an externally supplied immutable package digest when a packaging layer already owns that identity.

## Conformance tests

The Oracle profile tests:

- Oracle identity and opaque package-digest binding;
- declared input scoping and digest integrity;
- failure separation and detail-code preservation;
- result/Evidence integrity;
- execution-record and accepted-result binding, including output-substitution rejection.

## Reference implementation

The Python reference runtime provides immutable `OraclePackage`, `OracleEvaluationContext`, `OracleExecutionArtifact`, bounded worker framing, exact Evidence digest checks, trusted-parent execution-record validation, and immutable Oracle Evaluation Record publication. These are implementation evidence. Only behavior promoted by this AEP and its normative specification is protocol authority.

## Alternatives

### Standardize every runner failure as a top-level Validity value

Rejected. It permanently couples protocol compatibility to implementation-specific process failure modes.

### Collapse all Oracle failures and discard the specific reason

Rejected. Operators need diagnostic detail for reliability analysis and incident review.

### Treat a Python package descriptor digest as the portable package digest algorithm

Rejected. It would make a language-specific serialization rule accidentally normative.

### Infer accepted results only from runner output

Rejected. A verifier may reject, filter, or enrich runner output; acceptance provenance must remain explicit.

### Standardize the current Python subprocess framing

Rejected. AVP requires interoperable verification semantics, not one language/runtime's IPC mechanism.
