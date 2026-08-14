# AVP Environment Contract v0.1

Status: draft normative candidate

## 1. Scope

This specification defines the language-neutral evaluator contract for provisioning, observing, mutating, snapshotting, restoring, diffing, faulting, and releasing an AVP Environment. It does not standardize a backing runtime technology or implementation language.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are interpreted as requirement terms for conformance.

## 2. Environment identity and ownership

### AVP-ENVIRONMENT-001 — Authoritative ownership and opaque handles

An Environment implementation MUST own its mutable authoritative resources. Runtime and Subject code MUST interact using an opaque environment identity/handle or equivalent boundary and MUST NOT require adapter-private mutable resource objects.

### AVP-ENVIRONMENT-002 — Scenario-bound provisioning

Provisioning MUST bind the environment instance to the ScenarioInstance identity used to create it. Operations performed through a handle MUST apply to that bound instance. Reusing a handle for a different ScenarioInstance without explicit reprovisioning MUST fail closed.

## 3. Reset and logical time

### AVP-ENVIRONMENT-003 — Deterministic reset target

For each reset target an implementation declares as supported, reset MUST either establish that target's declared semantics or fail closed. A successful reset response MUST bind the before and after authoritative state identities and MUST NOT claim equivalence that was not established.

### AVP-ENVIRONMENT-004 — Logical-time semantics

When logical time is exposed by the selected profile, the value MUST be scoped to one environment instance, deterministic with respect to that environment's execution history, and monotonic within an unreverted execution lineage. Restore or reset MAY move logical time to the value defined by the restored/reset lineage. AVP does not prescribe wall-clock units.

## 4. Observation and authoritative state

### AVP-ENVIRONMENT-005 — Subject observation isolation

Subject observation MUST be actor-scoped. It MUST expose only information authorized for that actor and MUST NOT disclose evaluator-only state, hidden grader material, private security data, or future fault schedules.

### AVP-ENVIRONMENT-006 — Authoritative projection and digest binding

An evaluator projection MUST identify the selected projection semantics and MUST bind the returned authoritative data to a stable digest. For the same projection definition, equal digest values MUST represent equal normalized projection semantics. An implementation MUST NOT use a digest from one projection as evidence for another projection.

## 5. Snapshots, restore, and diff

### AVP-ENVIRONMENT-007 — Snapshot identity and ownership

A snapshot reference MUST bind the snapshot to its owning environment instance and to the authoritative state identity represented by the snapshot. Restore of a snapshot from another environment instance MUST fail closed unless a separately selected profile explicitly standardizes portable snapshots.

### AVP-ENVIRONMENT-008 — Restore equivalence honesty

A restore result MUST state an equivalence level no stronger than the implementation establishes. v0.1 defines the semantic levels `EXACT`, `STATE_EQUIVALENT`, and `NON_EQUIVALENT`:

- `EXACT`: all profile-defined authoritative state and execution-relevant environment state represented by the snapshot are restored exactly;
- `STATE_EQUIVALENT`: profile-defined authoritative state is restored to an equivalent state, but implementation-internal or non-authoritative execution state may differ;
- `NON_EQUIVALENT`: the restore did not establish state equivalence.

A conforming implementation MUST NOT report `EXACT` when it can establish only state equivalence.

### AVP-ENVIRONMENT-009 — State-diff binding

A StateDiff MUST bind the before-state identity, after-state identity, and selected projection semantics. The reported changes MUST describe semantic change for that projection. A diff MUST NOT be treated as evidence for unrelated snapshots, states, or projections.

## 6. Fault control

### AVP-ENVIRONMENT-010 — Fault lifecycle and occurrence semantics

A scheduled fault MUST have evaluator-controlled identity, target, and activation condition. For occurrence-based activation, the fault MUST NOT activate before the declared occurrence. Clearing a fault MUST prevent later activation unless the profile explicitly defines another lifecycle. Hidden future fault configuration MUST remain evaluator-private as required by AVP Security.

## 7. Release

### AVP-ENVIRONMENT-011 — Released-handle failure

Release MUST invalidate the environment instance for subsequent operations through that handle. Operations using a released or otherwise stale handle MUST fail closed and MUST NOT silently recreate or switch authoritative resources.

## 8. Non-normative implementation freedom

Conforming implementations MAY use in-memory state, databases, browser contexts, containers, virtual machines, remote services, or other backing technologies. AVP v0.1 does not prescribe Python types, identifier formats, snapshot serialization, one diff algorithm, wall-clock units, or one fault-scheduler data structure.

## 9. Security composition

Environment conformance does not imply process, network, tenant, or sandbox isolation. Such claims remain governed by the Security assurance contract. Subject observation MUST compose with Security hidden-material and fault-secrecy requirements.
