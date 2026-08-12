# AVP TCK Runner Contract

Status: Draft, non-wire tooling contract for AVP v0.1.

This document defines the minimum behavior expected from a TCK runner without prescribing a programming language, process model, transport, or deployment topology.

## Inputs

A runner consumes one TCK registry revision, one declared conformance profile, the case vectors selected by that profile/registry, an implementation-under-test descriptor, and implementation-specific binding/configuration needed to exercise the vectors. Binding configuration is runner-specific and is not AVP protocol semantics.

## Integrity before execution

Before executing any case, a runner MUST reject an internally inconsistent TCK bundle. At minimum it verifies that every selected case is registered exactly once; registry paths resolve to matching case IDs, profiles, and requirement sets; referenced requirements exist; mandatory profile requirements are covered; and TCK schemas are valid.

The repository implementation of these checks is `scripts/validate_tck.py`; third-party runners may implement equivalent checks independently.

## Result states

Each selected case produces exactly one of `PASS`, `FAIL`, or `SKIP`.

`PASS` means the observable behavior satisfies the case. `FAIL` means it contradicts the referenced requirement(s). `SKIP` is permitted only when a declared conditional applicability predicate is false.

A runner MUST NOT use `SKIP` to hide infrastructure errors, unsupported mandatory Core behavior, or an execution failure. Those conditions prevent a positive profile-conformance claim.

## Conditional cases

A conditional case may be skipped only when both the profile and normative requirement index identify the same applicability condition and the implementation does not advertise that capability. If the capability is advertised, the case becomes mandatory and must `PASS`.

## Reports

A runner emits a report conforming to `schemas/conformance-report.schema.json`. Aggregate counts MUST equal the case-result list. A conforming runner MUST NOT report profile conformance when any applicable case is `FAIL` or any mandatory case is `SKIP`.

## Non-authority of runners

Runner implementation behavior is not a source of AVP semantics. Conflicts among runner behavior, case vectors, schemas, and normative specification must be resolved through AVP specification/conformance governance rather than by treating one runner as authoritative.
