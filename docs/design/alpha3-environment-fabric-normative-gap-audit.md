# Alpha 3 Environment Fabric — Normative Gap Audit

Status: Design audit for Draft AEP-0009. Non-normative.

## Purpose

This audit separates the semantics proposed by AEP-0009 into five classes before any Alpha 3 normative specification, schema, TCK, or backend implementation is created:

- **REUSE** — an existing normative AVP requirement already defines the required semantics and must remain authoritative;
- **EXTEND** — an existing contract remains authoritative but needs a new cross-resource rule that cannot be expressed by merely repeating the existing requirement;
- **NEW** — a genuinely new Environment Fabric semantic is required;
- **PROFILE** — the semantic belongs in a conditional domain profile rather than the base Fabric contract;
- **NON-NORMATIVE** — implementation, architecture, product, or deployment detail that must not become portable AVP semantics.

The audit enforces the repository authority chain:

```text
Normative Spec -> Schema -> TCK -> Reference Runtime
```

It is deliberately performed before PostgreSQL/MySQL, browser, network, time, container, or microVM backend implementation. A backend must not be used to discover the public protocol after the fact.

## Authority baseline

The Alpha 3 Fabric design must compose with, not duplicate, these existing normative surfaces:

- `spec/environment/environment-contract.md` and `spec/environment/requirement-index.yaml`;
- `spec/core/episode-lifecycle.md` and `spec/core/requirement-index.yaml`;
- `spec/scenario/scenario-contract.md` and `spec/scenario/requirement-index.yaml`;
- `spec/security/security-boundary-contract.md` and `spec/security/requirement-index.yaml`;
- `spec/evidence/evidence-artifact-identity.md` and `spec/evidence/requirement-index.yaml`.

The historical `docs/design/alpha-v0.1/07-environment-fabric.md` remains provenance-only. Draft AEP-0009 and this audit may learn from it, but historical terminology does not regain normative authority unless it is deliberately re-specified and conformance-tested.

## Findings summary

The existing contracts already define almost all *single-Environment* invariants needed by Alpha 3: authoritative ownership, ScenarioInstance binding, reset honesty, Environment logical time, observation visibility, evaluator projection identity, snapshot ownership, restore fidelity honesty, semantic diff binding, fault control, stale-handle failure, Episode lifecycle projection, Subject/evaluator separation, secret handling, assurance honesty, and exact-byte Artifact identity.

The base Environment Fabric therefore needs to stay small. Its genuinely new portable surface is limited to **composition semantics**:

1. identified Environment Resource membership;
2. resource-level portable capability declarations distinct from Subject authorization;
3. a language-neutral Fabric manifest binding composition identity;
4. required/optional participation semantics derived from the materialized execution contract;
5. resource-level results for composite operations;
6. aggregate success/fidelity/atomicity honesty across required resources;
7. protocol-observable retry-safe cleanup;
8. real-operation conformance for capability claims.

Relational, browser, network, time-control, compute, and microVM behavior does **not** belong in the base Fabric contract merely because those domains are Alpha 3 implementation targets.

## Normative gap matrix

