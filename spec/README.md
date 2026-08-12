# AVP Specification

`spec/` is the normative human-readable protocol surface of AVP.

## Authority

When semantics conflict, resolution order is: `spec/` -> `schemas/` -> `conformance/` -> reference implementation. Reference-runtime behavior is never normative merely because it exists in code.

## Belongs here

- language-neutral concepts and terminology;
- observable lifecycle/state-machine semantics;
- evidence, verdict, validity, replay, and authority semantics;
- trust-boundary, extension, and version-negotiation requirements.

## Does not belong here

- Python implementation details;
- commercial control-plane behavior;
- benchmark scoring heuristics;
- product-specific convenience APIs.

Material normative changes follow `GOVERNANCE.md` and the AEP process under `rfcs/`.
