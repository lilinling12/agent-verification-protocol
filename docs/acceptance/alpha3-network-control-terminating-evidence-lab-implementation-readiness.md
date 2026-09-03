# Alpha 3 Network Control Terminating Evidence Lab Implementation Readiness Audit

Status: **IMPLEMENTATION GATED — TERMINATING LAB ARCHITECTURE READY; INDEPENDENT INITIATION WITNESS MUST BE IMPLEMENTED AND PROVEN BEFORE ACCEPTANCE EVIDENCE**

Audited main baseline: `2cd288fed26e11131ec017da33b2af627ba3f67c`

Governing candidate authority and reviewed engineering baselines:

- AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- AEP-0012 — Network Control Resource Profile v0.1 (`Proposed`)
- `docs/design/alpha3-network-control-cross-mechanism-research.md`
- `docs/design/alpha3-network-control-cross-mechanism-evidence-architecture.md`
- `docs/design/alpha3-network-control-npr011-evidence-contract-detailed-design.md`
- `docs/OPEN_SOURCE_ENGINEERING_STANDARD.md`

Prepared: 2026-09-03

## 1. Purpose

This audit decides whether AVP can begin the NPR-011 terminating/intercepting-class evidence implementation without allowing Toxiproxy, container networking, packet capture, Linux behavior, or an implementation convenience to redefine AEP-0012.

It is deliberately an **implementation-readiness gate**, not a provider implementation, protocol amendment, future Network Control Spec/Schema/TCK, public backend SPI, plugin design, CI workflow authorization, or AEP lifecycle decision.

The audit specifically closes the questions that must be answered before code is written:

1. exact terminating topology;
2. Toxiproxy artifact/version/digest strategy;
3. process and resource lifecycle;
4. fixture boundary;
5. Subject-side and upstream-side transport-initiation witnesses;
6. retry/reconnect/fallback detection;
7. active-cut mechanism;
8. activation settlement, clear, and recovery;
9. target isolation;
10. cleanup and residual-state proof;
11. negative-mode assembly;
12. retained artifacts;
13. local versus CI execution;
14. privilege and trust boundaries;
15. failure taxonomy;
16. test strategy;
17. no-rewrite risk.

## 2. Decision

**AEP-0012 does not need to be weakened or reopened to use Toxiproxy as the terminating NPR-011 evidence mechanism.**

Source review of Toxiproxy `v2.12.0` shows that its proxy accept loop performs one `net.Dial("tcp", proxy.Upstream)` after each accepted client connection. If that dial fails, the accepted client is closed and the loop returns to accepting a new client; there is no per-client upstream retry/reconnect loop in that path.

That source property is useful implementation evidence, but it is **not sufficient to certify AEP-0012 initiation cardinality**. The terminating lab remains fail-closed unless an independent controlled-boundary witness proves the actual run contains:

- exactly one Subject-facing TCP connection initiation for each certified attempt;
- exactly one corresponding upstream TCP connection initiation to the bound fixture endpoint;
- no additional reconnect/retry initiation;
- no alternate endpoint/path fallback.

Therefore the repository is ready for a narrow terminating-lab implementation slice **only in this order**:

```text
sealed provider-neutral evidence inputs
  -> deterministic fixture + attempt client
  -> independent transport-initiation witness
  -> witness integrity/negative tests
  -> pinned Toxiproxy mechanism binding
  -> positive + negative terminating evidence execution
  -> retained bundle + provider-neutral comparator assessment
```

A `ToxiproxyBackend`, generic `NetworkBackend`, provider registry, plugin system, future TCK harness, or broad provider SPI is explicitly out of scope.

The first implementation must treat inability to establish trustworthy transport-initiation evidence as `EVIDENCE_INVALID` / unsupported evidence execution, never as assumed provider correctness.

## 3. Authority boundary

The authority direction for this work remains:

```text
AEP-0012 Proposed semantics
  -> NPR-011 project acceptance evidence
  -> acceptance-oriented protocol re-review
  -> explicit Proposed -> Accepted decision
  -> normative Spec
  -> Schema where required
  -> provider/language-neutral TCK
  -> backend-neutral conformance harness
  -> reference implementation
```

This lab tests the current AEP candidate. It does not define the future normative serialization or API.

