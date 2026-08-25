# AEP-0009 — Environment Fabric Composition and Capability Contract

- Status: Accepted
- Authors: AVP maintainers and contributors
- Created: 2026-08-23
- Accepted: 2026-08-23
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric

## Summary

This AEP defines the accepted portable composition direction for AVP Alpha 3 Environment Fabric.

AVP Environment v0.1 already defines authoritative environment ownership, ScenarioInstance binding, reset semantics, environment-scoped logical time, actor-scoped observations, evaluator projections and digests, snapshot/restore honesty, semantic diff binding, fault lifecycle semantics, and fail-closed stale-handle behavior. Alpha 3 MUST extend that contract rather than replace it.

The Environment Fabric model represents one AVP Environment as a composition of identified resources that expose explicit portable capabilities. A resource may be backed by a relational database, browser context, network control point, time-control mechanism, OCI-compatible compute runtime, or another implementation technology, but product and vendor APIs do not become AVP protocol semantics merely because a reference adapter uses them.

The central rule is:

> Portable semantics are defined before backend implementation, and backend implementation never becomes the authority for portable semantics.

This AEP deliberately does not standardize PostgreSQL, MySQL, Playwright, Linux `netem`, Docker, containerd, Firecracker, Kata Containers, or any other specific implementation. Those technologies are implementation evidence and interoperability targets.

## Problem

Environment v0.1 intentionally keeps database, browser, container, VM, scheduler, and adapter choices non-normative. That separation is correct, but Alpha 3 introduces a new interoperability problem: a realistic verification Environment is often composed from several independently managed resources.

For example, one Episode may need all of the following at once:

- a relational database whose authoritative state can be projected and restored;
- an isolated browser session with explicit storage-state handling;
- a controlled network path where faults can be scheduled without leaking future fault plans to the Subject;
- a controllable time source with honest boundaries around what is and is not virtualized;
- a compute execution boundary whose image/configuration identity is reproducible;
- evaluator-visible Evidence binding all resource identities and state transitions together.

Without a portable composition contract, independent implementations are likely to converge on incompatible assumptions:

1. capability support may be inferred from backend type rather than declared and proven;
2. a composite snapshot may be called "exact" even if one resource is only logically state-equivalent after restore;
3. one backend may expose privileged control operations through a Subject route;
4. a global `deterministic=true` flag may conceal real nondeterminism in wall time, networking, browser behavior, or external services;
5. backend-specific error types may leak into protocol-level validity or task verdicts;
6. a reference implementation may accidentally define protocol semantics through its Python class layout or backend control flow;
7. TCK adapters may self-certify by inspecting capability tables or fixtures instead of executing the claimed operation.

Alpha 3 therefore needs a small, language-neutral composition layer before any production backend is treated as an AVP Environment Fabric implementation.

## Existing contract and compatibility baseline

This AEP is additive to the existing authority chain:

```text
Environment v0.1 normative specification
        -> Environment schemas / requirement index
        -> avp-environment-v0.1 TCK
        -> independent implementations / reference runtime
```

A conforming Environment Fabric remains an AVP Environment. It MUST preserve all applicable Environment v0.1 requirements and Core lifecycle projection.

This AEP does not change the meaning of:

- `Environment`;
- `ScenarioInstance` binding;
- `Evidence` or `ArtifactRef` identity;
- Core Episode lifecycle states;
- `SecurityAssurance` dimensions;
- Environment restore fidelity values already defined by the Environment contract;
- Task Verdict, Validity, or infrastructure failure separation.

Existing implementations that conform to `avp-environment-v0.1` are not required to claim Environment Fabric capabilities.

## Design principles

### 1. Capability semantics, not backend names

Portable capability declarations MUST describe observable behavior, not implementation products.

An implementation MUST NOT obtain a capability claim solely because a backend is named `postgres`, `mysql`, `playwright`, `docker`, `containerd`, `firecracker`, or another recognized technology.

A backend may support a capability only when the implementation can satisfy the corresponding portable requirements and conformance cases.

### 2. Composition without a distributed-transaction fiction

Environment Fabric MUST NOT imply that all resources can be atomically snapshotted, restored, reset, or faulted as one distributed transaction.

When an operation spans multiple resources, the portable result MUST preserve per-resource outcomes and MUST NOT report stronger aggregate fidelity or atomicity than the weakest relevant resource can demonstrate.

