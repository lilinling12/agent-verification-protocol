# AEP-0012 Draft → Proposed Readiness Audit

Status: **READY FOR PROTOCOL REVIEW — PROPOSED ELIGIBLE**

AEP: `rfcs/AEP-0012-network-control-resource-profile.md`
Parent: AEP-0009 (`Accepted`)
Portability baseline: `docs/design/alpha3-network-control-resource-portability-audit.md`
Audit date: 2026-09-02

## 1. Audit purpose

This audit determines whether the reconciled AEP-0012 is sufficiently complete to move from `Draft` to `Proposed` under AVP governance.

`Proposed` means sufficiently complete for formal protocol review. It does **not** make the design normative, does not authorize `Accepted`, does not authorize Network Control Spec/Schema/TCK adoption, and does not authorize a provider implementation.

This audit is evidence only. AEP-0012 remains `Draft` until a separate explicit protocol-maintainer lifecycle decision records `Draft -> Proposed`.

## 2. Governance criteria

A Draft → Proposed candidate must provide:

1. a written interoperability problem and bounded scope;
2. explicit alternatives and compatibility impact;
3. security and authority analysis;
4. an executable, implementation-independent conformance strategy;
5. no unresolved design blocker that would force downstream Spec, Schema, TCK, harness, or reference code to invent portable semantics.

The later `Proposed -> Accepted` decision is outside this audit.

## 3. Problem and scope

**PASS**

AEP-0012 identifies the interoperability failure precisely: network-fault mechanisms operate at different layers and cannot be normalized by copying one kernel, proxy, service-mesh, DNS, TLS, or cloud API.

The reconciled scope is intentionally small:

- one independently owned controlled TCP path;
- declared Subject-side and upstream-side endpoint boundaries;
- deterministic fresh-connection baseline exchange;
- Environment-governed fault activation;
- independent data-plane transport-cut settlement;
- privileged clear;
- independent fresh-connection recovery settlement;
- behavioral path-coverage proof;
- provider-neutral execution identity and conformance.

The AEP does not attempt to standardize a whole Environment network, a universal packet emulator, arbitrary protocol faults, global time virtualization, live TCP checkpoints, or provider APIs.

## 4. Parent-authority composition

**PASS**

The reconciled AEP reuses rather than duplicates:

- Environment fault identity, target, activation condition, occurrence semantics, clear behavior, hidden future schedule, reset honesty, and stale/released-handle rules;
- Fabric Resource Capability identity/revision, REQUIRED/OPTIONAL participation, Subject Capability separation, composite-result honesty, and cleanup;
- Scenario immutable execution-input binding;
- Core lifecycle and `QUIESCING` side-effect admission boundary;
- Security Subject/Evaluator/privileged Control separation and `SecurityAssurance` non-inflation;
- Evidence/Artifact exact-byte identity and visibility discipline.

No second fault lifecycle, Artifact identity system, security taxonomy, or Episode lifecycle is introduced.

`AVP-ENVIRONMENT-010` remains authoritative for scheduled fault identity, target, activation condition, and clear semantics.

## 5. Controlled-path resource boundary

**PASS**

NC-BR-001 is closed with a provider-neutral resource definition: one declared Subject-side → upstream-side controlled TCP path.

The AEP explicitly rejects mechanism-native identity such as:

- qdisc/filter/interface handles;
- proxy listener/toxic IDs;
- firewall/routing native rule IDs;
- mesh resource names;
- cloud rule/object IDs;
- socket descriptors and process IDs.

Path coverage is behavioral rather than configuration-self-certified. A bypassing implementation must fail conformance even if its provider metadata claims the fault is installed.

The exact serialized endpoint/path declaration syntax remains downstream because the semantic boundary is already fixed.

## 6. Mandatory base fault vocabulary

**PASS**

NC-BR-002 is closed by narrowing rather than over-generalizing.

Mandatory v0.1 base semantics are:

1. deterministic baseline forwarding/exchange;
2. Environment-governed activation;
3. independently settled fresh-connection transport cut;
4. privileged clear;
5. independently settled fresh-connection recovery.

The base does not silently alias latency, probabilistic loss, DNS, TLS, HTTP/application faults, UDP behavior, or established-connection termination into one generic `fault` object.

This is sufficiently precise for formal review without choosing one provider mechanism.

## 7. Environment activation composition

**PASS**

