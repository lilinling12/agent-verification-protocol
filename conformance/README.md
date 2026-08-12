# AVP Conformance

`conformance/` is the implementation-independent conformance surface for AVP. It is derived from normative requirements in `spec/` and machine-readable contracts in `schemas/`; it does not define protocol semantics independently.

The language-independent Conformance Test Kit lives under `conformance/tck/`. Its authoritative machine-readable catalog is `conformance/tck/registry.yaml`; lifecycle vectors live only under `conformance/tck/cases/lifecycle/`. Reference-runtime smoke checks under `src/avp_ref/` and implementation tests under `tests/` consume protocol semantics and MUST NOT be treated as TCK authority.

Conformance answers whether an implementation satisfies a declared AVP profile. Benchmarks answer how well an Agent System performs. These concerns remain separate.

A mature TCK case identifies normative requirement IDs, deterministic vector or precondition, expected observable behavior, negative behavior where applicable, and evidence expectations. Cross-resource integrity is enforced by:

- `scripts/validate_spec_traceability.py` for bidirectional requirement-to-case mappings;
- `scripts/validate_tck_registry.py` for registry, profile, case, and report-schema integrity;
- `scripts/validate_lifecycle_contract.py` for lifecycle state/transition consistency; and
- `scripts/validate_tck_report.py` for executable report generation and checked-in example validation.

Legacy flat lifecycle vectors and the former `suite-manifest.json` are intentionally removed once their semantics are migrated into the registry-backed TCK. New conformance work MUST NOT reintroduce parallel sources of authority.
