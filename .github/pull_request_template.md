## Summary

<!-- What does this PR change? Keep this focused on one coherent unit. -->

## Motivation

<!-- What concrete problem, ambiguity, interoperability need, maintenance risk, or governance risk does this solve? -->

## Protocol / conformance impact

- [ ] No normative protocol change
- [ ] Normative protocol change; proposal/AEP: <!-- link or identifier -->
- [ ] Schema/API change
- [ ] TCK/conformance change

Describe observable semantic changes, if any:

## Architecture / repository-boundary impact

<!-- Does this change authority direction, public/private boundaries, package ownership, optional dependencies, implementation layering, or future repository placement? State "none" with rationale when appropriate. -->

- [ ] Protocol authority still flows `spec -> schema -> conformance -> reference implementation`
- [ ] No private platform behavior/data becomes a hidden requirement for public conformance
- [ ] Reference/backend-specific mechanics remain non-normative

## Security / trust-boundary impact

<!-- Subject, Environment, Evaluator, Oracle, MCP, telemetry, secrets, authority, sandboxing, artifact integrity, etc. State "none" with rationale when appropriate. Do not paste sensitive vulnerability details, real secrets, production/customer data, or private infrastructure information into a public PR. -->

## Compatibility / versioning

<!-- Backward compatibility, migration requirements, deprecations/removals, and expected release impact. -->

## Test evidence

<!-- Exact automated/manual checks run. Add negative/failure-path coverage for trust-boundary changes. -->

- [ ] Unit/integration tests added or updated
- [ ] `bash scripts/quality.sh` passes
- [ ] Built-wheel smoke/conformance tested when packaging changed

## Stack metadata

Parent PR: <!-- none or #N -->

Dependent PRs: <!-- none or #N, #N -->

- [ ] This PR diff contains only this stack layer
- [ ] Parent dependency is stable enough for review

## Review checklist

- [ ] Public API/protocol models are typed and documented
- [ ] Failure semantics distinguish Agent failure from infrastructure/evaluation invalidity
- [ ] No evaluator secret/authority boundary is weakened unintentionally
- [ ] No compatibility shim is added without an explicit released/protocol reason
- [ ] Documentation and migration notes are updated where required
- [ ] No unrelated formatting/refactoring is bundled