| Candidate semantic | Classification | Existing authority / future owner | Decision |
|---|---|---|---|
| Environment remains evaluator-owned authoritative external state | REUSE | `AVP-ENVIRONMENT-001` | Fabric is an Environment; do not create separate ownership semantics. |
| Fabric provisioning is bound to the materialized ScenarioInstance | REUSE | `AVP-ENVIRONMENT-002`, `AVP-SCENARIO-005`, `AVP-SCENARIO-008` | Reuse existing Scenario/Environment identity binding. |
| Required unresolved execution inputs fail before execution | REUSE | `AVP-SCENARIO-003` | Fabric must consume resolved inputs; it must not create a second Scenario resolution model. |
| Subject-visible capabilities derive from materialized actor projection | REUSE | `AVP-SCENARIO-007`, `AVP-SECURITY-002` | Resource Capability support must not be confused with Subject authorization. |
| Environment reset establishes declared target or fails closed | REUSE | `AVP-ENVIRONMENT-003` | Per-resource reset mechanisms remain profile/implementation details. |
| Environment logical time is deterministic and monotonic within an unreverted lineage | REUSE | `AVP-ENVIRONMENT-004` | Fabric must not redefine logical time or imply host wall-clock virtualization. |
| Subject observation excludes evaluator-only/hidden material | REUSE | `AVP-ENVIRONMENT-005`, `AVP-SECURITY-004` | Resource descriptors and operation results inherit visibility rules. |
| Evaluator projection identity binds projection id + digest | REUSE | `AVP-ENVIRONMENT-006` | Resource profiles may define projections but not a competing projection identity model. |
| Snapshot ownership binds Environment and represented state identity | REUSE | `AVP-ENVIRONMENT-007` | Resource snapshots inherit the same fail-closed ownership rule. |
| Restore fidelity cannot be overstated | REUSE | `AVP-ENVIRONMENT-008` | Reuse the existing fidelity vocabulary; Fabric adds only aggregation semantics. |
| StateDiff binds before/after/projection semantics | REUSE | `AVP-ENVIRONMENT-009` | Domain profiles may add diff semantics without redefining StateDiff identity. |
| Fault identity/target/activation/clear remain evaluator-controlled | REUSE | `AVP-ENVIRONMENT-010`, `AVP-SECURITY-005` | Network fault mechanisms do not create a second fault lifecycle. |
| Released/stale handles fail closed | REUSE | `AVP-ENVIRONMENT-011` | Applies to Fabric/resource references as applicable; does not by itself define retry-safe cleanup. |
| One unambiguous Core Episode lifecycle projection | REUSE | `AVP-CORE-001`, `AVP-CORE-008`, `AVP-CORE-009` | No Fabric-specific Episode state machine. |
| No new Subject side effects after `QUIESCING` | REUSE | `AVP-CORE-011` | Resource settling may complete already accepted work only. |
| Lifecycle/Validity/Task Verdict remain distinct | REUSE | `AVP-CORE-006`, `AVP-CORE-010`, `AVP-SCENARIO-009` | Provision/reset/restore/cleanup infrastructure failure must not become Agent failure. |
| Subject/control/evaluator routes remain separated | REUSE | `AVP-SECURITY-001` | Fabric privileged controls stay outside Subject routes. |
| Undeclared Subject capability access fails closed | REUSE | `AVP-SECURITY-002` | This governs authorization, not whether an implementation supports a Resource Capability. |
| Evaluator credentials remain outside Subject context | REUSE | `AVP-SECURITY-003` | Resource credentials inherit this rule. |
| Hidden evaluator material remains hidden | REUSE | `AVP-SECURITY-004` | Applies to snapshots, manifests, fixtures, control metadata, and diagnostics. |
| Future fault schedules remain private | REUSE | `AVP-SECURITY-005` | Network/domain profiles must compose with this rule. |
| Isolation assurance is dimensional and non-inflating | REUSE | `AVP-SECURITY-006`, `SecurityAssurance` schema | Do not create Fabric isolation levels. |
| Retained bytes use exact-byte Artifact identity | REUSE | `AVP-EVIDENCE-001..007` | Fabric manifests/snapshots/traces that become Evidence reuse Artifact/Evidence identity. |
| Environment is composed from independently identified resources | NEW | Base Fabric spec | Define Environment Resource membership and ownership semantics. |
| Resource identifier is a protocol reference, not Artifact content identity | NEW + REUSE | Base Fabric spec + Evidence identity | Define reference identity while explicitly preserving Evidence digest semantics. |
| Portable resource kind is implementation/vendor-neutral | NEW | Base Fabric spec | Base vocabulary should define coarse kinds only when interoperability value is clear. |
| Resource Capability Declaration is conformance-bearing and revision-bound | NEW | Base Fabric spec | A declaration activates the requirements/TCK for its governed semantic revision/profile; backend/product name is insufficient. |
| Resource Capability support is distinct from Subject Capability authorization | NEW boundary rule | Base Fabric spec + Scenario/Security reuse | Prevent implementation support metadata from widening Subject access. |
| Undeclared required Resource Capability causes compatibility failure before the requested side effect | NEW | Base Fabric spec | This is implementation/Scenario compatibility, not `AVP-SECURITY-002` Subject authorization. |
| Required/optional participation is derived from the materialized execution contract | NEW | Base Fabric spec + Scenario reuse | Backend availability can satisfy or fail requiredness but cannot rewrite it. |
| Fabric manifest binds Environment identity, Scenario identity, resource membership, kinds, revision-bound capabilities, and immutable identity references | NEW | Base Fabric spec + future schema | Define language-neutral representation; do not promote Python `EpisodeManifest`. |
| Composite operation reports machine-readable per-resource outcome | NEW | Base Fabric spec + future schema | Required for reset/snapshot/restore/release honesty. |
| Composite success requires every required participant to satisfy the requested operation semantics | EXTEND | Environment operation semantics + base Fabric spec | Adds multi-resource aggregation; does not change single-resource semantics. |
| Composite restore fidelity is no stronger than every required participating resource can establish | EXTEND | `AVP-ENVIRONMENT-008` + base Fabric spec | Define aggregation without creating new fidelity values. |
| Composite snapshot/restore/reset does not imply atomic distributed transaction | NEW | Base Fabric spec | Atomicity may only be claimed through a separately defined cross-resource capability with conformance evidence. |
| Partial operation failure is never silently normalized to success | NEW/EXTEND | Base Fabric spec + Core result separation | Preserve per-resource failure evidence and evaluator validity decision. |
| Cleanup is safe to retry at the protocol-observable level | NEW | Base Fabric spec | Repeated cleanup must not resurrect resources or create a new Subject-visible side effect merely because cleanup was retried. |
| Capability conformance must execute real implementation behavior | NEW conformance rule | Fabric TCK design | Self-reported capability tables, class shape, fixtures, or backend names are insufficient evidence. |
| A negative implementation may preserve metadata while violate behavior and must fail TCK | NEW conformance rule | Fabric TCK design | Prevent metadata-only/self-certifying profiles. |
| Global `deterministic=true` is prohibited as a substitute for scoped claims | NEW design constraint | Base Fabric/profile design | Define only claims whose controlled dimensions and observations can be specified and tested. |
| Relational projection/schema/data/reset/snapshot behavior | PROFILE | Future relational-state profile | PostgreSQL/MySQL mechanics remain implementation evidence. |
| Browser context/state/restore behavior | PROFILE | Future browser profile | Playwright is a reference adapter candidate, not protocol authority. |
| Network perturbation semantics | PROFILE | Future network-control profile | `netem`, proxy, service mesh, etc. remain implementation mechanisms. |
| Wall-clock/timer virtualization semantics | PROFILE | Future time-control profile | Must remain distinct from existing Environment logical time. |
| OCI-backed compute identity/runtime semantics | PROFILE | Future compute profile | Compose with OCI rather than duplicate OCI image/runtime standards. |
| microVM semantics | PROFILE / EXPERIMENTAL | Future decision only after portable semantics + executable TCK | No mandatory base Fabric dependency. |
| PostgreSQL/MySQL SQL, transaction APIs, snapshot token formats | NON-NORMATIVE | Backend implementation | Must not leak into base Fabric API or language-neutral TCK. |
| Playwright classes/handles/storage filenames | NON-NORMATIVE | Browser adapter | Must not become AVP resource model. |
| Linux `tc`/`netem` commands, qdisc handles, kernel-specific timing | NON-NORMATIVE | Network adapter | Portable TCK observes semantic behavior only. |
| Docker/containerd/Firecracker/Kata technology label | NON-NORMATIVE | Compute deployment | Technology name never proves capability or SecurityAssurance. |
| Python Protocol/dataclass/enum shapes | NON-NORMATIVE | Reference runtime | Must follow spec/schema/TCK after those surfaces exist. |
| Giant universal adapter with optional methods / scattered `supports_*` | NON-NORMATIVE / REJECT | Architecture guardrail | Use resource composition and Resource Capability contracts instead. |
| Compatibility shims for unreleased Alpha 3 internal layouts | NON-NORMATIVE / REJECT | Repository policy | Design final public abstraction before implementation; do not preserve throwaway internal API. |