The following are implementation/evidence choices only:

- Toxiproxy `v2.12.0`;
- OCI/container runtime and network IDs;
- Toxiproxy proxy/toxic names;
- Linux interfaces/veth names;
- packet/SYN capture representation;
- native socket errors;
- container/process IDs;
- exact module/class/function names;
- diagnostic fixture accept records;
- mechanism-control API responses.

No portable comparator expectation may branch on `toxiproxy` or any other provider name.

## 4. Toxiproxy artifact binding

### 4.1 Reviewed release

The reviewed terminating mechanism baseline is Shopify Toxiproxy `v2.12.0`:

- source tag commit: `3ccd6a79cbc6c6a72b884d295ad314b75cdf3962`;
- release: <https://github.com/Shopify/toxiproxy/releases/tag/v2.12.0>;
- source: <https://github.com/Shopify/toxiproxy/tree/v2.12.0>.

As of this audit, GitHub Container Registry exposes `2.12.0` as the latest tagged container release.

### 4.2 Immutable OCI identity

Tag-only pulls are prohibited for reviewed NPR-011 evidence.

The currently published image identities are:

- multi-platform OCI index: `sha256:9378ed52a28bc50edc1350f936f518f31fa95f0d15917d6eb40b8e376d1a214e`;
- `linux/amd64` manifest: `sha256:a3e244375123dad8849091bcc59775e188624d3f602db01901f9af855682fef8`;
- `linux/arm64` manifest: `sha256:5ab4b4e8f476fd5452eb9584a608dd7cf8c11135878a8f7953722a9fcb9b3d87`.

Registry source: <https://github.com/Shopify/toxiproxy/pkgs/container/toxiproxy>.

The canonical CI evidence lane SHOULD initially bind `linux/amd64` and the exact platform manifest digest, while also retaining the OCI index digest and resolved platform. A local run on another supported architecture is a different lab binding and must retain its exact platform digest.

The evidence plan must never record only `2.12.0`, `v2`, or `latest` as the executable artifact identity.

If the registry digest changes, the image becomes unavailable, or the runtime resolves a different platform artifact, the plan must be rematerialized and reviewed rather than silently substituting bytes.

## 5. Toxiproxy connection-lifecycle feasibility

Toxiproxy `v2.12.0` `proxy.go` has the following relevant ordering for one accepted client:

```text
listener.Accept()
  -> net.Dial("tcp", proxy.Upstream)
  -> register the two connection halves
  -> start upstream/downstream toxic links
```

This has two important consequences for AVP evidence:

1. the reviewed source path does not contain a hidden retry loop around the one upstream dial;
2. a stream toxic may prevent the exact-byte exchange **after** one upstream initiation has already occurred.

The implementation must still prove actual runtime behavior at the controlled boundary. Source inspection, provider logs, proxy connection maps, API state, or fixture `accept()` count cannot replace the independent witness.

A future Toxiproxy upgrade requires a fresh source/lifecycle review and new artifact identity. The lab must not assume this property is stable across versions.

## 6. Exact terminating topology

The canonical terminating evidence topology is an ephemeral, literal-addressed local topology with separate data and control authority:

```text
                         Evaluator / Control
                               |
                               | admin-only network
                               v
                       Toxiproxy admin API

Subject role                                    Fixture role
    |                                               ^
    | data network                                  |
    | exactly one Subject initiation                | exactly one upstream initiation
    v                                               |
selected Toxiproxy listener ------------------------+

Subject role
    |
    +----> non-target Toxiproxy listener ----> non-target fixture
```

Required structural properties:

- Subject, Toxiproxy, fixture, and witness resources are unique per evidence run;
- every protocol-significant endpoint is a materialized literal address + TCP port before the plan is sealed;
- the selected listener and upstream fixture are distinct bound endpoint identities;
- a separate non-target listener/fixture is materialized for target-isolation evidence;
- no public Internet service participates in the exact-byte exchange;
- Subject has no route/access to the Toxiproxy admin endpoint;
- Subject receives no container-runtime socket, provider credential, admin token/handle, future fault schedule, or private future challenge material;
- Toxiproxy upstream configuration uses the literal bound fixture endpoint, not a hostname;
- the data topology has no implicit DNS/address-family/alternate-destination fallback;
- container/network IDs remain diagnostics only.