An implementation MAY offer stronger atomic coordination through a separately specified cross-resource capability when that property has portable semantics and conformance evidence. It MUST NOT be assumed by the base Fabric contract.

### 3. Honest reproducibility dimensions

Environment Fabric MUST NOT define a single global deterministic boolean.

Reproducibility claims must remain scoped to the behavior actually controlled or observed, including where relevant:

- authoritative state equivalence;
- operation ordering;
- Environment logical-time behavior;
- wall-clock control;
- timer behavior;
- network-fault scheduling;
- external dependency identity;
- browser/runtime identity;
- compute/image identity.

Unsupported or uncontrolled dimensions remain explicitly unclaimed.

### 4. Security assurance is reused, not reinvented

Alpha 3 MUST reuse the existing AVP Security contract and `SecurityAssurance` resource. Environment Fabric MUST NOT create a competing numeric or ordinal "isolation level" that conflates API capability separation, credential separation, process isolation, network isolation, tenant isolation, and sandbox assurance.

### 5. Evidence identity is reused, not reinvented

Fabric manifests, resource snapshots, projections, traces, and diagnostic outputs that are retained as verification evidence MUST compose with AVP Evidence/Artifact identity. Exact retained bytes are identified by the existing Artifact digest rules.

A locator, backend identifier, database snapshot token, browser storage filename, OCI tag, or VM snapshot path MUST NOT replace AVP Artifact content identity when verification relies on retained bytes.

### 6. Core lifecycle remains the top-level lifecycle

Environment Fabric MAY have internal resource lifecycle states, but those states MUST project unambiguously onto the existing AVP Core Episode lifecycle and Environment operation semantics.

Alpha 3 MUST NOT introduce a competing Episode state machine.

## Portable model direction

### Environment Fabric

An **Environment Fabric** is an AVP Environment whose authoritative external state and capability surface are composed from one or more identified Environment Resources.

The Fabric is the control-plane composition boundary. It is not a hosted scheduler, cluster manager, cloud provisioning product, or commercial control plane.

### Environment Resource

An **Environment Resource** is one independently identifiable component whose state or behavior participates in an Environment Fabric.

A portable resource description contains at least:

- a stable resource identifier within the Environment instance;
- a portable resource kind;
- the declared Resource Capability identifiers and semantic revision/profile bindings for that resource;
- immutable identity material required by the selected resource profile;
- the ScenarioInstance / Environment ownership binding needed to reject foreign or stale use;
- optional namespaced implementation metadata that does not redefine protocol semantics.

Resource identifiers are protocol references, not content digests. Where a resource has immutable serialized configuration or retained snapshot material, those bytes are separately bound through AVP Artifact identity.

### Resource kind

Resource kinds provide coarse interoperability classification. The base Fabric design anticipates, but does not make mandatory, kinds such as:

- state;
- browser;
- network;
- time;
- compute.

The exact registered vocabulary belongs in the normative specification/schema work following this AEP acceptance. Vendor/product names MUST NOT be used as the primary portable resource kind.

### Resource Capability declaration

A **Resource Capability** is a portable, conformance-bearing behavior that an Environment Resource implementation claims it can provide. It answers what portable Environment behavior the resource can satisfy; it does not answer what the Subject is authorized to call or observe.

A **Subject Capability** retains its existing Scenario/Security meaning: the operation or access surface exposed to the Subject by the materialized actor capability projection. Resource Capability support MUST NOT grant, expand, or substitute for Subject Capability authorization.

A **Resource Capability Declaration** binds a Resource Capability identifier to a governed protocol/profile revision, or another reviewed semantic-version identity, sufficient to make the applicable requirements and TCK obligations unambiguous. A stable capability name MUST NOT silently acquire incompatible mandatory semantics under an unchanged declaration identity. Exact serialized version/revision fields belong to subsequent normative schema work.

A Resource Capability Declaration means the implementation claims the observable semantics required by that capability revision. It is not a discovery hint with no conformance consequence.

Rules:

1. an undeclared optional Resource Capability MUST NOT be assumed;
2. a required Resource Capability absent from the implementation MUST cause compatibility/provisioning failure before the requested side effect occurs;
3. when a Resource Capability is declared, all mandatory requirements for the bound capability revision/profile become applicable;
4. the corresponding TCK cases MUST execute the real adapter/runtime operation needed to observe the behavior;
5. a capability table, class inheritance relation, backend name, or fixture alone is not conformance evidence;
6. Resource Capability support MUST NOT widen the materialized Subject Capability projection.

