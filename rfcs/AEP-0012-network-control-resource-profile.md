# AEP-0012 — Network Control Resource Profile v0.1

- Status: Draft
- Authors: AVP maintainers and contributors
- Created: 2026-09-02
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Network Control Resource

## Summary

AEP-0012 starts the portable design for the network-control resource domain required by AVP Alpha 3 Environment Fabric.

The core design constraint is inherited from AEP-0009:

> AVP must define network-control semantics before a proxy, Linux traffic-control mechanism, service mesh, kernel facility, or user-space interceptor is treated as an official Alpha 3 implementation, and implementation behavior must never become protocol authority by precedent.

The base Environment Fabric contract already recognizes `network` as a coarse Resource Kind. That classification is not a Network Control Resource Profile. It does not define a controlled path boundary, portable fault vocabulary, fault activation/settlement semantics, recovery semantics, observation model, execution identity, Subject visibility, or conformance-bearing capability.

This Draft therefore does **not** select Toxiproxy, Linux `tc/netem`, Envoy, Istio, a service mesh, a kernel API, or another provider. It does not yet create a normative specification, schema, capability registration, TCK profile, or reference runtime. Its purpose is to establish the problem boundary, standards alignment, candidate scope, security constraints, and design blockers that must be resolved before AEP-0012 can advance to `Proposed`.

A working capability/profile identity may be discussed during design, but no identifier in this Draft is an accepted protocol claim until the AEP lifecycle and downstream authority chain approve it.

## Problem

A network fault is not one portable packet-level primitive.

Real implementations inject perturbations at materially different layers and boundaries:

- kernel queueing and traffic-control facilities can delay, drop, duplicate, reorder, corrupt, or rate-limit packets subject to host-kernel timing and queue behavior;
- user-space TCP proxies can accept, reject, stall, close, reset, or forward connections but do not necessarily control every packet or preserve kernel-identical timing behavior;
- HTTP proxies and service-mesh filters can inject request/response delay or abort semantics at the application protocol layer rather than the transport layer;
- DNS resolvers and interceptors can alter name-resolution behavior without controlling an already-established transport connection;
- TLS termination or interception can expose application-layer control but changes trust, endpoint, and certificate behavior;
- browser, container, VM, and host-network boundaries determine which traffic actually traverses a selected control point;
- remote dependencies can remain outside Environment authority even when a local client path is controlled.

If AVP copied one implementation API into the protocol, independent implementations would be forced to emulate provider-specific mechanics rather than prove the same observable verification property.

Examples of invalid backend-first standardization include:

- declaring Linux `netem` delay distributions to be the AVP latency model;
- declaring Toxiproxy toxic names or ordering rules to be AVP fault identity;
- declaring Envoy HTTP fault-filter abort codes to be a generic network disconnect;
- treating an Istio VirtualService fault rule as proof that all Subject traffic crossed the intended control point;
- treating successful provider configuration as proof that the requested fault became active before Subject traffic was admitted;
- treating removal of a provider rule as proof that pre-existing affected connections recovered;
- claiming exact packet-level equivalence across kernels, TCP stacks, proxy implementations, and application protocols.

The Network Control Resource Profile must instead define only portable, observable claims whose boundaries and failure semantics can be tested independently of implementation technology.

## Existing AVP authority reused

AEP-0012 specializes existing contracts and must not create competing concepts.

### Environment v0.1

Reused unchanged:

- authoritative Environment ownership and ScenarioInstance binding;
- fault lifecycle semantics and evaluator-private future fault scheduling;
- actor-scoped Subject observations;
- evaluator-authoritative observations/projections where defined;
- Environment logical time without implying host wall-clock or kernel-clock virtualization;
- reset target honesty;
- stale/foreign handle rejection;
- lifecycle, Validity, infrastructure health, and Task Verdict separation;
- Artifact identity for retained exact Evidence bytes.

### Environment Fabric

Reused unchanged:

- `resourceKind: network` as coarse resource classification only;
- Resource Capability declaration and semantic-revision binding;
- REQUIRED/OPTIONAL participation from the materialized execution contract;
- Resource Capability versus Subject Capability authorization separation;
- resource identity and profile-required immutable identity Artifacts;
- per-resource/composite operation-result honesty;
- no implicit cross-resource atomicity;
- Security/Evidence composition;
- execution-sensitive capability conformance;
- retry-safe cleanup.