NC-BR-003 is closed while preserving existing authority.

For occurrence-based activation:

- qualifying pre-trigger Subject traffic remains admissible;
- that traffic may be needed to reach the occurrence;
- it must not be faulted early;
- provider preparation before the occurrence does not make the fault active;
- Network Control does not redefine occurrence counting.

Only after the Environment condition is satisfied may Network Control enter a subordinate settlement interval. This is not a competing top-level fault lifecycle.

## 8. Activation settlement

**PASS**

The AEP defines a behavioral settlement predicate: after the Environment condition is satisfied, an independent privileged data-plane probe must establish the selected transport-cut property on a fresh attempt through the controlled path before post-activation fault-sensitive observations are accepted.

The following cannot self-certify settlement:

- provider API success;
- rule/toxic/qdisc/filter/mesh object existence;
- provider metadata;
- Subject self-report;
- arbitrary sleep.

This closes the semantic gap without standardizing one native timeout/error mode.

## 9. Fresh-connection transport cut and established connections

**PASS**

NC-BR-004 is closed by separating the portable base from mechanism-sensitive established-stream behavior.

After activation settlement, a selected **fresh** connection/exchange must fail to complete the deterministic baseline exchange while the cut is active.

The protocol does not require refusal, reset, FIN, timeout, blackhole, unreachable, or another specific native manifestation.

Connections established before activation have no base disposition guarantee. A future requirement to terminate them must be a separately reviewed capability/profile with its own TCK.

This avoids requiring kernel, proxy, route, and application implementations to imitate one another's in-flight behavior.

## 10. Clear and recovery

**PASS**

NC-BR-005 is closed with independent recovery evidence.

- clear is privileged control, not proof of data-plane recovery;
- recovery is established by successful fresh baseline exchange(s) through the same selected path;
- recovery does not promise repair of an already-broken connection;
- a cleared occurrence cannot silently reactivate later under Environment semantics.

A `FalseRecoveryAdapter` that reports success while fresh exchange remains broken is explicitly rejectable.

## 11. Timing and latency

**PASS — DEFERRED FROM BASE**

NC-BR-006 is closed by refusing to standardize an under-specified timing contract.

Mandatory v0.1 does not claim exact or bounded injected latency. A future latency profile must first define measurement endpoints, monotonic clock source, baseline treatment, additive-versus-total delay, tolerance, warm-up/sample policy, host-noise treatment, timeout interaction, and platform-independent acceptance statistics.

This is a complete design decision, not an unresolved semantic hole in the base profile.

## 12. Loss semantics

**PASS — DEFERRED FROM BASE**

NC-BR-007 is closed by excluding probabilistic packet loss from mandatory base v0.1.

Finite execution cannot prove an exact probability without a statistical model, provider layers may count different units, and TCP retransmission may hide packet loss at the application boundary.

A future loss capability therefore needs an explicit observation unit and statistical acceptance model. Base deterministic transport cut is not misnamed `100% packet loss`.

## 13. DNS, TLS, HTTP/application, and transport layering

**PASS**

NC-BR-008 is closed through strict layer separation.

- DNS/name-resolution failure is not transport cut;
- HTTP status/abort/delay is not transport cut;
- TLS interception/failure is not implied by Network Control support;
- UDP/datagram behavior is not inferred from TCP semantics.

Future capabilities may govern these layers separately when concrete verification use cases and portable semantics justify them.

This prevents an implementation from satisfying a transport requirement using a higher-layer error merely because the Subject observes failure.

## 14. Reset and snapshot participation

**PASS**

NC-BR-009 is closed conservatively.

Base reset means establishing and independently verifying the profile-defined fault-free baseline on the selected path.

Base v0.1 does not snapshot or restore live sockets, TCP sequence/retransmission state, kernel queues/qdisc/filter state, proxy buffers, NAT/conntrack state, resolver caches, or mesh/provider runtime internals.

The profile therefore does not make a false `EXACT` or `STATE_EQUIVALENT` claim over those excluded internals.

## 15. Execution identity

**PASS**

NC-BR-011 is closed by separating provider-neutral execution identity from deployment diagnostics.

Relevant downstream identity may bind:

- profile/revision;
- controlled-path resource identity;
- Subject-side/upstream-side endpoint declarations;
- TCP transport declaration;
- Environment fault identity/target/condition references;
- deterministic fixture/program identity;
- other execution-relevant immutable configuration that materially affects verification.

