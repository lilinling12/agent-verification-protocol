# Alpha 3 Network Control Packet-Path Evidence Lab Implementation Readiness Audit

Status: **IMPLEMENTATION-READINESS CANDIDATE — NO PACKET-PATH IMPLEMENTATION AUTHORITY UNTIL REVIEW-CLOSED AND MAIN-ADOPTED**

Audited main baseline: `c7eaec4d80c52fa78acaa57ffdd3bb40b476c368`

Governing candidate authority and reviewed engineering baselines:

- AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- AEP-0012 — Network Control Resource Profile v0.1 (`Proposed`)
- `docs/design/alpha3-network-control-cross-mechanism-research.md`
- `docs/design/alpha3-network-control-cross-mechanism-evidence-architecture.md`
- `docs/design/alpha3-network-control-npr011-evidence-contract-detailed-design.md`
- `docs/design/alpha3-network-control-npr011-evidence-contract-traceability.md`
- `docs/acceptance/alpha3-network-control-terminating-evidence-tel003-adoption.md`
- `docs/OPEN_SOURCE_ENGINEERING_STANDARD.md`
- `docs/BRANCHING.md`

Prepared: 2026-09-04

## 1. Purpose

This audit decides whether AVP can begin the materially independent **non-terminating packet-path** NPR-011 evidence implementation without allowing Linux namespaces, veth devices, nftables, a privileged CI runner, packet capture, or implementation convenience to redefine AEP-0012.

The terminating/intercepting evidence class is already main-adopted. At the audited baseline, exact-main CI #911, Relational Parity #304, and Browser Reference #177 are successful after the ROADMAP reconciliation that identifies packet-path evidence as the next legal NPR-011 Work Unit.

No packet-path-specific implementation-readiness audit currently closes the mechanism-specific questions that arise before privileged code is introduced. This document fills that gate. It is deliberately an **engineering readiness review**, not a protocol amendment, normative Spec/Schema/TCK, future Network Control backend API, provider SPI, privileged workflow change, evidence execution, lifecycle decision, or release action.

The audit closes the following questions before implementation:

1. exact packet-path topology and authority boundaries;
2. namespace, veth, routing, and forwarding ownership;
3. nftables transport-cut realization and target scope;
4. literal endpoint and path materialization;
5. Subject-side connection-initiation evidence and escape-path detection;
6. activation settlement, Subject active cut, clear, recovery, and stability;
7. selected versus non-target path isolation;
8. negative-mode assemblies against the unchanged C1-C12 comparator;
9. cleanup and residual-state proof;
10. Linux/kernel/tool provenance and reproducibility limits;
11. ordinary-CI versus privileged-live validation;
12. trusted-main workflow security boundaries;
13. failure taxonomy and fail-closed behavior;
14. implementation decomposition and no-rewrite risk.

## 2. Decision candidate

The reviewed cross-mechanism design is implementable without changing AEP-0012.

The packet-path evidence class SHOULD use an ephemeral three-namespace Linux topology:

```text
subject namespace
      |
    veth
      |
control/router namespace  <-- privileged routing + nftables mutation
      |
    veth
      |
fixture namespace
```

The selected base transport-cut mechanism is a narrowly scoped nftables `drop` rule in the dedicated control/router namespace. `tc netem loss 100%` is not an acceptable substitute for the canonical base evidence path because AEP-0012 standardizes observable transport cut, not packet-loss/qdisc semantics.

If this readiness audit is review-closed and main-adopted, implementation may begin only in this order:

```text
packet-path topology + bounded lifecycle plumbing
  -> packet-path witness/qualification and fail-closed integrity tests
  -> positive + required negative local mechanism assembly
  -> separately reviewed trusted-main privileged execution lane
  -> retained packet-path evidence bundle
  -> independent packet-path evidence adoption
  -> cross-mechanism portability assessment
```

