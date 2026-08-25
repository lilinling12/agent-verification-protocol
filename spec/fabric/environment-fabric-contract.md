# AVP Environment Fabric Contract v0.1

Status: draft normative candidate

## 1. Scope

This specification defines the language-neutral composition contract for an AVP Environment whose authoritative external state or controlled behavior is composed from one or more independently identified Environment Resources.

Environment Fabric is additive to the AVP Environment v0.1 contract. A Fabric implementation MUST satisfy all applicable Environment, Scenario, Core, Security, and Evidence requirements selected for the Episode. This specification does not replace those contracts and does not define a second Episode lifecycle, Artifact identity model, isolation scale, or Task Verdict model.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are interpreted as requirement terms for conformance.

The base Fabric contract deliberately does not standardize PostgreSQL, MySQL, Playwright, Linux networking primitives, OCI runtimes, containers, microVMs, or another backend product. Domain profiles MAY define portable resource behavior separately when that behavior has implementation-independent semantics and executable conformance coverage.

## 2. Portable model

An **Environment Fabric** is an AVP Environment composed from one or more **Environment Resources**.

An **Environment Resource** is an independently identifiable member of one Fabric whose state or behavior participates in verification. A Resource Identifier is a protocol reference scoped to its owning Environment instance. It is not an Artifact content digest.

The v0.1 base **Resource Kind** vocabulary is closed to:

- `state`;
- `browser`;
- `network`;
- `time`;
- `compute`.

These values classify portable interoperability domains. Vendor or product names are implementation metadata and MUST NOT be substituted for Resource Kind values.

A **Resource Capability** is a portable, conformance-bearing behavior supported by an Environment Resource. A Resource Capability Declaration binds a capability identifier to a governed profile and semantic revision. It describes implementation support; it does not grant Subject authorization.

A resource and each declared Resource Capability has materialized participation of `REQUIRED` or `OPTIONAL`. Participation is derived from the materialized execution contract and is immutable for the lifetime of the bound Fabric instance.

A **Composite Operation Result** preserves one Resource Operation Result for each resource in the operation scope. Resource operation status is one of `SUCCEEDED`, `FAILED`, or `NOT_PARTICIPATING`. `NOT_PARTICIPATING` is valid only for an optional resource that the selected operation/profile permits not to participate.

For restore, this specification reuses the Environment v0.1 fidelity values `EXACT`, `STATE_EQUIVALENT`, and `NON_EQUIVALENT`; it does not define another restore scale.

## 3. Resource identity and classification

### AVP-FABRIC-001 — Resource membership and ownership

Every Environment Resource MUST bind a non-empty Resource Identifier and the owning Environment instance identity. Resource Identifiers MUST be unique within one Fabric manifest. A resource reference used with a different Environment instance, or after the owning Fabric/resource reference has become stale or released, MUST fail closed and MUST NOT silently select, create, or resurrect authoritative resources. A Resource Identifier MUST NOT be treated as Artifact content identity.

### AVP-FABRIC-002 — Portable resource classification

Every Environment Resource MUST declare exactly one Resource Kind from the v0.1 base vocabulary and MUST express portable Resource Capability support through Resource Capability Declarations rather than backend or vendor identity. A backend/product name, class name, process type, image label, or implementation inheritance relationship MUST NOT by itself establish Resource Kind semantics or Resource Capability conformance.

## 4. Resource Capability contract

### AVP-FABRIC-003 — Capability honesty and revision binding

Every Resource Capability Declaration MUST bind a capability identifier, governed profile identifier, semantic revision, and materialized participation. A declaration activates the mandatory semantics of that selected capability/profile revision for the resource. An implementation MUST NOT silently change incompatible mandatory semantics under an unchanged declaration identity. If a `REQUIRED` Resource Capability is absent, unknown, or incompatible with the selected revision, compatibility/provisioning MUST fail before the requested side effect occurs. Capability metadata alone MUST NOT be treated as proof that the declared behavior is implemented.

### AVP-FABRIC-004 — Subject authorization separation

Resource Capability support MUST NOT grant, widen, or substitute for Subject Capability authorization. The Subject-visible operation and observation surface MUST remain the materialized Scenario/Security capability projection even when the implementation supports additional privileged Resource Capabilities. Privileged Fabric controls and their credentials MUST remain outside Subject authority.

## 5. Fabric manifest and participation

### AVP-FABRIC-005 — Fabric manifest binding

A portable `EnvironmentFabricManifest` MUST bind the owning Environment instance identity, the ScenarioInstance identity, and a non-empty resource membership set. Each resource entry MUST bind its Resource Identifier, Resource Kind, materialized participation, Resource Capability Declarations, and profile-required immutable identity Artifact references. Resource membership, resource participation, and capability participation in the manifest MUST remain immutable for the lifetime of the bound Fabric instance.

When manifest bytes or referenced immutable identity material are retained as verification Evidence, their identity MUST use the existing AVP Artifact identity rules. The portable manifest MUST NOT carry evaluator credentials, future hidden fault schedules, or other material forbidden by the Security visibility contract. Adapter-private implementation metadata MAY exist outside the portable manifest; base v0.1 does not define an untyped portable metadata bag.

### AVP-FABRIC-006 — Required resource and capability completeness

