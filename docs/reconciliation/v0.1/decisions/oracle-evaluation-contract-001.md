# Oracle Evaluation Contract Reconciliation Decision 001

Status: Proposed for the AVP v0.1 draft candidate.

## Context

The historical Oracle SDK and security design require Oracles to be versioned, evidence-scoped, privileged evaluators whose failures affect evaluation validity rather than Subject task success. The reference implementation already has immutable Oracle package/context/execution identities and detailed isolated-runner statuses.

A semantic mismatch remains: Python currently promotes runner-specific `TIMEOUT`, `CRASHED`, `PROTOCOL_ERROR`, and `SECURITY_VIOLATION` into four top-level `Validity` enum values. The historical design instead has a stable generic Oracle failure class, while the current isolated runner already retains the detailed execution status separately.

## Decision

1. AVP v0.1 defines Oracle identity as `oracleId`, `version`, and immutable SHA-256 `packageDigest`.
2. A portable Oracle evaluation MUST be limited to declared inputs/projections/Evidence. Live mutable Subject or privileged evaluator handles are not part of the Oracle input contract.
3. Oracle evaluation inputs MUST be integrity-bound to the Episode/scenario/manifest context sufficiently to detect substitution.
4. Oracle execution failure MUST NOT be represented as Subject task failure. A blocked evaluation produces task verdict `INCONCLUSIVE`.
5. The stable top-level evaluation validity for Oracle execution failure is `ORACLE_FAILURE`.
6. Runner-specific causes remain available through `validityDetail.code`. AVP v0.1 standardizes four initial detail codes: `ORACLE_TIMEOUT`, `ORACLE_CRASH`, `ORACLE_PROTOCOL_ERROR`, and `ORACLE_SECURITY_VIOLATION`.
7. Oracle results MUST NOT reference missing or integrity-invalid Evidence.
8. A verifier MUST preserve an auditable execution record binding Oracle/package identity, input identity, and execution outcome.
9. Python class names, subprocess framing, POSIX limits, container/microVM choice, filesystem layout, worker module naming, and network-sandbox mechanism are implementation details unless a later profile explicitly promotes them.

## Rejected alternatives

### Keep runner-specific failure modes as top-level Validity values

Rejected because adding execution mechanisms would continually expand the protocol's stable compatibility surface.

### Make an Oracle crash a task FAIL

Rejected because evaluator malfunction is not evidence that the Subject failed its task.

### Promote `avp.oracle/v2` as the wire protocol

Rejected because it is a private reference-runtime worker framing and is neither needed nor appropriate for cross-language AVP conformance.

## Consequences

- Python runtime alignment removes four Oracle-specific top-level `Validity` members and adds structured validity detail.
- Existing execution artifacts continue preserving the detailed runner status.
- Oracle conformance can be implemented by runtimes using subprocesses, containers, microVMs, or remote evaluators.
- Full Subject/Evaluator security isolation remains a separate security reconciliation slice rather than being accidentally defined by this Oracle runner implementation.
