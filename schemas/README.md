# AVP Schemas

`schemas/` contains machine-readable protocol contracts derived from the normative specification.

Schemas define serializable shapes and validation constraints. They do not independently create semantics absent from `spec/`.

Rules:

- JSON Schema uses Draft 2020-12 unless a versioned specification says otherwise.
- Breaking schema changes require protocol/versioning analysis.
- Stable releases require stable identifiers and explicit versioning.
- Packaged schema copies used by the reference runtime must remain synchronized with canonical schemas.
- Schema acceptance does not imply behavioral conformance.

Python models under `src/avp_ref/` consume these contracts; they are not their authority source.