The accepted base direction intentionally avoids freezing a large capability catalog. Domain profile work will define exact Resource Capability identifiers only when their portable semantics and tests are sufficiently precise.

A future Fabric-level capability may describe genuinely cross-resource semantics, such as a precisely defined coordinated consistency property, but such a capability is distinct from ordinary Resource Capability support and requires its own portable contract and conformance evidence.

### Required and optional participation

Whether a resource or Resource Capability is required is determined by the **materialized execution contract**: the bound ScenarioInstance together with the selected governed profile/capability requirements. That required/optional classification is immutable for the lifetime of the bound Fabric instance.

Backend availability MAY satisfy or fail that materialized contract. It MUST NOT rewrite a required resource/capability into an optional one because support is absent, and it MUST NOT silently promote an available optional backend feature into required Scenario semantics.

An optional resource or capability that is not required by the materialized execution contract does not become mandatory merely because the implementation can provide it.

## Fabric identity and manifest

Alpha 3 requires a language-neutral composition identity; it MUST NOT promote the Python reference runtime's `EpisodeManifest` or `resource_manifest_digest` field into protocol authority.

The follow-up normative specification SHOULD define an `EnvironmentFabricManifest` (name subject to specification review) that binds:

- the owning Environment instance identity;
- the ScenarioInstance identity required by Environment v0.1;
- the ordered or canonically represented resource membership set;
- each resource's portable kind and declared Resource Capability revision/profile bindings;
- each resource's immutable identity references required by its profile;
- required/optional participation as derived from the materialized execution contract where representation is needed;
- optional namespaced implementation metadata;
- the manifest representation's AVP Artifact identity when retained as Evidence.

The manifest MUST NOT include evaluator secrets or future hidden fault schedules in Subject-visible representations.

Two Fabric instances MUST NOT be treated as the same verification input merely because they use the same vendor products. Identity is established from the protocol-defined manifest and referenced immutable material, not from product labels.

## Lifecycle and operation coordination

### Provision

Fabric provisioning occurs within the existing `PROVISIONING` phase.

Before the Episode becomes `READY`, all resources and Resource Capabilities required by the materialized execution contract MUST either:

- be provisioned and bound to the Environment instance with the required semantics; or
- cause provisioning to fail closed with an infrastructure/protocol-validity result appropriate to the existing Core contracts.

Backend availability cannot weaken or rewrite those requirements. Optional resources and capabilities that are not required by the materialized execution contract do not become mandatory merely because a reference implementation can provision them.

### Reset

Fabric reset preserves Environment v0.1 reset semantics.

For a multi-resource reset, the operation result MUST retain resource-level status. The Fabric MUST NOT report successful establishment of the requested reset target while any required resource failed to establish its target state.

No distributed transaction is implied.

### Snapshot

A Fabric snapshot is a composition record, not an assertion that every backend supports identical snapshot mechanisms.

A portable Fabric snapshot SHOULD bind:

- Fabric / Environment ownership identity;
- one snapshot reference or explicitly declared non-participation result per required resource;
- the projection/state identity required to validate that snapshot under the resource profile;
- an immutable composition-manifest representation when retained.

A foreign, stale, missing, or integrity-invalid required component MUST cause fail-closed behavior.

### Restore

Restore fidelity MUST be reported honestly per resource.

An aggregate Fabric restore MUST NOT be reported with stronger fidelity than is justified by all required resources participating in the restored state. In particular, a single state-equivalent resource prevents an aggregate claim of exact restoration unless the future specification defines and the implementation proves a stronger cross-resource property.

A partial restore failure MUST NOT be silently converted into success. Implementations MUST expose sufficient machine-readable per-resource results for the Evaluator to determine whether the Episode remains valid.

### Quiescing

The existing Core `QUIESCING` side-effect boundary applies to the Fabric.

After entering `QUIESCING`, no new Subject-requested side effect may be initiated. Resource-specific settling MAY continue for operations accepted before the boundary according to the applicable profile. Those settled effects remain evidence.

### Release / cleanup

Resource cleanup MUST be safe to retry at the protocol-observable level and MUST preserve stale-handle fail-closed behavior. Repeating cleanup after successful release MUST NOT resurrect the resource, establish a new authoritative resource under the stale reference, or initiate a new Subject-visible side effect solely because cleanup was retried.

Cleanup retry safety is a distinct Fabric composition requirement candidate; it is not inferred solely from stale-handle rejection.