## Capability vocabulary decision

The word **capability** already has an important AVP meaning at the Subject/Scenario/Security boundary. Alpha 3 must not overload it ambiguously.

The normative Fabric drafting phase should use these terms:

### Resource Capability

A **Resource Capability** is a portable, conformance-bearing behavior that an Environment Resource implementation claims it can provide.

Examples in future profiles might include state snapshot/restore, browser storage-state reset, bounded network latency injection, controlled wall-clock advance, or OCI compute launch identity. Exact identifiers are not frozen by this audit.

A Resource Capability answers:

> What portable Environment behavior can this resource implementation satisfy?

It does **not** answer:

> What is the Subject authorized to call or observe?

### Subject Capability

**Subject Capability** retains its existing Scenario/Security meaning: the operation or access surface exposed to the Subject by the materialized actor capability projection and enforced fail-closed.

Resource Capability support MUST NOT grant or widen Subject Capability authorization.

This distinction is mandatory for the follow-up spec. A conforming implementation may support a privileged Resource Capability such as snapshot/restore while exposing no corresponding Subject Capability at all.

### Resource Capability Declaration

A **Resource Capability Declaration** is a machine-readable claim that a specific Environment Resource supports a named Resource Capability under a governed semantic profile/revision.

The declaration is conformance-bearing. It is neither a feature flag nor evidence by itself.