`resourceKind: network` alone does not claim any fault-injection semantics.

### Scenario and Core

Reused unchanged:

- unresolved required execution inputs fail before Episode execution;
- materialized execution semantics remain immutable during an Episode;
- Subject capability exposure derives only from the materialized actor projection;
- Core lifecycle remains the only Episode lifecycle;
- `QUIESCING` closes admission of new Subject-requested side effects;
- already accepted work may settle under the selected profile;
- lifecycle, infrastructure condition, Validity, and Task Verdict remain separate.

### Security and Evidence

Reused unchanged:

- Subject, Evaluator, and privileged Control authority remain separated;
- future hidden fault schedules remain evaluator-private unless the Scenario explicitly exposes them;
- evaluator/control credentials and native control handles do not enter Subject execution context;
- retained traces/configuration/result bytes use AVP Artifact identity;
- locators, socket descriptors, proxy IDs, qdisc handles, route names, mesh resource names, process IDs, and provider object IDs are not substitutes for Artifact content identity;
- technology names do not inflate `SecurityAssurance`.

## Why the base Fabric contract is not enough

The base Fabric normative candidate deliberately defines composition-level semantics only. Its closed `network` Resource Kind means that a resource belongs to the network interoperability domain. It does not mean any of the following:

- a particular Subject flow is guaranteed to traverse the resource;
- the resource controls transport packets rather than HTTP requests;
- latency, loss, disconnect, DNS failure, bandwidth, corruption, duplication, or reordering is supported;
- a fault can be activated at an exact host-wall-clock instant;
- an active fault applies retroactively to established connections;
- clearing a fault repairs or recreates existing connections;
- a successful provider API call proves a fault is active;
- provider-native fault configuration is portable Evidence;
- the Subject may inspect or mutate future fault schedules.

A network adapter that claimed portable behavior from `resourceKind: network` alone would violate AEP-0009 capability honesty and backend-first implementation rules.

## Standards and interoperability analysis

The Network Control Resource Profile should reuse transport and application standards where they own wire semantics and add only the AVP verification-facing control boundary.

### TCP

TCP provides a reliable ordered byte-stream abstraction to applications. It does not preserve application write boundaries as portable protocol messages, and TCP implementations may differ in segmentation, retransmission timing, buffering, queueing, congestion behavior, reset presentation, and error timing.

Therefore an AVP base network profile must not define conformance in terms of exact packet counts, exact TCP segment boundaries, exact retransmission schedules, or one operating system's socket error text.

Where the profile eventually claims a transport-level connection cut or recovery property, the claim must be expressed through application-observable connection behavior at a controlled test boundary rather than provider-native packet traces alone.

### IP, packet scheduling, and Linux traffic control

Operating-system traffic-control mechanisms are valuable implementation evidence for delay, loss, corruption, duplication, reordering, and rate behavior. They are not a portable semantic baseline by themselves.

Timer granularity, queue discipline, TCP Small Queues, offload, host scheduling, virtualization, and kernel versions can materially change observed timing and packet behavior. AEP-0009 already rejects exact packet-level equivalence as a base assumption.

A portability audit must determine whether any bounded latency/loss claim can be specified with tolerances and statistical/finite-run evidence strong enough for independent TCK execution without turning one kernel's mechanics into protocol authority.

### HTTP fault injection and service meshes

HTTP-aware proxies and service meshes commonly support request delay and abort/error injection. These mechanisms operate above the transport layer and can produce valid application-protocol responses rather than a network transport failure.

AVP must not collapse these into one generic `disconnect` semantic. A future application-protocol fault capability may be useful, but it is distinct from a transport-path claim and requires separately reviewable semantics.

### DNS

Name resolution is its own control surface. DNS failure before connection establishment is not equivalent to transport failure after an endpoint address has already been resolved or a connection has already been established.

The base Draft therefore treats name-resolution faults as a separate candidate semantic family whose inclusion in v0.1 must be justified by portability evidence rather than convenience.

### TLS

TLS interception/termination can make higher-layer fault injection easier but changes endpoint authentication and certificate behavior. A network-control profile must not require transparent TLS interception as a universal implementation mechanism, and a deployment must not claim stronger security/isolation merely because a proxy terminates TLS.

