# Alpha 2 Baseline Reconciliation Closure Audit

Status: **NOT READY FOR STABLE RELEASE DECISION**

Audit date: 2026-08-17

Audit baseline: `main@a14bd9e28d672c7b4230bd7e5162f39e2196bb63`

Released protocol evidence point: `v0.3.0-rc.1` → `ef199124017b0dcc8c4a966d00c4f407760f9a06`

## Purpose

This audit checks whether the repository is ready to move from Alpha 2 protocol finalization into a stable `v0.3.0` release decision. It is deliberately broader than AEP lifecycle finalization.

AEP-0001 through AEP-0008 are already `Final`. This audit does not reopen those decisions. It verifies that the repository's historical design provenance, reconciliation records, normative inventory, conformance assets, and reference implementation remain traceable enough to support a stable-release decision without silently losing design intent or promoting implementation behavior into protocol semantics.

The governing authority direction remains:

```text
historical design
    -> reconciliation
    -> AEP / normative specification
    -> schemas
    -> language-neutral conformance / TCK
    -> reference implementation
```

A green implementation CI run is necessary evidence, but it is not sufficient evidence of design closure.

## Evidence inspected

The audit inspected the current repository surfaces at the audit baseline, including:

- `docs/design/alpha-v0.1/README.md`;
- `docs/design/alpha-v0.1/CLASSIFICATION.md`;
- `docs/design/alpha-v0.1/SOURCE-MANIFEST.json`;
- `docs/reconciliation/v0.1/` decisions and matrices;
- `rfcs/AEP-0001` through `AEP-0008`;
- `spec/` and domain requirement indexes;
- `conformance/tck/` profile registration;
- `src/avp_ref/` reference-runtime surfaces;
- `ROADMAP.md`;
- `docs/RELEASE_PROCESS.md`;
- published `v0.3.0-rc.1` release evidence;
- post-Finalization `main` CI.

The original historical source documents referenced by `SOURCE-MANIFEST.json` were also located in the project-maintainer source library and independently checked by file size and SHA-256 before this audit. All 20 source documents matched the manifest's recorded byte count and SHA-256. That external availability does not make them normative and does not substitute for repository provenance closure.

## Finding 1 — historical baseline tree is incomplete

**Severity: stable-release blocker**

`SOURCE-MANIFEST.json` declares 20 immutable historical source documents and assigns each one a repository `target_path` under `docs/design/alpha-v0.1/`.

At the audit baseline, the Git tree under `docs/design/alpha-v0.1/` contains only:

- `README.md`;
- `CLASSIFICATION.md`;
- `SOURCE-MANIFEST.json`.

The 20 source documents named by the manifest are not present at their declared target paths.

This is a provenance and auditability defect, not a normative-protocol defect. The source texts remain explicitly `historical-non-normative`, but the repository currently cannot independently demonstrate the complete design input that its reconciliation framework says was reviewed.

### Required closure

Before stable-release eligibility can be declared:

1. restore all 20 historical source documents at the exact manifest `target_path` values;
2. preserve exact bytes; do not edit historical text while restoring it;
3. verify, for every restored file:
   - byte count;
   - SHA-256;
   - Git blob SHA-1;
4. reject the restoration if any identity differs from `SOURCE-MANIFEST.json`;
5. add an automated repository check so a future deletion or mutation of the immutable baseline fails CI;
6. keep the baseline explicitly non-normative.

Restoration must use a byte-safe import path. Copying large historical files through a lossy or truncating text transport is not acceptable even when the rendered Markdown appears plausible.

## Finding 2 — normative surface inventory drift

**Severity: stable-release blocker; low implementation risk**

The current Git tree contains the normative `spec/trust/` domain and AEP-0008 is `Final`. The registered TCK also contains the Artifact Trust profile.

However, the `spec/README.md` current normative-surface inventory does not list `trust/`.

This does not alter protocol semantics, but it makes the normative entry point incomplete. A stable release must not require consumers to discover a Final normative domain only by walking the tree.

### Required closure

Add `trust/` to the normative-surface inventory with language consistent with AEP-0008 and the existing Artifact Trust specification. This is an index/documentation correction only; it must not introduce new requirements.

## Finding 3 — no single global disposition ledger for the historical design set

**Severity: stable-release blocker**

`CLASSIFICATION.md` assigns an initial disposition to historical documents 03 through 21 and ADR-001. The current reconciliation directory contains domain decisions and matrices for the protocol surfaces promoted during Alpha 1 and Alpha 2.

