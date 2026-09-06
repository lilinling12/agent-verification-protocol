# Alpha 3 Network Control PTL-003 Packet-Path Evidence Adoption

Status: **EVIDENCE ADOPTION CANDIDATE — NO ROADMAP, CROSS-MECHANISM, NPR-011, OR AEP CLOSURE UNTIL REVIEW-CLOSED AND MAIN-ADOPTED**

Evidence baseline under review: `main@f477afeeb780cb06cd4df90aa11a4b316887c981`

Prepared: 2026-09-06

## 1. Purpose

This record independently reviews and adopts, subject to review closure and main adoption of this document, the non-terminating packet-path NPR-011 project acceptance evidence produced by the separately reviewed PTL-002 trusted-main lane.

The evidence uses the materially independent Linux network-namespace / veth / nftables packet-path mechanism required by the reviewed Network Control cross-mechanism architecture. It consumes the already-adopted provider-neutral Evidence Plan / Fixture / Result / Comparator responsibilities without sharing terminating/Toxiproxy mechanism-control code.

This is an **acceptance-evidence adoption record only**. It does not change AEP-0012 semantics or lifecycle state, does not close the cross-mechanism NPR-011 acceptance gate, does not authorize Network Control normative Spec / requirement-index / Schema / TCK work, does not introduce a generic Network backend/provider abstraction, and does not select, publish, sign, or attest a release.

The authority direction remains:

```text
AEP-0012 Proposed semantics
  -> terminating/intercepting NPR-011 project acceptance evidence  [main-adopted]
  -> non-terminating packet-path NPR-011 project acceptance evidence [this record]
  -> retained cross-mechanism portability acceptance evidence
  -> acceptance-oriented exact-head protocol re-review
  -> explicit protocol-maintainer Proposed -> Accepted decision
  -> normative Spec / requirement index / Schema / TCK
```

AEP-0012 therefore remains **Proposed**.

## 2. Exact trusted-main execution

PR #166, `fix(alpha3): hand off privileged packet evidence for retention`, was squash-merged into `main` at:

```text
f477afeeb780cb06cd4df90aa11a4b316887c981
```

GitHub verifies that merge commit as `verified=true`, `reason=valid`, with exact parent:

```text
45a58478bc9baaa86136baa14ed256acde6d93b3
```

The trusted-main push automatically started the separately reviewed packet-path lane:

- workflow: `Network Control Packet-Path Privileged Evidence`
- run number: `#5`
- run ID: `34028504186`
- job: `PTL-002 / Linux netns+nftables / amd64`
- job ID: `101473669345`
- event: `push`
- exact head: `f477afeeb780cb06cd4df90aa11a4b316887c981`
- conclusion: `SUCCESS`

The run completed every ordered gate successfully:

1. trusted exact-main checkout;
2. default-branch exact-revision guard;
3. constrained Python/dependency verification;
4. runner and Linux network provenance capture;
5. read-only Subject worker workspace preparation;
6. same-run packet-path qualification;
7. positive and all required negative packet-path cases;
8. Subject workspace cleanup;
9. execution-manifest construction and verification;
10. retained evidence-bundle upload.

No manual rerun, failed-job retry, changed evidence head, or post-hoc replacement artifact is used by this adoption candidate.

## 3. Same-run packet-path qualification

The retained qualification format is:

```text
avp-project-network-packet-path-github-qualification-v0.1
```

and reports:

```text
ready                  = true
runId                  = ptl002-qualification-34028504186-1
semanticBaselineCommit = f477afeeb780cb06cd4df90aa11a4b316887c981
localQualificationSha256 = 5ae486587544c34f5d0411862a8765211fb454d560e2c9011ae1aed16b841c67
```

The same run verified every required qualification property before the acceptance matrix was admitted:

- native Linux execution;
- privileged evaluator authority;
- required `ip`, `nft`, Python, and `setpriv` tooling;
- three distinct Subject / control-router / fixture namespaces;
- selected and non-target traffic routed through the reviewed control boundary;
- no admitted route escape;
- Subject privilege isolation and control isolation;
- selected exact-byte transport cut under the bounded observation budget;
- non-target survival while the selected cut is active;
- fresh recovery probe #1;
- fresh recovery probe #2;
- distinct stability witness;
- retry/retransmission discrimination;
- alternate-target visibility;
- residual-free cleanup.

Capture assurance reports all reviewed predicates as true:

```text
egressCoverageVerified       = true
directionalityVerified       = true
offloadNormalizationVerified = true
preSynConnectGapClosed        = true
```

Qualification remains mechanism-local infrastructure evidence. It does not itself issue a C1-C12 portable verdict.

## 4. Retained evidence bundle and independent retrieval

The successful run published exactly one packet-path evidence artifact:

- artifact ID: `9987837192`
- name: `avp-network-control-ptl002-f477afeeb780cb06cd4df90aa11a4b316887c981-34028504186-1`
- size reported by GitHub: `324236` bytes
- GitHub artifact digest: `sha256:3beee7b92d728650c9cb22fa00702d8e963900eef8a4a6dec51e223ba42896d6`
- created: `2026-09-06T10:50:56Z`
- current retention expiry: `2026-12-05T10:49:54Z`

For this adoption review, the artifact was independently retrieved from GitHub Actions and the downloaded ZIP SHA-256 was recomputed from the downloaded bytes:

```text
3beee7b92d728650c9cb22fa00702d8e963900eef8a4a6dec51e223ba42896d6
```

The recomputed digest exactly matches GitHub's artifact digest.

The archive contains `362` ZIP entries: one `MANIFEST.json` and `361` manifested evidence files.

The manifest reports:

```text
format     = avp-project-network-packet-path-github-evidence-manifest-v0.1
commit     = f477afeeb780cb06cd4df90aa11a4b316887c981
runId      = 34028504186
runAttempt = 1
files      = 361
```

Independent adoption inspection recomputed every manifest entry and confirmed:

- manifest entries: `361`;
- actual non-manifest files: `361`;
- unmanifested files: `0`;
- missing manifested files: `0`;
- SHA-256 mismatches: `0`;
- size mismatches: `0`;
- content-addressed evidence blobs checked: `340`;
- content-addressed path-versus-content digest mismatches: `0`.

Each of the nine matrix `result.json` files references three critical content-addressed objects: its sealed Evidence Plan, implementation record, and materialization provenance. All `27` references resolved uniquely within the corresponding case-local artifact store and independently matched the declared SHA-256 and size. Reference problems: `0`.

### 4.1 Retention limitation

The workflow intentionally uses finite GitHub Actions artifact retention. The current bundle is therefore **not a permanent protocol archive**.

This record preserves the exact run/artifact identity, independently recomputed archive digest, complete manifest-integrity result, semantic assessments, and materialization provenance. It does not claim that a 90-day GitHub Actions artifact is sufficient durable archival for later cross-mechanism protocol acceptance.

Before the cross-mechanism NPR-011 acceptance/re-review boundary, durable evidence archival must be explicitly reviewed or made unnecessary by a governed replacement evidence run whose identity and integrity are reviewed. That future disposition must not be silently inferred from this record.

## 5. Runner and materialization provenance

The retained runner evidence records:

- Ubuntu `24.04.4 LTS`;
- Linux kernel `6.17.0-1022-azure`, x86_64;
- Python `3.13.15`;
- iproute2 utility `6.1.0`, package `6.1.0-1ubuntu6.4`;
- nftables `1.0.9`, package `1.0.9-1ubuntu0.1`;
- util-linux / `setpriv` `2.39.3`, package `2.39.3-9ubuntu6.6`.

The positive materialization record uses:

```text
mechanism = linux-netns-veth-nftables
```

with distinct Subject, control/router, and fixture namespaces. It retains two point-to-point `/30` segments, selected port `42101`, non-target control port `42102`, the dedicated nftables table/chain identity, and ruleset snapshots before fault activation, while the fault is active, and after clear.