A declaration must bind enough profile/revision identity to prevent semantic drift under a stable capability identifier. A stable name must not silently acquire incompatible mandatory behavior while retaining an unchanged declaration identity. The exact serialized versioning shape is deferred to normative/schema design rather than inferred from Python class versions.

### Fabric-level capability

The base design does not use `Fabric Capability` as a synonym for Resource Capability. A future Fabric-level capability is reserved for genuinely cross-resource semantics, such as a precisely defined coordinated-consistency property, and would require its own portable contract and conformance evidence.

## Resource vocabulary decision

The following vocabulary is sufficiently stable to carry into normative drafting.

### Environment Fabric

An AVP Environment whose authoritative external state/capability surface is composed from one or more Environment Resources. It remains subject to all applicable Environment requirements.

### Environment Resource

An independently identifiable member of one Environment Fabric whose state or behavior participates in verification.

A resource is not necessarily a process, container, service, machine, database, or browser. Those are possible implementation forms.

### Resource Identifier

A stable identifier unique within the owning Environment instance for the lifetime in which the reference is valid.

A Resource Identifier is not an Artifact digest and must not be reused to bypass stale/foreign ownership checks.

### Resource Kind

A coarse portable interoperability classification. Initial candidate kinds for specification review are:

- `state`
- `browser`
- `network`
- `time`
- `compute`

These values should remain a deliberately small closed vocabulary for the first Fabric schema if adopted. Vendor/product names are implementation metadata, not Resource Kind values.

No new kind should be added merely because a backend product exists; it should represent a distinct portable interoperability domain.

### Required Resource / Required Resource Capability

A resource or Resource Capability whose presence/semantics are prerequisites of the **materialized execution contract**: the bound ScenarioInstance together with the selected governed profile/capability requirements.

Requiredness is immutable for the lifetime of the bound Fabric instance. Backend availability may satisfy or fail that requirement; it may not downgrade it to optional.

### Optional Resource / Optional Resource Capability

A resource or Resource Capability not required by the materialized execution contract. Its mere implementation availability must not silently make it mandatory or alter Scenario semantics.

### Fabric Manifest

The proposed language-neutral immutable composition description that binds:

- owning Environment instance identity;
- ScenarioInstance identity;
- resource membership;
- Resource Identifier;
- Resource Kind;
- revision/profile-bound Resource Capability Declarations;
- materialized required/optional participation where representation is needed;
- profile-required immutable identity references;
- permitted namespaced implementation metadata.