`REQUIRED` versus `OPTIONAL` participation MUST be determined by the materialized execution contract, not by backend availability. Backend availability MAY satisfy or fail that contract but MUST NOT downgrade a required resource/capability to optional or silently promote an available optional feature into required Scenario semantics. A Fabric MUST NOT become ready while any required resource is absent or while any required Resource Capability is absent or incompatible. Absence of an optional resource/capability MAY be accepted only when the selected execution contract and applicable profiles do not require it.

## 6. Composite operation results

### AVP-FABRIC-007 — Per-resource composite outcomes

A reset, snapshot, restore, release, or other Fabric operation spanning multiple resources MUST produce a machine-readable Composite Operation Result that preserves the operation identity and one unambiguous Resource Operation Result for every resource in the operation scope. Resource results MUST retain Resource Identifier, materialized participation, and portable operation status. A required participant MUST NOT be omitted or represented as `NOT_PARTICIPATING`. Partial resource outcomes MUST NOT be discarded when an aggregate result is derived.

### AVP-FABRIC-008 — Aggregate success honesty

A Composite Operation Result MUST NOT report aggregate `SUCCEEDED` when any `REQUIRED` resource failed to establish the semantics required by that operation. A failed required participant therefore forces aggregate `FAILED`. Failure or non-participation of an `OPTIONAL` resource does not by itself force aggregate failure unless the materialized execution contract or selected profile makes that resource required for the operation. Aggregate status MUST NOT erase the per-resource outcome that justified it.

### AVP-FABRIC-009 — Aggregate restore fidelity honesty

For an aggregate restore reported as `SUCCEEDED`, `aggregateRestoreFidelity` MUST be no stronger than the restore fidelity established by every `REQUIRED` resource participating in restored state. The ordering from strongest to weakest is `EXACT`, `STATE_EQUIVALENT`, `NON_EQUIVALENT`. If a required restore fails to establish the requested restored state, aggregate status MUST be `FAILED` and aggregate restore fidelity MUST NOT claim equivalence stronger than `NON_EQUIVALENT`. An optional participant MAY NOT lower the aggregate fidelity unless the materialized execution contract/profile makes its restored state required.

### AVP-FABRIC-010 — No implicit cross-resource atomicity

Aggregate success, per-resource success, a Fabric snapshot, and a Fabric restore MUST NOT be interpreted as proof that the participating resources changed atomically or shared a distributed transaction boundary. The base Fabric contract defines no cross-resource atomicity claim. A stronger coordinated-consistency or atomicity property requires a separately governed capability/profile with explicit semantics and executable conformance evidence. On partial failure, already-established resource effects MUST remain observable in the per-resource result/evidence rather than being hidden behind an atomicity fiction.

## 7. Security, Evidence, and conformance

### AVP-FABRIC-011 — Evidence and security composition

Fabric manifests, resource descriptors, operation results, snapshots, projections, diagnostics, and immutable identity material MUST compose with the existing AVP Security and Evidence contracts. Subject-visible representations MUST exclude evaluator credentials, hidden grader/control material, future fault schedules, and other evaluator-private state. Retained exact bytes MUST use AVP Artifact identity rather than Resource Identifiers, backend locators, snapshot tokens, image tags, or filesystem paths as substitutes. Fabric implementation technology MUST NOT inflate `SecurityAssurance` claims or create a competing isolation level.

### AVP-FABRIC-012 — Executed capability conformance

Conformance for a claimed Resource Capability MUST execute an implementation path that can observe whether the behavior required by the bound capability/profile revision is actually satisfied. A capability declaration, manifest entry, backend/product name, fixture, class shape, or self-reported support table MUST NOT be sufficient by itself. A conformance test MUST be capable of rejecting an implementation that advertises the same capability metadata as a conforming implementation but violates the required observable behavior.

## 8. Release and cleanup

### AVP-FABRIC-013 — Retry-safe cleanup and failure separation

After successful release, repeating Fabric/resource cleanup MUST be safe at the protocol-observable level: it MUST NOT resurrect a released resource, establish a new authoritative resource under the stale reference, or initiate a new Subject-visible side effect solely because cleanup was retried. Operations through released/stale Fabric or resource references MUST continue to fail closed. Cleanup failure MUST be represented as infrastructure/validity information and MUST NOT be converted into Agent Task Verdict failure solely because cleanup did not complete.

## 9. Schema and extension rules

The v0.1 serialized base resources are defined by the companion JSON Schemas for Resource Capability Declaration, Environment Resource, Environment Fabric Manifest, and Fabric Operation Result.

Protocol-owned objects use closed fields. This version intentionally omits a generic implementation metadata property bag. Future portable extension points require a governed specification/schema revision rather than relying on unknown fields.

Schema validation is necessary but not sufficient for conformance. Cross-object rules such as resource-id uniqueness, owner equality, requiredness aggregation, restore-fidelity aggregation, stale-reference behavior, Subject authorization separation, and executed capability behavior require semantic TCK execution.

## 10. Non-normative implementation freedom

Conforming implementations MAY use in-memory resources, databases, browsers, proxies, operating-system controls, OCI runtimes, containers, virtual machines, remote services, or other mechanisms. Those choices remain implementation evidence unless a separately selected profile defines portable semantics for them.
