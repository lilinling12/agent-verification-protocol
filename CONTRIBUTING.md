# Contributing to AVP

AVP is intended to become a vendor-neutral Agent Verification protocol, not a product-specific API.

## Contribution paths

- **Bug / ambiguity**: open an issue with the affected requirement or schema.
- **Small compatible change**: open a PR with tests.
- **New protocol semantic**: submit an **AEP — AVP Enhancement Proposal** under `rfcs/`.
- **New adapter**: keep upstream protocol semantics intact and add conformance coverage.

## Required for normative changes

A normative change should include:

1. problem and motivating interoperability case;
2. why MCP/A2A/OpenTelemetry/JSON Schema/OCI/etc. do not already own the concern;
3. backward-compatibility analysis;
4. security and evaluator-leakage analysis;
5. schema/OpenAPI changes when applicable;
6. conformance tests;
7. at least one reference implementation change.

## Local checks

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
avp conformance
python -m pip install PyYAML jsonschema
python scripts/validate_assets.py
```

## Design principle

A proposed feature belongs in AVP Core only if independent implementations need the same observable verification semantics.