The preferred implementation uses isolated ephemeral container/OCI networks because they provide a real structural Subject/control boundary and a narrow place to attach passive witnesses. Docker/OCI networking is execution plumbing, not protocol identity and not a requirement on third-party conformers.

### 6.1 Admin-plane isolation

Toxiproxy `v2.12.0` exposes `-host` and `-port` specifically for its API listener. The lab must bind the API only to the evaluator/control-side address.

The selected proxy listener itself binds a distinct data-network literal address.

The implementation test must prove from the Subject role that the admin endpoint is unreachable. Merely omitting the address from Subject configuration is not an authority boundary.

## 7. Deterministic fixture boundary

The evaluator-owned fixture remains a separate responsibility from Toxiproxy and from the transport witness.

For an admitted application connection it must:

1. accept the connection;
2. read the exact materialized request length;
3. validate exact request bytes and the current attempt challenge;
4. emit the exact materialized expected response once for a valid request;
5. retain an immutable exchange event;
6. close according to fixture-local hygiene.

Fixture application `accept()` accounting is a useful cross-check but is **not upstream initiation-cardinality proof**. A SYN/connection attempt can occur without becoming an accepted application connection.

This audit therefore treats the older wording in `alpha3-network-control-cross-mechanism-evidence-architecture.md` that describes fixture accepts as verifying the upstream one-initiation property as incomplete implementation guidance. The later reviewed NPR-011 detailed design controls this implementation decision: independent fixture-boundary/equivalent transport-initiation evidence is mandatory. Any textual reconciliation of the older architecture document should be a separate focused reconciliation work unit rather than bundled into this readiness audit.

## 8. Independent transport-initiation witness

### 8.1 Required observation model

The terminating lab must use an observational mechanism that is independent of:

- Toxiproxy control/API state;
- Toxiproxy logs/counters;
- Subject self-report;
- fixture application `accept()` count;
- provider configuration objects.

The preferred implementation for this lab is **passive Linux transport-boundary observation on the isolated data topology**, retaining initial TCP SYN evidence and a reviewed normalization step.

Two logical witness channels are required:

```text
W-front:
  Subject role -> selected Toxiproxy listener

W-upstream:
  Toxiproxy role -> selected evaluator fixture
```

The witness must observe all relevant outgoing TCP initiations from the Subject role and the Toxiproxy data-plane role during an armed certified-attempt window, not only packets already filtered to the expected endpoint. Otherwise an alternate-endpoint fallback could escape observation.

### 8.2 Retransmission is not retry

Raw SYN packet count is **not** initiation cardinality because TCP may retransmit the same connection's SYN.

Normalization must distinguish:

- retransmission of the same connection initiation;
- a second `connect`/reconnect attempt;
- an alternate endpoint/port attempt;
- a failed/unaccepted extra attempt.

At minimum, the raw witness must retain enough tuple/sequence/direction information to group retransmissions of one TCP initiation while treating a different connection attempt as a separate initiation. Native tuple/sequence information remains diagnostic evidence and must not become portable AVP identity.

### 8.3 Attempt binding

The witness cannot attribute traffic to an attempt by wall-clock coincidence alone.

The implementation must use an explicit arm/admit/close barrier:

```text
collector.arm(attemptId, role identities, bound endpoints)
  -> collector acknowledges observation window
  -> evaluator admits exactly one certified attempt
  -> evaluator/comparator reaches the attempt terminal observation boundary
  -> collector closes the window and seals raw witness bytes
```

Role/container/network identity and the sealed endpoint plan constrain the collection scope. Fixture challenge/exchange evidence cross-binds successful application exchanges to the attempt.

### 8.4 Capture integrity

The witness must fail closed when trustworthy counting cannot be established.

Examples:

- capture drop/overflow is non-zero or unknowable;
- the expected interface/namespace identity changed after plan sealing;
- packet direction is ambiguous;
- offload/virtualization makes unique initiation normalization ambiguous;
- the capture starts after attempt admission;
- raw witness bytes cannot be retained/integrity-verified;
- an unobserved network escape path exists.

