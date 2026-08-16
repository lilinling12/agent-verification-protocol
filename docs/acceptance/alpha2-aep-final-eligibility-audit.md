# Alpha 2 AEP Final Eligibility Audit

Status: **ELIGIBLE FOR MAINTAINER FINALIZATION DECISION**

Audit baseline: `main@9f7394ed0b9cdcd4dcd853acc53e0644106fd9f5`

Released protocol evidence point: `v0.3.0-rc.1` → `ef199124017b0dcc8c4a966d00c4f407760f9a06`

This document audits whether AEP-0001 through AEP-0008 satisfy the repository's technical eligibility criteria for the `Accepted` → `Final` lifecycle transition. It does **not** perform that transition. Every AEP remains `Accepted` until the protocol maintainer explicitly authorizes a Final-status change.

## Governing rule

`GOVERNANCE.md` defines `Final` as the state in which normative text and required conformance coverage are merged and released.

For this audit, an AEP is technically eligible only when all of the following are true:

1. the AEP is already `Accepted`;
2. its language-neutral normative contract is merged into `main`;
3. its required machine-readable schema or requirement index is merged when the contract requires one;
4. its portable TCK/conformance profile is merged and maps the required normative behavior;
5. reconciliation and acceptance evidence contain no unresolved release-blocking semantic contradiction;
6. the normative/conformance content was included in a published release evidence point;
7. the published release bytes have been independently revalidated from an external-consumer path;
8. no post-release change to protocol semantics invalidates that release evidence point.

Eligibility is necessary but not sufficient for Final. The status transition remains a separate maintainer decision recorded in an AEP/governance PR.

## Release evidence and drift control

The `v0.3.0-rc.1` prerelease is bound to exact source commit `ef199124017b0dcc8c4a966d00c4f407760f9a06`. The published-release acceptance audit passed after downloading the actual release assets, validating their digests and manifest binding, installing the wheel in clean environments, and rerunning every registered TCK profile.

The only commit between that release source and this audit baseline is PR #36. Its changes are limited to release validation automation, release/roadmap/changelog reconciliation, and acceptance documentation. It changes no file under `rfcs/`, `spec/`, `schemas/`, or `conformance/`. The released protocol/conformance baseline is therefore still the current protocol baseline for this Final-eligibility decision.

## Per-AEP eligibility

| AEP | Normative contract | Required schema/index | Portable conformance | Acceptance/reconciliation | Released in RC1 | Eligibility |
| --- | --- | --- | --- | --- | --- | --- |
| AEP-0001 Oracle Evaluation Contract | `spec/oracle/oracle-evaluation-contract.md` | `schemas/oracle-evaluation.schema.json`, `spec/oracle/requirement-index.yaml` | `avp-oracle-v0.1` | accepted; Oracle reconciliation and audit evidence complete | yes | **ELIGIBLE** |
| AEP-0002 Security Boundary Contract | `spec/security/security-boundary-contract.md` | `schemas/security-assurance.schema.json`, `spec/security/requirement-index.yaml` | `avp-security-v0.1` | accepted; Alpha 2 Security Composition Review PASS | yes | **ELIGIBLE** |
| AEP-0003 Scenario / ScenarioInstance Contract | `spec/scenario/scenario-contract.md` | Scenario schemas and `spec/scenario/requirement-index.yaml` | `avp-scenario-v0.1` | accepted; reconciliation has no unresolved semantic contradiction | yes | **ELIGIBLE** |
| AEP-0004 Environment Contract | `spec/environment/environment-contract.md` | `spec/environment/requirement-index.yaml` | `avp-environment-v0.1` | accepted; environment acceptance audit passed | yes | **ELIGIBLE** |
| AEP-0005 MCP Tools Interoperability Profile | `spec/mcp/mcp-tools-interop-contract.md` | `spec/mcp/requirement-index.yaml` | `avp-mcp-interop-v0.1` | accepted; MCP remains upstream wire authority; AVP binding audit passed | yes | **ELIGIBLE** |
| AEP-0006 OpenTelemetry Mapping Profile | `spec/opentelemetry/opentelemetry-mapping-contract.md` | `spec/opentelemetry/requirement-index.yaml` | `avp-otel-mapping-v0.1` | accepted; mapping audit passed without making telemetry verdict-authoritative | yes | **ELIGIBLE** |
| AEP-0007 Subject Adapter Interoperability Contract | `spec/subject/subject-adapter-contract.md` | `spec/subject/requirement-index.yaml` | `avp-subject-v0.1` | accepted; Subject acceptance audit passed | yes | **ELIGIBLE** |
| AEP-0008 Artifact Trust / Attestation Contract | `spec/trust/artifact-trust-attestation-contract.md` | artifact trust schemas and `spec/trust/requirement-index.yaml` | `avp-artifact-trust-v0.1` | accepted; trust acceptance audit passed, including conditional publication-authority honesty | yes | **ELIGIBLE** |

## AEP-0001 note

AEP-0001 was already `Accepted` before the batch Alpha 2 AEP acceptance decision for AEP-0002 through AEP-0008. Its normative Oracle contract, schema, requirement index, portable TCK profile, and reference-runtime alignment are part of the same released RC baseline. Its earlier acceptance date does not create a weaker Final criterion.

## Optional implementation items do not block Final

The Roadmap still lists signed/attested artifact **publication** as an unimplemented reference-runtime capability. That item is intentionally not a blocker for AEP-0008 Final eligibility: AEP-0008 standardizes verification semantics and assurance honesty, while production publication/signing mechanisms remain deployment/upstream-owned. The conditional publication-authority TCK must fail when an implementation falsely claims unsupported authority isolation.

Likewise, Alpha 3 database, browser, network-fault, virtual-clock, container, and microVM work is outside the Alpha 2 protocol contracts and is not required to finalize these v0.1 AEPs.

## Finalization decision boundary

This audit recommends the following governance conclusion:

> AEP-0001 through AEP-0008 have satisfied the repository's technical `Final` eligibility prerequisites as of the audited baseline. They should remain `Accepted` until the protocol maintainer explicitly authorizes an `Accepted` → `Final` status transition.

A future Finalization PR SHOULD be narrow:

- update only the AEP lifecycle metadata/status and the corresponding governance/release documentation required to record the decision;
- cite this audit and the published RC1 acceptance evidence;
- introduce no new normative semantics;
- rerun CI/Governance on the exact PR head;
- require explicit protocol-maintainer authorization before merge.

Finalization does **not** by itself authorize stable `v0.3.0`, PyPI/package-index publication, Alpha 3 implementation, or any new normative change.