The manifest representation, when retained as verification Evidence, is itself identified by normal AVP Artifact exact-byte semantics.

The Fabric Manifest is not the Python reference runtime `EpisodeManifest` and must not inherit that implementation's field layout by convenience.

### Resource Operation Result

A machine-readable result for one resource participating in a composite Fabric operation. It must preserve at least the resource identity and portable operation outcome required to evaluate the aggregate operation. Domain profiles may add namespaced diagnostics but may not redefine base outcome semantics.

### Composite Operation Result

The result of a Fabric operation spanning multiple resources. It binds the requested operation to the participating resource result set and derives aggregate status only from portable rules.

A Composite Operation Result is not evidence of distributed atomicity.

### Participation

A resource's role in a composite operation as fixed by the materialized execution contract and the applicable operation/profile semantics. The base contract needs to distinguish at least required participation, permitted non-participation, and operation failure. Exact serialized values belong in the schema design.

### Aggregate Restore Fidelity

The restore fidelity that the Fabric may truthfully claim after considering every required resource participating in the restored state. It reuses the existing Environment fidelity vocabulary and never invents a stronger value than the resource results justify.

## Base Fabric normative candidate set

The follow-up normative specification should be intentionally compact. This audit recommends drafting approximately these requirement families rather than copying the existing Environment contract:

1. **FABRIC-001 — Resource membership and ownership**  
   Every resource belongs to one owning Environment instance and carries a stable resource reference sufficient for foreign/stale rejection.

2. **FABRIC-002 — Portable resource classification**  
   Resource Kind and Resource Capability declarations use protocol-defined semantics rather than vendor/product identity.

3. **FABRIC-003 — Resource capability honesty and revision binding**  
   A declared Resource Capability activates the selected governed capability/profile revision requirements; unsupported required capability negotiation fails before the requested side effect, and a stable declaration identity cannot silently acquire incompatible mandatory semantics.

4. **FABRIC-004 — Authorization separation**  
   Resource Capability support never widens the materialized Subject Capability projection.

5. **FABRIC-005 — Fabric manifest binding**  
   The composition manifest binds Environment/Scenario identity, resource membership, portable kinds, revision-bound capabilities, required immutable identity references, and materialized participation information required by the contract.

6. **FABRIC-006 — Required resource/capability completeness**  
   Requiredness is derived from the materialized execution contract and cannot be rewritten by backend availability; the Fabric cannot become ready while a required resource/capability is absent or incompatible.

7. **FABRIC-007 — Per-resource composite outcomes**  
   Multi-resource operations preserve machine-readable per-resource participation/outcome rather than collapsing partial results.

8. **FABRIC-008 — Aggregate success honesty**  
   A composite operation cannot report success while any Required Resource failed to establish the operation's required semantics.

9. **FABRIC-009 — Aggregate restore honesty**  
   Fabric restore fidelity cannot exceed the fidelity established by every Required Resource participating in restored state.

10. **FABRIC-010 — No implicit atomicity**  
    Composite operation success does not imply cross-resource atomicity; stronger atomicity requires separately specified and conformance-tested cross-resource semantics.

11. **FABRIC-011 — Evidence/security composition**  
    Fabric descriptors/results inherit existing AVP visibility, secret, Artifact integrity, Subject capability, and SecurityAssurance rules rather than redefining them.

12. **FABRIC-012 — Executed capability conformance**  
    Conformance for a claimed Resource Capability requires an execution path that observes the claimed behavior; metadata-only self-certification is insufficient.

13. **FABRIC-013 — Retry-safe cleanup**  
    Repeating cleanup after successful release is safe at the protocol-observable level: it does not resurrect the resource, establish a new authoritative resource under a stale reference, or initiate a new Subject-visible side effect solely because cleanup was retried. Cleanup failure remains infrastructure/validity information rather than Task Verdict.

