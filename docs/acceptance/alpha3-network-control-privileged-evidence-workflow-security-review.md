# Alpha 3 Network Control Privileged Evidence Workflow Security Review

Status: **TEL-RB-003 RECONCILED FOR REVIEW — TRUSTED-MAIN EXECUTION ONLY; TEL-003 ADOPTION NOT YET CLAIMED**

Prepared: 2026-09-04

Reconciled target baseline: `c637be27d19283da541c5a2d07ca4689c922cb64`

Main-adopted prerequisites:

- PR #151 — `fix(alpha3): drain witness terminal capture queue` (`bc01bc028e8bd37dbff324fb98d4b980aecbf5be`);
- PR #152 — `test(alpha3): add upstream hidden-retry negative assembly` (`c637be27d19283da541c5a2d07ca4689c922cb64`).

Exact-main post-merge CI, Relational Parity, and Browser Reference push gates passed after each prerequisite.

## 1. Purpose

TEL-RB-003 establishes the separately reviewed privileged execution lane needed to collect terminating-class Network Control evidence. The main-adopted TEL-002 lab requires native Linux Docker and one-shot AF_PACKET witness sidecars with `CAP_NET_RAW`; ordinary repository CI intentionally does not exercise that evidence authority.

This Work Unit is execution and evidence plumbing only. It does **not** adopt TEL-003 evidence, advance AEP-0012 from `Proposed`, introduce normative Network Control Spec/Schema/TCK surfaces, create a provider SPI, or authorize release/publication/signing/attestation.

## 2. Reconciliation after evidence prerequisites

Focused review of the first TEL-RB-003 draft exposed two prerequisites outside the privileged workflow itself.

First, the provider-neutral AF_PACKET witness could stop after the terminal signal without draining a SYN already queued for the capture socket. PR #151 corrected that race with a bounded terminal drain and was main-adopted before this workflow proceeds.

Second, the terminating-lab readiness audit requires two independent `HiddenRetry/Fallback` faulty assemblies judged by the same provider-neutral comparator:

1. an additional Subject-facing initiation;
2. an additional upstream initiation from the Toxiproxy role/network namespace while the Subject-facing count remains one.

PR #152 main-adopted the second test-only assembly without changing C1-C12 or adding a new portable negative mode. This workflow must execute **both** variants and require the same C10 rejection.

This branch is rebuilt linearly on exact `main@c637be27d19283da541c5a2d07ca4689c922cb64`. Neither prerequisite is duplicated or redefined here.

## 3. Threat model and trust boundary

The privileged lane executes container workloads that can observe or deliberately inject packets inside isolated test network namespaces. Primary risks are:

- executing untrusted pull-request code with packet-observation/injection authority;
- exposing repository credentials or secrets to test containers;
- allowing Subject-role code to access Docker control authority;
- widening network reachability beyond the sealed lab topology;
- treating provider acknowledgements or workflow success as portable semantic evidence;
- circularly asserting capture quality before it has been qualified;
- under-counting a boundary-adjacent initiation while the collector is being sealed;
- treating two raw SYN packets from one initiation as two independent connects;
- failing to exercise both required HiddenRetry faulty directions;
- losing failed-run evidence before review.

The reviewed control boundary is:

```text
reviewed repository code merged to main
  -> trusted GitHub-hosted ubuntu-24.04 VM
  -> read-only checkout, persisted credentials disabled
  -> Docker control retained only by workflow/evaluator process
  -> isolated run-scoped qualification/lab networks
  -> NET_RAW granted only to one-shot witness/qualification injector sidecars
  -> retained evidence artifact + SHA-256 manifest
  -> separate TEL-003 engineering review/adoption decision
```

## 4. Workflow trigger and token policy

`.github/workflows/network-control-privileged-evidence.yml` has no `pull_request` or `pull_request_target` trigger.

Automatic execution occurs only when the workflow itself is adopted by a push to `main`. `workflow_dispatch` permits explicit maintainer reruns only after the workflow exists on the default branch. The job independently requires `GITHUB_REF == refs/heads/main` and verifies checkout `HEAD == GITHUB_SHA` before privileged evidence execution.

Permissions are exactly:

```yaml
permissions:
  contents: read
```

`actions/checkout` uses `persist-credentials: false`. No repository/environment secret, cloud credential, OIDC `id-token`, package publication credential, or write-scoped GitHub token is requested. Subject, fixture, probe, witness, and qualification injector containers do not receive the Docker socket.

## 5. Exact executable identities

The lane reuses the exact TEL-002 artifact bindings already reviewed and main-adopted:

- Toxiproxy `v2.12.0` exact linux/amd64 manifest digest;
- exact reviewed Python helper linux/amd64 manifest digest;
- exact commit SHAs for `actions/checkout`, `actions/setup-python`, and `actions/upload-artifact`.

Mutable tags are not evidence identity.

## 6. Non-circular exact-run capture qualification

`CaptureAssurance` is explicitly a set of reviewed preflight facts that packet parsing cannot prove by itself. Qualification witnesses therefore start with all four assurance inputs false:

```text
egressCoverageVerified = false
directionalityVerified = false
offloadNormalizationVerified = false
preSynConnectGapClosed = false
```

The provider-neutral witness consequently emits the four expected provisional markers:

```text
egress-coverage-unverified
directionality-unverified
offload-normalization-unverified
pre-syn-connect-gap-unclosed
```

Qualification permits exactly those four markers and nothing else. Any additional global or channel validity problem — including interface drift, unknown/non-zero capture drops, ambiguous packet direction, failure to admit, or another integrity condition — fails closed. A missing provisional marker also fails, preventing accidental reintroduction of pre-seeded assurance.

