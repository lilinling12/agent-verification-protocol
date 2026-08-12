# AVP TCK Runner Contract v0.1

Status: Draft

## Purpose

This document defines the portable execution contract between an AVP TCK runner and an Agent implementation under test.

The runner is not an Agent runtime. The runner evaluates conformance cases and produces a conformance report.

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
Agent Implementation
```

## Inputs

A runner MUST receive:

- Conformance profile identifier.
- Immutable TCK registry version.
- Case selection or complete profile execution request.
- Implementation identity.
- Declared capabilities.

Example:

```yaml
profile: avp-core-v0.1
tckVersion: 0.1.0
implementation:
  name: example-agent
  version: 1.0.0
capabilities:
  - pause-capability-advertised
```

## Outputs

A runner MUST emit a `ConformanceReport` satisfying:

```
conformance/tck/reports/report.schema.json
```

The report MUST contain:

- TCK registry identity.
- Implementation identity.
- Executed cases.
- PASS / FAIL / SKIP result.
- Evidence references.

## Result semantics

PASS:

The implementation satisfied the case assertions.

FAIL:

The implementation violated the protocol requirement.

SKIP:

The case was not applicable because an explicit capability condition was false.

A mandatory case MUST NOT be SKIPPED.

## Evidence

Evidence is implementation-produced material referenced by the report. TCK defines evidence requirements, not storage technology.

Examples:

- Signed transition records.
- Lifecycle event streams.
- Verification artifacts.
- Replay manifests.

## Non-goals

The runner does not standardize:

- Agent architecture.
- Model provider.
- Tool implementation.
- Deployment platform.
- Performance benchmark.
