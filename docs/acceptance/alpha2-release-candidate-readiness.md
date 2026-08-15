# Alpha 2 Acceptance Audit and Release-Candidate Readiness

Status: **IN PROGRESS — NOT READY FOR RC**

Audit baseline: `c37ea4746d960f46528a1cabcbd5d06ec302f277` on the stacked Artifact Trust phase, with governance updates recorded on the `chore/alpha2-acceptance-audit` branch.

This document audits Alpha 2 as an integrated protocol/conformance candidate. It does not make a release, change protocol semantics, or treat reference implementation behavior as normative authority.

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

Reference-only capabilities, including concrete Python APIs, cryptographic fixtures, hosted services, database adapters, browser runtimes, containers, and microVMs, are not silently promoted into protocol release requirements.

## 2. Release-process gates

The repository release process requires all of the following before a release commit can be selected:

| Gate | Current evidence | Status |
|---|---|---|
| Release commit comes from `main` | Subject PR #31 and Artifact Trust PR #32 remain unmerged stacked changes | **BLOCKED** |
| Required CI / Governance green | Artifact Trust final head `c37ea474...` passed Quality 3.11/3.12/3.13, Package 3.13 and Governance; audit-branch governance changes require exact-head revalidation | PASS on protocol stack; audit head must remain green |
| Protocol and packaged schemas synchronized | Enforced by quality tests and built-wheel validation | PASS on stack head; must re-run after integration |
| Conformance passes from built wheel | Package job performs clean unconstrained install, installed-wheel identity, reference smoke and TCK smoke | PASS on stack head; must re-run after integration |
| Normative AEP references are sufficiently accepted for RC review | AEP-0001 through AEP-0008 are now `Accepted`; AEP-0002 through AEP-0008 were explicitly approved on 2026-08-16 | **PASS** |
| Changelog / release notes distinguish normative and non-normative changes | Alpha 2 Environment/MCP/OTel/Subject/Trust and security/reference impacts are recorded under Unreleased | PASS for audit branch; final release notes still generated from integrated `main` |
| Migration notes for incompatible published changes | Repository has no GitHub Release and no tag; there is no prior published compatibility baseline | N/A for first RC; development-period changes remain documented in Unreleased notes |
| Security-impact review | `docs/acceptance/alpha2-security-composition-review.md` found no release-blocking cross-profile authority/security conflict | PASS on stacked audit baseline; re-audit if integration changes semantics |
| No unresolved release-blocking issues | Open issue #23 is branch-cleanup hygiene and is currently classified non-blocking | PASS, subject to final issue review |
| Reproducible artifact identifiers | Package build is validated; published-release identifiers cannot be recorded before release artifacts exist | DEFERRED TO RELEASE PROCEDURE |

## 3. AEP lifecycle audit

Governance defines `Accepted` as an approved protocol direction and `Final` as normative text/conformance merged and released.

On 2026-08-16 the protocol maintainer explicitly approved AEP-0002 through AEP-0008 from `Proposed` to `Accepted`. The decision explicitly did **not** authorize any AEP to become `Final`, and did not authorize merge, tag, release, or package publication.

Current status:

| AEP | Domain | Status | RC action |
|---|---|---|---|
| AEP-0001 | Oracle Evaluation | Accepted | retain; verify release references |
| AEP-0002 | Security Boundary | Accepted | retain as non-Final until release |
| AEP-0003 | Scenario / ScenarioInstance | Accepted | retain as non-Final until release |
| AEP-0004 | Environment | Accepted | retain as non-Final until release |
| AEP-0005 | MCP Tools Interop | Accepted | retain as non-Final until release |
| AEP-0006 | OpenTelemetry Mapping | Accepted | retain as non-Final until release |
| AEP-0007 | Subject Adapter | Accepted | integrate PR #31, then final validation |
| AEP-0008 | Artifact Trust / Attestation | Accepted | integrate PR #32 after parent, then final validation |

The detailed decision record is `docs/acceptance/alpha2-aep-acceptance-review.md`.

## 4. Conformance completeness audit

The integrated stack currently reports:

- 87 indexed normative requirements;
- 71 registered language-neutral TCK cases;
- 10 conformance profiles;
- strict registry/requirement/profile traceability validation;
- mandatory-vs-conditional applicability validation;
- report-pipeline identity and summary invariants;
- 172 reference-runtime unit tests on Python 3.11 at the Artifact Trust acceptance head;
- Quality gates across Python 3.11, 3.12 and 3.13;
- clean built-wheel validation on Python 3.13.

These numbers are evidence of coverage, not a substitute for semantic audit. Final Alpha 2 acceptance must additionally verify that:

1. every Alpha 2 requirement has a stable owning normative specification;
2. every MUST/MUST NOT requirement has portable conformance evidence or an explicit justified exception;
3. no TCK case requires Python class names, exception types, private frame syntax, or reference-only algorithms;
4. conditional capabilities cannot be used to skip mandatory behavior;
5. composite profiles do not create contradictory ownership or failure semantics;
6. reference behavior does not introduce normative semantics absent from AEP/spec/TCK.

## 5. Cross-profile security audit

The detailed review is recorded in `docs/acceptance/alpha2-security-composition-review.md` and passes on the stacked audit baseline.

The review verified:

- Scenario remains the source of Subject visibility and actor capability projection;
- Security remains the deny-by-default Subject/Evaluator capability and secret boundary;
- Environment owns mutable authoritative state and actor-scoped observation;
- Subject Adapter cannot become an alternate Scenario/Security/Environment/MCP/OTel/Oracle/Evidence authority;
- MCP cannot bypass AVP capability enforcement and does not replace MCP-native authorization semantics;
- Core `QUIESCING` preserves the side-effect boundary before evaluator verification;
- Core, Scenario, Subject, MCP, Oracle, OTel, and Trust preserve infrastructure/verification failures separately from Task Verdict;
- Evidence exact-byte integrity remains distinct from Artifact Trust authentication and policy acceptance;
- telemetry remains observational and cannot become a second Oracle;
- Security/Subject/Environment/Trust assurance claims remain non-inflating;
- upstream MCP, OpenTelemetry/W3C, DSSE/in-toto/Sigstore/X.509/SLSA and deployment security mechanisms retain their authority.

No release-blocking cross-profile security contradiction was identified. Any later semantic change during stack integration requires targeted re-audit.

## 6. Reference implementation non-blocking boundary

The Roadmap separately lists `signed/attested artifact publication` as reference implementation availability. AVP-TRUST-008 is conditional on an implementation declaring `artifact-attestation-publication`; verifier-only Artifact Trust conformance does not require a signing implementation.

Therefore absence of a production signing backend is **not automatically an Alpha 2 protocol RC blocker**. It becomes blocking only if the selected RC explicitly promises that optional reference capability. The in-process reference publisher must continue to fail rather than claim credential-context isolation it cannot demonstrate.

## 7. Published-version baseline

As of this audit, the repository has no GitHub Release and no Git tag. The current reference distribution version `0.3.0a1` is development metadata, not evidence of a published compatibility target.

Consequences:

- there is no prior public release against which a mandatory migration guide can be truthfully written;
- Alpha 2 RC release notes must still explain the accumulated normative candidate semantics and non-normative implementation changes;
- version selection and any `rc` version transition belong to the later release-preparation step from integrated `main`, not to this audit branch.

## 8. Current blockers

Alpha 2 is **not Ready for RC** while either of the following remains true:

1. #31 Subject Adapter and #32 Artifact Trust are not integrated into `main` through the separately authorized squash-merge sequence, including required retarget/rebase validation for stacked descendants.
2. Final integrated `main` has not passed required CI, Governance, clean built-wheel tests, conformance, drift, issue and review-thread checks.

The AEP lifecycle-acceptance blocker is closed: AEP-0002 through AEP-0008 are `Accepted`, and none is `Final`.

## 9. Readiness rule

The audit may change to `READY FOR RC PREPARATION` only when both blockers above are closed with repository evidence. That state authorizes preparation of an RC from `main`; it does **not** itself authorize a merge, tag, GitHub Release, or package publication.

Any merge still requires the explicit authorization required by the project governance rules. No AEP may move to `Final` until its normative text and required conformance coverage are merged and an actual release completes.