Cleanup failure is an infrastructure condition, not a Task Verdict. A cleanup failure MUST NOT be rewritten as Agent task failure.

Implementations SHOULD produce evaluator-visible diagnostics sufficient to identify leaked or incompletely released resources without exposing evaluator credentials or hidden verification material to the Subject.

## Resource-profile direction

This AEP establishes the composition contract. Domain semantics are intentionally separated so that they can evolve without turning the base Fabric into a vendor-specific union type.

### Relational state resources

A relational state profile should define portable state projection, snapshot/restore, reset, schema/data identity, and semantic-diff behavior.

It MUST NOT standardize PostgreSQL or MySQL transaction internals as AVP Core semantics. PostgreSQL snapshot export/import and MySQL/InnoDB consistent-read behavior are implementation evidence whose guarantees differ; the profile must normalize only properties that can be stated and tested portably.

### Browser resources

A browser profile should use an isolated browser-session/context boundary and explicitly define which state surfaces participate in AVP state identity or restore.

Cookies, local storage, IndexedDB, downloads, popups, service workers, cross-origin behavior, and browser/version identity MUST NOT be silently collapsed into one generic "browser state" claim.

A Playwright BrowserContext is a strong reference implementation candidate because it provides isolated browser sessions, but Playwright behavior is not the protocol.

### Network-control resources

A network profile should define semantic perturbations such as bounded latency, loss, disconnect, or name-resolution failure only where their observable semantics can be made portable.

Linux `netem`, proxy-based fault injection, service meshes, and user-space interceptors are implementation mechanisms. Kernel timer granularity, TCP queue behavior, TLS interception, and DNS behavior make exact packet-level equivalence non-portable in the base profile.

Future fault schedules remain evaluator-private under the existing Security contract.

### Time-control resources

A time-control profile must distinguish Environment logical time from host wall time and monotonic clocks.

Freeze/advance/timer controls may be declared only for clocks and processes actually under the implementation's authority. Database, browser, kernel, remote service, certificate-validity, and external-provider time dependencies MUST NOT be described as virtualized when they remain tied to real time.

### Compute resources

A compute profile should compose with OCI image/runtime concepts where applicable rather than redefining container configuration and lifecycle.

OCI image content identities and runtime configuration provide important implementation inputs, but AVP still needs its own verification-facing binding to the Environment/Scenario and Evidence model.

Container use MUST NOT automatically imply `process`, `network`, `tenant`, or `sandbox` assurance is `verified`.

### microVMs

microVM support remains experimental and conditional in Alpha 3.

Firecracker, Kata Containers, Cloud Hypervisor, and similar mechanisms may provide stronger deployment isolation than a conventional shared-kernel container, but startup model, host kernel, CPU model, device model, snapshot compatibility, and CI availability materially affect portability.

No mandatory AVP Fabric conformance profile should require a microVM until portable verification semantics and practical independent TCK execution are demonstrated.

## Failure semantics

Environment Fabric MUST preserve the existing separation between lifecycle, Validity, infrastructure health, and Task Verdict.

Backend-specific exceptions and status codes may appear in evaluator diagnostics under namespaced metadata, but they MUST be mapped to portable operation outcomes before they are used for conformance or evaluation validity.

Examples of infrastructure conditions include:

- required resource provisioning failure;
- required resource reset failure;
- integrity-invalid snapshot material;
- required restore failure;
- cleanup failure that prevents a trustworthy verification boundary;
- loss of privileged control-plane authority needed to complete the Episode.

These conditions MUST NOT be converted into Agent task failure solely because the Subject happened to be running when they occurred.

## Security analysis

Environment Fabric expands the privileged Control Plane and therefore increases risk.

Required security properties include:

1. Subject routes MUST remain distinct from privileged provision/reset/snapshot/restore/fault/time-control routes.
2. Evaluator/control credentials MUST NOT enter Subject execution contexts.
3. Future fault schedules MUST remain evaluator-private until the Environment contract makes an activated effect observable.
4. Resource descriptors and evidence MUST avoid embedding retrievable secrets when an opaque identity or evaluator-confidential reference is sufficient.
5. Compute/container/microVM implementations MUST not inflate SecurityAssurance claims based on technology labels.
6. Network-control implementations MUST not introduce unintended unrestricted egress or privileged-host routes.
7. Cleanup must be robust against untrusted Subject behavior and must not trust Subject cooperation to release privileged resources.
8. Snapshot/restore material must be ownership-bound and integrity-checked so one Environment cannot restore another Environment's privileged state by reference substitution.
9. Resource Capability support metadata MUST NOT be interpreted as Subject authorization; Subject Capability remains derived from the materialized actor projection and enforced by existing Security semantics.

