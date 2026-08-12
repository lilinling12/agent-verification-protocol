# AVP Conformance Test Kit (TCK)

Status: Draft architecture for AVP v0.1.

The AVP TCK is the implementation-independent conformance surface. It proves whether an implementation satisfies normative AVP requirements; it does not define those requirements and it is not the Python reference runtime test suite.

Authority remains one-way:

```text
specification -> requirement index -> schemas/TCK -> implementation conformance report
```

## Resources

- `profiles/`: named conformance profiles and conditional capabilities.
- `cases/`: machine-readable conformance vectors grouped by protocol domain.
- `registry.yaml`: the unique registry of TCK case identities, paths, requirements, and applicability.
- `reports/report.schema.json`: the portable result contract emitted by a conforming TCK runner.

## Conformance rules

A profile claim is valid only when every mandatory requirement in the profile has at least one registered TCK case and every applicable case passes. Conditional requirements are evaluated only when their declared capability condition is true. A skipped mandatory case never counts as a pass.

TCK cases MUST map to existing normative requirement IDs and MUST NOT invent protocol semantics. The Python reference implementation MAY execute these vectors, but Python-specific code and unit tests remain non-authoritative implementation evidence.

Benchmark scores are not conformance results.
