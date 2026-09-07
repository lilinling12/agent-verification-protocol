# Alpha 3 Network Control NPR-011 Cross-Mechanism Portability Acceptance

Status: **EVIDENCE ACCEPTANCE CANDIDATE — NO ROADMAP, NPR-011, AEP, SPEC, SCHEMA, TCK, HARNESS, OR RELEASE CLOSURE UNTIL REVIEW-CLOSED AND MAIN-ADOPTED**

Candidate parent baseline: `main@0ccac4339ed4c8f773b6413428e3df3b15f6b79e`

AEP: `rfcs/AEP-0012-network-control-resource-profile.md` — **Proposed**

Governing non-normative evidence design:

- `docs/design/alpha3-network-control-cross-mechanism-evidence-architecture.md`;
- `docs/design/alpha3-network-control-npr011-evidence-contract-detailed-design.md`;
- `docs/design/alpha3-network-control-npr011-evidence-contract-traceability.md`.

Independently adopted source evidence:

- terminating/intercepting TEL-003 adoption:
  `docs/acceptance/alpha3-network-control-terminating-evidence-tel003-adoption.md`;
- non-terminating packet-path PTL-003 adoption:
  `docs/acceptance/alpha3-network-control-packet-path-evidence-ptl003-adoption.md`.

This record is project acceptance evidence. It does not create or amend Network
Control protocol semantics.

## 1. Acceptance question

The two required NPR-011 mechanism classes have already produced independent,
main-adopted evidence. Independent green evidence is necessary but is not by
itself cross-mechanism portability evidence.

This Work Unit asks the stronger question:

> When the retained terminating/intercepting and non-terminating packet-path
> evidence are independently integrity-verified, rebound to the same exact
> AEP-0012 semantic source, and reassessed by the current provider-neutral
> topology-aware comparator, do both classes satisfy the same positive portable
> predicates and reject every required faulty assembly through the same portable
> predicate families without provider-name branching?

The candidate evidence answers **yes**.

This answer remains a candidate until the PR is review-closed and main-adopted.

## 2. Why retained-evidence reassessment is valid

The detailed evidence design explicitly permits later comparator reassessment when
all observations required by the later comparator were retained. It also requires
a new live run when a later semantic question needs an observation that the old
bundle did not retain.

A new live run is not required for this candidate because:

1. AEP-0012's exact semantic source bytes did not change between the two source
   executions or the candidate parent baseline;
2. the later topology-aware C10 comparator needs only endpoint topology plus the
   already-retained initiation observations;
3. TEL-003 retained independent Subject-side and upstream initiation evidence;
4. PTL-003 retained Subject-side initiation evidence and a sealed same-socket
   packet-path topology, for which a fabricated second upstream TCP initiation is
   specifically forbidden;
5. all C1-C12 observations required by the current comparator are present;
6. source bundle, manifest, content-addressed record, attempt, exchange, witness,
   and plan identities remain verifiable from the retained source artifacts used
   to construct this candidate.

The reassessment is therefore recorded as `retained-evidence`; it is not presented
as a fresh behavioral execution.

## 3. Exact source evidence and integrity

### 3.1 Terminating/intercepting source

TEL-003 trusted-main evidence:

- source commit: `bb63d0859444d76e53743aae409f424e47178eab`;
- workflow run: `33846543402`;
- artifact ID: `9926819468`;
- exact ZIP SHA-256:
  `381f28d3357c210e813f3993c620b3404f9e205cb18cd88f2ad2ae67f1c37d02`;
- manifest format: `avp-project-tel003-github-evidence-manifest-v0.1`;
- manifest coverage independently reverified in this Work Unit: **452 / 452**
  payload files.

The source matrix contains one positive case and the eight required negative
families. `HiddenRetry/Fallback` deliberately has two terminating variants:

- `front-extra-connect`;
- `upstream-extra-connect`.

The second variant is required by the detailed design so upstream retry evidence
cannot be reduced to fixture `accept()` accounting.

### 3.2 Non-terminating packet-path source

PTL-003 trusted-main evidence:

- source commit: `f477afeeb780cb06cd4df90aa11a4b316887c981`;
- workflow run: `34028504186`;
- artifact ID: `9987837192`;
- exact ZIP SHA-256:
  `3beee7b92d728650c9cb22fa00702d8e963900eef8a4a6dec51e223ba42896d6`;
- manifest format:
  `avp-project-network-packet-path-github-evidence-manifest-v0.1`;
- manifest coverage independently reverified in this Work Unit: **361 / 361**
  payload files.

For every PTL retained attempt consumed by reassessment, the loader verifies the
content-addressed attempt, exchange, normalized witness, and raw witness
references. It also verifies that the normalized witness embeds the exact retained
raw-witness bytes and that attempt identity can be reproduced from the sealed run,
phase, ordinal, path, exchange-program identity, and retained challenge.

## 4. Semantic-source identity

The source plans record different repository commits, so commit equality is not
used as a shortcut for semantic equality.

