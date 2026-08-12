# Agent Verification Protocol — Alpha Monorepo

This repository develops the proposed **Agent Verification Protocol (AVP)** together with its open-source reference implementation and early conformance assets.

It is intentionally an Alpha monorepo while protocol semantics are evolving. The repository layout does not make reference implementation behavior normative.

## Authority and repository boundaries

```text
spec/          normative protocol semantics
schemas/       machine-readable protocol contracts
conformance/   implementation-independent conformance/TCK assets
runtime/       reference runtime distribution boundary
adapters/      reference integration boundary
src/avp_ref/   current Python reference implementation
tests/         Python reference implementation tests
benchmarks/    AVS capability/reliability benchmark packs
```

Authority order: `Specification -> Schemas -> Conformance -> Reference Implementation`.

See `docs/ARCHITECTURE_BOUNDARIES.md` and `repository-boundaries.json`.

## Protocol ownership

```text
MCP  = Agent <-> Tool / Context
A2A  = Agent <-> Agent
OTel = Telemetry / trace propagation
AVP  = Scenario / Environment / Evidence / Verification / Replay
```

AVP does not require the commercial Agent Verification Platform. Hosted scheduling, enterprise environment fabric, production mining, failure intelligence, dashboards, and private benchmark data are separate product capabilities that may implement AVP.

## Reference implementation

The current Python implementation demonstrates immutable ScenarioInstance compilation, Episode lifecycle and Agent/Evaluator separation, Environment/Subject adapter SPIs, authoritative state projection/diff/snapshot, MCP verification, OpenTelemetry correlation, isolated Oracle execution, evidence verification, and early conformance/benchmark runners.

## Quick start

```bash
python -m pip install -e '.[dev]'
bash scripts/quality.sh
avp demo
avp conformance
```

Optional HTTP server:

```bash
python -m pip install -e '.[http]'
avp serve --port 8790
```

## Status

AVP is a draft open protocol, not a formal standards-body standard. Alpha releases may intentionally make breaking changes when doing so improves the eventual language-neutral protocol.

Repository governance is defined by `CONTRIBUTING.md`, `GOVERNANCE.md`, `SECURITY.md`, `docs/BRANCHING.md`, and `docs/RELEASE_PROCESS.md`.
