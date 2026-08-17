# AVP Specification

`spec/` is the normative human-readable protocol surface of AVP.

## Authority

When semantics conflict, resolution order is: `spec/` -> `schemas/` -> `conformance/` -> reference implementation. Reference-runtime behavior is never normative merely because it exists in code.

## Current normative surfaces

- `core/` — Episode lifecycle, replay identity, result/validity separation, and core execution semantics;
- `scenario/` — ScenarioTemplate to ScenarioInstance materialization, identity, immutability, reference binding, and Subject projection semantics;
- `environment/` — Environment ownership, reset/time, observation/projection, snapshot/restore, diff, fault, and stale-handle semantics;
- `evidence/` — evidence identity, integrity, publication, and metadata semantics;
- `oracle/` — Oracle execution/evaluation separation, failure validity, result binding, and audit semantics;
- `security/` — Subject/Evaluator trust boundary and machine-readable assurance semantics;
- `mcp/` — AVP verification mappings around MCP tool execution while MCP remains the external protocol authority;
- `opentelemetry/` — AVP verification-correlation, outcome, completeness, minimization, and Evidence mappings when OpenTelemetry-compatible telemetry is used;
- `subject/` — Subject Adapter identity, Agent System binding, invocation budgets, controlled capability gateway, outcome separation, stale-handle behavior, and transport/isolation claim honesty;
- `trust/` — Artifact attestation authentication, signer identity, evaluator-owned trust-policy acceptance, publication-authority claims, and fail-closed trust outcomes.

Presence under `spec/` does not by itself establish accepted protocol authority. Each domain is tied to recorded governance/reconciliation lineage, a requirement index, and its conformance surface.

## Requirement-index status

The top-level `status` in a domain `requirement-index.yaml` describes the authority state of that machine-readable requirement set. It is intentionally separate from AEP lifecycle state, TCK architecture/profile metadata, and release maturity.

The allowed values are:

- `draft-normative-candidate` — the requirement set is a governed candidate and is not yet the current accepted machine-readable requirement authority for the domain;
- `normative` — the requirement set is the current machine-readable normative requirement authority for the domain, backed by the domain's recorded accepted lineage and normative specification/conformance surface.

`normative` does **not** mean that a governing AEP is necessarily `Final`, that a stable AVP release has been published, or that repository-wide Normative Surface Closure is `READY`. Those are separate governance and release decisions. Core and Evidence, for example, may have `normative` requirement indexes through accepted reconciliation lineage without manufacturing an AEP solely to normalize history.

Unknown requirement-index status values are invalid. Status transitions must follow the applicable governance path and must not be used to bypass semantic review or conformance evidence.

## Belongs here

- language-neutral concepts and terminology;
- observable lifecycle/state-machine semantics;
- Scenario materialization and execution-contract semantics;
- evidence, verdict, validity, replay, and authority semantics;
- trust-boundary, extension, interoperability, and version-negotiation requirements.

## Does not belong here

- Python implementation details;
- authoring-DSL convenience syntax unless explicitly standardized;
- commercial control-plane behavior;
- benchmark scoring heuristics;
- product-specific convenience APIs.

Material normative changes follow `GOVERNANCE.md` and the AEP process under `rfcs/`.
