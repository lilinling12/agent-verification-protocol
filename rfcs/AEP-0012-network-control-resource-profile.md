# AEP-0012 — Network Control Resource Profile v0.1

- Status: Proposed
- Authors: AVP maintainers and contributors
- Created: 2026-09-02
- Portability audit: `docs/design/alpha3-network-control-resource-portability-audit.md`
- Proposed-readiness evidence: `docs/design/alpha3-network-control-resource-proposed-readiness-audit.md`
- Lifecycle decision: `docs/acceptance/alpha3-aep-0012-proposed-decision.md`
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Network Control Resource

## Summary

AEP-0012 defines the review-ready portable direction for the first Network Control Resource profile under AVP Environment Fabric.

The core rule is:

> AVP standardizes an observable controlled-network-path verification boundary; proxy APIs, kernel queue disciplines, firewall/routing rules, service-mesh objects, native socket errors, and other provider mechanics remain implementation details and must not become protocol semantics by precedent.

The reconciled v0.1 design is deliberately narrow. One independently owned resource represents one declared **controlled TCP path** between a Subject-side endpoint boundary and an upstream-side endpoint boundary. Its mandatory base claim is limited to a deterministic fresh-connection baseline exchange, Environment-governed activation, independently observed transport-cut settlement, privileged clear, independently observed fresh-connection recovery, and behavioral proof that selected traffic traverses the controlled path.

Established-connection termination, exact latency, probabilistic packet loss, DNS/name-resolution failure, TLS interception, HTTP/application faults, UDP behavior, packet counts, TCP segment boundaries, retransmission timing, and provider-native socket error identity are not mandatory base semantics.

AEP-0012 is **Proposed** by explicit protocol-maintainer lifecycle authorization on 2026-09-03 so the reconciled design can enter formal protocol review. `Proposed` does not make these choices Accepted or normative and does not authorize Network Control Spec/Schema/TCK, a conformance harness, provider/reference implementation, release selection, publication, signing, or attestation.

## Problem

A network fault is not one portable packet-level primitive. Implementations inject effects at materially different layers:

- kernel traffic-control, firewall, routing, or namespace mechanisms affect packets/routes subject to host-kernel timing and queue behavior;
- user-space TCP proxies can reject, stall, close, reset, or forward connections without reproducing kernel-identical mechanics;
- HTTP proxies/service meshes can delay or abort requests while the underlying transport remains available;
- DNS controls affect name resolution and caches rather than an already-resolved TCP path;
- TLS interception/termination changes endpoint authentication and trust behavior;
- browser, container, VM, host, and remote-network boundaries determine whether selected Subject traffic actually crosses a control point.

AVP must therefore define observable verification properties rather than copy one provider API. Provider configuration success, packet traces, native error strings, qdisc/proxy IDs, or service-mesh objects cannot define portable conformance by themselves.

## Existing AVP authority reused

AEP-0012 specializes existing contracts and does not create competing lifecycle, identity, evidence, or security systems.

### Environment v0.1

Reused unchanged:

- authoritative Environment ownership and ScenarioInstance binding;
- evaluator-controlled fault identity, target, activation condition, and clear semantics;
- occurrence-based no-early-activation semantics;
- evaluator-private future fault schedules;
- actor-scoped Subject observation;
- evaluator-authoritative observation/projection where defined;
- Environment logical time without implying wall-clock/kernel/network timer virtualization;
- reset honesty and stale/foreign/released-handle failure;
- lifecycle, infrastructure condition, Validity, and Task Verdict separation;
- Artifact identity for retained exact Evidence bytes.

`AVP-ENVIRONMENT-010` remains top-level authority for scheduled fault identity, target, activation condition, and clear semantics. Network Control adds subordinate data-plane settlement only after the Environment activation condition is satisfied.

### Environment Fabric

Reused unchanged:

- `resourceKind: network` as coarse classification only;
- Resource Capability identity/revision and REQUIRED/OPTIONAL participation;
- Resource Capability versus Subject Capability separation;
- resource identity and immutable execution-input binding;
- per-resource/composite result honesty and no implicit cross-resource atomicity;
- Security/Evidence composition, execution-sensitive conformance, and retry-safe cleanup.

`resourceKind: network` alone does not claim transport-cut or recovery semantics.

### Scenario, Core, Security, and Evidence

Reused unchanged:

- unresolved required execution inputs fail before Episode execution;
- materialized execution semantics remain immutable during an Episode;
- Core lifecycle remains the only Episode lifecycle;
- `QUIESCING` closes admission of new Subject-requested side effects while already accepted work may settle;
- Subject, Evaluator, and privileged Control authority remain separated;
- provider credentials/native control handles do not enter Subject execution context;
- exact retained bytes use Artifact identity;
- technology names do not inflate `SecurityAssurance`.

## Standards and interoperability basis

### TCP

TCP exposes a reliable ordered byte stream, not portable application-write or packet boundaries. Implementations differ in segmentation, buffering, retransmission timing, congestion/queue behavior, reset presentation, and native errors.

Therefore portable Network Control conformance is expressed through fresh connection attempts and deterministic end-to-end application exchanges. Exact packet counts, TCP segment boundaries, retransmission schedules, queue state, or native socket error strings are excluded from portable outcome identity.

### Kernel and proxy mechanisms

Kernel traffic-control/routing/firewall mechanisms and user-space TCP proxies are useful independent implementation classes. Neither is protocol authority. Timer granularity, queueing, TCP Small Queues, offload, host scheduling, buffering, and provider event loops make exact timing/error equivalence non-portable.

Provider API completion is control-plane evidence only; it cannot prove data-plane activation or recovery settlement.

### Application, DNS, and TLS layers

HTTP abort/status/delay is application-layer behavior and cannot satisfy a transport-cut requirement merely because a request failed. DNS/name-resolution behavior has resolver/cache/TTL semantics distinct from an already-resolved TCP path. TLS interception changes endpoint-authentication semantics and is not implied by Network Control support.

## Portable resource boundary

One Network Control v0.1 resource represents one independently owned **controlled TCP path** between:

1. a declared Subject-side endpoint boundary; and
2. a declared upstream-side endpoint boundary.

The resource is narrower than "the Environment network". Traffic outside the selected path may remain uncontrolled.

Portable resource identity does not use Linux interface/qdisc/filter handles, proxy listener/toxic IDs, service-mesh resource names, cloud rule IDs, socket descriptors, process IDs, or equivalent mechanism-native objects.

### Behavioral path-coverage proof

Configuration presence is insufficient. Conformance must behaviorally establish that selected traffic actually traverses the controlled path and must reject an implementation that advertises the capability while secretly bypassing the control point.

Provider-native packet traces may be useful diagnostics, but are not the sole portable proof.

## Mandatory v0.1 semantics

### Baseline forwarding

Before the selected fault is active, a deterministic evaluator-controlled upstream fixture must complete the selected baseline request/response exchange over a **fresh TCP connection** through the declared path.

If the baseline cannot be established, the fault claim is not validly testable.

### Environment-governed activation

The Environment owns fault identity, target, and activation condition. For occurrence-based activation:

- qualifying pre-trigger Subject traffic is admissible and may be required to reach the occurrence;
- the fault MUST NOT affect that traffic before the declared occurrence;
- preparing provider-private control state before the occurrence does not make the fault active;
- Network Control does not reinterpret occurrence counting.

After the Environment condition is satisfied, Network Control may enter a subordinate settling interval before post-activation fault-sensitive observations are accepted.

### Activation settlement

Activation is settled only after a privileged independent data-plane observation proves the selected transport-cut property on a fresh attempt through the controlled path.

Provider API success, rule/object existence, metadata flags, Subject self-report, or arbitrary sleep are insufficient by themselves.

Failure to settle is infrastructure/Validity information, not Agent Task Verdict failure by itself.

### Fresh-connection transport cut

After activation settlement, a selected fresh connection/exchange through the controlled path must not complete the deterministic baseline exchange while the cut remains active.

The protocol does not prescribe refusal, RST, FIN/close, timeout/blackhole, unreachable behavior, route withdrawal, proxy termination, or another native mechanism. Exact exception classes, numeric OS error codes, localized error text, TCP flags, packet counts, or retransmission schedules are non-portable diagnostics.

### Established connections

Base v0.1 makes **no guarantee** about a connection established before activation. It may be preserved, drained, reset, blackholed, partially progress, or fail according to implementation mechanics.

A future use case that requires established-connection termination must define a separately reviewed capability/profile and TCK rather than hiding that requirement inside base `transport cut`.

### Clear and recovery

Clear is a privileged operation against the selected Environment-governed fault instance. Provider acknowledgement of rule removal does not prove recovery.

Recovery settlement requires independent successful fresh baseline exchange(s) after clear through the same selected path. Base recovery does not promise repair of a connection already broken by the prior fault.

After clear, the same governed occurrence must not silently reactivate. A later distinct occurrence/fault remains separately Environment-governed.

## Deferred and separated semantics

### Latency

