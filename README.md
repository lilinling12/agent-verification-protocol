# Agent Verification Protocol — Reference Implementation v0.1

This repository is a **working reference implementation** for the proposed Agent Verification Protocol (AVP).

It is intentionally small, inspectable and local-first. It demonstrates:

- Episode lifecycle
- Agent/Evaluator separation
- authoritative State
- State digests and diffs
- snapshot/restore
- claim/evidence verification
- false-success detection
- replay/intervention metadata
- AVP event timeline
- an initial conformance runner

## Architecture

```text
MCP  = Agent ↔ Tool
A2A  = Agent ↔ Agent
OTel = Telemetry
AVP  = Scenario / Environment / Evidence / Verification / Replay
```

## Quick start

```bash
python -m pip install -e .
avp demo
avp conformance
```

Optional HTTP server:

```bash
python -m pip install -e '.[http]'
avp serve --port 8790
```

## Important

This is a **draft open protocol/reference implementation**, not a formal standards-body standard.

The commercial Agent Verification OS should be able to replace every runtime component while preserving AVP conformance.

## Alpha benchmark smoke run

```bash
avp benchmark --runs 8
```

The bundled `enterprise-action-v0.1` AVS pack expands the design surface to Commerce, Calendar, Email, Files, Approval, and MCP orchestration. Only the Commerce Refund world is executable in the reference runtime today; the remaining templates drive the next Environment adapters.

## Repository governance

See `CONTRIBUTING.md`, `GOVERNANCE.md`, `SECURITY.md`, `ROADMAP.md`, and the AEP template under `rfcs/`.
