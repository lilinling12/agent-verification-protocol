# Alpha 3 Network Control Resource Portability / Proposed-Readiness Audit

Status: **DESIGN AUDIT — RECONCILIATION INPUT**

Baseline: `main@c205b2c18ace92663854026df58cc113a9e32037`

Related authority and design surfaces:

- `rfcs/AEP-0009-environment-fabric.md` — Accepted Environment Fabric direction;
- `rfcs/AEP-0012-network-control-resource-profile.md` — current Network Control Resource Profile v0.1 Draft;
- `spec/environment/environment-contract.md` and `spec/environment/requirement-index.yaml` — existing Environment v0.1 fault-schedule authority, including `AVP-ENVIRONMENT-010` and private-schedule constraints;
- `spec/fabric/environment-fabric-contract.md` — existing Fabric composition/capability boundary;
- `ROADMAP.md` — current Alpha 3 Network Control sequencing.

## 1. Purpose

This audit determines whether the design questions recorded as NC-BR-001 through
NC-BR-012 in AEP-0012 can be resolved in a provider-independent way before a
separate AEP reconciliation / Draft-to-Proposed-readiness work unit.

The audit is intentionally implementation-independent. It may narrow, split,
defer, or reject Draft directions where a portable base contract cannot be
justified. It does not make the selected directions normative by itself.

The governing dependency direction remains:

```text
reviewed AEP design
    -> normative contract
    -> schema / canonical resources where required
    -> provider/language-neutral execution-sensitive TCK
    -> backend-neutral conformance harness / controlled fixture
    -> reference provider implementation(s)
    -> provider-specific evidence
```

Provider behavior MUST NOT be generalized into protocol semantics after the
fact.

## 2. Non-authorizations

This audit does **not** authorize or perform any of the following:

- AEP-0012 `Draft -> Proposed`, `Accepted`, or `Final`;
- lifecycle advancement of AEP-0009, AEP-0010, or AEP-0011;
- creation or modification of a Network Control normative specification,
  requirement index, schema, TCK, conformance harness, or runtime;
- selection of Linux `tc/netem`, Toxiproxy, Envoy, Istio/service-mesh,
  kernel-native facilities, cloud controls, DNS controls, TLS interception, or
  another mechanism as protocol authority;
- a generic provider/plugin framework or speculative `BaseNetworkBackend`;
- release selection, release-mode transition, tag, GitHub Release, package
  publication, signing, or attestation publication;
- weakening existing Environment, Fabric, Security, Evidence, Schema, TCK, or
  release Gates.

AEP-0012 remains **Draft** after this audit. The decisions below are inputs to a
separate reconciliation/readiness change.

## 3. Evidence and portability method

The audit uses protocol standards and multiple implementation classes to identify
what can be observed consistently without standardizing one provider's internal
mechanics.

### 3.1 TCP transport semantics

RFC 9293 defines TCP as a reliable, in-order byte-stream transport. Application
write boundaries are not portable TCP segment boundaries, and segmentation,
retransmission behavior, congestion behavior, queueing, and native error
presentation remain implementation-dependent.

Consequences for AVP:

- a portable Network Control base profile must not standardize packet counts,
  TCP segment boundaries, retransmission counts/timing, qdisc queue state, or
  provider-native socket error strings;
- conformance observations should be expressed in terms of connection attempts
  and end-to-end application exchanges over a declared transport path;
- an implementation may use packet-, stream-, proxy-, route-, or kernel-level
  mechanics internally without those mechanics becoming protocol semantics.

### 3.2 Kernel traffic shaping

Linux `tc-netem` exposes delay, loss, corruption, duplication, reordering, and
related traffic effects, but the observable result depends on kernel scheduling,
timer granularity, queueing, transport behavior, and placement in the stack.
Linux documentation also identifies limitations such as timer granularity and
TCP Small Queues interactions.

Consequences for AVP:

- exact wall-clock latency and exact packet-loss counts are not suitable as
  universal mandatory base semantics;
- Linux queue disciplines and handles cannot become portable resource identity;
- a Linux implementation can later provide evidence for a reviewed semantic
  profile, but cannot define that profile by precedent.