These Linux names, addresses, versions, commands, rule identities, and kernel/runtime details remain project evidence provenance only. They are not portable AVP semantics or mandatory third-party implementation technology.

## 6. Positive packet-path evidence

The positive case result format is:

```text
avp-project-network-packet-path-case-result-v0.1
```

The retained implementation record format is:

```text
avp-project-network-packet-path-live-result-v0.1
```

The unchanged provider-neutral assessment is:

```text
classification: SATISFIED
primaryProblem: null
secondaryProblems: []
```

It additionally records:

```text
cleanupNoninterferenceOk = true
securityProjectionOk     = true
infrastructureProblems   = []
```

The positive run retains distinct attempts for:

1. baseline;
2. pre-trigger;
3. privileged activation settlement;
4. Subject active cut;
5. non-target control;
6. recovery #1;
7. recovery #2;
8. stability.

The Subject active-cut exchange retained the portable observations:

```text
completed                = false
observationBudgetExpired = true
mismatchObserved         = false
additionalConnectAttempted = false
nativeError              = null
```

Its W-front witness retained:

```text
totalInitiations           = 1
expectedTargetInitiations  = 1
alternateTargetInitiations = 0
rawSynPackets               = 1
retransmittedSynPackets     = 0
captureDrops                = 0
validityProblems            = []
```

For this non-terminating packet-path class there is deliberately **no second provider-created upstream TCP initiation**. The selected Subject destination and fixture endpoint identify the same logical socket; forwarding through the router is not another AVP connection initiation. This is the materially important topology distinction from the terminating/intercepting class and is handled by the same topology-aware C10 predicate rather than by mechanism-name branching.

The sealed positive Evidence Plan records a finite `1,000,000,000 ns` evaluator observation budget, literal IPv4 selected endpoint `198.18.67.166:42101`, distinct non-target endpoint `198.18.67.166:42102`, and the exact AEP-0012 semantic baseline commit.

The positive evidence therefore establishes, for this reviewed packet-path mechanism binding:

- baseline exact-byte exchange succeeds;
- qualifying pre-trigger traffic succeeds;
- selected fault effect is not admitted early;
- activation settlement is independently observed by a fresh privileged attempt;
- the distinct Subject certified active-cut attempt does not complete within budget and does not mismatch;
- the non-target control path remains exchange-capable while selected cut is active;
- exactly two fresh recovery probes succeed after clear;
- a distinct stability witness succeeds;
- the certified Subject attempt has exactly one expected target initiation and no alternate target initiation;
- cleanup/noninterference and Subject/control security projection succeed.

## 7. Required negative matrix

All eight required faulty assemblies executed against the same provider-neutral comparator and were rejected without using nftables command success, rule handles, packet counters, or native socket errors as portable pass/fail authority.

| Case | Negative mode | Assessment | Primary problem |
|---|---|---|---|
| bypass-fault | `BypassFault` | `SEMANTIC_VIOLATION` | `C4:activation-settlement:exact-exchange-completed` |
| early-activation | `EarlyActivation` | `SEMANTIC_VIOLATION` | `C3:pre-trigger:exact-exchange-not-completed` |
| false-settled | `FalseSettled` | `EVIDENCE_INVALID` | `C1:missing-observation:activation-settlement` |
| false-recovery | `FalseRecovery` | `EVIDENCE_INVALID` | `C1:missing-observation:recovery-2` |
| schedule-leak | `ScheduleLeak` | `SEMANTIC_VIOLATION` | `C12:security-projection-failed` |
| hidden-retry-fallback | `HiddenRetry/Fallback` | `SEMANTIC_VIOLATION` | `C10:subject-active-cut:W-front:total-initiations=2` |
| collateral-target | `CollateralTarget` | `SEMANTIC_VIOLATION` | `C6:non-target-control:exact-exchange-not-completed` |
| residual-cleanup | `ResidualStateCleanupFailure` | `SEMANTIC_VIOLATION` | `C11:cleanup-noninterference-failed` |

