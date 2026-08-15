# Alpha 2 Acceptance Audit and Release-Candidate Readiness

Status: **FINAL VALIDATION — NOT YET READY FOR RC PREPARATION**

Integrated protocol baseline: `65d7c7413d7fe2def4d9d1593fdeb09753da6324` on `main`.

This document audits Alpha 2 as an integrated protocol/conformance candidate. It does not make a release, change protocol semantics, authorize a pull-request merge, or treat reference implementation behavior as normative authority.

## 1. Authority and scope

The audit preserves the repository authority direction:

```text
historical design -> reconciliation -> AEP/RFC -> normative spec -> schema -> TCK -> reference runtime -> acceptance audit -> readiness
```

The Alpha 2 protocol/conformance scope is:

- Scenario / ScenarioInstance;
- Environment;
- MCP verification interoperability;
- OpenTelemetry mapping interoperability;
- Subject Adapter interoperability;
- Artifact Trust / attestation;
- the pre-existing Alpha 1 Core, Evidence, Oracle, and Security contracts that those profiles compose with.

Reference-only capabilities, including concrete Python APIs, cryptographic fixtures, hosted services, database adapters, browser runtimes, containers, microVMs, and production signing backends, are not silently promoted into protocol release requirements.

## 2. Integration result

The authorized stacked integration completed in dependency order:

1. PR #31 Subject Adapter was final-head revalidated and squash-merged into `main` as `1823d877409386d84fea502fa3d7265fb85060e3`.
2. PR #32 Artifact Trust was retargeted/rebased onto that exact main baseline so its diff contained only Artifact Trust changes.
3. The rebased #32 candidate passed fresh Quality / Package / Governance gates, had `behind_by=0`, and had no unresolved review threads.
4. PR #32 was squash-merged into `main` as `65d7c7413d7fe2def4d9d1593fdeb09753da6324`.
5. PR #33 was then retargeted/rebased onto that exact integrated main baseline and now contains only Alpha 2 audit/governance material.

No #33 merge, tag, GitHub Release, package publication, or AEP `Final` transition is authorized by this integration.

## 3. Release-process gates

| Gate | Current evidence | Status |
|---|---|---|
| Protocol stack integrated into `main` | #31 and #32 were authorized, revalidated, and squash-merged in dependency order | **PASS** |
| Integrated-main CI green | `main@65d7c741...` push CI #357 completed successfully | **PASS** |
| Quality matrix | Python 3.11, 3.12, and 3.13 Quality jobs succeeded on integrated main | **PASS** |
| Protocol/package schema and traceability validation | Enforced by `scripts/quality.sh` in the successful integrated-main Quality jobs | **PASS** |
| Clean built-wheel validation | Package / Python 3.13 built distributions, validated metadata, installed the wheel in an unconstrained clean environment, verified installed identity, and ran reference/TCK smoke successfully | **PASS** |
| Governance | Governance is intentionally a `pull_request` workflow, not a main-push workflow; the final audit PR exact head must pass it | **PENDING FINAL #33 HEAD** |
| AEP lifecycle | AEP-0001 through AEP-0008 are approved `Accepted`; none is `Final` | **PASS** |
| Changelog / release notes | Alpha 2 protocol/conformance, reference implementation, repository engineering, and security impacts are recorded under Unreleased | **PASS** |
| Migration notes against prior public release | No GitHub Release or Git tag exists, so there is no prior published compatibility target | **N/A FOR FIRST RC** |
| Cross-profile security composition | Detailed Security Composition Review found no release-blocking authority/security contradiction | **PASS** |
| Open release-blocking issues | Final issue review finds only #23, repository branch-cleanup hygiene; it remains non-release-blocking | **PASS** |
| Review threads / drift | Final #33 exact-head review-thread and `main` drift check still required after this document update | **PENDING FINAL #33 HEAD** |
| Reproducible published artifact identifiers | Published release artifacts do not exist yet | **DEFERRED TO RELEASE PROCEDURE** |

