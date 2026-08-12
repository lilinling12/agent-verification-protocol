# AVP Conformance

`conformance/` is the implementation-independent conformance surface for AVP. It is derived from normative requirements in `spec/` and machine-readable contracts in `schemas/`; it does not define protocol semantics independently.

The language-independent Conformance Test Kit lives under `conformance/tck/`. Reference-runtime smoke checks under `src/avp_ref/` and implementation tests under `tests/` are consumers of protocol semantics and MUST NOT be treated as TCK authority.

Conformance answers whether an implementation satisfies a declared AVP profile. Benchmarks answer how well an Agent System performs. These concerns remain separate.

A mature TCK case identifies the normative requirement(s), deterministic vector or precondition, expected observable behavior, negative behavior where applicable, and evidence expectations. The registry, profiles, case files, and report schema are cross-validated by `scripts/validate_tck.py`.