In those cases the lab result is evidence-invalid/unsupported. It is not transport-cut PASS.

### 8.5 Stronger audit channel

A kernel/eBPF connect-attempt audit MAY be added as an independent supplemental channel to detect attempted connects that fail before an observable SYN crosses the selected interface. If used, it must remain evidence plumbing, be pinned/reviewed as an implementation dependency, and must not replace the boundary observation with provider/process self-report.

The first implementation must not invent a generic cross-provider witness SPI. The terminating lab should expose only the concrete witness responsibility it actually needs; reuse can be considered after the packet-path lab provides the second real consumer.

## 9. Active-cut mechanism selection

The selected Toxiproxy cut realization is an **upstream `timeout` toxic with `timeout = 0` and full application to the selected proxy path**.

Toxiproxy `v2.12.0` documents/implements this behavior as:

- stop data from flowing through the toxic;
- when timeout is zero, do not close the connection on a provider-owned timer.

This choice is preferred over using a positive provider timeout because AEP-0012's cut decision must remain owned by the evaluator's finite monotonic `exchangeObservationBudget`.

For the selected terminating topology the sequence is:

```text
Subject connects once
  -> Toxiproxy accepts once
  -> Toxiproxy initiates upstream once
  -> upstream timeout toxic drops request-stream bytes
  -> exact expected response cannot complete
  -> evaluator-owned observation budget adjudicates non-completion
```

The toxic's name, direction, configuration object, and API acknowledgement remain diagnostics. The portable predicate is exact exchange non-completion within the governed budget after valid settlement.

The implementation must regression-test this exact behavior against the pinned image digest before collecting acceptance evidence.

### 9.1 Hygiene timeout rule

Process/client hygiene limits may exist only outside the portable decision boundary.

They must never expire earlier than, or substitute for, the evaluator-owned observation budget. If a hygiene watchdog terminates the attempt before the portable budget can be validly adjudicated, the run is evidence-invalid/infrastructure failure, not active-cut success.

After the evaluator has reached the portable terminal observation boundary, it may close the attempt's local socket/process for cleanup. That cleanup action must not be reinterpreted as the fault mechanism.

## 10. Ordered phase lifecycle

The terminating runner consumes the same sealed provider-neutral phase program as the eventual packet-path runner:

```text
P0  materialize and seal plan
P1  baseline certified fresh exchange
P2  qualifying pre-trigger Subject exchange
P3  Environment trigger becomes satisfied
P4  create selected fault mechanism state
P5  privileged activation-settlement certified fresh cut probe
P6  distinct Subject-side certified active-cut attempt
P7  non-target control exchange while cut remains active
P8  privileged clear
P9  privileged recovery probe #1
P10 privileged recovery probe #2
P11 distinct post-recovery stability witness
P12 cleanup / residual-state noninterference verification
```

Exact evidence-model phase labels remain non-normative implementation vocabulary.

Hard ordering invariants:

- no fault effect before the Environment trigger;
- provider API success does not establish settlement;
- settlement probe and Subject active attempt are different attempts/challenges;
- no attempt reuses a TCP connection;
- clear acknowledgement does not establish recovery;
- recovery is exactly two consecutive privileged fresh successful probes followed by one distinct stability witness;
- no unbounded retry loop is permitted;
- cleanup cannot overwrite the primary failure.

## 11. Target isolation

The terminating lab must materialize two independent Toxiproxy listener/upstream pairs in the same isolated run:

```text
selected listener -> selected fixture
control listener  -> control fixture
```

Only the selected listener receives the active fault toxic.

During the selected cut, a certified control exchange through the non-target listener must remain baseline-capable.

Using two explicit proxy paths is preferable to a direct bypass-only control because it tests narrow provider-object targeting without changing the portable expectation. Provider names/IDs remain diagnostics.

If the process crashes or otherwise makes the control path unavailable, the narrow-target evidence fails; broad failure cannot be normalized into selected-path cut success.

## 12. Retry, reconnect, and fallback detection

A positive certified attempt is valid only if retained evidence establishes:

- `frontInitiations == 1` for the bound selected Subject destination;
- `upstreamInitiations == 1` for the bound selected fixture endpoint;
- no additional Subject-role TCP initiation under the attempt window;
- no additional Toxiproxy-role upstream TCP initiation under the attempt window;
- no alternate destination/port/path initiation;
- no connection reuse from a prior attempt.