### 3.3 User-space TCP proxy mechanisms

Toxiproxy demonstrates a separate implementation class in which faults are
applied through a user-space TCP proxy and provider-specific toxics such as
timeouts or peer resets.

Consequences for AVP:

- a portable cut semantic can be defined without standardizing whether a
  provider realizes it by reset, close, reject, blackhole, timeout, or another
  mechanism;
- provider API completion is control-plane evidence only and is insufficient to
  prove data-plane activation or recovery;
- provider-native proxy names, toxic names, stream chunks, listener IDs, or
  control handles are not portable protocol identity.

### 3.4 HTTP/application-layer fault injection

Envoy's HTTP fault filter demonstrates that delay and abort can be injected at
an HTTP layer. HTTP abort/status behavior is meaningfully different from an
unavailable or cut transport path.

Consequences for AVP:

- HTTP status/abort injection must not satisfy a transport-cut requirement;
- application-layer faults require a separate reviewed semantic surface if AVP
  later standardizes them;
- a Network Control resource does not imply generic application-protocol fault
  ownership.

### 3.5 DNS/name-resolution behavior

DNS failure and negative answers have resolver-, cache-, TTL-, and
name-resolution-layer behavior independent from an already resolved TCP path.
Negative caching itself is standardized separately from transport behavior.

Consequences for AVP:

- DNS/name-resolution failure is not part of the mandatory base transport-cut
  semantic;
- future DNS control should have an explicit selected name-resolution target and
  lifecycle rather than being inferred from generic `network` ownership;
- a cached resolution must not accidentally make a DNS-failure test appear to
  exercise a transport cut.

## 4. Portability boundary selected by this audit

The v0.1 reconciliation direction should use the smallest semantic surface that
can be independently exercised across materially different implementation
mechanisms.

The candidate mandatory base is therefore narrowed to a **controlled TCP path
with fresh-connection exchange semantics**:

1. a declared Subject-side endpoint boundary;
2. a declared upstream-side endpoint boundary;
3. a deterministic evaluator-controlled upstream fixture;
4. a baseline fresh TCP connection plus deterministic request/response exchange;
5. a governed activation condition inherited from Environment v0.1;
6. after activation settlement, fresh connection/exchange attempts through the
   selected path exhibit the selected **transport cut** behavior;
7. after clearing and recovery settlement, fresh connection/exchange attempts
   again complete the deterministic baseline exchange;
8. selected traffic is behaviorally shown to traverse the controlled path.

`transport cut` is an observable inability to complete the selected fresh
connection/exchange while the fault is active. The portable semantic does not
require one native mechanism such as SYN rejection, TCP RST, FIN, silent drop,
blackhole, proxy timeout, route withdrawal, or a specific socket error.

This narrow base deliberately avoids claiming that all network impairment forms
are equivalent.

## 5. NC-BR decision matrix

