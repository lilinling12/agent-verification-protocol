# Alpha 2 AEP Final Eligibility Audit

Status: **BLOCKED ON GOVERNANCE CLARIFICATION**

Audit baseline: `main@9f7394ed0b9cdcd4dcd853acc53e0644106fd9f5`

Published release evidence: `v0.3.0-rc.1`, source commit `ef199124017b0dcc8c4a966d00c4f407760f9a06`, GitHub Prerelease, with external-consumer release acceptance recorded as `PASS` in `docs/acceptance/alpha2-rc1-release-acceptance.md`.

## Purpose

This audit asks whether AEP-0001 through AEP-0008 have reached the evidence threshold at which a maintainer could consider an `Accepted` → `Final` transition. It does **not** perform that transition and does not reinterpret reference implementation behavior as protocol authority.

The audit is intentionally split into two questions:

1. **Mechanical readiness** — do the accepted AEPs have merged normative text, requirement indexes, reconciliation records, portable TCK profiles, integrated-main validation, and released consumer evidence?
2. **Governance eligibility** — does the repository's lifecycle policy define the published `v0.3.0-rc.1` prerelease as satisfying the word `released` in the `Final` definition?

The first question is currently satisfied for all eight AEPs. The second is not defined by the current governance text and therefore blocks Final eligibility.

## Governing rule

`GOVERNANCE.md` defines `Final` as:

> normative text and required conformance coverage are merged and released.

The governance document does not currently distinguish a stable release from a prerelease for this predicate. The published RC and its release notes deliberately preserve AEP-0001 through AEP-0008 as `Accepted`, not `Final`. This audit therefore MUST NOT infer that publication of a prerelease automatically satisfies the Final lifecycle transition.

A separate explicit protocol-maintainer decision is required to choose one of the following policies:

- a prerelease counts as `released` for AEP Final eligibility; or
- AEP Final requires a stable protocol release.

Until that decision is recorded, `prereleaseFinality` remains `UNDEFINED` and every AEP remains blocked on governance clarification.

## Evidence reviewed

The audit is based on repository state after the RC publication and external-consumer acceptance work:

- AEP-0001 through AEP-0008 are present under `rfcs/` and remain `Status: Accepted`;
- each AEP has a language-neutral normative contract under `spec/` and a requirement index;
- each AEP has a reconciliation decision record;
- each AEP has a registered portable TCK profile;
- schema/TCK/spec traceability and repository governance are part of the normal quality gate;
- the RC package was built reproducibly from exact source and published with digest-bound release evidence;
- the actual public release assets were independently downloaded, verified, installed in clean environments, and exercised across the registered TCK profiles;
- PR #36 external-consumer release acceptance was merged after exact-head CI, Release Validation, and Governance succeeded;
- post-merge `main@9f7394ed0b9cdcd4dcd853acc53e0644106fd9f5` passed exact-main CI #392 across Python 3.11, 3.12, 3.13 and the package/conformance job.

These facts remove the engineering blockers recorded in the earlier Alpha 2 AEP Acceptance Review. They do not themselves resolve the lifecycle-policy ambiguity.

## Per-AEP eligibility matrix

| AEP | Normative spec | Requirement index | Portable TCK profile | Reconciliation | Mechanical readiness | Final eligibility |
| --- | --- | --- | --- | --- | --- | --- |
| AEP-0001 Oracle Evaluation | `spec/oracle/oracle-evaluation-contract.md` | `spec/oracle/requirement-index.yaml` | `avp-oracle-v0.1` | Oracle evaluation decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0002 Security Boundary | `spec/security/security-boundary-contract.md` | `spec/security/requirement-index.yaml` | `avp-security-v0.1` | Security boundary decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0003 ScenarioInstance | `spec/scenario/scenario-contract.md` | `spec/scenario/requirement-index.yaml` | `avp-scenario-v0.1` | Scenario instance decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0004 Environment | `spec/environment/environment-contract.md` | `spec/environment/requirement-index.yaml` | `avp-environment-v0.1` | Environment decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0005 MCP Interop | `spec/mcp/mcp-tools-interop-contract.md` | `spec/mcp/requirement-index.yaml` | `avp-mcp-interop-v0.1` | MCP interop decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0006 OpenTelemetry Mapping | `spec/opentelemetry/opentelemetry-mapping-contract.md` | `spec/opentelemetry/requirement-index.yaml` | `avp-otel-mapping-v0.1` | OTel mapping decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0007 Subject Adapter | `spec/subject/subject-adapter-contract.md` | `spec/subject/requirement-index.yaml` | `avp-subject-v0.1` | Subject adapter decision | READY | BLOCKED — prerelease finality undefined |
| AEP-0008 Artifact Trust | `spec/trust/artifact-trust-attestation-contract.md` | `spec/trust/requirement-index.yaml` | `avp-artifact-trust-v0.1` | Artifact trust decision | READY | BLOCKED — prerelease finality undefined |

The machine-readable source of this matrix is `docs/acceptance/alpha2-finalization-manifest.json`.

## Automated guard

`scripts/validate_aep_finalization_readiness.py` validates the audit fail-closed. Among other checks it requires:

- exactly AEP-0001 through AEP-0008, without duplicates;
- every referenced RFC, normative spec, requirement index, reconciliation record, and TCK profile to exist;
- each audited RFC to remain `Accepted` while this audit is unresolved;
- release acceptance evidence to remain `PASS` and bound to the published release source commit;
- Final transitions never to be automatic;
- no AEP to be represented as `ELIGIBLE` while prerelease finality is `UNDEFINED`.

The validator is part of `scripts/quality.sh`, so later changes that accidentally bypass the recorded governance boundary fail the normal quality gate.

## Findings

### F-01 — Mechanical Final-readiness evidence is complete for the audited Alpha 2 AEP set

**Result: READY.**

The prior engineering blockers — unmerged Alpha 2 protocol work, missing release, and missing integrated-main validation — no longer describe current repository state.

This finding means the protocol artifacts are mature enough for a lifecycle-policy decision. It does not mean that the decision has already been made.

### F-02 — The meaning of `released` for prereleases is undefined

**Result: BLOCKING.**

The repository has a published and independently validated GitHub Prerelease, but governance does not state whether a prerelease is sufficient for AEP Final. Treating it as sufficient without an explicit policy decision would make release mechanics define protocol governance by implication.

Required resolution: a protocol-maintainer governance decision recorded before any AEP status is changed to `Final`.

### F-03 — Finality must remain independent from stable release, package-index publication, and Alpha 3 authorization

Regardless of the policy chosen for F-02, this audit grants no authority to:

- publish `v0.3.0` stable;
- publish to PyPI or another package index;
- start Alpha 3;
- merge this audit PR;
- transition any AEP status automatically.

Those remain separate actions requiring their own readiness evidence and explicit authorization where required by repository governance.

## Audit conclusion

AEP-0001 through AEP-0008 are **mechanically ready for a Final-eligibility decision**, but they are **not currently eligible to be transitioned to `Final`** because the lifecycle treatment of prereleases is undefined.

Current required state:

- AEP-0001..0008: `Accepted`
- mechanical readiness: `READY`
- overall Final eligibility: `BLOCKED_ON_GOVERNANCE_CLARIFICATION`
- blocker: `PRERELEASE_FINALITY_UNDEFINED`

The next governance boundary is an explicit protocol-maintainer decision on the release predicate. This audit must be merged and validated independently before any subsequent status-transition change is proposed.