## Alternatives considered

### Alternative A — backend-first implementation, abstraction later

Rejected.

Starting with PostgreSQL, Playwright, Docker, or another backend and extracting a common API after implementation would allow reference code to become de facto protocol authority. It also tends to preserve vendor-specific concepts in the eventual abstraction.

Alpha 3 requires the portable contract first.

### Alternative B — one universal EnvironmentAdapter with optional methods

Rejected.

A large interface containing `snapshot_database`, `open_browser`, `inject_network_fault`, `advance_clock`, `start_container`, and similar methods would produce backend-dependent nullability and scattered `supports_*` booleans. It would be difficult for independent implementations to negotiate or test capabilities consistently.

The Fabric uses explicit resource composition and declarative Resource Capability contracts instead.

### Alternative C — one mandatory full-stack `avp-environment-fabric` profile

Rejected as the primary conformance model.

Requiring database + browser + network + virtual time + container capabilities together would make conformance expensive, platform-dependent, and hostile to independent implementations. Base composition semantics should be portable, while domain capabilities are separately claimable and testable.

A small base Fabric conformance profile may be created for composition semantics, with resource profiles layered conditionally.

### Alternative D — define AVP isolation levels

Rejected.

The existing SecurityAssurance model already separates API capability, credential context, process, network, tenant, and sandbox claims. An ordinal Fabric isolation level would erase these distinctions and encourage overclaiming.

### Alternative E — promise atomic composite snapshot/restore

Rejected for the base contract.

Different resources have materially different snapshot semantics. A database transaction snapshot, browser storage-state capture, filesystem snapshot, container checkpoint, and VM snapshot are not automatically one atomic consistency point. Stronger coordination may be introduced only as an explicit cross-resource capability with evidence.

## Conformance strategy

The base Fabric TCK should remain language-neutral and test observable composition behavior through an implementation adapter.

Mandatory base cases should cover at least:

- resource inventory and stable ownership binding;
- Resource Capability declaration/revision honesty;
- rejection of an undeclared required Resource Capability before its requested side effect;
- Resource Capability versus Subject Capability authorization separation;
- required/optional participation derived from the materialized execution contract rather than backend availability;
- Fabric/Scenario binding;
- multi-resource operation result completeness;
- snapshot composition identity and tamper/foreign-resource rejection;
- restore-fidelity non-inflation;
- stale/released resource failure;
- cleanup retry safety/idempotency and infrastructure-failure separation.

Resource-profile TCK cases become mandatory only when the corresponding Resource Capability/profile revision is claimed.

Negative tests MUST include implementations that advertise the same static Resource Capability metadata as a conforming adapter but fail actual runtime behavior. Such implementations MUST fail conformance. This prevents capability-table inspection from becoming a substitute for execution evidence.

Built-wheel CI MUST continue discovering registered TCK profiles dynamically rather than maintaining a hard-coded profile allowlist.

## Implementation gate — no transitional architecture

This AEP establishes a project gate for Alpha 3:

> No database, browser, network, time, container, or microVM backend may be merged as the official Alpha 3 implementation of a new portable capability until the corresponding portable semantics, machine-readable contract where required, and executable TCK coverage are reviewable in the authority chain.

This does not prohibit research spikes outside the governed implementation path, but disposable research code MUST NOT be merged into the reference runtime or exposed as a public compatibility surface.

The following patterns are explicitly rejected for governed Alpha 3 implementation:

- backend-first APIs that are promised to be generalized later;
- temporary compatibility shims for pre-release internal layouts;
- public `dict[str, Any]` bags used instead of a reviewed schema for protocol resources;
- scattered `supports_*` booleans instead of declarative Resource Capability contracts;
- a global `deterministic` boolean;
- a numeric/ordinal isolation level duplicating SecurityAssurance;
- hard-coded backend-name branches in language-neutral TCK semantics;
- fixture/table inspection as proof of runtime behavior;
- reporting `EXACT` restore when only logical/state equivalence is demonstrated;
- converting backend/infrastructure failure into Agent task failure;
- treating container or microVM technology names as security-assurance proof.

## Governance and release boundary

