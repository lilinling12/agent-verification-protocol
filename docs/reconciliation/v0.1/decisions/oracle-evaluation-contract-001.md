# Oracle Evaluation Contract Reconciliation Decision 001

Status: Proposed for the AVP v0.1 draft candidate.

## Context

The historical Oracle SDK and security design require Oracles to be versioned, evidence-scoped, privileged evaluators whose failures affect evaluation validity rather than Subject task success. The reference implementation already has immutable Oracle package/context/execution identities and detailed isolated-runner statuses.

Two additional drift risks were identified during acceptance review: the reference implementation's package descriptor digest could be mistaken for a portable package canonicalization rule, and the execution record did not explicitly preserve the verifier's accepted result representation after parent-side validation/enrichment.

## Decision

1. AVP v0.1 defines Oracle identity as `oracleId`, `version`, and immutable SHA-256 `packageDigest`.
2. `packageDigest` is an opaque identity of the immutable package representation selected for evaluation. AVP Oracle v0.1 does not define a universal package serialization; consumers MUST NOT recompute it from identity fields without a packaging profile that defines the preimage.
3. A portable Oracle evaluation MUST be limited to declared inputs/projections/Evidence. Live mutable Subject or privileged evaluator handles are not part of the Oracle input contract.
4. Oracle evaluation inputs MUST be integrity-bound to the Episode/scenario/manifest context sufficiently to detect substitution.
5. Oracle execution failure MUST NOT be represented as Subject task failure. A blocked evaluation produces task verdict `INCONCLUSIVE`.
6. The stable top-level Oracle evaluation validity for Oracle execution failure is `ORACLE_FAILURE`.
7. Runner-specific causes remain available through `validityDetail.code`. AVP v0.1 standardizes four initial detail codes: `ORACLE_TIMEOUT`, `ORACLE_CRASH`, `ORACLE_PROTOCOL_ERROR`, and `ORACLE_SECURITY_VIOLATION`.
8. Oracle results MUST NOT reference missing or integrity-invalid Evidence.
9. A verifier MUST preserve an immutable execution record binding Oracle/package identity, input identity, execution outcome, and runner output identity.
10. A verifier MUST preserve a separate Oracle Evaluation Record containing the exact result values it accepts. Successful records reference the execution record; Oracle-failure records contain no accepted results.
11. Python class names, worker framing, POSIX limits, container/microVM choice, filesystem layout, package-descriptor serialization, and network-sandbox mechanism are implementation details unless a later profile explicitly promotes them.

## Rejected alternatives

### Keep runner-specific failure modes as top-level Validity values

Rejected because adding execution mechanisms would continually expand the protocol's stable compatibility surface.

### Make an Oracle crash a task FAIL

Rejected because evaluator malfunction is not evidence that the Subject failed its task.

### Make Python package-descriptor canonicalization normative

Rejected because language-neutral package identity must not depend on a Python-specific descriptor representation unless a dedicated packaging profile adopts that representation.

### Infer accepted results only from the runner response

Rejected because trusted-parent validation may reject or enrich runner output. Auditability requires the accepted representation to be explicit.

### Promote the reference worker framing as the wire protocol

Rejected because it is a private reference-runtime worker framing and is neither needed nor appropriate for cross-language AVP conformance.

## Consequences

- Python runtime alignment removes four Oracle-specific top-level `Validity` members and adds structured validity detail.
- Existing execution artifacts continue preserving detailed runner status and output identity.
- The trusted parent validates execution-record identity before accepting Oracle results.
- The verifier publishes an immutable Oracle Evaluation Record that preserves accepted result values.
- Oracle conformance can be implemented by runtimes using subprocesses, containers, microVMs, WASM, or remote evaluators.
- Full Subject/Evaluator security isolation remains a separate security reconciliation slice rather than being accidentally defined by this Oracle runner implementation.