The comparator must not infer these facts from the reviewed Toxiproxy source. Source review only establishes implementation plausibility.

A fixture accept record may confirm that the one upstream initiation reached application acceptance, but a count of one fixture accept does not prove there was only one initiation.

## 13. Negative-mode implementation

All negative modes use the same sealed semantic baseline and provider-neutral comparator. They intentionally assemble incorrect implementation/evidence behavior; they do not alter expected semantics.

### 13.1 BypassFault

Do not apply the selected cut while mechanism metadata/runner state claims activation. The active Subject exact-byte exchange succeeds; comparator must reject the evidence.

### 13.2 EarlyActivation

Apply the selected toxic before the qualifying pre-trigger exchange. Pre-trigger exact exchange is affected; comparator must reject.

### 13.3 FalseSettled

Treat provider API acknowledgement as settled while omitting or invalidating the independent privileged settlement probe. Comparator must reject the missing/invalid settlement evidence.

### 13.4 FalseRecovery

Clear mechanism state but provide fewer than the required two consecutive recovery probes or omit the distinct stability witness. Comparator must reject.

### 13.5 ScheduleLeak

Deliberately project future fault schedule/control or unreleased future challenge material into the Subject-visible context. Security projection validation must reject.

### 13.6 HiddenRetry/Fallback

At least two negative variants are required:

1. one certified Subject attempt performs a second Subject-facing connection initiation;
2. an intentionally faulty same-role/namespace helper creates an extra upstream initiation during the certified attempt window.

The boundary witness must report cardinality greater than one and the same comparator must reject both.

The helper is test-only negative assembly; it does not become a provider API or portable mechanism.

### 13.7 CollateralTarget

Apply the cut to both selected and non-target proxy paths. The non-target control exchange fails; comparator must reject the narrow-target claim.

### 13.8 ResidualStateCleanupFailure

Intentionally retain selected toxic/proxy/network state or make the cleanup sentinel observe residual interference. Cleanup/noninterference assessment must reject the run.

## 14. Process and resource lifecycle

The implementation must use explicit readiness/termination conditions, not arbitrary sleeps.

Recommended startup order:

1. validate runtime/platform prerequisites;
2. resolve/pull the exact pinned Toxiproxy digest before sealing execution inputs;
3. allocate unique run-scoped data/admin network resources;
4. start selected and control fixtures;
5. start/arm independent transport witness;
6. start pinned Toxiproxy with admin listener bound to control-only address;
7. verify exact Toxiproxy version/artifact identity;
8. create selected/control proxies with literal endpoints;
9. prove Subject cannot reach admin plane;
10. run a bounded infrastructure preflight;
11. seal the evidence plan and begin governed phases.

Recommended teardown order preserves primary failure:

1. stop admitting new attempts;
2. close any already-adjudicated attempt sockets;
3. remove toxic state where still reachable;
4. delete proxy objects where still reachable;
5. stop Toxiproxy;
6. stop fixtures;
7. close/seal witness capture and verify capture integrity;
8. retain evidence/diagnostics;
9. remove run-scoped networks/containers/processes;
10. verify no matching residual run resources remain;
11. run the designed cleanup/noninterference sentinel where applicable.

Every cleanup operation should be idempotent where the underlying resource permits it. Cleanup errors are retained separately and never overwrite an earlier semantic/evidence failure.

## 15. Retained evidence

The terminating Evidence Bundle must retain at least:

### Governed / portable-core inputs and observations

- exact sealed Evidence Plan bytes + SHA-256 + byte length;
- AEP semantic baseline commit/path identity;
- run/phase/attempt identities;
- literal endpoint/path identities;
- exchange-program identity;
- exact request/expected-response byte references/digests;
- attempt challenge evidence/commitments according to secrecy rules;
- evaluator-owned observation budget;
- normalized front/upstream initiation facts;
- exact exchange completion/non-completion observations;
- fixture exchange observations;
- target-control observations;
- recovery/stability observations;
- cleanup/noninterference observation;
- comparator revision and assessment.

### Implementation provenance / diagnostics