Provider-native qdisc, proxy, socket, process, cloud, firewall, or mesh IDs are excluded from portable identity.

The exact serialization belongs downstream; the identity boundary does not.

## 16. Security and hidden control

**PASS**

NC-BR-010 is closed while preserving AVP trust planes.

- future schedules remain Evaluator/Control-private;
- provider/admin credentials and privileged handles remain outside Subject context;
- control-point reach does not authorize exposure of unrelated Environment traffic;
- payload capture and TLS interception are not implied;
- Subject-visible diagnostics must not leak private topology/control authority;
- provider/container/mesh/kernel technology names do not inflate `SecurityAssurance`;
- infrastructure/control failures do not automatically become Agent Task Verdict failures.

`ScheduleLeakAdapter` provides a concrete negative conformance direction.

## 17. Conformance strategy

**PASS**

NC-BR-012 is closed with an executable provider/language-neutral direction.

Mandatory cases use a deterministic local upstream fixture, a Subject-side client, a privileged control seam inaccessible to Subject code, evaluator-controlled ordering, independent settlement probes, and real controlled-path behavior.

The minimum execution flow covers:

1. baseline success;
2. pre-trigger traffic without early activation;
3. Environment condition satisfaction;
4. independent activation settlement;
5. post-activation fresh-exchange failure;
6. bypass detection;
7. privileged clear;
8. independent fresh-exchange recovery;
9. no later reactivation of the cleared occurrence;
10. future schedule/control secrecy;
11. stale/released use failure;
12. cleanup/leaked-fault detection.

Required negative directions include `BypassFaultAdapter`, `EarlyActivationAdapter`, `FalseSettledFaultAdapter`, `FalseRecoveryAdapter`, and `ScheduleLeakAdapter`.

Portable expected outcomes cannot branch on provider or platform names.

## 18. Cross-mechanism portability evidence

**PASS**

The AEP distinguishes third-party conformance from AVP's own evidence burden.

A third-party implementation is not automatically required to implement several network-control mechanisms. However, AVP's acceptance/reference evidence should exercise materially independent mechanism classes where the portability claim depends on independence, such as a user-space TCP proxy class and a kernel/routing/firewall-style class.

The purpose is to detect accidental dependencies on provider API shape, timing, native errors, buffering, teardown behavior, or identifiers.

Deferred latency/loss/DNS profiles must earn their own portability evidence.

## 19. Failure and Validity semantics

**PASS**

The AEP distinguishes infrastructure invalidity from Agent task failure. Examples include failed baseline, bypassed path, unsupported mandatory semantic, activation/recovery settlement failure, stale/foreign control, execution-identity drift, authority loss, schedule leakage, and cleanup failure.

Provider-specific status/error strings remain diagnostics. This preserves the existing AVP separation among lifecycle, infrastructure health, Validity, and Task Verdict.

## 20. Alternatives

**PASS**

The reconciled AEP explicitly rejects or defers, with interoperability rationale:

- provider-first implementation/generalization;
- Linux `tc/netem` or Toxiproxy APIs as protocol authority;
- HTTP abort as transport cut;
- DNS failure as generic network loss;
- implicit established-connection termination;
- mandatory latency without a timing model;
- mandatory probabilistic loss without statistical semantics;
- arbitrary sleeps and provider API success as settlement proof;
- live network/provider snapshot/restore;
- future schedule/control exposure;
- generic provider/plugin architecture before stable semantics and real consumers.

## 21. Backward compatibility and release boundary

**PASS**

Network Control v0.1 is additive under AEP-0009.

- existing Environment/Fabric implementations need not claim it;
- `resourceKind: network` alone remains insufficient;
- Alpha 2, Relational State, and Browser semantics remain unchanged;
- no public release version is selected;
- release-development state is unchanged;
- no tag, release, package publication, signing, or attestation is authorized.

## 22. Transitional-implementation audit

**PASS**

No reconciled decision requires:

- Toxiproxy-first or `netem`-first public APIs generalized later;
- a generic `BaseNetworkBackend`;
- provider plugin discovery before an extension contract exists;
- broad `supports_latency/loss/dns/...` flag bags;
- compatibility shims for unreleased Network Control layouts;
- provider-name branches in portable TCK;
- provider API success or metadata as conformance proof;
- unconditional provider dependencies in the base package.