| Blocker | Audit decision | Reconciliation direction |
| --- | --- | --- |
| NC-BR-001 — controlled-path boundary | **Resolved for reconciliation** | Define one resource as a declared Subject-side to upstream-side controlled TCP path. Resource ownership is narrower than the Environment network. Selected traffic must be behaviorally demonstrated to traverse the path. |
| NC-BR-002 — fault vocabulary | **Resolved by narrowing** | Mandatory v0.1 base vocabulary is baseline forwarding, deterministic transport cut for fresh exchanges, clear, and recovery. Latency, probabilistic loss, DNS, application-layer abort, TLS interception, UDP, and established-connection termination are not silently aliases of this base semantic. |
| NC-BR-003 — activation settlement / Environment authority | **Resolved for reconciliation** | Environment v0.1 remains authoritative for fault identity, target, and activation condition. Network Control supplies subordinate activation settlement. No post-trigger fault-sensitive observation may be evaluated until an independent data-plane probe demonstrates active cut behavior. Provider API success or arbitrary sleep is insufficient. |
| NC-BR-004 — established connections | **Resolved by explicit exclusion from base** | Base cut conformance is defined on fresh post-activation connections/exchanges. Whether already-established connections are reset, drained, blackholed, preserved, or partially progress is not guaranteed by the base profile. A future established-connection capability/profile must be separately reviewed if needed. |
| NC-BR-005 — recovery settlement | **Resolved for reconciliation** | Clearing ends the selected fault instance. Recovery is proven by independent successful fresh baseline exchanges after clear; control-plane acknowledgement alone is insufficient. The governed schedule must not reactivate the cleared occurrence later. |
| NC-BR-006 — timing / latency | **Resolved by deferral from mandatory base** | Do not standardize exact mandatory latency in v0.1 base. A future bounded-latency profile requires explicit clock source, tolerance model, sample protocol, warm-up policy, and noise budget before it can claim portable conformance. |
| NC-BR-007 — loss semantics | **Resolved by deferral from mandatory base** | Do not use probabilistic finite-run packet loss as a mandatory v0.1 conformance semantic. A future loss profile must define statistical confidence/sample semantics and avoid provider packet-accounting assumptions. Deterministic transport cut is not named `100% packet loss` in the portable protocol. |
| NC-BR-008 — DNS / application layering | **Resolved by layer separation** | Base profile is TCP-path transport control. DNS/name-resolution faults and HTTP/application faults require separately selected semantics. HTTP abort/status cannot prove transport cut; DNS failure cannot be inferred from generic connection failure. TLS interception is not implied. |
| NC-BR-009 — reset / snapshot participation | **Resolved for reconciliation** | `reset` participates by establishing and independently verifying the fault-free baseline. Base v0.1 does not snapshot or restore live TCP/socket/kernel/proxy internals and does not claim byte-for-byte network-stack state restoration. |
| NC-BR-010 — hidden schedule / security | **Resolved for reconciliation** | Future fault schedule, privileged control credentials, provider handles, and activation-control details remain Evaluator/Control-private. Subject-visible interfaces may expose only protocol-authorized observation/evidence and cannot obtain future schedule/control authority. Network Control does not inflate SecurityAssurance. |
| NC-BR-011 — execution identity | **Resolved for reconciliation** | Portable identity binds the selected resource/path definition and execution-relevant provider-neutral inputs required to reproduce the verification claim. Provider-native listener IDs, qdisc handles, socket descriptors, process IDs, mesh object names, and transient control handles are not portable Artifact/resource identity. |
| NC-BR-012 — conformance portability | **Resolved for reconciliation** | The future TCK must be provider- and language-neutral, execution-sensitive, use a deterministic fixture plus privileged control seam, reject self-certification, and include negative adapters. A semantic should not be called portable merely because one provider passes; acceptance evidence should exercise materially independent mechanism classes where the claim depends on mechanism independence. |

The matrix closes the **design questions for purposes of the next reconciliation
step**. It does not close the ROADMAP item `close NC-BR-001..NC-BR-012 Draft ->
Proposed blockers`; that lifecycle/governance conclusion belongs to the separate
AEP reconciliation and Proposed-readiness review.

## 6. Detailed selected semantics for reconciliation

### 6.1 Controlled-path identity

A base Network Control resource should identify one controlled path using
provider-neutral endpoint declarations rather than a provider object.

The eventual normative surface should be able to answer, without knowing the
backend:

- where selected Subject traffic enters the controlled path;
- which upstream fixture/service endpoint is the selected peer;
- which transport family/profile is selected;
- which Environment fault instance targets this resource;
- which execution-relevant configuration is bound into verification identity.

It should not require a portable representation of a Linux interface/qdisc,
proxy process, service-mesh route object, cloud network rule, socket descriptor,
or equivalent mechanism-native object.

### 6.2 Behavioral path-coverage proof

Configuration presence is not enough to establish that Subject traffic actually
traversed the controlled path.

The future conformance harness should therefore include a bypass-negative case:

1. baseline exchange succeeds through the declared path;
2. the selected fault is activated according to Environment authority;
3. independent settlement proves the path is faulting;
4. the Subject's selected post-activation exchange is unable to complete;
5. an adapter that secretly bypasses the controlled path must fail conformance.

