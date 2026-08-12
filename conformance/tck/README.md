# AVP Conformance Test Kit (TCK)

Status: Draft architecture.

The TCK is the protocol conformance contract. It is independent from the Python reference runtime.

## Layers

- `profiles/`: negotiated AVP capability profiles.
- `cases/`: machine-readable conformance vectors.
- `reports/`: implementation result contract.

A reference implementation test suite may execute TCK cases, but it does not define protocol semantics.
