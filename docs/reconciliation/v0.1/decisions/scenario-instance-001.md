# Scenario / ScenarioInstance Reconciliation Decision 001

Status: Proposed

## Context

Historical AVP/AVS design material mixes benchmark-authoring DSL concerns, compilation mechanics, runtime execution state, security visibility, generator behavior, and reference resolution. The current Python reference compiler implements a useful subset, but implementation details must not become normative merely because they exist in code.

Security v0.1 now depends on Scenario capability projection, hidden evaluator material, and fault visibility. Core lifecycle and replay also depend on a stable materialized scenario identity. These dependencies require a first-class Scenario contract.

## Decision

1. `ScenarioTemplate` is unresolved authoring input; `ScenarioInstance` is the materialized execution contract consumed by an Episode.
2. AVP Scenario v0.1 standardizes observable compilation outcomes, not one authoring syntax or compiler architecture.
3. Compilation MUST resolve every required execution-relevant input under the selected profile before execution begins; unresolved required inputs fail closed.
4. ScenarioInstance identity MUST bind execution-relevant materialized content and MUST be stable for equivalent compilation inputs.
5. ScenarioInstance semantics are immutable during Episode execution.
6. Subject-visible projection is a protocol security boundary. Evaluator-only success criteria, invariants, hidden fault configuration, graders, private security material, and equivalent answer-key content MUST remain excluded unless another normative contract explicitly makes a field observable.
7. Actor capability projection MUST derive from the materialized instance and MUST NOT introduce undeclared privileged capabilities.
8. External references that influence execution MUST have identity binding appropriate to the selected profile; strict/content-backed profiles fail closed when identity cannot be established.
9. Scenario compilation/validation failure is not Agent task failure.
10. Python compiler name/version fields, exact internal seed-stream layout, generator plugin APIs, resolver class names, and Python immutability mechanisms remain non-normative implementation details.

## Rejected alternatives

### Make the existing ScenarioTemplate JSON Schema the entire protocol

Rejected. The current schema primarily validates authoring shape and does not by itself define deterministic materialization, instance identity, visibility, reference binding, or failure separation.

### Freeze the Python compiler serialization as the standard

Rejected. This would couple independent implementations to reference-runtime provenance and internal mechanics.

### Keep Scenario semantics distributed across Core and Security

Rejected. The materialized execution object needs one authoritative contract and requirement index.

## Consequences

- Scenario receives its own normative specification and TCK profile.
- Existing schema/compiler behavior must be reconciled requirement-by-requirement before promotion.
- AVS authoring features may evolve independently when they compile into a conforming ScenarioInstance.
- Security can depend on the Scenario projection contract rather than duplicate projection semantics.