- Toxiproxy tag/source commit;
- exact OCI index + platform manifest digest;
- container/runtime/platform identity sufficient for audit;
- exact selected/control proxy and toxic configuration snapshots;
- raw transport-boundary witness artifact(s);
- witness normalization revision;
- capture integrity/drop statistics;
- fixture accept/exchange logs;
- Toxiproxy logs/control responses;
- cleanup logs/resource inventory.

Mechanism diagnostics cannot independently establish portable PASS.

Evidence reassessment later means rerunning the comparator over retained observations. It does not mean pretending a new missing observation was collected. If a later assessment needs an observation absent from the bundle, a new live run is required.

## 16. Privilege and security model

### 16.1 Subject

The Subject role receives only the selected/control data endpoints and current-attempt material required for its ordinary exchange.

It must not receive:

- Toxiproxy admin connectivity;
- container runtime socket;
- host network namespace handles;
- packet-capture control;
- evaluator/control credentials;
- future fault schedule;
- future challenge material.

### 16.2 Mechanism controller

The evaluator/control-side runner may own the Toxiproxy admin API and container lifecycle. This is privileged evidence authority and must be structurally separate from Subject execution.

### 16.3 Witness

Passive packet/transport observation may require `CAP_NET_RAW` or equivalent host observation privilege. That privilege belongs only to the witness/evaluator context.

The Toxiproxy container itself does not need `CAP_NET_ADMIN` or `CAP_NET_RAW` merely to implement the selected user-space fault mechanism.

If a future witness uses eBPF or another stronger kernel observer, its required privilege must be separately minimized and reviewed.

## 17. Local versus CI execution model

### 17.1 Local evidence development

The first implementation may run on a controlled Linux developer/maintainer environment that can provide:

- an OCI/container runtime;
- isolated ephemeral networks;
- passive transport observation with trustworthy capture-integrity reporting;
- no production/customer network or credentials.

Unsupported platforms must fail closed with a precise prerequisite error. They must not silently downgrade the independent witness.

### 17.2 CI

This readiness audit **does not authorize a privileged GitHub Actions workflow**.

Before the terminating evidence lane is added to repository CI, a separate focused CI/security review must decide:

- exact runner class;
- permissions/capabilities;
- Docker/OCI daemon exposure;
- `CAP_NET_RAW`/eBPF requirement if any;
- fork-PR behavior and untrusted-code exposure;
- network egress restrictions;
- pinned external artifacts/actions;
- concurrency/run isolation;
- artifact retention;
- cleanup after cancellation/failure;
- absence of release/signing credentials;
- cost/runtime/flakiness policy.

Ordinary CI remains unprivileged. The evidence lab must not force privileged networking into every PR quality job.

## 18. Failure taxonomy

The implementation must localize materially different failures instead of returning one boolean.

The following engineering classes are required; names may change in code and are not normative AVP statuses:

| Class | Examples | Assessment consequence |
|---|---|---|
| `MATERIALIZATION_INVALID` | unresolved hostname, zero budget, endpoint drift, missing artifact digest | fail closed before governed execution |
| `ARTIFACT_INVALID` | wrong Toxiproxy digest/version/platform | evidence invalid |
| `TOPOLOGY_SETUP_FAILED` | data/admin isolation unavailable | infrastructure/evidence invalid |
| `FIXTURE_FAILED` | fixture cannot start or deterministic exchange contract broken | infrastructure/evidence invalid |
| `WITNESS_INVALID` | capture loss, ambiguity, late arm, missing raw artifact | evidence invalid |
| `CONTROL_FAILED` | toxic create/delete/API operation failed | infrastructure/evidence invalid unless a negative mode intentionally assembles it |
| `INITIATION_CARDINALITY_FAILED` | extra Subject/upstream initiation or fallback | portable predicate failure/evidence rejection |
| `EXCHANGE_PREDICATE_FAILED` | baseline mismatch, early effect, active exchange unexpectedly succeeds | portable predicate failure |
| `TARGET_ISOLATION_FAILED` | non-target control is affected | portable predicate failure |
| `RECOVERY_FAILED` | fewer/failed recovery witnesses, silent reactivation | portable predicate failure |
| `SECURITY_PROJECTION_FAILED` | future schedule/control leaks to Subject | portable/security predicate failure |
| `EVIDENCE_INTEGRITY_FAILED` | retained bytes/digest mismatch | evidence invalid |
| `CLEANUP_FAILED` | residual run resources/fault state | infrastructure/Validity evidence failure; preserve primary failure |