The exact `rfcs/AEP-0012-network-control-resource-profile.md` Git blob at:

- TEL source commit `bb63d085...`;
- PTL source commit `f477afe...`;
- candidate parent `0ccac433...`;

is the same immutable Git object:

`0b5ebdddb45533cf91a7bc264dcfe7548b54391c`

Therefore the two executions and this reassessment bind the same exact AEP-0012
semantic source bytes even though their repository commits differ.

If that Git blob identity differed, this Work Unit would fail closed rather than
normalize the difference away.

## 5. Comparator lineage

Historical comparator source identity is intentionally not misrepresented as
byte-identical:

- TEL source comparator Git blob:
  `05c4025f8ed839e367683f736d8822c13fe1bc92`;
- PTL source comparator Git blob:
  `39169f40083e204560606cd9db0d8f1a1dda57bd`;
- current candidate-parent comparator Git blob:
  `39169f40083e204560606cd9db0d8f1a1dda57bd`.

PR #159 made C10 topology-aware. A terminating/intercepting plan binds distinct
Subject-visible and upstream fixture socket endpoints and therefore requires an
independent upstream initiation observation. A non-terminating packet-path plan
binds the same socket endpoint on both plan positions and therefore must not
fabricate a second TCP connection solely to fit terminating evidence shape.

For that reason, cross-mechanism acceptance is established by **reassessing both
retained source classes with the current comparator**, not by claiming both
historical runs used identical comparator bytes.

The current comparator remains provider-neutral. Its topology decision is derived
from sealed literal endpoint identity, not from `toxiproxy`, `nftables`, provider
names, or mechanism labels.

## 6. Portable plan compatibility

The retained plans are not required to be byte-identical across materially
independent labs. Provider-neutral portability is checked at the semantic fields
that affect the comparator and canonical matrix.

Across all retained cases the reassessor verifies:

- one exact AEP semantic path and Git-blob identity;
- the same finite evaluator-owned observation budget: `1,000,000,000 ns`;
- the same ordered portable phase program:
  baseline, pre-trigger, trigger, activation-settlement, subject-active-cut,
  non-target-control, clear, recovery-1, recovery-2, stability,
  cleanup-noninterference;
- a materialized selected logical path;
- a materialized non-target control path;
- literal IP/TCP endpoints validated before comparator execution;
- the same eight required negative families.

Mechanism-local design revisions, exchange-program IDs, literal addresses, ports,
witness technologies, and controller diagnostics are retained as evidence
provenance and are **not** compared as portable value equality. They are also not
silently erased: each case keeps its exact sealed plan in the derived record.

## 7. Current-comparator reassessment results

The current topology-aware comparator was applied to the normalized retained
observations for every source case, not to the historical result label alone.

| Portable family | Terminating/intercepting | Packet path |
| --- | --- | --- |
| Positive | `SATISFIED` | `SATISFIED` |
| `BypassFault` | `SEMANTIC_VIOLATION` — C4 | `SEMANTIC_VIOLATION` — C4 |
| `EarlyActivation` | `SEMANTIC_VIOLATION` — C3 | `SEMANTIC_VIOLATION` — C3 |
| `FalseSettled` | `EVIDENCE_INVALID` — missing activation-settlement | `EVIDENCE_INVALID` — missing activation-settlement |
| `FalseRecovery` | `EVIDENCE_INVALID` — missing recovery-2 | `EVIDENCE_INVALID` — missing recovery-2 |
| `ScheduleLeak` | `SEMANTIC_VIOLATION` — C12 | `SEMANTIC_VIOLATION` — C12 |
| `HiddenRetry/Fallback` | `SEMANTIC_VIOLATION` — C10 at W-front **and** W-upstream variants | `SEMANTIC_VIOLATION` — C10 at W-front |
| `CollateralTarget` | `SEMANTIC_VIOLATION` — C6 | `SEMANTIC_VIOLATION` — C6 |
| `ResidualStateCleanupFailure` | `SEMANTIC_VIOLATION` — C11 | `SEMANTIC_VIOLATION` — C11 |

All **19** retained source cases were reassessed:

- 10 terminating/intercepting cases;
- 9 packet-path cases.

Every current-comparator assessment exactly matched the historical source
classification and primary/secondary problem sequence. More importantly for
cross-mechanism portability, both mechanism classes agree at the portable
negative-family / C-predicate level while preserving the extra terminating
upstream-retry proof required by its topology.

A negative family is never allowed to count as acceptance by failing to execute:
missing required evidence remains `EVIDENCE_INVALID`, and no required negative may
self-certify as `SATISFIED`.

## 8. Retained derived reassessment record

The candidate adds:

`docs/acceptance/evidence/alpha3-network-control-cross-mechanism-npr011-v0.1.json.gz.b64`

Retained text-archive identity:

- archive encoding: deterministic gzip of the exact JSON, then one-line base64;
- archive size: `18773` bytes;
- archive SHA-256:
  `30f2da733781f12827ee49f0ea1aace56ba2992a20a017cb806e66af3a50f079`.