What is still missing is a single closure artifact that proves every material historical design area was intentionally handled rather than merely omitted during implementation.

For stable-release review, each historical area must have an explicit disposition such as:

- `PROMOTED` — retained as current normative behavior;
- `SPLIT` — decomposed into multiple current normative/profile surfaces;
- `SUPERSEDED` — replaced by a later governed design;
- `NON_NORMATIVE` — intentionally retained as architecture, methodology, tooling, SDK, product, or implementation guidance;
- `DEFERRED` — intentionally postponed to a future protocol/profile phase;
- `REJECTED` — intentionally not carried forward, with rationale.

The ledger must link, where applicable, to AEPs, normative specification paths, requirement IDs, schemas, TCK cases/profiles, and reference-runtime evidence.

## Finding 4 — historical profile names and current TCK profiles require an explicit mapping

**Severity: stable-release blocker**

The historical AVP design described profile groupings such as Core, Environment, Snapshot, Verification, Replay, Chaos, and Telemetry. Alpha 2 now exposes a more precise registered profile set around Core, Evidence, Oracle, Security, Scenario, Environment, MCP interoperability, OpenTelemetry mapping, Subject Adapter interoperability, and Artifact Trust.

This evolution is expected and is not itself a defect. It becomes a defect only if the repository cannot explain whether historical profile responsibilities were promoted, split, moved to another authority domain, made non-normative, or deferred.

The global disposition ledger must therefore include profile-responsibility mapping. It must not restore obsolete profile names merely for compatibility with an unpublished historical draft.

## Finding 5 — protocol version and reference-distribution version are distinct

**Severity: release-documentation requirement**

The current normative profiles use protocol/profile version `v0.1`, while the Python reference distribution uses the independent package/repository release line `0.3.0rc1` for the published release candidate.

This distinction is valid and should remain explicit:

```text
AVP protocol/profile line: v0.1
reference distribution / repository release: v0.3.0-rc.1 -> v0.3.0 candidate
```

Stable release notes must not accidentally describe the normative protocol itself as "AVP Protocol v0.3.0" unless a separate governed decision intentionally changes protocol versioning.

## Finding 6 — implementation health is green but does not close design traceability

**Severity: informational until the alignment audit**

The post-Finalization `main` CI run passed after AEP-0001 through AEP-0008 were merged as `Final`. Existing quality gates already exercise Python 3.11/3.12/3.13 quality, reproducible package construction, clean installed-wheel behavior, the complete registered TCK profile set, and release-evidence generation.

This is strong implementation and conformance evidence.

The remaining question is different: for every normative `MUST` / `MUST NOT`, does the current requirement index and TCK provide the intended portable coverage, and does the reference runtime implement that behavior without defining additional protocol semantics of its own?

That question requires a dedicated design/spec/conformance/runtime alignment audit after the historical disposition ledger is complete.

## Stable-release closure gates

Stable `v0.3.0` release readiness must remain blocked until all of the following are true:

- [ ] all 20 historical baseline documents are restored byte-for-byte and automatically integrity-checked;
- [x] the missing `trust/` normative-surface inventory entry is corrected in the closure-audit change set;
- [ ] a global historical-design disposition ledger covers documents 03–21 and ADR-001;
- [ ] historical profile responsibilities are explicitly mapped to current profiles/domains or intentional non-goals/deferred work;
- [ ] AEP ↔ spec ↔ requirement-index ↔ schema ↔ TCK traceability is audited for all Final Alpha 2 domains;
- [ ] spec/TCK ↔ reference-runtime alignment is audited without treating Python behavior as normative authority;
- [ ] any discovered semantic gap is resolved through the normal reconciliation/AEP lifecycle rather than by weakening schemas or TCK;
- [ ] the resulting stable-release eligibility audit concludes `READY` or `READY WITH NON-BLOCKING GAPS`;
- [ ] exact-main CI and governance checks are green on the final release-candidate source.

## Decision

**Alpha 2 protocol finalization remains valid, but stable `v0.3.0` release decision is not yet eligible.**

The next repository phase is **Alpha 2 Baseline Reconciliation Closure**, not stable publication.

The immediate execution order is:

1. byte-safe historical baseline restoration + automated integrity enforcement;
2. global historical-design disposition ledger;
3. full normative/conformance/runtime alignment audit;
4. stable-release eligibility audit;
5. only then, a separate maintainer stable-release decision.

No item in this audit authorizes stable `v0.3.0`, package-index publication, or Alpha 3 implementation.