Latency is not mandatory base v0.1. A future bounded-latency profile requires explicit measurement endpoints, monotonic clock requirements, baseline treatment, additive-versus-total definition, tolerance window, warm-up/sample policy, host-noise treatment, timeout interaction, and platform-independent acceptance statistics.

### Probabilistic loss

Probabilistic packet loss is not mandatory base v0.1. A future loss profile requires an explicit observation unit, sample/confidence rule, and transport-retransmission interaction model. The deterministic base cut is named **transport cut**, not `100% packet loss`.

### DNS, TLS, HTTP/application, and UDP

DNS/name-resolution faults, TLS interception/failure, HTTP/application abort/delay, and UDP/datagram behavior require separate reviewed semantics. None is silently inferred from base TCP transport cut.

## Time and ordering boundary

Environment logical time is not host wall time, kernel timer time, proxy event-loop time, or TCP retransmission time. Network Control does not claim those clocks are virtualized.

Any future exact time-triggered activation or deterministic delay claim requires composition with a separately governed Time Control Resource or another reviewed timing contract.

## State, control, observation, and Evidence

Network Control is primarily a controlled-behavior resource, not automatically a snapshot-able byte-state resource.

### Privileged control

Fault preparation/activation coordination, clear, reset, provider administration, and hidden fixture controls remain privileged Evaluator/Control operations unless a separately governed Subject contract grants narrower authority.

### Evaluator and Subject observation

Evaluator observations may include baseline result, activation/recovery settlement, selected exchange outcomes, path-coverage/bypass evidence, sanitized diagnostics, fault transition traces, and cleanup diagnostics.

The Subject observes fault consequences only through its authorized ordinary operations. It does not automatically receive future schedules, privileged fault APIs, provider credentials, evaluator probes, native handles, or private topology diagnostics.

### Evidence

Retained exact bytes use Artifact identity. Provider-native configuration/traces may be implementation Evidence, but do not replace the portable behavioral result or become portable resource identity.

## Reset, snapshot, and restore boundary

Base Network Control v0.1 participates in reset by establishing and independently verifying the profile-defined **fault-free baseline** on the selected controlled path.

Base v0.1 does not define snapshot/restore of live sockets/connections, TCP sequence/retransmission state, kernel queues/qdisc/filter state, proxy buffers, NAT/conntrack state, resolver caches, or service-mesh/provider internals.

Those mechanisms are not one stable portable logical state image. Base v0.1 therefore makes no `EXACT` or `STATE_EQUIVALENT` restoration claim for them.

## Execution-relevant immutable identity

Portable verification identity must bind enough provider-neutral input to interpret and reproduce the claim. Candidate downstream inputs include:

- Network Control profile/revision;
- selected controlled-path resource identity;
- Subject-side and upstream-side endpoint declarations;
- TCP transport declaration;
- Environment fault identity/target/activation-condition references;
- deterministic fixture/program identity where it affects the exchange;
- execution-relevant immutable configuration outside logical state that may alter the result.

Excluded from portable identity are qdisc/filter/firewall handles, proxy IDs, socket descriptors, process IDs, cloud rule IDs, mesh object names, and transient provider-generated control IDs. These may remain sanitized diagnostic Evidence.

Missing, ambiguous, stale, foreign, or drifted required execution identity fails closed.

## Security considerations

Network Control expands privileged Environment authority and can become an interception/exfiltration surface if boundaries are weak.

Required rules:

1. Subject traffic operations remain distinct from Evaluator/Control fault operations.
2. Future fault schedules remain evaluator-private unless explicitly exposed by governed Scenario semantics.
3. Provider/control credentials and packet-capture authority do not enter Subject execution context.
4. The control point must not expose unrelated Environment traffic merely because the implementation can observe it.
5. Payload capture and TLS interception are not implied by fault-control capability.
6. Subject-visible diagnostics must not leak private topology or control authority.
7. Provider/container/mesh/kernel labels do not establish `SecurityAssurance` by themselves.
8. Control/settlement failure remains infrastructure/Validity information rather than direct Task Verdict failure.
9. Cleanup must remove privileged fault effects without resurrecting stale authority.

A `ScheduleLeakAdapter`-style implementation must fail conformance.

## Failure and Validity semantics

Infrastructure/Validity failures include, where applicable:

- unavailable control point or failed baseline;
- selected traffic bypassing the declared path;
- unsupported mandatory transport-cut semantic;
- activation or recovery settlement failure;
- stale/foreign resource/control reference;
- missing/drifted required execution identity;
- loss of Evaluator/Control authority;
- hidden schedule/control leakage;
- cleanup failure leaving an untrustworthy network state.