This is the intended role of `BypassFaultAdapter`.

A provider-native packet trace may be useful diagnostic evidence, but must not be
the only portable proof because equivalent mechanisms may not expose the same
trace vocabulary.

### 6.3 Activation composition and settlement

Environment v0.1 remains the top-level authority for the scheduled fault's
identity, target, and activation condition.

For an occurrence-based condition, qualifying pre-trigger Subject traffic:

- is allowed;
- may be required to satisfy the occurrence condition;
- must not be faulted early;
- must not be rejected merely because Network Control has already prepared its
  private provider mechanism.

After the Environment condition becomes satisfied, Network Control enters a
subordinate settling interval. Settlement is reached only after a privileged,
independent data-plane probe observes the selected transport-cut signature on a
fresh attempt through the controlled path.

The following do not independently prove activation settlement:

- provider configuration accepted;
- provider API returned success;
- a toxic/qdisc/filter/rule object exists;
- elapsed sleep duration;
- Subject self-report;
- metadata declaring the fault active.

`EarlyActivationAdapter` must fail by applying the cut before the Environment
activation condition. `FalseSettledFaultAdapter` must fail by claiming settled
before the independent cut observation is available.

### 6.4 Fresh-connection cut semantic

The mandatory base semantic is intentionally expressed around fresh attempts.

After activation settlement, a selected fresh connection/exchange through the
controlled path must not complete the baseline deterministic exchange while the
cut remains active.

The base contract should not prescribe which of the following is observed:

- connection refusal;
- reset;
- timeout;
- no route / unreachable behavior;
- proxy close;
- silent drop;
- another implementation-specific transport failure.

It also should not compare exact native exception classes, numeric OS error
codes, or localized error text as a universal conformance requirement.

The evaluator should classify the portable observation as failure to complete
the selected baseline exchange under the active cut, retaining provider/native
diagnostics only as non-normative evidence where useful.

### 6.5 Established connections

The base profile makes **no claim** that a connection established before
activation is destroyed or repaired in a uniform way.

Reasons:

- providers operate at different layers and may affect established streams
  differently;
- a proxy can close/reset an owned connection while route/kernel mechanisms may
  exhibit different timing and buffering behavior;
- transport stacks may already have accepted or buffered bytes;
- exact in-flight packet/segment disposition is not portable.

If a future use case requires termination of established connections, that must
be a distinct selected capability with its own semantic and TCK rather than a
hidden requirement inside base `transport cut`.

### 6.6 Clear and recovery settlement

Clear is a privileged control operation for the selected fault instance. It does
not itself prove that the data plane has recovered.

Recovery settlement should require independent successful fresh baseline
exchanges after clear. A single provider acknowledgement or arbitrary delay is
insufficient.

The future TCK should use enough repeated fresh exchanges to reject a stale or
partially cleared provider state without turning the requirement into a
probabilistic availability SLA. The exact count belongs to later TCK design;
this audit does not standardize it.

`FalseRecoveryAdapter` must fail by claiming recovery while fresh baseline
exchange remains broken.

Environment schedule semantics remain authoritative for preventing an already
cleared occurrence from silently reactivating later. A later distinct fault
instance/occurrence remains separately governed.

### 6.7 Latency

Latency remains a useful future capability but is not sufficiently portable for
the mandatory base without a stronger measurement model.

A future latency profile would need, at minimum:

- explicit measurement endpoints;
- clock source and monotonicity requirements;
- baseline treatment;
- additive-vs-total latency definition;
- tolerance window rather than exact time equality;
- warm-up and sample selection;
- host scheduling/noise treatment;
- timeout interaction;
- platform-independent acceptance statistics.

Until that work exists, provider delay knobs and observed wall-clock sleeps are
implementation evidence, not a portable normative contract.

### 6.8 Loss

Probabilistic loss is similarly deferred from the mandatory base.

A finite run cannot prove an exact probability without a statistical model, and
providers may count different units depending on where the mechanism sits in the
stack. TCP retransmission can also mask packet-level loss from an application
exchange.

