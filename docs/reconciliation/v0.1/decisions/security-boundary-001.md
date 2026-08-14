# Security Boundary Reconciliation Decision 001

Status: Proposed

## Context

The AVP historical security model defines privileged Evaluator and Control Planes and an untrusted Subject Agent Plane. It requires evaluator credentials and hidden evaluator material to remain unavailable to the Subject.

The reference runtime currently provides a narrow SubjectSession gateway exposing observation, tool invocation, and trace correlation. This is an API boundary, not a hardened sandbox.

## Decision

1. AVP Security v0.1 defines observable trust-boundary semantics, not a specific sandbox technology.
2. Subject capabilities MUST be explicitly separated from evaluator capabilities.
3. Undeclared privileged capability access MUST fail closed.
4. Evaluator credentials and hidden benchmark/oracle materials MUST NOT cross into Subject execution context.
5. Future fault schedules MUST remain evaluator-private until scenario-defined activation.
6. Implementations MUST disclose the isolation layer proven by their conformance result.
7. In-process reference implementations MUST NOT claim process, network, tenant, or sandbox isolation.

## Rejected alternatives

### Use reflection resistance as sandbox proof

Rejected. Language-level object hiding is not equivalent to adversarial process isolation.

### Standardize containers or microVMs as AVP security protocol

Rejected. Deployment isolation mechanisms belong to implementation profiles.

### Publish one security=true capability flag

Rejected. Security assurance requires a declared profile and conformance evidence.

## Consequences

- API-plane isolation can be tested by the reference runtime.
- Hardened deployment profiles remain future Security-HighAssurance work.
- TCK must distinguish capability separation from sandbox isolation.