The implementation remains downstream of reviewed authority.

## 23. NC-BR-001..NC-BR-012 disposition

All original Draft design blockers are explicit in the reconciled AEP:

| Blocker | Result |
|---|---|
| NC-BR-001 controlled-path boundary | CLOSED |
| NC-BR-002 fault vocabulary | CLOSED |
| NC-BR-003 activation settlement / Environment authority | CLOSED |
| NC-BR-004 established connections | CLOSED |
| NC-BR-005 recovery settlement | CLOSED |
| NC-BR-006 timing / latency | CLOSED by base deferral |
| NC-BR-007 loss semantics | CLOSED by base deferral |
| NC-BR-008 DNS / application layering | CLOSED by layer separation |
| NC-BR-009 snapshot / reset participation | CLOSED |
| NC-BR-010 hidden schedule / security | CLOSED |
| NC-BR-011 execution identity | CLOSED |
| NC-BR-012 conformance portability | CLOSED |

Closure means the semantic choices are explicit enough for formal review. It does not mean they have been `Accepted`.

## 24. Non-blocking details intentionally left downstream

The following may be resolved in later normative Spec/Schema/TCK work because the AEP already fixes their semantic constraints:

- final capability/profile identifier spelling;
- exact endpoint/path declaration wire syntax;
- exact JSON properties/media types/size limits where serialized resources are required;
- canonical representation details that do not change the selected identity boundary;
- exact bounded retry/observation parameters for settlement tests, provided they test the defined behavioral predicate rather than arbitrary sleep;
- exact requirement and TCK case IDs/file organization;
- language-specific SPI/interface names;
- provider setup/cleanup commands and diagnostic mapping.

If any such detail changes portable meaning rather than encodes it, the AEP must be amended before acceptance.

## 25. Open formal protocol-review questions

No original Draft blocker remains, but formal review should challenge these choices:

1. Is controlled TCP plus fresh-connection exchange the correct smallest mandatory v0.1 boundary?
2. Is `transport cut` the best provider-neutral vocabulary?
3. Is excluding established-connection disposition appropriately conservative?
4. Is the independent fresh-attempt activation-settlement predicate strong enough without standardizing native timeout/error behavior?
5. Should recovery require a normative bounded count of successful exchanges or can TCK encode the already-defined recovery predicate?
6. Is deferring latency/probabilistic loss the correct first-profile tradeoff?
7. Is DNS/TLS/HTTP/UDP layer separation sufficiently strict?
8. What is the smallest endpoint/path declaration grammar that proves coverage while avoiding private-topology leakage?
9. At which later lifecycle gate should cross-mechanism evidence become mandatory when portability depends on it?
10. Does Core `QUIESCING` / Environment activation / cleanup composition need additional normative constraints?

These are review questions, not missing definitions.

## 26. Readiness conclusion

The portability decisions are now reconciled into AEP-0012. The AEP contains:

- a bounded provider-neutral controlled-path resource;
- a deliberately small mandatory base fault vocabulary;
- exact Environment activation-authority composition;
- independent activation and recovery settlement requirements;
- explicit fresh-connection semantics and established-connection exclusion;
- explicit latency/loss deferral;
- DNS/TLS/HTTP/UDP layer separation;
- reset without false live-stack snapshot claims;
- provider-neutral execution identity boundaries;
- Subject/Evaluator/Control and hidden-schedule security rules;
- execution-sensitive negative-control conformance strategy;
- cross-mechanism reference evidence expectations;
- compatibility/release boundaries;
- rejected transitional implementation patterns;
- explicit disposition of NC-BR-001..NC-BR-012.

No remaining Draft design blocker requires downstream code or TCK to invent the base portable semantics.

Therefore:

**AEP-0012 IS READY TO MOVE FROM `Draft` TO `Proposed` FOR FORMAL PROTOCOL REVIEW.**

AEP-0012 nevertheless remains **Draft** in this work unit. A future `Draft -> Proposed` transition requires a separate explicit recorded protocol-maintainer decision after this exact reconciliation/readiness candidate is review-closed and adopted as governed.

This audit does not authorize:

- AEP lifecycle transition;
- Network Control Spec/requirement-index/Schema/TCK adoption;
- conformance harness or provider implementation;
- provider selection;
- repository merge;
- release selection/publication;
- package publication;
- signing or attestation.