Provider-native status/error strings and object IDs are diagnostics, not portable AVP outcome identity.

## Conformance strategy

A future `avp-network-control-v0.1` TCK must be provider-neutral, language-neutral, and execution-sensitive. Mandatory cases execute real behavior at the controlled-path boundary; metadata, mocks, provider configuration, fixture inspection, or self-report cannot substitute for the behavior being certified.

A deterministic local fixture should provide an evaluator-controlled upstream service, a Subject-side client, privileged control inaccessible to Subject code, evaluator-controlled ordering, independent settlement probes, and negative implementation modes.

A minimal mandatory execution flow must prove:

1. baseline fresh exchange succeeds;
2. qualifying pre-trigger Subject traffic remains admissible/unfaulted;
3. the Environment activation condition is reached;
4. activation settles through independent data-plane observation;
5. post-activation fresh exchange cannot complete;
6. bypass is detected;
7. clear is issued through privileged authority;
8. recovery settles through successful fresh exchange(s);
9. the cleared occurrence does not silently reactivate;
10. future schedule/control material remains hidden;
11. stale/released use fails closed;
12. cleanup does not leave a hidden active fault.

Required negative directions include:

- `BypassFaultAdapter`;
- `EarlyActivationAdapter`;
- `FalseSettledFaultAdapter`;
- `FalseRecoveryAdapter`;
- `ScheduleLeakAdapter`.

Portable TCK expectations MUST NOT branch on provider/platform names to define different protocol outcomes. Provider-specific setup belongs behind privileged implementation seams.

## Cross-mechanism portability evidence

One provider passing the future TCK is not enough to prove that AVP's own semantic choices are protected from one-mechanism precedent where portability depends on mechanism independence.

Project acceptance/reference evidence should therefore exercise materially independent implementation classes where practical, for example a user-space TCP proxy/interceptor and a kernel/routing/firewall-style path-control class.

This is an AVP reference/acceptance evidence expectation, not automatically a requirement that every third-party conforming implementation implement multiple providers.

Deferred latency/loss/DNS profiles require their own portability evidence.

## Reference implementation gate

A controlled network-fault reference implementation may begin only after:

1. AEP-0012 reaches the lifecycle state required by governance;
2. Network Control normative Spec and requirement index encode the reviewed semantics;
3. serialized portable resources receive schemas where required;
4. the provider/language-neutral execution-sensitive TCK is reviewable;
5. any backend-neutral fixture/control prerequisites identified by review are closed.

No generic `BaseNetworkBackend`, provider/plugin framework, or broad `supports_*` capability bag is justified before stable reviewed semantics and real consumers exist.

## Alternatives rejected

The reconciled design rejects:

- provider-first implementation followed by retroactive generalization;
- Linux `tc/netem` or Toxiproxy APIs as protocol authority;
- HTTP abort as transport cut;
- DNS failure as generic network loss;
- established-connection termination as an implicit base guarantee;
- mandatory v0.1 latency without a portable timing model;
- mandatory probabilistic loss without a statistical conformance model;
- arbitrary sleeps or provider API success as settlement proof;
- snapshot/restore of live network/provider internals;
- exposing future schedules/control through Subject-visible interfaces;
- generic provider/plugin architecture before a stable extension contract exists.

## Backward compatibility and release boundary

Network Control v0.1 is additive under AEP-0009. Existing Environment/Fabric implementations need not claim it, and `resourceKind: network` remains insufficient by itself. Alpha 2, Relational State, and Browser semantics are unchanged.

No public release version is selected, release-development state remains unchanged, and this AEP does not authorize publication, signing, or attestation.

## Draft design-blocker disposition

The portability audit and this reconciliation resolve the original Draft blockers as explicit formal-review inputs:

