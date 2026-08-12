# AVP Conformance Test Kit (TCK)

Status: Draft architecture for AVP v0.1.

The AVP TCK is the implementation-independent conformance surface for verifying that an implementation satisfies a declared AVP profile. It is not the Python reference runtime and it does not acquire normative authority beyond the requirements it traces to in `spec/`.

## Authority

The authority direction is:

```text
spec -> schemas -> TCK -> implementations
```

TCK cases prove normative requirements. A case MUST NOT invent semantics that are absent from the referenced specification.

## Layout

- `profiles/`: named conformance profiles and conditional capabilities.
- `cases/`: machine-readable conformance vectors grouped by protocol domain.
- `schemas/`: machine contracts for TCK metadata and reports.
- `reports/`: examples and report documentation.
- `registry.yaml`: the canonical discovery index for TCK case files.
- `RUNNER_CONTRACT.md`: language-neutral runner behavior and result semantics.

## Versioning

TCK resource documents use the `avp.tck/v0.1` API namespace. TCK resource versioning is distinct from the AVP protocol wire/specification version and from any reference implementation package version.

A profile declares the exact normative requirement set it covers. Requirements with an applicability condition remain conditional requirements; they are not silently removed from the profile.

## Pass semantics

For an implementation to claim conformance to a profile:

- every applicable mandatory case MUST report `PASS`;
- `FAIL` means the profile is not satisfied;
- `SKIP` does not count as `PASS`;
- a conditional case MAY report `SKIP` only when its declared applicability condition is false for the implementation under test.

The report MUST validate against `schemas/conformance-report.schema.json`.
