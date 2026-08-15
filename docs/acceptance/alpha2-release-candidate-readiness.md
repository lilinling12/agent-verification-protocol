# Alpha 2 Acceptance Audit and Release-Candidate Readiness

Status: **READY FOR RC PREPARATION**

Integrated protocol baseline: `65d7c7413d7fe2def4d9d1593fdeb09753da6324` on `main`.

This document records the completed Alpha 2 integrated protocol/conformance acceptance audit. `READY FOR RC PREPARATION` means the audited protocol baseline is ready for a separately governed release-candidate preparation step. It does **not** authorize merging this audit PR, creating a tag or GitHub Release, publishing a package, or moving any AEP to `Final`.

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

## 2. Integrated baseline

The authorized stacked integration completed in dependency order:

1. PR #31 Subject Adapter was final-head revalidated and squash-merged into `main` as `1823d877409386d84fea502fa3d7265fb85060e3`.
2. PR #32 Artifact Trust was retargeted/rebased onto that exact main baseline so its diff contained only Artifact Trust changes.
3. The rebased #32 candidate passed fresh Quality / Package / Governance gates, was `behind_by=0`, and had no unresolved review threads.
4. PR #32 was squash-merged into `main` as `65d7c7413d7fe2def4d9d1593fdeb09753da6324`.
5. PR #33 was retargeted/rebased onto that exact integrated main baseline so it contains only Alpha 2 audit/governance changes.

The squash/rebase sequence preserved the audited protocol file trees; it changed commit topology rather than protocol semantics.

## 3. Release-readiness evidence

| Gate | Evidence | Result |
|---|---|---|
| Protocol stack integrated into `main` | #31 and #32 squash-merged in dependency order after final-head revalidation | **PASS** |
| Integrated-main CI | `main@65d7c741...` push CI #357 | **PASS** |
| Quality matrix | Python 3.11, 3.12, and 3.13 Quality jobs | **PASS** |
| Schema / governance / traceability / TCK registry validation | Executed through the integrated-main quality gate | **PASS** |
| Clean built-wheel validation | Build, metadata validation, unconstrained clean install, installed-wheel identity, reference smoke, and installed-wheel TCK smoke | **PASS** |
| Audit-candidate full CI | Retargeted #33 validation candidate CI #359 | **PASS** |
| Audit-candidate Governance | Retargeted #33 Governance #383 | **PASS** |
| AEP lifecycle | AEP-0001 through AEP-0008 are `Accepted`; none is `Final` | **PASS** |
| Changelog / release notes | Alpha 2 protocol/conformance, reference, repository, and security impacts recorded under Unreleased | **PASS** |
| Migration against prior published release | Repository has no GitHub Release or Git tag | **N/A FOR FIRST RC** |
| Cross-profile security composition | No release-blocking authority/security contradiction found | **PASS** |
| Open release-blocking issues | Only open issue #23 is superseded-branch cleanup and remains non-release-blocking | **PASS** |
| Published release artifact identifiers | No published RC artifacts exist yet | **DEFERRED TO RELEASE PROCEDURE** |

The final document-state #33 HEAD must retain successful required CI/Governance, `behind_by=0`, and zero unresolved review threads. These are evidence checks for this readiness statement, not authorization to merge #33.

## 4. AEP lifecycle result

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

The detailed governance decision record is `docs/acceptance/alpha2-aep-acceptance-review.md`.

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

These counts are evidence, not protocol authority. The semantic audit additionally verified stable normative ownership, portable conformance boundaries, fail-closed conditional behavior, non-conflicting cross-profile failure semantics, and that Python reference behavior does not define protocol semantics absent from AEP/spec/TCK.

## 6. Cross-profile security result

`docs/acceptance/alpha2-security-composition-review.md` verifies the composed authority chain across Core, Scenario, Environment, Security, Subject Adapter, MCP, OpenTelemetry, Evidence/Artifact, Oracle, and Artifact Trust.

The review confirms capability and secret boundaries, deny-before-side-effect behavior, Core quiescing semantics, infrastructure/verdict separation, Evidence-integrity versus Trust-authentication layering, telemetry non-authority, and assurance non-inflation. No release-blocking cross-profile security contradiction was identified.

## 7. Reference implementation boundary

The Roadmap separately lists `signed/attested artifact publication` as reference implementation availability. AVP-TRUST-008 is conditional on an implementation declaring `artifact-attestation-publication`; verifier-only Artifact Trust conformance does not require a production signing implementation.

Absence of a production signing backend is therefore not an Alpha 2 protocol RC blocker unless a later release explicitly promises that optional capability. The reference implementation must continue to fail rather than claim credential-context or isolation assurance it cannot demonstrate.

## 8. Published-version baseline

The repository has no GitHub Release and no Git tag. The reference distribution version `0.3.0a1` is development metadata, not a published compatibility target.

Consequences:

- migration notes against a prior public AVP release are N/A for this first RC;
- release notes must still explain accumulated normative candidate semantics and non-normative implementation changes;
- RC version selection belongs to a later release-preparation step from the accepted baseline.

## 9. Readiness boundary

Alpha 2 protocol/conformance acceptance is complete and is **READY FOR RC PREPARATION**.

This state does not itself authorize:

- merging PR #33;
- creating a release branch, tag, or GitHub Release;
- publishing a package;
- changing any AEP from `Accepted` to `Final`;
- beginning Alpha 3 changes as part of this audit PR.

Those actions remain separate governance decisions. Any future release commit must be selected from `main` and must follow `docs/RELEASE_PROCESS.md` with its own exact-commit release validation.