A future loss profile therefore requires an explicit observation unit,
statistical acceptance model, sample size/confidence rule, and interaction with
transport retransmission. It must not simply copy a provider's `loss=NN%` knob
into the protocol.

The deterministic base cut should be named and tested as **transport cut**, not
as `100% packet loss`.

### 6.9 DNS and application-layer faults

Name-resolution, transport, TLS, HTTP, and application semantics must remain
layer-distinct.

The base Network Control profile does not imply:

- DNS poisoning/NXDOMAIN/timeout control;
- resolver-cache eviction;
- TLS certificate substitution/interception;
- HTTP status injection;
- HTTP response delay;
- application protocol errors.

These may later be separate capabilities if there is a concrete verification use
case and provider-independent semantic model.

### 6.10 Reset and snapshot boundary

Network Control participates in Environment reset by establishing a verified,
fault-free baseline for the selected controlled path.

Base v0.1 should not claim snapshot/restore of:

- live socket state;
- TCP sequence/retransmission state;
- kernel queue/qdisc internals;
- proxy buffers;
- NAT/conntrack state;
- resolver caches;
- mesh/provider runtime internals.

Those mechanisms are neither a stable logical state image nor portable across
implementations. If a future resource profile identifies logical network state
that is actually snapshot-able, it requires separate reviewed semantics.

### 6.11 Security and hidden control

Network fault control is privileged Environment control.

The future harness/runtime separation should preserve:

```text
Subject
  -> ordinary selected network endpoint only

Evaluator
  -> observations, verification logic, non-secret evidence

Privileged fixture/control seam
  -> fault preparation/activation/clear/reset
  -> future schedule and provider credentials/handles
```

The Subject must not receive future fault schedules or privileged handles that
allow it to predict, suppress, move, or clear faults outside the protocol's
ordinary observable behavior.

`ScheduleLeakAdapter` must fail if it exposes evaluator-private future schedule
or privileged control material through Subject-visible interfaces/evidence.

### 6.12 Execution identity

Verification identity must bind enough provider-neutral execution input to make
the claim interpretable and reproducible without binding transient provider
objects.

Candidate identity inputs for later reconciliation/specification include:

- Network Control profile/version;
- selected controlled-path resource identity;
- selected endpoint/transport declarations;
- selected Environment fault identity/target/condition references;
- deterministic fixture/program identity where it affects the exchange;
- execution-relevant configuration outside logical state that can alter the
  verification result.

Excluded as portable identity:

- qdisc/filter handles;
- proxy/toxic IDs;
- socket file descriptors;
- process IDs;
- cloud rule IDs;
- service-mesh object names;
- ephemeral provider-generated control IDs.

Provider-native values may be retained as diagnostic implementation evidence if
properly scoped and sanitized.

## 7. Candidate future TCK shape

This section is non-normative planning evidence for later TCK work. It does not
create tests in this audit.

The future provider/language-neutral conformance path should use:

- an immutable deterministic upstream echo/application fixture;
- a Subject client that performs the selected baseline exchange;
- a privileged fixture-control seam not visible to Subject code;
- an evaluator that controls ordering and independently verifies settlement;
- execution-sensitive negative adapters.

A minimal execution flow should be capable of proving:

1. baseline fresh exchange succeeds;
2. qualifying pre-trigger Subject traffic can occur without early faulting;
3. the Environment activation condition is reached;
4. activation settles through independent data-plane observation;
5. post-activation fresh exchange cannot complete through the selected path;
6. bypass attempts are detected;
7. clear is issued through privileged control;
8. recovery settles through independent successful fresh exchange(s);
9. the cleared occurrence does not later reactivate;
10. future schedule/control material remains hidden from the Subject.

Existing negative-adapter directions remain appropriate:

- `BypassFaultAdapter`;
- `FalseSettledFaultAdapter`;
- `FalseRecoveryAdapter`;
- `ScheduleLeakAdapter`;
- `EarlyActivationAdapter`.

The TCK must not contain branches such as `if provider == "toxiproxy"` or `if
platform == "linux-netem"` to define different portable outcomes. Provider-
specific fixture setup belongs behind privileged implementation seams.

## 8. Cross-mechanism portability evidence

