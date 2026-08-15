# AEP-0003 — Scenario and ScenarioInstance Contract v0.1

- Status: Accepted
- Authors: AVP maintainers
- Created: 2026-08-14
- Accepted: 2026-08-16
- Acceptance decision: Approved by the protocol maintainer during the Alpha 2 readiness review. This approves the protocol direction only; the AEP is not Final and this decision does not authorize merge, tag, or release.
- Target AVP version: 0.1

## Problem

AVP already relies on Scenario semantics across lifecycle, Security, Evidence, Oracle, replay, and reference-runtime execution, but those semantics are not yet represented by a dedicated normative Scenario contract.

The repository currently contains an authoring-oriented ScenarioTemplate schema and a Python compiler that materializes immutable ScenarioInstance objects. Treating the current Python behavior as the protocol would accidentally standardize implementation choices such as compiler identity, internal seed partitioning, generator APIs, and resolver classes.

## Motivation / interoperability case

Independent AVP implementations need to agree on the observable contract between authored scenario input and the immutable scenario instance that an Episode executes.

The interoperable boundary is:

1. a ScenarioTemplate describes unresolved scenario intent;
2. compilation/materialization resolves all execution-relevant nondeterminism and references required by the selected profile;
3. a ScenarioInstance is immutable for the duration of an Episode and has a stable content identity;
4. Subject-visible projection excludes evaluator-only material;
5. compilation failures are configuration/infrastructure failures and never Agent task failures.

AVP does not standardize one YAML authoring language or one compiler implementation.

## Proposed semantics

### AVP-SCENARIO-001 Template and instance separation

A conforming implementation MUST distinguish unresolved ScenarioTemplate input from the materialized ScenarioInstance used for execution.

### AVP-SCENARIO-002 Deterministic materialization

Given the same template identity, explicit compilation inputs, selected profile semantics, and resolved external reference identities, compilation MUST produce the same ScenarioInstance content identity.

### AVP-SCENARIO-003 Fail-closed unresolved inputs

Required parameters, placeholders, generators, or references that cannot be resolved under the selected compilation policy MUST fail compilation before Episode execution.

### AVP-SCENARIO-004 Instance identity binding

A ScenarioInstance MUST expose a stable content identity bound to all execution-relevant materialized fields except the field carrying that identity itself.

### AVP-SCENARIO-005 Immutable execution contract

Execution MUST NOT mutate the materialized ScenarioInstance. Implementations MAY use immutable in-memory structures or equivalent enforcement.

### AVP-SCENARIO-006 Subject projection confidentiality

The Subject projection MUST include only scenario material declared observable to that Subject and MUST exclude evaluator-only success criteria, invariants, hidden faults, graders, private security material, and equivalent answer-key content.

### AVP-SCENARIO-007 Actor capability projection

Subject capability exposure MUST be derived from the materialized ScenarioInstance for the relevant actor and MUST NOT grant undeclared evaluator capabilities.

### AVP-SCENARIO-008 Reference identity binding

When external references affect execution semantics, the materialized instance MUST bind the resolved reference identity required by the selected compilation profile. Strict/content-backed profiles MUST fail closed when that identity cannot be established.

### AVP-SCENARIO-009 Compilation failure separation

Scenario validation or compilation failure MUST NOT be represented as Agent task failure.

## Non-normative implementation freedom

This AEP intentionally does not standardize:

- compiler implementation language or compiler name/version format;
- a fixed number or naming scheme for internal random-seed streams;
- generator plugin interfaces or generator implementation versions;
- one URI resolver class hierarchy;
- Python mapping/tuple immutability mechanisms;
- one authoring serialization format.

Those details MAY appear in implementation provenance without becoming AVP protocol requirements.

## Protocol/schema changes

This AEP introduces a dedicated Scenario normative specification, requirement index, reconciliation matrix, and an `avp-scenario-v0.1` conformance profile.

The existing authoring-oriented `schemas/scenario.schema.json` must be reconciled before it is treated as the complete Scenario protocol contract. A separate ScenarioInstance schema MAY be introduced where that improves language-neutral validation.

## Security considerations

Scenario compilation is part of the evaluator trust boundary. Hidden evaluator material, future fault schedules, private graders, and privileged capabilities must not cross into Subject-visible projection merely because they exist in the source template or materialized evaluator view.

## Conformance direction

The Scenario TCK should verify observable semantics, including deterministic materialization, fail-closed unresolved inputs, instance identity binding, Subject projection confidentiality, capability projection, reference binding, and immutable instance behavior.

It MUST NOT require Python-specific compiler metadata or internal seed partitioning.

## Reference implementation

The Python reference compiler is evidence that the contract is implementable. Its implementation details are non-normative unless separately adopted by specification and conformance assets.

## Alternatives

### Standardize the current Python compiler output byte-for-byte

Rejected. This would make implementation provenance and internal compiler design part of the protocol accidentally.

### Treat AVS authoring syntax as AVP Core

Rejected. Authoring UX and benchmark DSL evolution should not constrain the language-neutral Scenario execution contract.

### Leave Scenario semantics implicit in Security and Runtime

Rejected. Independent implementations need a first-class contract for the object an Episode actually executes.