## Candidate portable resource boundary

The preferred design direction is one independently owned **controlled network path resource** that mediates traffic between a declared Subject-side endpoint boundary and a declared upstream-side endpoint boundary.

This direction is intentionally narrower than "the Environment network". One resource may control one path while other network traffic remains outside its authority.

The forthcoming portability audit must determine whether the path identity can be specified portably without depending on:

- Linux interface/qdisc identifiers;
- proxy listener object IDs;
- service-mesh route names;
- container network namespace names;
- cloud load-balancer identities;
- provider-native socket or connection handles.

### Control-point coverage

A conforming claim requires evidence that the traffic selected by the materialized execution contract actually traverses the controlled path.

Provider configuration alone is not enough. A TCK must be able to reject an implementation where the advertised fault is configured but test traffic bypasses the control point.

The exact mechanism for binding Subject-side and upstream-side endpoints remains a Draft question. It must preserve execution identity and avoid making private deployment topology part of portable protocol semantics.

## Fault semantics must be narrower than implementation APIs

The Draft distinguishes candidate semantic families from accepted v0.1 capability claims.

### Candidate family: baseline forwarding

Before any selected fault is active, the controlled path should establish a known-good forwarding baseline for the TCK fixture.

A profile cannot meaningfully certify a fault if the baseline path is already unavailable or ambiguous.

### Candidate family: disconnect / connection cut

A portability-friendly candidate is an evaluator-controlled state where selected new transport attempts cannot successfully establish the baseline application exchange across the controlled path, and where affected established connections have a profile-defined terminal disposition before the fault is reported settled.

This wording deliberately avoids standardizing whether the implementation uses reject, reset, close, blackhole, proxy teardown, route withdrawal, or another mechanism.

The portability audit must resolve:

- whether established connections must be terminated or may only block new connections;
- whether blackhole/time-out behavior is too timing-sensitive for mandatory v0.1;
- what terminal observation proves the cut is settled;
- whether one portable disconnect family should be split into explicit `connection-refused-like`, `reset-like`, or `unreachable-like` semantics rather than over-generalized.

### Candidate family: recovery

Clearing a fault must not be defined as "provider rule removed". Recovery must be independently observed.

A conservative candidate is that, after the network-control resource reports recovery settled, a **fresh** transport connection can again complete the known-good baseline exchange.

A base profile should not promise that a connection already broken by a prior fault becomes usable again. TCP and application protocols generally do not provide such a portable repair semantic.

### Candidate family: bounded latency

Bounded latency is useful but difficult to specify portably. Provider implementations may add delay at packet, connection, request, or response boundaries, and host scheduling contributes uncontrolled noise.

The portability audit must determine whether v0.1 can define a deterministic lower-bound/tolerance window around a local fixture without requiring statistical heuristics that are too flaky for conformance. Until that is proven, latency remains a candidate rather than a mandatory base claim.

### Candidate family: loss

Packet loss percentages and stochastic distributions are implementation-sensitive. A finite conformance run cannot prove a probabilistic distribution exactly, and a fixed deterministic drop pattern can accidentally standardize provider queue mechanics.

The portability audit must determine whether the portable requirement should instead use a deterministic finite failure pattern at a higher observable boundary, or defer loss from mandatory v0.1.

### Candidate family: name-resolution failure

DNS/name-resolution failure is semantically distinct from transport path interruption and should remain separately claimable if adopted.

The profile must not pretend a cached resolution, literal IP address, browser DNS cache, operating-system resolver cache, or already-established connection was affected when it was not.

## Fault lifecycle and settlement

Provider API completion is not sufficient evidence that a fault is active or cleared.

A future normative profile must define observable lifecycle transitions at least conceptually equivalent to:

```text
BASELINE -> ACTIVATING -> ACTIVE/SETTLED -> CLEARING -> BASELINE/SETTLED
```

The exact serialized vocabulary is downstream work.

Key requirements to resolve before `Proposed`:

1. the Evaluator/Control Plane can request a selected fault through privileged authority;
2. Subject traffic is not admitted into a fault-sensitive test window until activation settlement is established where the Scenario requires deterministic ordering;
3. activation settlement is proven by an implementation-independent observation, not a provider metadata flag alone;
4. clearing settlement is independently verified before a subsequent baseline/recovery claim is accepted;
5. failure to establish settlement is infrastructure/Validity information, not Agent Task Verdict failure by itself;
6. cleanup failure cannot retroactively rewrite the primary fault/conformance outcome;
7. future scheduled faults remain evaluator-private.

The profile must not require arbitrary sleep intervals as correctness evidence. Waiting may be an implementation mechanism, but conformance requires a bounded observable settlement predicate.

## Time and ordering boundary

AEP-0012 must not conflate Environment logical time with host wall time or packet scheduler time.

A network fault schedule may be expressed relative to Environment lifecycle or another governed ordering primitive without claiming that kernel timers, proxy event loops, remote services, or TCP retransmission clocks are virtualized.

If exact time-triggered fault activation becomes a portable claim, it requires explicit composition with a Time Control Resource profile or another reviewed timing contract. The network profile alone must not invent global deterministic time.

## State, control, observation, and Evidence must remain separate

A network-control resource is primarily a controlled behavior resource, not automatically a snapshot-able byte-state resource.

### Privileged control

Potential privileged controls include activating, clearing, scheduling, and releasing a fault. These controls are not Subject capabilities merely because the runtime implements them.

### Evaluator observation

Evaluator-visible observations may include:

- fault lifecycle state and settlement result;
- baseline probe result;
- selected connection/exchange outcomes;
- sanitized provider diagnostics;
- retained fault transition trace;
- coverage/bypass evidence where needed to prove the selected path was controlled.

Observation does not automatically become authoritative restorable state.

### Subject observation

The Subject may observe the consequence of a fault through its normal network/application operations. It must not automatically receive the hidden future schedule, privileged control API, evaluator diagnostics, or provider credentials.

### Evidence

Retained exact bytes use AVP Artifact identity. Provider-native configuration may be retained as implementation Evidence when useful, but it cannot replace the portable fault result or become portable identity merely because it exists.

## Reset, snapshot, and restore boundary

The Draft does not assume that a Network Control Resource supports Environment-style snapshot/restore of live connections or kernel/proxy internals.

A likely v0.1 direction is:

- **reset** establishes the profile-defined baseline fault-free control state and independently verifies the baseline path;
- **snapshot/restore** of live transport state is unsupported unless a separately governed capability defines it;
- fault configuration/state may be represented in operation Evidence without claiming exact restoration of socket queues, TCP sequence state, timers, retransmissions, or provider-internal state.

The portability audit must verify that this composition is compatible with Environment/Fabric snapshot participation rules and decide whether a network resource is explicitly non-participating in snapshots for the base profile or requires a narrow configuration-state snapshot semantic.

## Security considerations

Network control expands privileged Environment authority and can accidentally become a traffic interception or exfiltration surface.

Required design direction:

1. Subject traffic operations remain distinct from Evaluator/Control fault operations.
2. Future fault schedules remain evaluator-private unless explicitly exposed by Scenario semantics.
3. Control credentials, proxy admin tokens, kernel-control authority, mesh credentials, cloud control credentials, packet-capture credentials, and equivalent privileged handles do not enter Subject execution context.
4. A control point must not expose unrelated Environment traffic merely because its implementation can observe it.
5. Packet/application payload capture is not implied by fault-control capability and requires separate Evidence/visibility justification.
6. TLS interception is not implied by network-control capability.
7. Endpoint locators and provider diagnostics exposed to the Subject must not leak private topology or control-plane authority.
8. A proxy, container namespace, service mesh, VM, or kernel facility does not automatically establish `network`, `process`, `tenant`, or `sandbox` SecurityAssurance as `verified`.
9. Control-plane failure is infrastructure/Validity information and must not be converted directly into Agent task failure.
10. Cleanup must remove privileged fault effects without resurrecting stale resource authority.

## Failure and Validity semantics

Candidate network infrastructure/Validity failures include, as applicable:

- required control point unavailable;
- selected traffic bypasses the declared controlled path;
- baseline forwarding cannot be established;
- required fault semantic unsupported by the implementation;
- activation cannot settle or cannot be independently observed;
- clearing/recovery cannot settle or baseline cannot be re-established;
- stale/foreign resource or control reference;
- required execution identity missing or drifted;
- loss of Evaluator/Control authority;
- hidden future schedule or privileged control information leaked to the Subject;
- cleanup failure that leaves an untrustworthy network boundary.

