# Alpha 3 Network Control TEL-003 Terminating Evidence Adoption

Status: **EVIDENCE REVIEW-CLOSED — TERMINATING/INTERCEPTING NPR-011 ACCEPTANCE EVIDENCE PRODUCED ON TRUSTED MAIN**

Adopted evidence baseline: `main@bb63d0859444d76e53743aae409f424e47178eab`

Prepared: 2026-09-04

## 1. Purpose

This record adopts the reviewed TEL-003 terminating/intercepting-class NPR-011 project acceptance evidence produced from trusted exact `main` after the TEL-001 provider-neutral evidence foundation, TEL-002 pinned Toxiproxy mechanism binding, privileged-runner qualification, and the terminating transport-contract correction were all main-adopted.

This is an **acceptance-evidence adoption record only**. It does not change AEP-0012 semantics or lifecycle state, does not authorize Network Control Spec/requirement-index/Schema/TCK work, does not introduce a generic provider/backend abstraction, and does not select, publish, sign, or attest a release.

The authority direction remains:

```text
AEP-0012 Proposed semantics
  -> terminating/intercepting NPR-011 project acceptance evidence  [this record]
  -> non-terminating packet-path NPR-011 project acceptance evidence
  -> retained cross-mechanism portability acceptance evidence
  -> acceptance-oriented exact-head protocol re-review
  -> explicit protocol-maintainer Proposed -> Accepted decision
  -> normative Spec / requirement index / Schema / TCK
```

AEP-0012 therefore remains **Proposed**.

## 2. Exact trusted-main execution

PR #155, `fix(alpha3): align terminating transport evidence contract`, was squash-merged into `main` at:

```text
bb63d0859444d76e53743aae409f424e47178eab
```

GitHub verifies that merge commit as `verified=true`, `reason=valid`, with exact parent:

```text
9924c538d9d75ab33287135940a165f4766b9a79
```

Because PR #155 changed `.github/workflows/network-control-privileged-evidence.yml`, the trusted-main push automatically started:

- workflow: `Network Control Privileged Evidence`
- run number: `#4`
- run ID: `33846543402`
- job: `TEL-003 / Toxiproxy / Linux amd64`
- job ID: `100939581732`
- event: `push`
- exact head: `bb63d0859444d76e53743aae409f424e47178eab`
- conclusion: `SUCCESS`

The run completed every ordered step successfully:

1. trusted exact-main checkout;
2. default-branch execution guard;
3. constrained Python/dependency verification;
4. runner and Docker provenance capture;
5. AF_PACKET capture qualification;
6. capture-qualification assertions;
7. pinned Toxiproxy transport qualification;
8. transport-qualification assertions;
9. positive and required negative terminating matrix;
10. execution manifest construction;
11. privileged evidence-bundle upload.

No manual rerun, failed-job retry, or changed evidence head is used by this adoption record.

## 3. Retained evidence bundle

The successful run published one evidence artifact:

- artifact ID: `9926819468`
- name: `avp-network-control-tel003-bb63d0859444d76e53743aae409f424e47178eab-33846543402-1`
- size reported by GitHub: `349539` bytes
- GitHub artifact digest: `sha256:381f28d3357c210e813f3993c620b3404f9e205cb18cd88f2ad2ae67f1c37d02`
- downloaded ZIP SHA-256 independently recomputed during adoption review: `381f28d3357c210e813f3993c620b3404f9e205cb18cd88f2ad2ae67f1c37d02`
- created: `2026-09-04T07:01:07Z`
- current GitHub retention expiry: `2026-12-03T06:57:16Z`

The downloaded bundle contains `453` files total: one `MANIFEST.json` plus `452` manifested evidence files.

Independent adoption review recomputed every manifested file and confirmed:

- manifest commit equals exact evidence main SHA;
- manifest entries: `452`;
- actual non-manifest files: `452`;
- no actual file is missing from the manifest;
- no manifest path is absent from the bundle;
- every path has the exact recorded size;
- every path has the exact recorded SHA-256;
- integrity problems: `0`.

Each matrix `result.json` references a content-addressed `implementationRecord` and `materializationProvenance`. All `20` referenced objects resolved uniquely under their case-local artifact store and independently matched their declared SHA-256 and size. No dangling result reference was found.

### 3.1 Retention limitation

The workflow intentionally uses finite GitHub Actions artifact retention. The current artifact is therefore not a permanent protocol archive.

This TEL-003 record preserves the exact run/artifact identity, manifest integrity result, and semantic assessment, but it does **not** claim that a 90-day GitHub artifact is sufficient durable archival for final cross-mechanism protocol acceptance.

Before the later NPR-011 cross-mechanism acceptance/re-review boundary, durable evidence archival must be explicitly reviewed or otherwise made unnecessary by a governed replacement evidence run. That future decision must not be silently inferred from this adoption record.

## 4. Capture qualification evidence

AF_PACKET qualification v0.3 succeeded before any Toxiproxy evidence matrix execution.