Provider-native socket errors remain diagnostics and do not become result taxonomy.

## 19. Test strategy

The terminating implementation cannot be considered review-ready with only a positive Toxiproxy smoke test.

### 19.1 Evidence model / comparator tests

- sealed plan mutation changes identity;
- missing/zero/non-finite/provider-private budget fails closed;
- attempt/challenge identity cannot be reused across phases;
- portable comparator never branches on mechanism/provider name;
- reassessment cannot invent absent observations;
- primary failure is preserved when cleanup also fails.

### 19.2 Fixture tests

- exact request length and byte mismatch rejection;
- exact challenge validation;
- exact response emitted once;
- stale challenge/request cannot satisfy a later attempt;
- deterministic replay of retained fixture program.

### 19.3 Witness tests

- one initiation with SYN retransmission normalizes to one initiation;
- two real connections normalize to two initiations;
- failed/unaccepted second attempt is observed;
- alternate destination/port attempt is observed;
- front-side and upstream-side channels are independently attributable;
- capture loss/overflow/late-arm/interface drift fails closed;
- raw witness artifact digest is independently verified.

### 19.4 Real pinned Toxiproxy integration tests

- exact pinned digest/version verified at runtime;
- baseline selected/control exact-byte exchanges pass;
- source-reviewed one-dial behavior is confirmed by boundary evidence;
- `timeout=0` upstream toxic prevents exact exchange without using provider timeout as the portable clock;
- activation settlement and Subject active attempt remain distinct;
- clear followed by exactly two recovery probes + one stability witness passes;
- selected toxic does not affect non-target path;
- Subject cannot reach admin plane;
- no hidden reconnect/retry/fallback is observed;
- cleanup removes run-scoped state and the next clean sentinel is unaffected;
- repeated deterministic runs do not depend on arbitrary sleeps.

### 19.5 Required negative matrix

All eight required negative directions must be exercised against the same comparator:

- BypassFault;
- EarlyActivation;
- FalseSettled;
- FalseRecovery;
- ScheduleLeak;
- HiddenRetry/Fallback;
- CollateralTarget;
- ResidualStateCleanupFailure.

### 19.6 Concurrency and cancellation

- two run IDs do not share proxy/listener/network/witness state;
- cancellation during activation, active-cut, clear, and recovery preserves cleanup evidence;
- a failed run cannot poison the next run;
- port/address allocation races fail closed rather than aliasing another run.

## 20. Implementation work-unit boundaries

The next implementation must remain reviewable and should not combine all later Network Control milestones.

Recommended order:

### TEL-001 — terminating evidence core + fixture + independent initiation witness

Implement only the concrete evidence-plan materialization needed by this lab, deterministic fixture/client, witness collection/normalization, artifact retention, and tests including retransmission/retry distinction.

No Toxiproxy control code is allowed to define expected outcomes in this slice.

### TEL-002 — pinned Toxiproxy terminating mechanism binding

Add exact artifact lifecycle, selected/control proxies, `timeout=0` active cut, settlement/clear/recovery orchestration, and real positive/negative evidence execution against the already-reviewed comparator/witness responsibilities.

Do not create a generic provider base class.

### TEL-003 — terminating evidence execution/adoption record

Run the reviewed terminating matrix, retain exact evidence identities, review failure/cleanup results, and record the project acceptance evidence necessary for NPR-011 class A.

This still does not close NPR-011 because the independent packet-path mechanism remains required.

A later privileged CI workflow, if desired, is a separate work unit after CI/security review.

## 21. Readiness blockers and disposition

### Protocol blockers

**None newly identified.**

The terminating mechanism can test the current AEP-0012 Proposed semantics without changing the protocol meaning.

### Provider feasibility blocker

**Closed at design/readiness level.**

Toxiproxy `v2.12.0` has a source-reviewed one-upstream-dial-per-accepted-client path and a zero-timeout data-drop toxic compatible with evaluator-owned cut adjudication. Runtime evidence must still independently prove behavior.