Decoded exact reassessment identity:

- JSON size: `132654` bytes;
- JSON SHA-256:
  `b768f6f6d96327cffa550c0f6db1f0b35ff48696362e4113766cce7195ab28ac`;
- format:
  `avp-project-network-cross-mechanism-reassessment-v0.1`.

The text archive avoids an opaque binary Git blob while preserving the exact
reassessment bytes. The decoded record intentionally retains enough
provider-neutral material for later
comparator reassessment without requiring the GitHub Actions ZIPs to remain
online:

- source artifact/run/commit/manifest identities;
- source result and implementation-record references;
- original comparator lineage;
- exact sealed plan document for every case;
- normalized portable C1-C12 observations for every case;
- top-level source result / implementation-record / materialization-provenance references;
- whole source ZIP / manifest identities used to verify deeper raw lineage during construction;
- historical assessment;
- current reassessment;
- negative-family and terminating hidden-retry-variant identity;
- exact AEP semantic-source Git blob;
- exact current comparator Git blob.

Ordinary CI can therefore re-run the current comparator from the committed
derived record and fail closed on semantic-source drift, comparator-input drift,
negative-family loss, or retained assessment drift.

### 8.1 Raw-source retention boundary

This derived record does **not** pretend to be a byte-for-byte archival copy of
every raw packet frame, provider diagnostic, or source ZIP.

The original source ZIPs were independently integrity-verified against their
GitHub artifact digests and complete manifests before this record was generated.
Their exact identities remain recorded above and in the two main-adopted source
adoption documents. GitHub Actions artifact retention is finite.

The committed derived record permanently retains the normalized observations
needed by the current provider-neutral comparator plus their source lineage. It
supports later **portable reassessment**. It does not claim to provide permanent
raw-forensic replay once the external source artifact expires.

If a future semantic/comparator change requires a raw observation not represented
in the derived record and the original source bytes are no longer retrievable, the
detailed design's rerun rule applies: the project must run new live evidence
rather than infer the missing fact.

## 9. Fail-closed implementation properties

`tests/acceptance/network_control/cross_mechanism.py` is evidence-only code and:

- never activates or clears a network fault;
- never imports a mechanism controller;
- never introduces `BaseNetworkBackend`, registry, SPI, plugin, or provider
  capability abstraction;
- verifies whole-ZIP SHA-256 before reading source evidence;
- rejects duplicate/unsafe/symlink ZIP paths and bounded-size violations;
- verifies complete exact manifest coverage;
- verifies content-addressed reference digest and size;
- reconstructs sealed plans through the existing provider-neutral `EvidencePlan`;
- uses the unchanged `compare_portable_evidence` comparator;
- derives C10 topology from literal socket endpoints rather than mechanism name;
- preserves Evidence Validity / semantic-failure separation;
- requires one positive plus all eight reviewed negative families in each class;
- requires both terminating hidden-retry witness boundaries;
- emits deterministic exact JSON;
- re-verifies the emitted record using only its retained portable evidence.

The CLI additionally verifies the current repository Git-blob identities for
AEP-0012 and `portable_comparator.py` before producing a record.

## 10. Candidate disposition

At this candidate head, the cross-mechanism evidence is **coherent** under the
reviewed project evidence architecture:

1. both materially independent mechanism classes have independently adopted
   behavioral evidence;
2. both bind the same exact AEP-0012 semantic source bytes;
3. all required current-comparator observations were retained;
4. current topology-aware C1-C12 reassessment passes the positive case for both;
5. every mandatory faulty assembly is rejected through the reviewed portable
   predicate family;
6. terminating upstream retry evidence remains independently exercised;
7. the derived cross-mechanism reassessment is retained in deterministic,
   self-reassessable form.

This is sufficient for **candidate** closure of the ROADMAP evidence milestone
only after exact-head review, required CI/governance gates, squash merge, and
exact-main post-merge validation.

This PR itself must not mark the ROADMAP item complete. Following the TEL/PTL
precedent, ROADMAP reconciliation remains a separate Work Unit after main adoption.

## 11. Non-authorizations

This candidate does not authorize or modify:

- AEP-0012 `Proposed -> Accepted`;
- AEP-0012 `Final`;
- the acceptance-oriented exact-head protocol re-review gate;
- Network Control normative Spec or requirement index;
- Network Control Schema;
- language/provider-neutral Network Control TCK;
- backend-neutral Network Control conformance harness;
- Network Control reference implementation;
- a generic provider backend/SPI/plugin/registry;
- Toxiproxy or Linux netns/veth/nftables as third-party protocol requirements;
- release selection, versioning, tagging, publication, signing, or attestation.

The next legal action after this evidence is review-closed, main-adopted, and
post-merge-green is a separate ROADMAP reconciliation Work Unit. Only after that
may the separately governed acceptance-oriented exact-head AEP-0012 protocol
re-review begin.
