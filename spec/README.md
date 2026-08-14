# AVP Specification

`spec/` is the normative human-readable protocol surface of AVP.

## Authority

When semantics conflict, resolution order is: `spec/` -> `schemas/` -> `conformance/` -> reference implementation. Reference-runtime behavior is never normative merely because it exists in code.

## Current normative surfaces

- `core/` — Episode lifecycle, replay identity, result/validity separation, and core execution semantics;
- `scenario/` — ScenarioTemplate to ScenarioInstance materialization, identity, immutability, reference binding, and Subject projection semantics;
- `evidence/` — evidence identity, integrity, publication, and metadata semantics;
- `oracle/` — Oracle execution/evaluation separation, failure validity, result binding, and audit semantics;
- `security/` — Subject/Evaluator trust boundary and machine-readable assurance semantics.

Normative-candidate status is tracked by each domain's requirement index and reconciliation assets; presence under `spec/` does not by itself imply an accepted stable standard.

## Belongs here

- language-neutral concepts and terminology;
- observable lifecycle/state-machine semantics;
- Scenario materialization and execution-contract semantics;
- evidence, verdict, validity, replay, and authority semantics;
- trust-boundary, extension, and version-negotiation requirements.

## Does not belong here

- Python implementation details;
- authoring-DSL convenience syntax unless explicitly standardized;
- commercial control-plane behavior;
- benchmark scoring heuristics;
- product-specific convenience APIs.

Material normative changes follow `GOVERNANCE.md` and the AEP process under `rfcs/`.
