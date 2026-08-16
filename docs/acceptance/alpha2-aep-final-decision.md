# Alpha 2 AEP Final Decision

Status: **APPROVED FOR FINAL LIFECYCLE TRANSITION**

Decision date: 2026-08-17

Decision scope: AEP-0001 through AEP-0008

Decision baseline: `main@2ca0cbbd166e7b8b01214ef8dd602614e0be87fd`

Released evidence point: `v0.3.0-rc.1` → `ef199124017b0dcc8c4a966d00c4f407760f9a06`

Eligibility evidence: `docs/acceptance/alpha2-aep-final-eligibility-audit.md`

## Maintainer decision

The protocol maintainer explicitly authorized AEP-0001 through AEP-0008 to transition from `Accepted` to `Final` on 2026-08-17.

This decision relies on the merged Alpha 2 Final-eligibility audit, which established that the normative text and required portable conformance coverage for all eight AEPs were merged and included in the published `v0.3.0-rc.1` release evidence point.

The published release bytes were independently revalidated through the external-consumer path, including clean wheel installation and the complete registered language-neutral TCK profile set. No post-release protocol-semantic change between the RC source and the audited baseline invalidated that evidence.

## Finalized AEPs

- AEP-0001 — Oracle Evaluation Contract v0.1
- AEP-0002 — Security Boundary Contract v0.1
- AEP-0003 — Scenario and ScenarioInstance Contract v0.1
- AEP-0004 — Environment Contract v0.1
- AEP-0005 — MCP Tools Interoperability Profile v0.1
- AEP-0006 — OpenTelemetry Mapping Profile v0.1
- AEP-0007 — Subject Adapter Interoperability Contract v0.1
- AEP-0008 — Artifact Trust and Attestation Contract v0.1

The lifecycle update is intentionally metadata/governance-only. It introduces no new normative protocol semantics, schema behavior, TCK behavior, or reference-runtime behavior.

## Scope boundary

This Final decision does **not** authorize:

- stable `v0.3.0` publication;
- PyPI or any other package-index publication;
- moving or recreating `v0.3.0-rc.1`;
- beginning Alpha 3 implementation;
- weakening schema, TCK, governance, release, or security requirements;
- treating unimplemented reference-runtime capabilities as protocol requirements.

Stable `v0.3.0` remains a separate release-management and governance decision after this transition is merged and exact-main checks are green.

## Merge gate

The Final-transition PR may be merged only after exact-head CI and Governance checks pass, review threads are resolved, current `main` has not drifted in a way that invalidates the decision evidence, and the diff remains limited to lifecycle/governance records.