No `NetworkBackend`, `PacketPathBackend`, generic provider registry, plugin framework, or public provider SPI is justified by this work. The terminating and packet-path mechanisms remain separate concrete evidence-lab implementations. They may consume the already-adopted provider-neutral Evidence Plan / Fixture / Result / Comparator responsibilities, but they must not share mechanism-control code merely to reduce duplication.

## 3. Authority and non-authority

The authority direction remains:

```text
AEP-0012 Proposed semantics
  -> NPR-011 project acceptance evidence
  -> cross-mechanism portability assessment
  -> acceptance-oriented protocol re-review
  -> explicit Proposed -> Accepted decision
  -> normative Spec
  -> Schema where required
  -> provider/language-neutral TCK
  -> backend-neutral conformance harness
  -> reference implementation
```

Packet-path implementation choices are project evidence plumbing only. None of the following becomes portable AVP identity or semantics:

- Linux network namespace names or inode identities;
- veth device names, ifindex values, MAC addresses, or ephemeral link state;
- kernel routing-table entries or route-cache behavior;
- nftables table/chain/rule names, handles, counters, native expressions, or command output;
- `ip`, `nft`, `sysctl`, `nsenter`, or equivalent command syntax;
- kernel version-specific socket errors, TCP retransmission behavior, packet timing, or packet counts;
- CI runner image labels or host package-manager state;
- root/sudo availability;
- raw packet-capture representation;
- exact Python module/class/function names chosen by the evidence implementation.

Provider/mechanism control success can never directly produce `SATISFIED`. The unchanged provider-neutral comparator owns portable assessment.

## 4. Canonical topology

### 4.1 Structural roles

The evidence run materializes three structurally distinct network namespaces:

1. **Subject namespace** — contains the Subject attempt process and only the data-plane connectivity required by the sealed plan.
2. **Control/router namespace** — owns both veth-facing router interfaces, forwarding configuration, and nftables mutation.
3. **Fixture namespace** — contains the deterministic selected fixture and non-target control fixture/endpoints.

The host/root namespace is an orchestration boundary only. The selected packet fault MUST NOT be installed in the host namespace.

The Subject namespace MUST NOT own or receive:

- `CAP_NET_ADMIN`;
- nftables control access;
- namespace-control file descriptors or handles;
- access to a container/runtime control socket;
- privileged orchestration commands;
- future fault schedules;
- unreleased future challenge material;
- evaluator-private fixture/control credentials.

The fixture cannot mutate the fault. The mechanism controller cannot self-declare portable pass/fail.

### 4.2 Addressing and routing

The first reviewed evidence implementation MAY bind one explicit IPv4 topology because this is a project evidence binding, not a protocol restriction. AEP-0012 endpoint identity remains address-family aware and is not narrowed to IPv4 by this implementation choice.

Every protocol-significant endpoint is materialized as a literal address family/address/TCP port before the Evidence Plan is sealed. Hostnames, implicit DNS, automatic address racing, and alternate-destination fallback are excluded from the certified attempt.

The topology SHOULD use two point-to-point L3 segments:

```text
subject <-> control/router <-> fixture
```

with explicit routes such that selected and non-target fixture endpoints are reachable only through the reviewed router boundary. The readiness qualification MUST reject an unobserved direct route, host-network escape, alternate interface, or other path that could bypass the controlled packet path.

IPv4 forwarding, if required, MUST be enabled only inside the dedicated control/router namespace. The implementation must not depend on changing host-wide forwarding state.

### 4.3 Selected and non-target paths

The run materializes:

- one selected logical path to the selected exact-byte fixture endpoint; and
- one distinct non-target control logical path/end point used to make narrow target isolation falsifiable.

The two paths may traverse the same control/router namespace but must remain separately attributable through sealed logical path identity and exact endpoint/port identity.

A narrowly targeted packet fault that also breaks the non-target control path is a C6 failure, not successful transport cut.

## 5. nftables transport-cut realization

### 5.1 Placement

The selected fault rule lives in the **control/router namespace**, not the Subject or fixture namespace.