The exact requirement IDs and wording are not normative until the future Fabric specification and requirement index are reviewed. They are a drafting target derived from this audit.

## What must not enter the base Fabric specification

The base spec must not standardize:

- SQL dialects, database engine internals, transaction APIs, filesystem paths, snapshot token formats;
- browser automation library object models;
- packet/qdisc/kernel command syntax;
- process injection techniques for virtual time;
- Docker/containerd/CRI command APIs;
- microVM implementation APIs;
- one hosted scheduler, orchestration topology, worker model, cloud provider, or commercial control plane;
- an AVP-specific replacement for OCI image/runtime specifications;
- a new isolation-level ladder;
- a new Artifact identity scheme;
- a new Episode lifecycle;
- a new global determinism flag.

Those exclusions are architectural correctness requirements, not missing features.

## Schema consequences

If the base Fabric proposal advances, schema work should begin only after the normative requirement wording is reviewable. At minimum, schema review is expected for:

- `EnvironmentFabricManifest` (working name);
- Environment Resource descriptor;
- Resource Capability Declaration including semantic revision/profile identity;
- Resource Operation Result / Composite Operation Result as needed by the spec.

The schema must use `additionalProperties: false` for protocol-owned objects unless the specification deliberately defines a namespaced extension point. An untyped generic property bag must not be used as a temporary substitute for known normative structure.

Schema field presence must follow normative semantics; the schema must not invent requirements that the prose specification does not define.

## TCK consequences

A base Fabric TCK should prove composition semantics without requiring every Alpha 3 domain backend. It should include, at minimum:

- resource membership/ownership and foreign-resource rejection;
- required-resource/capability compatibility failure without backend-driven downgrade;
- Resource Capability semantic revision/profile binding;
- Resource Capability vs Subject Capability separation;
- manifest identity/binding behavior;
- multi-resource success with all required resources succeeding;
- partial required-resource failure that cannot be reported as aggregate success;
- mixed restore fidelity that cannot be inflated;
- stale/released resource failure;
- retry-safe cleanup and infrastructure-failure separation;
- Evidence/Security visibility composition where applicable;
- a negative adapter that advertises the same capability metadata as a conforming adapter but violates behavior, proving the TCK executes the operation instead of trusting declarations.

Relational/browser/network/time/compute TCK cases should be conditional profile suites layered after the base Fabric semantics are stable.

## Backend implementation gate

No official Alpha 3 backend implementation for newly portable Fabric semantics should merge before all of the following are reviewable for the relevant behavior:

1. accepted design direction in AEP-0009 or its successor decision;
2. normative requirement text;
3. requirement-index traceability;
4. machine-readable schema when serialized protocol resources are involved;
5. execution-sensitive TCK cases and profile/registry entries;
6. explicit security composition analysis.

A backend may be used privately for feasibility research, but private experiments do not define public API shape and must not be merged as a temporary protocol implementation.

This gate intentionally rejects the pattern "implement PostgreSQL/Playwright first, generalize later."

## Compatibility conclusion

The proposed base Fabric contract is additive to the stable Alpha 2 Environment contract. Existing `avp-environment-v0.1` implementations remain valid without claiming Fabric conformance. A future Fabric profile must explicitly depend on the applicable Environment/Core/Scenario/Security/Evidence semantics rather than copy them under new identifiers.

Because Alpha 3 introduces new normative semantics, it must not be smuggled into the current `0.3.1.dev0` maintenance identity as if it were a patch-level maintenance change. Protocol/release version selection remains a separate governed decision.

## Audit conclusion

**READY FOR AEP PROTOCOL REVIEW / NORMATIVE SPEC DRAFTING — NOT READY FOR BACKEND IMPLEMENTATION.**

The base Fabric's new portable surface is sufficiently bounded to review as an AEP and later draft as a small language-neutral specification without relying on a PostgreSQL, Playwright, Linux, OCI, or microVM implementation as authority.

The next authority-chain step after AEP acceptance is the Environment Fabric normative specification plus requirement index. Schema and executable TCK follow that specification; reference/backend implementation remains downstream.