### Implementation blocker TEL-RB-001 — independent initiation witness not yet implemented

The reviewed detailed design requires independent Subject-side and terminating-upstream initiation evidence. Existing fixture accepts/provider state are insufficient.

Disposition: implement TEL-001 first. Do not begin by writing a Toxiproxy wrapper.

### Implementation blocker TEL-RB-002 — capture integrity and retry/retransmission normalization not yet proven

A raw SYN counter would falsely treat retransmission as retry and may miss ambiguous/lost observations.

Disposition: TEL-001 must retain raw boundary evidence, deduplicate retransmission as one initiation, detect real second/alternate attempts, and fail closed on capture ambiguity/loss.

### CI blocker TEL-RB-003 — privileged evidence workflow not yet reviewed

Passive boundary observation may require host capability unavailable or inappropriate in ordinary CI.

Disposition: local/controlled evidence implementation may proceed after TEL-001 review; privileged CI requires a separate security/workflow review and is not part of TEL-001/TEL-002 by default.

### Documentation reconciliation note TEL-RB-004

The older cross-mechanism evidence-architecture text says fixture accept counters can verify exactly one upstream initiation. The later detailed design correctly requires an independent transport-initiation witness and makes fixture accepts supplemental only.

Disposition: do not follow the older wording in implementation. Reconcile that provenance document in a separate focused documentation work unit rather than changing protocol semantics or bundling unrelated edits into this audit.

## 22. No-rewrite review

| Question | Result |
|---|---|
| Will Accepted -> Spec -> Schema -> TCK require replacing the core topology? | **No expected rewrite.** Literal endpoints, fresh attempts, exact-byte fixture, independent observations, comparator, and evidence retention follow current AEP semantics. |
| Does Toxiproxy leak into portable semantic identity? | **No.** It exists only in Lab Binding/provenance/diagnostics. |
| Are we prematurely creating a provider abstraction? | **No.** TEL-001/TEL-002 are concrete responsibilities; no `BaseNetworkBackend`/registry/plugin is introduced. |
| Is a second consumer being assumed to justify an SPI? | **No.** Future packet-path reuse is not used to justify a generic interface now. |
| Is there a provider timeout/sleep/retry hack? | **No.** `timeout=0` avoids provider adjudication; arbitrary sleep/unbounded retry is prohibited. |
| Can retained evidence be reassessed independently? | **Yes, for recorded predicates.** Missing future observations require a rerun. |
| Can failure be localized? | **Yes.** Materialization, artifact, witness, control, semantic, security, evidence-integrity, and cleanup failures are separated. |
| Is cleanup provable? | **Designed to be.** Run-scoped teardown + residual inventory/sentinel evidence are mandatory; cleanup success is not inferred from API acknowledgement. |
| Is the security/privilege boundary real? | **Yes by design.** Subject lacks admin/runtime/witness authority and must be unable to reach the admin plane. |
| If Toxiproxy is replaced, how much changes? | **Lab binding/controller and mechanism diagnostics only.** Sealed semantic inputs, fixture contract, portable observations, comparator, and bundle layering remain. |

## 23. Final disposition

```text
AEP-0012 terminating semantic feasibility: READY
Toxiproxy v2.12.0 mechanism feasibility: READY WITH RUNTIME PROOF REQUIRED
Generic Network backend abstraction: NOT AUTHORIZED
Direct Toxiproxy-wrapper-first implementation: BLOCKED
Next implementation slice: TEL-001 INDEPENDENT EVIDENCE CORE + FIXTURE + INITIATION WITNESS
Privileged CI workflow: SEPARATELY GATED
NPR-011 overall: STILL OPEN until terminating + packet-path evidence both review-close
AEP-0012 Proposed -> Accepted: NOT AUTHORIZED
Normative Network Control Spec/Schema/TCK: NOT AUTHORIZED
Release/publication/signing/attestation: NOT AUTHORIZED
```

The key readiness conclusion is intentionally strict:

> Toxiproxy appears capable of satisfying the terminating topology, but AVP must prove the one-initiation invariant independently. The first code should therefore build trustworthy evidence observation, not a provider wrapper and not a new protocol abstraction.