The canonical first implementation should use a dedicated run-owned nftables table/chain attached to the forwarding path. The exact native rule representation remains diagnostic, but the intended matching scope must be reviewable and no broader than required for the materialized target.

The rule SHOULD constrain, as appropriate for the exact topology:

- address family;
- packet direction / forwarding path;
- selected fixture literal destination;
- selected TCP destination port;
- and, where necessary to remove ambiguity, the selected ingress/source-side interface or source subnet.

The implementation must prove that packets for the non-target control endpoint remain admissible while the selected path is cut.

### 5.2 Portable meaning

The nftables rule realizes a native packet drop. That native choice does not define the portable result.

Portable active-cut success remains:

> the independently admitted certified exact-byte attempt does not complete within the evaluator-owned finite observation budget after valid activation settlement.

A native timeout, SYN retransmission count, `ETIMEDOUT`, `EHOSTUNREACH`, `ECONNREFUSED`, nft counter, or provider command exit status is diagnostic only.

Rule creation/removal acknowledgement is control-plane evidence. It cannot substitute for settlement, Subject active-cut, recovery, or stability probes.

## 6. Attempt integrity and transport witness

### 6.1 Subject initiation rule

For the non-terminating packet-path class, one certified attempt still permits exactly one Subject-facing TCP connection initiation to the materialized destination.

Unlike the terminating Toxiproxy topology, there is no second provider-created upstream TCP connection whose cardinality must be proven. Packet forwarding across the router is not a second AVP connection initiation.

C10 nevertheless remains fully applicable to:

- Subject retry/reconnect;
- alternate destination/port fallback;
- alternate address family;
- alternate route/path escape;
- connection reuse/pooling that violates fresh-attempt semantics.

### 6.2 Witness reuse boundary

The already-adopted Linux transport-initiation witness may be reused only because its responsibility is provider-neutral evidence plumbing already defined by the NPR-011 evidence contract. Reuse does **not** authorize sharing Toxiproxy controller/lab orchestration with packet-path mechanism control.

Packet-path witness placement must be independently reviewed for the namespace topology. At minimum it must observe the Subject role's relevant egress initiation boundary and be able to detect unexpected target/port/path attempts rather than pre-filtering only the expected tuple.

The witness remains observational. It cannot mutate routing or nftables state.

### 6.3 Fail-closed capture integrity

The evidence execution is invalid/unsupported rather than successful when trustworthy initiation evidence cannot be established, including when:

- capture drop/overflow is non-zero or unknowable;
- capture starts after attempt admission;
- expected interface/namespace identity drifted after sealing;
- directionality is ambiguous;
- retransmission-versus-new-initiation normalization is ambiguous;
- offload/virtualization invalidates the reviewed observation boundary;
- raw evidence cannot be retained/integrity-checked;
- an unobserved network escape path exists;
- a connect can fail before the selected witness boundary in a way the reviewed qualification cannot safely account for.

The packet-path qualification may add a stronger supplemental connect-attempt audit if required, but must not invent a generic witness/provider SPI merely to do so.

## 7. Ordered lifecycle

The mechanism consumes the already-reviewed provider-neutral phase program. A concrete implementation may use local phase labels, but the ordering invariants are fixed by AEP-0012 and C1-C12:

```text
P0  materialize topology and seal Evidence Plan
P1  baseline certified fresh exchange
P2  qualifying pre-trigger Subject exchange
P3  Environment trigger satisfied
P4  install selected packet-path fault
P5  privileged activation-settlement fresh cut probe
P6  distinct Subject-side certified active-cut attempt
P7  non-target control exchange while cut remains active
P8  privileged clear/remove selected fault
P9  privileged recovery probe #1
P10 privileged recovery probe #2
P11 distinct post-recovery stability witness
P12 cleanup / residual-state noninterference verification
```

Hard invariants:

- selected DROP effect is not active before the Environment trigger;
- rule-install success is not settlement;
- settlement and Subject active-cut use distinct attempts/challenges;
- no attempt reuses a TCP connection;
- clear acknowledgement is not recovery;
- recovery is exactly two consecutive fresh successful privileged probes plus one distinct stability witness;
- no unbounded retry-until-success loop is permitted;
- cleanup cannot replace or erase a primary semantic/evidence failure.

## 8. Required negative assemblies

The packet-path lab must run the same provider-neutral comparator and make every required wrong implementation direction falsifiable.

### `BypassFault`

Assemble a real bypass, for example by placing the native drop on a non-crossed/wrong path or admitting an alternate route so the selected certified Subject exchange still completes while control metadata claims activation.

Expected portable rejection: C4/C5 path/settlement-active-cut failure according to the retained observation ordering. The negative must not fabricate comparator input.

### `EarlyActivation`

Install/effect the selected drop before the Environment occurrence condition is satisfied so qualifying pre-trigger traffic is affected.

Expected rejection: C3.

### `FalseSettled`

Treat rule-install acknowledgement as settlement while omitting/invalidating the required independent privileged settlement attempt.

Expected rejection: evidence invalid / C1 or C4 according to the retained missing observation shape; later Subject failure cannot retroactively repair settlement.

### `FalseRecovery`

Treat rule deletion as recovery while omitting one of the exact two recovery probes or the distinct stability witness.

Expected rejection: evidence invalid or C7-C9 according to the missing/failed retained evidence.

### `ScheduleLeak`

Expose future activation/control/challenge material in the Subject-visible projection.

Expected rejection: C12.

### `HiddenRetry/Fallback`

Cause one certified Subject attempt to execute a real second connection initiation or real alternate destination/path attempt. The normalizer must retain the actual witness evidence rather than fabricating a duplicate count.

Expected rejection: C10.

### `CollateralTarget`

Broaden the native rule so the non-target control exchange is also cut under a narrow selected target.

Expected rejection: C6.

### `ResidualStateCleanupFailure`

Intentionally leave relevant packet-path state such that the cleanup/noninterference verification or next fresh baseline is affected.

Expected rejection: C11.

Negative assemblies may differ mechanically from the terminating lab. Their expected portable predicates must not branch on mechanism name.

## 9. Cleanup and residual-state proof

Cleanup is a first-class evidence phase and must be bounded and idempotent.

The implementation must attempt to remove, in dependency-safe order, all run-owned state including:

- selected nftables table/chain/rules;
- namespace-local forwarding configuration relevant to the run;
- routes and addresses created for the run;
- veth pairs;
- fixture/Subject processes;
- subject/control/fixture namespaces;
- witness resources and retained temporary handles.

Namespace deletion is a strong implementation cleanup primitive, but teardown success alone does not prove the portable cleanup/noninterference predicate.

The retained cleanup record must distinguish:

- primary execution failure;
- cleanup problems;
- residual-state verification result.

The privileged qualification must verify that no run-owned namespace/veth/nftables state remains observable after teardown. It must also execute the reviewed residual/noninterference witness expected by C11 rather than assuming namespace deletion is sufficient.

The implementation MUST NOT flush host-global nftables tables, delete unrelated namespaces/interfaces, or use broad destructive cleanup to make the test pass.

## 10. Provenance and reproducibility

Packet-path evidence must retain enough implementation provenance to explain and reproduce the exact reviewed run without pretending the host kernel/toolchain is a content-addressed provider image.

At minimum retain:

- repository exact commit;
- runner OS/image metadata available from the execution environment;
- `uname` / kernel release and architecture;
- `ip -Version`;
- `nft --version`;
- installed package version/provenance for iproute2 and nftables where available;
- selected namespace/veth topology declaration;
- exact sealed literal endpoint/path identities;
- diagnostic nftables ruleset snapshots before/active/after clear as useful;
- run-owned namespace/interface identity diagnostics;
- relevant sysctl/forwarding state inside the control namespace;
- exact witness revision and raw evidence refs;
- exact Evidence Plan/Result/comparator identities.

