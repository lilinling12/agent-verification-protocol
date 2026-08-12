# AVP TCK Runner Contract v0.1

Status: Draft

## Purpose

This document defines the portable execution contract between an AVP TCK runner and an implementation under test. The runner evaluates registered conformance cases and emits a machine-valid `ConformanceReport`; it is not an Agent runtime and it is not a source of protocol semantics.

## Architecture

```text
TCK Registry
      |
      v
Runner
      |
      v
Implementation Adapter
      |
      v
Implementation Under Test
```

The registry, profile, and case resources are inputs. An adapter translates case actions into implementation-specific calls and translates observations back into case results. The adapter MUST NOT change TCK expectations to make an implementation pass.

## Inputs

A runner MUST receive or resolve:

- a conformance profile identifier;
- an immutable TCK registry identity;
- a complete-profile request or explicit case selection;
- implementation name and version; and
- declared conditional capabilities.

Example:

```yaml
profile: avp-core-v0.1
implementation:
  name: example-runtime
  version: 1.0.0
capabilities:
  - pause-capability-advertised
```

## Applicability

A `mandatory` or `mixed` case MUST execute and MUST NOT be reported as `SKIP`.

A `conditional` case executes when its `when` condition is present in the implementation's declared capabilities. When that condition is absent, the case MUST be reported as `SKIP` with an explicit `skipReason`. Runner or adapter implementation gaps are errors; they are never a reason to emit `SKIP`.

## Outputs

A successful runner execution MUST emit a `ConformanceReport` satisfying:

```text
conformance/tck/reports/report.schema.json
```

The report binds:

- profile identity;
- TCK registry version and digest;
- implementation name, version, and deterministic identity digest;
- declared capabilities;
- case PASS / FAIL / SKIP results and diagnostics; and
- an internally consistent result summary.

A runner MUST validate the report against the schema before publishing it. It MUST also verify semantic invariants that JSON Schema cannot express directly, including summary counts, case uniqueness, registry membership, conditional applicability, and identity digest consistency.

## Result semantics

`PASS` means the implementation satisfied the case assertions.

`FAIL` means the implementation was evaluated successfully and violated at least one assertion represented by the case.

`SKIP` means and only means that an explicit conditional capability was not declared and the case therefore did not apply.

A case evaluation that cannot be performed safely or deterministically because the runner, registry, adapter, schema, or implementation transport is invalid is a runner error, not `FAIL` and not `SKIP`.

## CLI exit status profile

The reference CLI uses the following portable convention:

- `0`: a valid report was produced and contains zero failed cases;
- `1`: a valid report was produced and contains one or more failed cases;
- `2`: no trustworthy conformance result could be produced because execution or contract validation failed.

Other TCK runners MAY expose platform-specific process status conventions, but they MUST preserve the distinction between protocol non-conformance and runner invalidity in their machine output or API.

## Evidence

Evidence is implementation-produced material referenced by a case result. The TCK defines evidence requirements and identity semantics, not storage technology. Evidence references may later resolve to content-addressed artifacts, signed event records, lifecycle streams, replay manifests, or other protocol-defined material.

## Non-goals

The runner does not standardize Agent architecture, model provider, tool implementation, deployment platform, benchmark score, or commercial certification service.