A semantic should not be promoted merely because one reference mechanism can
implement it.

For the mandatory base transport-cut/recovery semantics, later acceptance should
seek evidence from materially independent mechanism classes where practical,
for example:

- a user-space TCP proxy/interceptor class; and
- a kernel/routing/firewall or otherwise independently realized transport-path
  control class.

The purpose is not to standardize either implementation. It is to detect
accidental dependencies on one mechanism's API, timing, error behavior,
buffering, or identifiers.

Cross-mechanism evidence is especially important before claiming that an
observation is portable. It is not necessarily a universal third-party
conformance requirement unless the later normative protocol explicitly makes it
one.

Latency/loss/DNS profiles, if later proposed, require their own portability
evidence rather than inheriting support from the base cut profile.

## 9. Open-source engineering boundary

The later implementation should remain responsibility-driven and minimal.

This audit specifically rejects prematurely introducing:

- a universal `BaseNetworkBackend` hierarchy;
- provider registration/plugin systems with only one real consumer;
- broad `supports_loss`, `supports_latency`, `supports_dns`, `supports_tls`, etc.
  bags before those capabilities have reviewed protocol semantics;
- a single catch-all adapter owning Environment lifecycle, path identity,
  evaluator decisions, privileged control, provider mechanics, evidence, and
  fixture behavior;
- compatibility wrappers for unreleased Network Control APIs;
- unconditional optional-provider dependencies in the base package.

The correct implementation boundaries can be chosen only after the authority
surface and TCK require concrete seams.

## 10. Reconciliation checklist

A separate AEP-0012 reconciliation / Proposed-readiness change should, at
minimum:

1. incorporate the NC-BR-001 controlled-path definition;
2. narrow the mandatory base vocabulary to baseline / fresh-connection
   transport cut / clear / recovery;
3. preserve Environment v0.1 activation authority and encode subordinate
   Network settlement semantics;
4. explicitly exclude established-connection termination from the base claim;
5. encode behavioral recovery settlement and no-later-reactivation composition;
6. defer latency from mandatory base and record the requirements for any future
   profile;
7. defer probabilistic loss from mandatory base and record the statistical
   requirements for any future profile;
8. separate DNS, TLS, HTTP/application, and transport fault semantics;
9. make reset participation explicit and snapshot of live network internals
   unsupported in base v0.1;
10. preserve Subject/Evaluator/Control separation and future-schedule secrecy;
11. bind provider-neutral execution identity without mechanism-native IDs;
12. record provider/language-neutral TCK and cross-mechanism portability
    expectations;
13. re-run a full cross-contract review against Environment, Fabric, Security,
    Evidence, Scenario, and existing lifecycle semantics;
14. only then determine whether NC-BR-001..NC-BR-012 are sufficiently closed for
    a separately governed Draft-to-Proposed lifecycle step.

That next reconciliation must remain free to revise this audit if cross-contract
review discovers a contradiction.

## 11. Audit conclusion

**PORTABILITY AUDIT DECISIONS ARE READY FOR AEP RECONCILIATION.**

The strongest portable v0.1 direction is deliberately smaller than the broad
fault families listed in the initial Draft:

- one behaviorally verified controlled TCP path;
- deterministic baseline fresh-connection exchange;
- Environment-governed activation;
- independent data-plane activation settlement;
- deterministic fresh-connection transport cut;
- privileged clear;
- independently verified fresh-connection recovery;
- no silent later reactivation of the cleared occurrence;
- private schedules/control; and
- provider-neutral execution identity/conformance.

Established-connection termination, exact latency, probabilistic packet loss,
DNS/name-resolution failure, TLS interception, HTTP/application faults, UDP, and
provider-native packet/error semantics are **not** mandatory base semantics.
They require separate reviewed capabilities/profiles if later justified.

This audit resolves NC-BR-001..NC-BR-012 only as design inputs for the next
reconciliation work unit. It does not itself change AEP-0012 from **Draft**, does
not mark the ROADMAP blocker-closure item complete, and does not authorize
Normative Spec, Schema, TCK, harness, runtime, provider selection, or release
work.