A GitHub-hosted Ubuntu package version is not an immutable OCI digest. The evidence must not claim otherwise. If future review concludes tighter binary reproducibility is required, the privileged execution lane must pin a stronger runner/tool artifact boundary or move to an ephemeral managed runner whose image identity is reviewable. That is a later infrastructure decision, not a reason to invent a false digest today.

Any material kernel/tool/witness change used as acceptance evidence creates a new reviewed lab binding/provenance lineage.

## 11. CI and privilege model

### 11.1 Ordinary CI

Ordinary CI remains unprivileged. It should cover as much packet-path behavior as possible without root/network mutation, including:

- topology-plan validation;
- command/spec construction where applicable;
- lifecycle/state-machine ordering;
- exact cleanup ordering/idempotence with a fake/subprocess boundary;
- negative-mode assembly selection;
- provider-neutral observation/result integration;
- security projection tests;
- no provider-name branching in comparator behavior.

Tests must avoid becoming assertions about one exact `nft` text rendering when only the intended mechanism responsibility matters.

### 11.2 Privileged live qualification

Before any packet-path result can be accepted, a live Linux qualification must establish the actual runner supports the reviewed topology and observation assumptions.

Qualification must prove at least:

1. three namespaces can be created and wired through the intended veth topology;
2. Subject-to-selected and Subject-to-control baseline exchanges traverse the intended router boundary;
3. the Subject role cannot mutate nftables or obtain the controller authority used by the job;
4. a narrowly scoped selected DROP prevents selected exact-byte completion under the evaluator budget;
5. the non-target control path remains baseline-capable while selected DROP is active;
6. rule clear is followed by deterministic fresh recovery;
7. witness qualification can distinguish one initiation, a real second initiation, and alternate-target/path behavior without ambiguity;
8. teardown leaves no run-owned namespace/veth/nftables state;
9. qualification failure blocks acceptance-matrix execution.

Qualification output is project-local infrastructure evidence. It does not issue a C1-C12 portable verdict.

### 11.3 Trusted-main workflow boundary

The existing `Network Control Privileged Evidence` workflow is currently terminating/Toxiproxy-specific. Packet-path execution must not be silently appended to TEL-003 semantics or treated as if the terminating job already qualified netns/nftables behavior.

A later separately reviewed workflow/job change may add the packet-path lane only with these minimum safeguards:

- execution from trusted exact `main` only; no PR, fork, or `pull_request_target` trigger;
- exact checkout SHA guard;
- `permissions: contents: read` unless a separately justified narrower need is reviewed;
- `persist-credentials: false`;
- no release/signing/attestation credentials;
- no OIDC/write token requirement;
- hardened Linux runner with bounded job timeout;
- privilege used only by the orchestration/control boundary;
- Subject command executed inside the Subject namespace without receiving controller handles/credentials;
- evidence retained even when the matrix fails, without turning workflow success into portable success;
- same-run qualification precedes the packet-path matrix.

This readiness PR does not modify the workflow and does not authorize privileged execution from its own branch.

## 12. Failure taxonomy

The packet-path implementation must preserve AVP failure/Validity separation.

Examples that are **evidence/infrastructure invalid or unsupported**, not semantic transport-cut success:

- namespace/veth/nft setup failure;
- unexpected route topology or path escape;
- witness capture ambiguity/drop;
- missing required observation;
- evaluator budget truncated by an earlier hygiene timeout;
- insufficient privileges on the qualified runner;
- ruleset state cannot be independently inspected enough to establish reviewed setup/cleanup provenance;
- cleanup unable to prove bounded teardown/noninterference.

Examples that are portable **semantic violations** when evidence is otherwise valid include the intentionally assembled early activation, bypass, hidden retry/fallback, collateral-target, residual-state, and schedule-leak directions localized by the unchanged comparator.

Native `nft`/`ip` return codes and socket errors remain diagnostics and must not be converted into new protocol verdict enums.

## 13. Test and review strategy

