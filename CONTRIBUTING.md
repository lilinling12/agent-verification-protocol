# Contributing to AVP

AVP is an experimental, vendor-neutral Agent Verification protocol and reference implementation. Contributions should improve interoperable verification semantics rather than bind AVP to one model, vendor, framework, or deployment stack.

## Start here

Before opening a change, read:

- `GOVERNANCE.md` for decision rights, policy authority, and normative-change rules;
- `docs/ARCHITECTURE_BOUNDARIES.md` for protocol/reference/product and public/private repository boundaries;
- `docs/OPEN_SOURCE_ENGINEERING_STANDARD.md` for implementation structure, dependency, fixture, testing, compatibility, and maintainability requirements;
- `docs/BRANCHING.md` for branch, commit, pull-request, and stacked-PR rules;
- `docs/RELEASE_PROCESS.md` for versioning and release requirements;
- `SECURITY.md` for vulnerability reporting and security-sensitive disclosure.

Do not put vulnerability details, production/customer data, real credentials, private infrastructure information, or non-redistributable evaluation assets into a public issue or pull request. Follow `SECURITY.md` for sensitive reports.

## Contribution licensing

Unless a contribution explicitly states otherwise before submission and the maintainers agree to different terms, contributions submitted to this repository are provided under the same Apache License 2.0 terms as the project.

By opening a pull request or otherwise submitting code, documentation, tests, schemas, conformance assets, or other repository content, you represent that you have the right to contribute that material under those terms.

This project does not currently require a Contributor License Agreement (CLA). If contribution scale, organizational requirements, or intellectual-property policy later justify additional contributor attestation, that change must be documented through normal repository governance before it becomes a contribution requirement.

## Contribution paths

- **Bug or ambiguity**: use the bug issue form and include a minimal synthetic reproducer when possible.
- **Small compatible change**: open a focused pull request with tests.
- **Normative protocol change**: open a protocol proposal; accepted proposals that materially change interoperable semantics must be captured as an AEP under `rfcs/` before they become Final.
- **New adapter or implementation**: preserve upstream protocol ownership boundaries and add conformance coverage.
- **Repository/engineering policy change**: use a focused governance PR and update machine-readable enforcement when the rule can be checked safely and deterministically.
- **Security-sensitive issue**: use the private disclosure path in `SECURITY.md`, not a public issue containing exploit or secret material.

## Normative changes

A change is normative when an independent implementation would need to change behavior to remain conformant. A normative proposal must explain:

1. the interoperability problem and motivating cases;
2. why the concern belongs to AVP rather than MCP, A2A, OpenTelemetry, JSON Schema, OCI, or another upstream standard;
3. observable semantics and failure behavior;
4. backward-compatibility and versioning impact;
5. security, authority, evaluator-leakage, and privacy impact;
6. schema/OpenAPI changes when applicable;
7. conformance tests and negative tests;
8. reference implementation changes or a reason they are not yet possible.

Implementation code alone does not define protocol semantics. Normative behavior must be documented and testable by independent implementations.

Security confidentiality does not create a normative exception: a released conformance requirement cannot depend on a hidden private rule, service, dataset, or implementation detail. A security fix may be coordinated privately, but any resulting normative semantics must be reconciled into the public protocol surfaces before release.

## Local quality gate

Use Python 3.11 or newer and run the same repository gate used by CI:

```bash
python -m pip install -e '.[dev]'
bash scripts/quality.sh
```

Before requesting review, also build and install the wheel when packaging behavior changed:

```bash
python -m build
python -m venv .wheel-venv
.wheel-venv/bin/python -m pip install dist/*.whl
.wheel-venv/bin/avp conformance
```

On Windows, use the equivalent `.wheel-venv\\Scripts\\...` executables.

## Pull-request expectations

Every PR must be reviewable as one coherent change. The PR template requires protocol, architecture/repository-boundary, security, compatibility, testing, and stacked-dependency information. Do not mix unrelated formatting, refactors, dependency upgrades, and semantic changes.

PR titles use Conventional Commit form because squash-merged PR titles become durable repository history, for example:

```text
feat(oracle): add isolated execution
fix(runtime): reject invalid transition
docs(governance): clarify AEP lifecycle
```

## Design rule

A capability belongs in AVP Core only when independent implementations need the same observable verification semantics. Product convenience, vendor-specific behavior, and reference-runtime implementation details belong outside the core protocol unless an AEP establishes an interoperability requirement.

Commercial/private platform capabilities may implement AVP but must not become hidden prerequisites for public conformance. Repository placement and implementation structure must remain consistent with `docs/ARCHITECTURE_BOUNDARIES.md`, `repository-boundaries.json`, and `docs/OPEN_SOURCE_ENGINEERING_STANDARD.md`.