- **NC-BR-001 — CLOSED:** one resource is a declared Subject-side → upstream-side controlled TCP path with behavioral path-coverage proof independent of provider identity.
- **NC-BR-002 — CLOSED:** base vocabulary is baseline forwarding, fresh-connection transport cut, privileged clear, and fresh-connection recovery; other layer/fault families are not aliases.
- **NC-BR-003 — CLOSED:** Environment owns fault identity/target/condition; occurrence no-early-activation is preserved and activation settlement requires independent post-trigger data-plane proof.
- **NC-BR-004 — CLOSED:** established connections have no base disposition guarantee; a separate profile is required for such a claim.
- **NC-BR-005 — CLOSED:** clear does not self-certify recovery; fresh successful exchange proves recovery and the cleared occurrence cannot silently reactivate.
- **NC-BR-006 — CLOSED:** latency is deferred until a portable clock/tolerance/sampling/noise model exists.
- **NC-BR-007 — CLOSED:** probabilistic loss is deferred until observation-unit/statistical conformance semantics exist.
- **NC-BR-008 — CLOSED:** DNS, TLS, HTTP/application, UDP, and TCP path semantics remain layer-distinct.
- **NC-BR-009 — CLOSED:** reset establishes a verified fault-free baseline; live network/provider internals are not base snapshot/restore state.
- **NC-BR-010 — CLOSED:** future schedules/control remain evaluator-private and Network Control does not inflate `SecurityAssurance`.
- **NC-BR-011 — CLOSED:** provider-neutral path/profile/fault/execution inputs bind verification identity; provider handles are diagnostics only.
- **NC-BR-012 — CLOSED:** future TCK is provider/language-neutral, deterministic-fixture-based, execution-sensitive, negative-adapter-capable, and supported by cross-mechanism AVP evidence where mechanism independence matters.

Closure means each design choice is explicit enough for formal review. It does **not** mean the choices are already `Accepted` or cannot be revised by formal Proposed review.

## Non-blocking downstream details

Later Spec/Schema/TCK work may define exact capability/profile spelling, JSON fields/media types/limits, provider-neutral endpoint/path declaration syntax, canonical representation for serialized resources, bounded retry/observation parameters, requirement/TCK IDs, language-specific SPI names, and provider diagnostic mappings.

Those details are downstream only while they encode the semantics above. If formal review finds that one would change portable meaning, AEP-0012 must be amended before acceptance.

## Open protocol-review questions

Formal review should challenge, rather than assume, these choices:

1. Is controlled TCP + fresh-connection exchange the correct smallest mandatory v0.1 boundary?
2. Is `transport cut` the clearest mechanism-neutral term?
3. Is excluding established-connection disposition appropriately conservative?
4. Is independent fresh-attempt data-plane settlement sufficient without standardizing timeout/error behavior?
5. Should recovery require a normative minimum/bounded count of successful fresh exchanges, or can TCK encode that predicate without creating new semantics?
6. Is deferring latency and probabilistic loss the correct v0.1 interoperability tradeoff?
7. Is the DNS/TLS/HTTP/UDP separation strict enough to prevent provider-layer equivalence?
8. What is the smallest endpoint/path declaration grammar that proves coverage without exposing private topology?
9. Should cross-mechanism evidence be required before Accepted, before an official reference implementation claim, or both?
10. Does Core `QUIESCING` / Environment activation / cleanup composition need any further constraint before normative closure?

These are formal review questions, not unresolved Draft definitions.

## Governance boundary

AEP-0012 is **Proposed** on this lifecycle candidate by explicit protocol-maintainer authorization on 2026-09-03. The authorization permits this lifecycle-only mutation and formal Proposed review after adoption; it is not merge authorization.

This lifecycle transition does not authorize:

- `Proposed -> Accepted` or `Accepted -> Final`;
- Network Control normative Spec, requirement index, schema, capability registration, or TCK adoption;
- backend-neutral harness/fixture implementation;
- any provider as protocol authority or an official reference implementation;
- a generic provider/plugin framework;
- lifecycle advancement of AEP-0009, AEP-0010, or AEP-0011;
- release selection/mode change, tag, GitHub Release, package publication, signing, or attestation;
- Gate/Evidence weakening;
- repository merge without separate authorization.

After this lifecycle candidate is exact-head reviewed and separately authorized for squash merge into `main`, the next governed work unit is formal Proposed protocol review. Any semantic change discovered there must be reviewed as a semantic AEP amendment and cannot be smuggled into this lifecycle-only transition.

## References

- AEP-0009 — `rfcs/AEP-0009-environment-fabric.md`
- Environment contract — `spec/environment/environment-contract.md`
- Environment requirement index — `spec/environment/requirement-index.yaml`
- Environment Fabric contract — `spec/fabric/environment-fabric-contract.md`
- Network Control portability audit — `docs/design/alpha3-network-control-resource-portability-audit.md`
- RFC 9293 — TCP
- Linux `tc-netem` documentation — implementation evidence only
- Toxiproxy documentation/source — implementation evidence only
- Envoy HTTP fault-filter documentation — layer-separation evidence only
- DNS standards/negative-caching semantics — layer-separation evidence only

External standards and implementation documentation constrain interoperability analysis; they do not become AVP normative semantics merely by citation.