Provider-specific status codes, socket error strings, qdisc handles, proxy toxic names, HTTP status codes, or mesh object statuses are diagnostics rather than portable AVP outcome identity unless a future profile explicitly standardizes an application-protocol semantic.

These conditions must not be converted into Agent Task Verdict failure solely because they occurred.

## Conformance strategy direction

A future `avp-network-control-v0.1` TCK must execute real behavior at the selected network boundary.

Portable SUT obligations are expected to include observable equivalents of:

- provision/bind a controlled path;
- prove a known-good baseline exchange;
- activate one selected portable fault;
- establish and observe fault settlement;
- exercise Subject-side traffic through the real path;
- clear the fault;
- establish and observe recovery settlement;
- prove a fresh baseline exchange succeeds again;
- preserve Subject/Evaluator/Control separation;
- release and reject stale use.

Exact programming-language methods, proxy commands, kernel configuration, service-mesh resources, and provider APIs are non-normative.

### Privileged fixture controls

Executable conformance requires a privileged local fixture-control seam that may:

- run a deterministic upstream echo/application fixture;
- originate Subject-side connections/exchanges through the selected path;
- coordinate an established connection before fault activation where the selected semantic requires it;
- test fresh connections during and after faults;
- activate negative implementation behavior;
- prove bypass detection by deliberately routing a control flow outside the claimed control point.

Fixture controls are TCK harness mechanics, not Resource Capabilities or Subject APIs.

### Mandatory conformance families to resolve

Before normative closure, the design must settle at least:

1. controlled-path ownership and stale references;
2. baseline forwarding and path-coverage proof;
3. exact portable v0.1 fault vocabulary;
4. activation settlement semantics;
5. established-connection disposition where applicable;
6. clearing/recovery settlement semantics;
7. lifecycle ordering and `QUIESCING` interaction;
8. evaluator-private future schedule non-disclosure;
9. Subject/Evaluator/Control authority separation;
10. reset/snapshot participation semantics;
11. cleanup and leaked-fault detection;
12. execution-sensitive capability honesty.

### Negative implementations

At minimum, the TCK must be capable of rejecting metadata-identical broken implementations such as:

- `BypassFaultAdapter` — advertises the capability and reports fault activation while the TCK traffic bypasses the controlled path;
- `FalseSettledFaultAdapter` — reports a fault active/settled before the observable fault property is established;
- `FalseRecoveryAdapter` — reports recovery settled while a fresh baseline exchange still cannot succeed;
- `ScheduleLeakAdapter` — exposes evaluator-private future fault scheduling information to the Subject.

TCK PASS must derive from observed runtime behavior, not capability metadata, provider configuration, fixture inspection, backend product labels, or implementation self-report alone.

## Portability evidence required before Proposed

The next governed step after this Draft is an implementation-independent portability and Proposed-readiness audit.

That audit must compare at least distinct implementation classes rather than two wrappers around the same mechanism, including evidence from:

- an operating-system traffic-control mechanism such as Linux `tc/netem` where applicable;
- a user-space transport proxy such as Toxiproxy or an equivalent controlled proxy;
- an application/service-mesh fault mechanism such as Envoy/Istio where useful to prove layer differences and prevent false unification.

The audit is not required to make all three conform to one mandatory profile. Its purpose is to identify the smallest semantics that genuinely survive implementation differences and to document where semantics must remain separate.

The audit must explicitly decide:

- resource/path identity and coverage proof;
- mandatory v0.1 fault family or families;
- whether latency is deterministic enough for portable mandatory conformance;
- whether loss can be specified without probabilistic self-certification;
- whether disconnect must distinguish new versus established connections;
- whether DNS belongs in the base profile or a separate capability;
- whether HTTP abort/delay belongs in a separate application-protocol capability;
- activation/clearing settlement predicates and bounded failure behavior;
- reset and snapshot participation;
- execution-relevant identity inputs;
- Evidence needed for independent review;
- required multi-mechanism reference evidence before implementation is called portable.

## Draft blockers before Proposed