Only after independent structural and real-traffic checks succeed does the qualification document derive the four final `captureAssurance=true` facts used by TEL-003.

### 6.1 Egress coverage basis

- the source role is attached only to a run-scoped Docker `--internal` network;
- namespace inventory contains exactly one non-loopback IPv4 address;
- the witness shares that exact source namespace and resolves the interface for the literal source address;
- expected and alternate targets are distinct literal addresses on the same isolated network;
- an alternate-destination real connect must be retained as alternate rather than disappearing through target filtering.

This qualifies the concrete runner/topology, not arbitrary hosts.

### 6.2 Directionality basis

The Linux witness rejects a captured SYN whose AF_PACKET packet type is not outgoing. Because provisional qualification permits only the four assurance markers, any `ambiguous-packet-direction` marker immediately fails qualification. Successful real-connect canaries therefore demonstrate outgoing-role boundary classification for the exact runner/topology.

### 6.3 SYN retransmission/normalization basis

The readiness authority requires raw SYN retransmission to be distinguished from a second `connect`/reconnect attempt. Counting raw SYN packets is insufficient.

Three ordinary real-connect canaries prove one-connect, two-independent-connect, and alternate-target classification. A fourth same-run canary additionally launches one qualification-only injector in the **exact source network namespace** with:

```text
--network container:<qualification source>
--read-only
--cap-drop=ALL
--cap-add=NET_RAW
--security-opt=no-new-privileges
<exact pinned helper image digest>
```

The injector receives no Docker socket, `NET_ADMIN`, or `SYS_ADMIN`. It sends exactly two byte-identical IPv4/TCP initial SYN packets with the same literal source/destination, source/destination port, and initial sequence.

The witness must retain both raw SYN observations while normalizing them to one initiation:

```text
rawSynPackets >= 2
totalInitiations == 1
expectedTargetInitiations == 1
alternateTargetInitiations == 0
retransmittedSynPackets == rawSynPackets - 1
```

Any different result fails qualification. This makes `offloadNormalizationVerified=true` evidence-backed for the exact SYN-only witness responsibility instead of inferring retransmission behavior from unrelated successful connects.

The canary does not claim general payload offload correctness, kernel connect-attempt auditing, or portable provider semantics.

### 6.4 Pre-SYN connect-gap basis

No qualification traffic is admitted until the witness has completed:

```text
arm -> admit -> ready acknowledgement
```

At the terminal boundary, main PR #151 drains queued AF_PACKET frames until the first existing bounded receive-inactivity timeout after close is signalled. This prevents a queued SYN from disappearing merely because the stop flag raced with `recvfrom()`.

Together these establish the reviewed admission/sealing boundary without arbitrary sleep or an unbounded wait.

## 7. Qualification canaries and retained evidence

The qualification uses a private address pool distinct from TEL-002. The source has one non-loopback IPv4 path. Expected and alternate servers are read-only, cap-dropped containers. The witness shares the source namespace, is read-only, drops all capabilities, and receives only `NET_RAW`.

Four canaries execute after readiness:

1. one expected TCP connection;
2. two independent expected TCP connections;
3. one expected plus one alternate-destination TCP connection;
4. two byte-identical initial SYN packets that must normalize to one initiation.

Every canary requires exact helper digest verification, native linux/amd64 Docker, explicit Docker Desktop rejection, available packet statistics, zero capture drops, exact provisional validity markers only, raw witness retention with SHA-256 identity, and cleanup followed by residual resource verification.

The output records both `provisionalWitnessAssurance=false` and separately derived final `captureAssurance=true`.

## 8. TEL-003 execution matrix

After qualification succeeds, the workflow executes fresh isolated TEL-002 labs for:

- positive terminating path;
- `BypassFault`;
- `EarlyActivation`;
- `FalseSettled`;
- `FalseRecovery`;
- `ScheduleLeak`;
- `HiddenRetry/Fallback` / `front-extra-connect`;
- `HiddenRetry/Fallback` / `upstream-extra-connect`;
- `CollateralTarget`;
- `ResidualStateCleanupFailure`.

Both HiddenRetry variants reuse the same `NegativeMode.HIDDEN_RETRY_FALLBACK`, and both must be rejected by the unchanged provider-neutral comparator through C10. The workflow additionally checks the project-local `hiddenRetryVariant` field to prove the intended faulty assembly actually ran; that field remains diagnostic provenance and never defines the portable verdict.

Provider API acknowledgements remain diagnostics and cannot define PASS.

## 9. Evidence retention and failure policy

The workflow retains, including on failure where available:

- runner kernel/Docker provenance;
- exact repository SHA;
- capture qualification document;
- raw qualification witness artifacts, including the duplicate-SYN canary;
- positive/negative matrix artifacts;
- one result document per matrix case;
- top-level SHA-256 manifest.

The lane fails closed on prerequisite, qualification, image identity, witness integrity, matrix execution, expected-negative rejection, cleanup, or evidence staging failure. Artifact upload success is not TEL-003 acceptance.

## 10. Governance boundary after merge

If this Work Unit is independently reviewed and later adopted, its first trusted-main run may produce a candidate terminating evidence bundle. TEL-003 remains a separate Work Unit that must identify the exact run/artifact, verify manifest identities, inspect positive and every required negative result plus raw witness evidence, confirm no evidence-invalid/infrastructure ambiguity is hidden, and record an explicit adoption or rejection decision.

The independent non-terminating packet-path mechanism class remains required before NPR-011 cross-mechanism closure and any acceptance-oriented AEP-0012 lifecycle decision.

This Work Unit does not authorize normative Spec/Schema/TCK work, provider SPI, release/publication/signing/attestation, or AEP-0012 lifecycle advancement.
