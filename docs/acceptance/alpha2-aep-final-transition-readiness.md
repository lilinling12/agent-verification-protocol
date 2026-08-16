# Alpha 2 AEP Final Transition Readiness

Status: **READY FOR EXPLICIT MAINTAINER FINALIZATION DECISION**

Preparation baseline: `main@2ca0cbbd166e7b8b01214ef8dd602614e0be87fd`

Final-eligibility evidence: `docs/acceptance/alpha2-aep-final-eligibility-audit.md`

Released protocol evidence point: `v0.3.0-rc.1` → `ef199124017b0dcc8c4a966d00c4f407760f9a06`

This document prepares the repository for a possible explicit protocol-maintainer decision to transition AEP-0001 through AEP-0008 from `Accepted` to `Final`. It does **not** perform or authorize that lifecycle transition.

## Governance boundary

Under `GOVERNANCE.md`, `Final` means that the normative text and required conformance coverage are merged and released. The Alpha 2 Final-eligibility audit established that AEP-0001 through AEP-0008 satisfy the repository's technical eligibility criteria after publication and external-consumer validation of `v0.3.0-rc.1`.

Technical eligibility is not self-executing. The lifecycle transition requires an explicit protocol-maintainer decision and must be recorded as a reviewable governance change.

## Current lifecycle state

The following AEPs remain `Accepted` at this preparation baseline:

| AEP | Contract | Current state | Final eligibility |
| --- | --- | --- | --- |
| AEP-0001 | Oracle Evaluation Contract v0.1 | Accepted | Eligible |
| AEP-0002 | Security Boundary Contract v0.1 | Accepted | Eligible |
| AEP-0003 | Scenario and ScenarioInstance Contract v0.1 | Accepted | Eligible |
| AEP-0004 | Environment Contract v0.1 | Accepted | Eligible |
| AEP-0005 | MCP Tools Interoperability Profile v0.1 | Accepted | Eligible |
| AEP-0006 | OpenTelemetry Mapping Profile v0.1 | Accepted | Eligible |
| AEP-0007 | Subject Adapter Interoperability Contract v0.1 | Accepted | Eligible |
| AEP-0008 | Artifact Trust and Attestation Contract v0.1 | Accepted | Eligible |

No AEP is changed to `Final` by this readiness record.

## Required shape of a later Final transition

If the protocol maintainer explicitly authorizes Finalization, the transition PR should be deliberately narrow and atomic:

1. change `Status: Accepted` to `Status: Final` in AEP-0001 through AEP-0008;
2. add a `Finalized: YYYY-MM-DD` metadata field to every transitioned AEP;
3. add a concise `Final decision:` record identifying the maintainer decision and the evidence basis;
4. preserve the historical `Accepted:` date and acceptance decision rather than rewriting history;
5. normalize AEP-0001 decision metadata so its lifecycle record is equivalent in auditability to AEP-0002 through AEP-0008;
6. update `ROADMAP.md` to mark the explicit `Accepted` → `Final` lifecycle transition complete;
7. do not modify normative protocol semantics, schemas, TCK behavior, or reference-runtime semantics in the same PR;
8. do not authorize or publish stable `v0.3.0`, package-index artifacts, or Alpha 3 in the same decision unless separately authorized.

## Decision record requirements

Each `Final decision:` entry should state, at minimum:

- that the protocol maintainer explicitly approved the `Accepted` → `Final` transition;
- that the decision relies on the merged Final-eligibility audit;
- that released evidence is bound to `v0.3.0-rc.1` / `ef199124017b0dcc8c4a966d00c4f407760f9a06`;
- that the published release bytes passed external-consumer and full TCK validation;
- that no post-release protocol-semantic drift invalidated the evidence point;
- that Finalization does not itself authorize stable-release publication.

The decision text should remain concise. Detailed evidence belongs in the acceptance audit rather than being duplicated into every AEP.

## Atomicity and failure policy

AEP-0001 through AEP-0008 form the Alpha 2 protocol baseline assessed by the shared eligibility audit. The preferred transition is therefore one reviewable governance PR covering all eight AEPs.

Before applying the batch transition, re-check every AEP against the current `main` HEAD. If any one AEP has acquired an unresolved semantic, conformance, security, or release-evidence gap, do **not** force the batch through. Keep all affected lifecycle states unchanged, document the blocker, and repair the gap first.

The transition must never weaken schema validation, TCK coverage, branch governance, or release checks merely to obtain a green result.

## Validation gates for the later transition PR

A Final-transition PR is ready for merge only when all of the following are true on its exact head:

- repository branch and PR-title governance pass;
- all required CI jobs pass on supported Python versions;
- package / clean-wheel checks pass where triggered;
- the full language-neutral TCK remains green;
- release-validation evidence remains green where triggered;
- no unresolved review thread remains;
- `main` has not drifted in a way that invalidates the eligibility evidence or proposed decision;
- the diff contains no unintended normative, schema, TCK, or reference-runtime semantic changes.

## Authorization boundary

The next lifecycle-changing action requires an unmistakable protocol-maintainer authorization such as:

`授权 AEP-0001 至 AEP-0008 从 Accepted 转为 Final`

Generic continuation instructions such as `继续` or `下一步` are not sufficient authorization for the lifecycle transition.

After Finalization is merged and exact-main checks are green, the stable `v0.3.0` release decision remains a separate governance and release-management gate.