AEP-0012 must not advance to `Proposed` until the following are resolved through reviewable evidence:

- **NC-BR-001 — controlled-path boundary:** define the exact portable Subject-side/upstream-side path boundary and how path coverage is proven without provider-native identity becoming protocol identity.
- **NC-BR-002 — fault vocabulary:** select the smallest mandatory v0.1 semantic fault set and reject false equivalence among packet, transport, DNS, TLS, HTTP, and provider-specific faults.
- **NC-BR-003 — activation settlement:** define an observable, bounded settlement predicate that does not use provider configuration success or arbitrary sleep as conformance proof.
- **NC-BR-004 — established connections:** define what each selected fault does or does not promise for connections already established at activation time.
- **NC-BR-005 — recovery settlement:** define what clearing means and require independent fresh-connection recovery evidence without promising repair of broken connections.
- **NC-BR-006 — timing/latency:** determine whether latency can be mandatory and portable, including tolerance/error semantics and host scheduling limits.
- **NC-BR-007 — loss semantics:** determine whether any loss claim can be tested portably without finite-run probabilistic self-certification or provider-specific packet patterns.
- **NC-BR-008 — DNS/application layering:** decide whether name-resolution and HTTP-level faults are excluded, separate capabilities, or part of a reviewed profile without collapsing layers.
- **NC-BR-009 — snapshot/reset participation:** define baseline reset and Fabric snapshot participation without pretending live network stacks are portably restorable.
- **NC-BR-010 — hidden schedule/security boundary:** prove future fault schedules and privileged control material remain evaluator-private and do not widen Subject authority.
- **NC-BR-011 — execution identity:** define which path/proxy/network configuration inputs are execution-relevant immutable identity versus deployment-private diagnostics.
- **NC-BR-012 — conformance portability:** define language-neutral case vectors, privileged fixture controls, negative implementations, and the minimum cross-mechanism evidence required before reference implementation work.

## Alternatives rejected at Draft stage

The Draft already rejects the following directions:

- standardizing a product API as the AVP network profile;
- treating `resourceKind: network` as a capability claim;
- one generic untyped `fault` map with provider-defined keys;
- exact packet traces or kernel qdisc state as portable fault identity;
- one global `networkDeterministic=true` flag;
- arbitrary sleeps as activation or recovery correctness proof;
- provider API success as fault settlement proof;
- silently treating HTTP abort as transport disconnect;
- silently treating DNS failure as packet/transport loss;
- requiring TLS interception for base conformance;
- assuming a cleared fault repairs already-broken transport/application sessions;
- exposing future fault schedules through Subject-visible configuration;
- backend-first implementation followed by retroactive generalization;
- a generic plugin/provider framework before stable portable semantics and multiple real consumers exist.

## Expected authority chain after acceptance

If AEP-0012 eventually becomes `Accepted`, downstream work must proceed in this order:

```text
Accepted AEP-0012
  -> Network Control Normative Spec
  -> Requirement Index
  -> Schema where serialized portable resources require it
  -> Provider/language-neutral execution-sensitive TCK
  -> Backend-neutral conformance harness / immutable local fixture
  -> Reference implementation mechanism(s)
  -> Cross-mechanism portability evidence where required
```

Schema and TCK must derive from normative specification semantics. They may not invent missing semantics or use provider behavior as authority.

A common implementation interface may be introduced only after its semantics are defined by the portable authority slice. It must not be one proxy API generalized later.

## Governance boundary

This AEP is **Draft**, not Proposed, Accepted, or Final.

This Draft authorizes design/review only. It does **not** authorize:

- normative Network Control specification/schema/TCK adoption;
- a Network Control Resource Capability registration;
- Toxiproxy, `tc/netem`, Envoy, Istio, service-mesh, kernel, cloud, or another provider as protocol authority;
- backend-first network implementation;
- a generic network backend/provider/plugin framework;
- AEP-0009, AEP-0010, AEP-0011, or AEP-0012 lifecycle advancement;
- selecting an Alpha 3 release version;
- entering release mode;
- tag or GitHub Release creation;
- package-index publication;
- signing or attestation publication;
- weakening existing Spec/Schema/TCK/Gate/Evidence requirements.

Merge of the Draft PR remains separately governed and requires explicit authorization under the repository workflow.
