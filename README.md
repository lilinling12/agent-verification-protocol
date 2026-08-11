# Agent Verification Protocol (AVP)

**Agent Verification Protocol (AVP)** is a proposed open protocol and reference implementation for verifying autonomous agents in reproducible environments.

AVP is built around one question:

> Can an independent evaluator prove what state changed, whether the change was authorized and correct, whether the evaluation itself was valid, and whether the result can be reproduced?

## Protocol boundary

```text
MCP  = Agent ↔ Tool / Context
A2A  = Agent ↔ Agent
OTel = Telemetry / trace context
AVP  = Scenario / Environment / Evidence / Verification / Replay
AVS  = Benchmark-as-Program DSL
```

## Core principles

- Agent Plane and Evaluator Plane are separate trust domains.
- Environment truth outranks Agent self-report.
- Agent failure and evaluator/environment failure are distinct.
- Verification results must be evidence-backed.
- Private chain-of-thought is not required.
- Replay fidelity must be declared rather than assumed.
- Reliability requires repeated runs and statistical evidence.

## Alpha reference implementation

The Python reference runtime currently demonstrates:

- Episode lifecycle
- capability-limited `SubjectSession`
- authoritative commerce State
- State digests and semantic diffs
- logical snapshot/restore
- state Oracles and evidence
- false-success detection
- first-bad-step localization
- deterministic fault lifecycle and recovery
- repeated reliability metrics
- conformance smoke tests

## Quick start

```bash
python -m pip install -e .
avp demo
avp conformance
avp benchmark --runs 8
```

Optional HTTP binding:

```bash
python -m pip install -e '.[http]'
avp serve --port 8790
```

## Status

AVP is currently an **experimental proposed open protocol**, not a formal standards-body standard.

The repository is intentionally structured so independent Java, Go, TypeScript, Python, SaaS and self-hosted implementations can conform to the same public protocol and TCK.