Material secondary findings are also retained rather than discarded:

- `BypassFault` additionally violates C5 because the Subject active-cut exchange completes;
- `FalseRecovery` additionally lacks the distinct stability observation;
- `HiddenRetry/Fallback` additionally records one alternate-target initiation.

No negative case fabricates a comparator verdict. Each case changes one reviewed assembly behavior and submits the retained evidence to the unchanged provider-neutral assessment path.

## 8. Failed-run provenance retained as non-adopted evidence

The successful run is the fifth trusted-main execution in this packet-path evidence series. Earlier runs are deliberately retained as fail-closed engineering provenance and are **not** rewritten as successful acceptance evidence.

1. run `33973647010` — the unprivileged Subject worker could not import `acceptance.network_control.packet_path.worker`; same-run qualification failed and the matrix was blocked;
2. run `33991637439` — after process-environment binding, the Subject still could not traverse the runner workspace after UID/GID privilege drop; qualification again failed and the matrix remained blocked;
3. run `33992696183` — Subject-readable run-scoped staging fixed that boundary, after which qualification exposed an incompatible packet-path fixture role binding; the matrix remained blocked;
4. run `33993518284` — fixture-role correction allowed same-run qualification and the full nine-case matrix to succeed, but ordinary-runner manifest construction and artifact upload failed because root-produced content-addressed files remained owner-only;
5. run `34028504186` — after the mechanism-local privileged-producer to unprivileged-retention handoff was reviewed and main-adopted, qualification, all nine cases, manifest verification, and retained artifact upload all succeeded at exact main `f477afeeb780cb06cd4df90aa11a4b316887c981`.

The corrections for these failures addressed import binding, filesystem traversal, fixture role alignment, and evidence-publication permissions. They did **not** weaken AEP-0012, remove C1-C12 predicates, convert provider acknowledgement into settlement/recovery, add retries to make the positive case pass, or create a generic Network backend abstraction.

This fail-closed history is material evidence that the successful packet-path result was reached by correcting observed execution-boundary defects rather than by relaxing the portable acceptance predicates.

## 9. PTL-003 disposition candidate

The non-terminating packet-path NPR-011 acceptance-evidence Work Unit is **eligible to become review-closed for this exact packet-path mechanism/runtime evidence class** once this adoption record itself is review-closed and main-adopted.

Only after that adoption may a separate reconciliation Work Unit mark the roadmap item:

```text
produce non-terminating packet-path NPR-011 acceptance evidence against the same portable predicates
```

as completed.

This record deliberately does **not** mark that roadmap item itself. Keeping the status reconciliation separate ensures that the evidence is reviewed and adopted before repository planning state claims completion.

After packet-path adoption and roadmap reconciliation, the next legal Network Control evidence Work Unit is:

```text
execute and retain cross-mechanism NPR-011 portability acceptance evidence
```

That future Work Unit must assess the already-adopted terminating/intercepting and packet-path evidence classes together against the same portable predicates. It must not make Toxiproxy behavior, Linux netns/veth/nftables behavior, or either evidence-lab implementation normative.

## 10. Non-authorizations

This record does not authorize or claim completion of:

- cross-mechanism NPR-011 portability acceptance evidence;
- NPR-011 acceptance-gate closure as a whole;
- acceptance-oriented exact-head AEP-0012 protocol re-review;
- AEP-0012 `Proposed -> Accepted`;
- Network Control normative Spec or requirement index;
- Network Control Schema;
- execution-sensitive Network Control TCK;
- backend-neutral Network Control conformance harness;
- controlled network-fault reference implementation;
- generic Network provider/backend registry, SPI, plugin framework, or base backend abstraction;
- AEP Final transition;
- release selection or publication;
- package-index publication;
- signing or attestation publication;
- permanent evidence archival strategy.

Those remain separate governed decisions and Work Units.