## 4. AEP lifecycle audit

Governance defines `Accepted` as an approved protocol direction and `Final` as normative text/conformance merged and released.

On 2026-08-16 the protocol maintainer explicitly approved AEP-0002 through AEP-0008 from `Proposed` to `Accepted`. The decision explicitly did **not** authorize any AEP to become `Final`, and did not authorize tag, release, or package publication.

| AEP | Domain | Status |
|---|---|---|
| AEP-0001 | Oracle Evaluation | Accepted |
| AEP-0002 | Security Boundary | Accepted |
| AEP-0003 | Scenario / ScenarioInstance | Accepted |
| AEP-0004 | Environment | Accepted |
| AEP-0005 | MCP Tools Interop | Accepted |
| AEP-0006 | OpenTelemetry Mapping | Accepted |
| AEP-0007 | Subject Adapter | Accepted |
| AEP-0008 | Artifact Trust / Attestation | Accepted |

The detailed governance record is `docs/acceptance/alpha2-aep-acceptance-review.md`.

## 5. Conformance completeness

The integrated Alpha 2 stack reports:

- 87 indexed normative requirements;
- 71 registered language-neutral TCK cases;
- 10 conformance profiles;
- strict registry/requirement/profile traceability validation;
- mandatory-vs-conditional applicability validation;
- report-pipeline identity and summary invariants;
- 172 reference-runtime unit tests at the Artifact Trust acceptance baseline;
- Quality validation across Python 3.11, 3.12, and 3.13;
- clean built-wheel validation on Python 3.13.

These numbers are evidence, not protocol authority. The semantic audit additionally verified that ownership remains explicit, portable TCK cases do not standardize Python implementation shapes, conditional capabilities do not erase mandatory behavior, cross-profile failure semantics remain distinct, and the reference runtime does not create semantics absent from AEP/spec/TCK.

## 6. Cross-profile security audit

`docs/acceptance/alpha2-security-composition-review.md` verifies the composed authority chain across Core, Scenario, Environment, Security, Subject Adapter, MCP, OpenTelemetry, Evidence/Artifact, Oracle, and Artifact Trust.

The review confirms capability and secret boundaries, deny-before-side-effect behavior, Core quiescing semantics, infrastructure/verdict separation, Evidence-integrity versus Trust-authentication layering, telemetry non-authority, and assurance non-inflation. The #31/#32 integration changed commit topology, not the audited protocol file trees, so no new semantic contradiction was introduced by the squash/rebase sequence.

## 7. Reference implementation boundary

The Roadmap separately lists `signed/attested artifact publication` as reference implementation availability. AVP-TRUST-008 is conditional on an implementation declaring `artifact-attestation-publication`; verifier-only Artifact Trust conformance does not require a production signing implementation.

Absence of a production signing backend is therefore not an Alpha 2 protocol RC blocker unless a later release explicitly promises that optional capability. The reference implementation must continue to fail rather than claim credential-context or isolation assurance it cannot demonstrate.

## 8. Published-version baseline

The repository has no GitHub Release and no Git tag. The reference distribution version `0.3.0a1` is development metadata, not a published compatibility target.

Consequences:

- migration notes against a prior public AVP release are N/A for this first RC;
- release notes must still explain accumulated normative candidate semantics and non-normative implementation changes;
- RC version selection belongs to release preparation from the accepted integrated baseline, not to this audit branch.

## 9. Remaining final-validation gates

All protocol integration and AEP-acceptance blockers are closed. The only remaining readiness gates are exact-head checks on this retargeted #33 audit candidate:

1. full CI, including Quality 3.11/3.12/3.13 and Package 3.13 clean built-wheel/TCK smoke;
2. Governance success on the exact PR head;
3. `behind_by=0` against unchanged integrated `main`;
4. zero unresolved review threads.

If those gates pass, this document may be promoted to **READY FOR RC PREPARATION**. That state does not authorize merging #33, tagging, releasing, publishing a package, or moving any AEP to `Final`.