The qualification established the reviewed capture-assurance basis, including:

- egress coverage;
- directionality;
- offload/retransmission normalization;
- pre-SYN observation-gap closure;
- raw capture retention;
- zero-drop/valid capture accounting.

The same run included the duplicate-SYN normalization canary and passed the workflow assertions. This proves the reviewed witness can normalize retransmission of one initiation without automatically treating a duplicate initial SYN as a second application initiation.

No terminating evidence case was permitted to execute until these capture assertions were satisfied.

## 5. Pinned Toxiproxy transport qualification

Before the full C1-C12 matrix, the same exact-main run executed the project-local pinned-provider transport qualification introduced by PR #155.

Reviewed concrete artifacts remained:

### Toxiproxy

- version: `2.12.0`
- source commit: `3ccd6a79cbc6c6a72b884d295ad314b75cdf3962`
- OCI index: `sha256:9378ed52a28bc50edc1350f936f518f31fa95f0d15917d6eb40b8e376d1a214e`
- linux/amd64 platform manifest: `sha256:a3e244375123dad8849091bcc59775e188624d3f602db01901f9af855682fef8`

### Helper image

- reviewed tag: `3.13.13-slim-bookworm`
- OCI index: `sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f`
- linux/amd64 platform manifest: `sha256:f576b530293e74140ea91d262232648d5c4f45640a95ec447757701bfcacf034`

The transport qualification result format is:

```text
avp-project-toxiproxy-transport-qualification-v0.1
```

Its reviewed three-attempt sequence succeeded exactly:

| Qualification attempt | completed | budget expired | front | upstream | validity |
|---|---:|---:|---:|---:|---|
| baseline pass-through | true | false | 1 | 1 | none |
| subject active cut (`timeout=0`) | false | true | 1 | 1 | none |
| fresh recovery | true | false | 1 | 1 | none |

For baseline and recovery, exact Fixture evidence and exchange diagnostics were retained. The active-cut attempt retained exchange diagnostics and bounded non-authoritative Fixture diagnostics. Cleanup returned exactly:

```json
{"ok": true, "problems": []}
```

This qualification proves only that the exact pinned provider/runtime can carry the already-reviewed evidence mechanics. It does not define portable semantics and does not issue a C1-C12 protocol verdict.

## 6. Positive terminating evidence

The positive TEL-003 result uses implementation record format:

```text
avp-project-toxiproxy-terminating-evidence-v0.1
```

and comparator revision:

```text
npr011-portable-c1-c12-v0.1
```

The provider-neutral assessment is:

```text
classification: SATISFIED
primaryProblem: null
secondaryProblems: []
```

The retained portable observation snapshot has no:

- evidence-validity problems;
- infrastructure problems;
- unsupported-materialization problems.

It also records:

```text
cleanupNoninterferenceOk = true
securityProjectionOk     = true
```

### 6.1 Exact positive phase behavior

| Phase | completed | budget expired | front | upstream | alternate | validity |
|---|---:|---:|---:|---:|---:|---|
| baseline | true | false | 1 | 1 | 0 | none |
| pre-trigger | true | false | 1 | 1 | 0 | none |
| activation-settlement | false | true | 1 | 1 | 0 | none |
| subject-active-cut | false | true | 1 | 1 | 0 | none |
| non-target-control | true | false | 1 | 1 | 0 | none |
| recovery-1 | true | false | 1 | 1 | 0 | none |
| recovery-2 | true | false | 1 | 1 | 0 | none |
| stability | true | false | 1 | 1 | 0 | none |

The non-target control attempt is bound to the distinct logical path:

```text
network-control-selected-path::non-target-control
```

Every listed attempt has `mismatchObserved=false` and empty witness/attempt validity problems.

This establishes, for the reviewed terminating mechanism class on this exact run:

- no effect before trigger;
- fault settlement proven by a fresh privileged attempt rather than provider API acknowledgement;
- a distinct Subject-side fresh active-cut attempt;
- non-target path remains baseline-capable while the selected cut is active;
- clear is followed by exactly two fresh recovery probes and one distinct stability witness;
- exactly one expected front initiation and one expected upstream initiation for every positive certified attempt;
- no alternate-target initiation;
- clean noninterference teardown;
- reviewed Subject/control security projection.

## 7. Required negative matrix

The full required negative matrix was executed against the same provider-neutral comparator and every faulty assembly was rejected.