This AEP is **Accepted**. Acceptance approves the Environment Fabric direction for downstream normative closure. It does not itself make this AEP `Final`, does not make downstream draft specifications normative merely by existence, and does not authorize backend-first implementation.

Acceptance authorizes the project to proceed in authority order with:

```text
Accepted AEP direction
  -> normative specification
  -> requirement index
  -> schema where serialized protocol resources require it
  -> execution-sensitive TCK
  -> reference implementation
  -> vendor/backend adapters
```

The specification/schema/TCK closure remains independently reviewable and must preserve the accepted boundaries in this AEP.

Acceptance does not:

- select a public AVP release;
- change `docs/releases/release-development-state.json` into release mode;
- authorize `v0.3.1` or another tag;
- authorize package-index publication;
- authorize signing/attestation publication;
- make any reference implementation behavior normative;
- authorize bypassing specification/schema/TCK work with backend implementation precedent.

Because AVP's current release policy says a pre-1.0 PATCH release must not intentionally introduce breaking normative changes, the eventual release vehicle for Alpha 3 protocol work must be chosen separately after the normative scope and compatibility impact are known. This AEP deliberately does not assign Alpha 3 to the currently planned `0.3.1` maintenance release.

## Accepted work decomposition

Work proceeds in authority order.

### Foundation

1. Environment Fabric normative specification.
2. Requirement index.
3. Schemas for new portable resources.
4. Base Fabric TCK profile and negative vectors.
5. Only then, reference composition implementation.

### Resource domains

Each resource domain should use a separate normative change only when it introduces protocol semantics beyond AEP-0009. Vendor-specific adapters alone do not require an AEP.

Expected domains:

- relational state resource profile, followed by PostgreSQL and MySQL reference adapters;
- browser resource profile, followed by Playwright reference adapter;
- network-control resource profile, followed by one or more proxy/kernel reference mechanisms;
- time-control resource profile, followed by a virtual-clock reference service where honest virtualization is possible;
- compute resource profile aligned with OCI, followed by a container reference runtime;
- microVM experiment kept conditional/non-normative until evidence supports a portable contract.

This decomposition avoids both extremes: one oversized AEP that permanently couples unrelated technologies, and one AEP per vendor integration.

## Accepted invariants

The following invariants are accepted direction and must be preserved by downstream normative closure unless a later governed AEP changes them:

1. no Fabric semantic duplicates or weakens Environment v0.1 without an explicit governed change;
2. SecurityAssurance remains the security-assurance model; Fabric does not add an isolation-level ladder;
3. Fabric identity composes with existing Evidence/Artifact identity rather than replacing it;
4. Core lifecycle projection remains unambiguous and no Fabric Episode state machine is introduced;
5. Resource Capability negotiation and semantic revision binding are language-neutral and distinct from Subject Capability authorization;
6. required/optional participation is fixed by the materialized execution contract rather than backend availability;
7. aggregate snapshot/restore semantics cannot overclaim atomicity or fidelity;
8. privileged Fabric controls remain separated from Subject routes and credentials;
9. mandatory vs conditional TCK boundaries must be testable by independent implementations;
10. negative TCK design must prove runtime execution rather than metadata self-certification;
11. cleanup retry safety has explicit base-Fabric requirement ownership and observable conformance semantics;
12. release/version selection remains a separate governance decision;
13. backend implementation remains downstream of portable semantics, schema where required, and executable conformance coverage.

## References and standards alignment

The normative specification phase should continue to prefer established external standards for mechanisms they already own.

Primary references informing this direction include:

- PostgreSQL transaction isolation and synchronized snapshot documentation: https://www.postgresql.org/docs/current/transaction-iso.html and https://www.postgresql.org/docs/current/functions-admin.html
- MySQL transaction isolation / consistent read documentation: https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html and https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html
- Playwright BrowserContext and storage-state documentation: https://playwright.dev/docs/api/class-browsercontext
- Linux `tc-netem` network-emulation semantics and limitations: https://man7.org/linux/man-pages/man8/tc-netem.8.html
- OCI Runtime Specification: https://specs.opencontainers.org/runtime-spec/
- OCI Image Specification: https://specs.opencontainers.org/image-spec/
- Firecracker project documentation for microVM implementation evidence: https://firecracker-microvm.github.io/

These sources inform implementation and interoperability boundaries. They do not become AVP normative text by reference unless a future AVP specification explicitly defines such a binding.