The implementation must be developed in small reviewable layers. A large PR containing topology code, privileged workflow, live evidence execution, adoption record, and cross-mechanism conclusion would violate the repository's coherent-Work-Unit rule and make trust-boundary review unreliable.

Recommended decomposition after this readiness gate is main-adopted:

### PTL-001 — packet-path mechanism + qualification foundation

Project-local test/evidence implementation only:

- concrete netns/veth/router/nftables lifecycle;
- literal selected/non-target topology materialization;
- Subject privilege separation;
- Subject-side initiation/escape-path witness integration;
- same mechanism-neutral Evidence Plan / Fixture / Result / C1-C12 comparator consumption;
- ordinary-CI unit tests;
- explicit opt-in local privileged qualification entrypoint;
- all required faulty assemblies structurally implementable.

No GitHub privileged lane and no acceptance-evidence adoption claim yet.

### PTL-002 — trusted-main packet-path evidence lane

Separately reviewed privileged workflow/job and same-run qualification, followed by positive + all required negative packet-path matrix execution and content-addressed retained artifact/manifest.

Workflow success is not evidence adoption.

### PTL-003 — packet-path evidence adoption

Independent retrieval/integrity inspection of one exact trusted-main packet-path evidence run, recorded in a separate acceptance document. ROADMAP status changes only after the adoption becomes main truth.

### Cross-mechanism acceptance

Only after both terminating and packet-path evidence are independently main-adopted may a separate work unit compare them against the same unchanged portable predicates and decide whether NPR-011 cross-mechanism evidence is sufficient for acceptance-oriented protocol re-review.

AEP-0012 `Proposed -> Accepted` remains a later separate explicit protocol-maintainer decision.

## 14. No-rewrite / abstraction boundary

The packet-path implementation should reuse only responsibilities already proven neutral by the terminating implementation and the reviewed evidence contract:

- immutable Evidence Plan and attempt/challenge materialization;
- exact-byte fixture/client semantics where the same role applies;
- provider-neutral normalized observations;
- content-addressed evidence utilities;
- provider-neutral C1-C12 comparator.

It must not reuse or generalize:

- Toxiproxy admin/control code;
- Docker-specific terminating topology orchestration;
- proxy/toxic configuration objects;
- terminating upstream initiation semantics;
- provider-specific cleanup/control classes.

A future backend-neutral Network Control harness belongs after AEP-0012 acceptance, Spec/Schema/TCK closure, and a separately reviewed implementation-readiness boundary. Similar-looking code in two current labs is not sufficient reason to create it early.

## 15. Readiness conclusion

**No AEP-0012 semantic amendment is required to implement the packet-path NPR-011 evidence class.**

The reviewed durable implementation direction is:

```text
unprivileged Subject namespace
        |
      veth
        |
privileged control/router namespace
  narrow selected nftables DROP
        |
      veth
        |
evaluator Fixture namespace
```

with a distinct non-target control path, independent attempt evidence, evaluator-owned observation budget, finite recovery, fail-closed cleanup, and the unchanged provider-neutral C1-C12 comparator.

If — and only if — this audit is focused-review closed, exact-head Gates are green, it is explicitly authorized for merge, main-adopted, and exact-main post-merge validation succeeds, the next legal implementation Work Unit is **PTL-001** as bounded above.

## 16. Non-authorization boundary

This audit does **not** authorize or perform:

- Linux netns/veth/nftables implementation code;
- privileged GitHub Actions changes or execution from this PR;
- packet-path acceptance evidence or NPR-011 cross-mechanism closure;
- AEP-0012 `Proposed -> Accepted` or `Accepted -> Final`;
- Network Control normative Spec, requirement index, Schema, or TCK;
- backend-neutral Network Control conformance harness;
- Network Control provider/reference implementation;
- generic `NetworkBackend`, provider registry, SPI, or plugin framework;
- release selection, tagging, publication, signing, or attestation;
- weakening or reinterpreting C1-C12 to fit Linux/nftables behavior.

Merge remains a separately governed transition requiring explicit authorization.