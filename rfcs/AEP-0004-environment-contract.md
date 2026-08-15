# AEP-0004 — Environment Contract v0.1

- Status: Accepted
- Authors: AVP maintainers
- Created: 2026-08-14
- Accepted: 2026-08-16
- Acceptance decision: Approved by the protocol maintainer during the Alpha 2 readiness review. This approves the protocol direction only; the AEP is not Final and this decision does not authorize merge, tag, or release.
- Target AVP version: 0.1

## Problem

AVP already depends on an Environment boundary for authoritative state, Subject tool execution, snapshots, restore, reset, state projections, diffs, logical time, and controlled fault injection. The Python reference implementation exposes these operations through an `EnvironmentAdapter`, but the language-neutral protocol semantics are not yet first-class normative assets.

Treating the current Python SPI as the protocol would accidentally standardize implementation details such as dataclass layouts, opaque-handle representations, in-memory storage choices, Python enum names, or one specific fault scheduler.

## Interoperability goal

Independent AVP implementations need to agree on the observable evaluator contract of a provisioned environment without agreeing on the backing technology.

A conforming environment may be implemented by an in-memory model, database, browser session, container, VM, external service, or another adapter, provided it satisfies the selected conformance profile.

## Proposed semantics

### AVP-ENVIRONMENT-001 Authoritative ownership and opaque handles

An Environment implementation MUST own its mutable authoritative resources. Runtime and Subject code MUST interact through an environment handle or equivalent opaque identity rather than depending on adapter-private mutable objects.

### AVP-ENVIRONMENT-002 Scenario-bound provisioning

Provisioning MUST bind the created environment instance to the ScenarioInstance identity used to create it. A handle MUST NOT be silently reused for a different ScenarioInstance.

### AVP-ENVIRONMENT-003 Deterministic reset target

When a declared reset target is supported, reset MUST restore the environment to the semantics of that target or fail closed. Reset success MUST NOT be reported when the implementation cannot establish the declared equivalence.

### AVP-ENVIRONMENT-004 Logical-time semantics

If logical time is exposed, it MUST be environment-scoped, deterministic with respect to the environment execution history under the selected profile, and monotonic within one unreverted execution lineage. AVP does not require wall-clock units or system-clock coupling.

### AVP-ENVIRONMENT-005 Subject observation isolation

Subject observation MUST be actor-scoped and MUST expose only the observation surface authorized for that actor. Evaluator-only authoritative state, hidden fault schedules, and private verification material MUST NOT be disclosed through Subject observation.

### AVP-ENVIRONMENT-006 Authoritative projection and digest binding

An evaluator projection MUST identify the projection requested and bind returned authoritative data to a stable digest. Digest equality MUST imply equality of the normalized projection semantics under the selected profile.

### AVP-ENVIRONMENT-007 Snapshot identity and ownership

A snapshot reference MUST bind at minimum the owning environment instance and authoritative state identity. Restore using a snapshot belonging to another environment instance MUST fail closed unless a separate profile explicitly defines portable snapshots.

### AVP-ENVIRONMENT-008 Restore equivalence honesty

Restore MUST report its actual equivalence level and MUST NOT claim stronger fidelity than the implementation establishes. v0.1 recognizes at least exact restore, state-equivalent restore, and non-equivalent outcome semantics.

### AVP-ENVIRONMENT-009 State-diff binding

A state diff MUST bind the before and after authoritative state identities and MUST represent semantic changes for the selected projection. The diff MUST NOT be accepted as evidence for unrelated snapshots or projections.

### AVP-ENVIRONMENT-010 Fault lifecycle and occurrence semantics

A scheduled fault MUST have evaluator-controlled identity, target, and activation condition. An occurrence-based fault MUST NOT activate before its declared occurrence. Hidden future fault configuration MUST remain compatible with the Security fault-secrecy requirement.

### AVP-ENVIRONMENT-011 Release and stale-handle fail-closed behavior

After release, operations using the released handle MUST fail closed. Implementations MUST NOT silently resurrect released authoritative resources through stale handles.

## Non-normative implementation freedom

This AEP does not standardize:

- Python protocol classes, dataclasses, enum spellings, or collection types;
- one handle identifier format;
- in-memory, database, browser, container, VM, or remote-service implementation choices;
- wall-clock units or one virtual-clock implementation;
- one state-diff algorithm or patch format;
- one fault scheduler data structure;
- adapter-specific fault parameters;
- one snapshot storage or serialization format.

## Security boundary

Environment is evaluator-controlled infrastructure. Subject-facing APIs must not expose evaluator credentials, hidden state, future fault schedules, private grader inputs, or unrestricted state projections. Environment conformance does not imply process, network, tenant, or sandbox isolation unless separately claimed and verified.

## Conformance direction

The Environment TCK should exercise observable behavior through portable vectors covering scenario binding, reset, logical time, actor observation, projection/digest, snapshot ownership, restore equivalence, diff binding, delayed fault occurrence, and released-handle failure.

The TCK MUST NOT require the Python `EnvironmentAdapter` type or in-memory implementation internals.

## Reference implementation

The current Python Environment adapter and in-memory implementation are implementation evidence only. They must be reconciled against this contract rather than defining it.