| Case | Negative mode | Assessment | Primary problem |
|---|---|---|---|
| bypass-fault | `BypassFault` | `SEMANTIC_VIOLATION` | `C4:activation-settlement:exact-exchange-completed` |
| early-activation | `EarlyActivation` | `SEMANTIC_VIOLATION` | `C3:pre-trigger:exact-exchange-not-completed` |
| false-settled | `FalseSettled` | `EVIDENCE_INVALID` | `C1:missing-observation:activation-settlement` |
| false-recovery | `FalseRecovery` | `EVIDENCE_INVALID` | `C1:missing-observation:recovery-2` |
| schedule-leak | `ScheduleLeak` | `SEMANTIC_VIOLATION` | `C12:security-projection-failed` |
| hidden-retry front | `HiddenRetry/Fallback` / `front-extra-connect` | `SEMANTIC_VIOLATION` | `C10:subject-active-cut:W-front:total-initiations=2` |
| hidden-retry upstream | `HiddenRetry/Fallback` / `upstream-extra-connect` | `SEMANTIC_VIOLATION` | `C10:subject-active-cut:W-upstream:total-initiations=2` |
| collateral-target | `CollateralTarget` | `SEMANTIC_VIOLATION` | `C6:non-target-control:exact-exchange-not-completed` |
| residual-cleanup | `ResidualStateCleanupFailure` | `SEMANTIC_VIOLATION` | `C11:cleanup-noninterference-failed` |

Important secondary observations include:

- bypass-fault additionally violates C5 because the Subject active-cut exchange completes;
- front HiddenRetry produces two front and two upstream expected-target initiations and is rejected by C10;
- upstream HiddenRetry leaves the front count at one while independently producing two upstream expected-target initiations, proving the second required retry/fallback negative does not merely duplicate the front-side helper;
- false-recovery additionally lacks the required stability observation and is fail-closed as evidence-invalid.

No negative assembly is accepted because a provider API call failed or because provider-native state says it should fail. Rejection remains owned by the unchanged provider-neutral comparator.

## 8. Post-merge ordinary validation

The same exact main commit also passed all ordinary push-triggered validation:

| Gate | Run | Result |
|---|---:|---|
| CI | #907 (`33846543295`) | SUCCESS |
| Relational Parity | #300 (`33846543538`) | SUCCESS |
| Browser Reference | #173 (`33846543298`) | SUCCESS |
| Network Control Privileged Evidence | #4 (`33846543402`) | SUCCESS |

CI #907 includes Python 3.11/3.12/3.13 Quality, reproducible packaging, installed-wheel governed TCK conformance, PostgreSQL 17.11/18.6, and MySQL 8.4.11/9.7.2 lanes. Relational Parity #300 passed both canonical PostgreSQL/MySQL pairings. Browser Reference #173 passed the real Playwright/Chromium provider foundation suite.

These unrelated regression gates matter because TEL-003 evidence adoption must not silently destabilize existing accepted resource profiles or package/conformance behavior.

## 9. Failed-run provenance retained as non-adopted evidence

The successful run is the fourth privileged execution in this evidence series. Earlier runs are deliberately not rewritten as success:

1. run `33824673863` — failed before AF_PACKET qualification because helper-image digest verification incorrectly treated Docker `RepoDigests` string representation as the identity oracle;
2. run `33833695091` — AF_PACKET qualification succeeded, then pinned Toxiproxy `/version` parsing incorrectly expected plaintext instead of the reviewed JSON response;
3. run `33840868116` — qualification and provider prerequisites succeeded, then the real positive path exposed a deterministic incompatibility between pre-response TCP half-close framing and pinned Toxiproxy stream forwarding;
4. run `33846543402` — after the reviewed corrections, capture qualification, provider transport qualification, full positive/negative matrix, manifest construction, and evidence upload all succeeded on exact main.

PRs #153, #154, and #155 corrected those concrete execution-boundary defects without changing AEP-0012, C1-C12, or the portable comparator.

This history is material evidence that the successful result was reached through fail-closed correction of observed integration defects rather than by weakening the predicates until the provider passed.

## 10. TEL-003 disposition

The terminating/intercepting NPR-011 acceptance-evidence Work Unit is **review-closed for this exact provider/runtime evidence class**.

The project may therefore record the roadmap item:

```text
produce terminating/intercepting-class NPR-011 acceptance evidence against the reviewed architecture
```

as completed once this adoption record itself is review-closed and main-adopted.

This disposition does **not** establish cross-mechanism portability by itself. The materially independent non-terminating packet-path evidence class remains mandatory.

The next legal Network Control evidence Work Unit after this adoption is therefore:

```text
produce non-terminating packet-path NPR-011 acceptance evidence against the same portable predicates
```

That work must consume the same provider-neutral Evidence Plan / Result / Fixture / Comparator responsibilities and must not retroactively make Toxiproxy behavior normative.

## 11. Non-authorizations

This record does not authorize or claim completion of:

- non-terminating packet-path NPR-011 evidence;
- retained cross-mechanism portability acceptance evidence;
- acceptance-oriented exact-head AEP-0012 protocol re-review;
- AEP-0012 `Proposed -> Accepted`;
- Network Control normative Spec or requirement index;
- Network Control Schema;
- execution-sensitive Network Control TCK;
- backend-neutral Network Control conformance harness;
- controlled network-fault reference implementation;
- generic Network provider/backend SPI or plugin architecture;
- AEP Final transition;
- release selection or publication;
- package-index publication;
- signing or attestation publication;
- permanent evidence archival strategy.

Those remain separate governed decisions and Work Units.