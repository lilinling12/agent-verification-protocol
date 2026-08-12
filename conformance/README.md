# AVP Conformance

`conformance/` is the implementation-independent conformance surface for AVP. It is not the Python reference implementation's unit-test directory; those tests remain under `tests/`.

Conformance cases are derived from requirements in `spec/` and contracts in `schemas/`. A case may clarify how a requirement is proven, but must not silently invent protocol semantics.

A mature case identifies the requirement, deterministic input/vector, expected observable result, negative behavior, required evidence/artifacts, and trust-boundary expectations when applicable.

Conformance answers whether an implementation satisfies AVP. Benchmarks answer how well an Agent System performs. Those concerns remain separate.
