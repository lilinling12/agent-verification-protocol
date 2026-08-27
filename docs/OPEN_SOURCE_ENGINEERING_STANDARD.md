# AVP Open-Source Engineering Standard

Status: **Repository engineering policy — non-protocol**

This document defines engineering rules for the public AVP protocol-development monorepo and its reference implementations. It governs how code, tests, dependencies, fixtures, implementation boundaries, and security-sensitive repository content are structured. It does **not** define AVP protocol semantics.

The protocol authority order remains:

```text
Normative specification -> schema -> TCK/conformance -> reference implementation
```

If an engineering convenience conflicts with that authority order, the engineering convenience must change.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are used as project engineering requirements. They are not automatically AVP protocol requirements.

## 1. Design evidence, not template copying

AVP uses mature open-source projects as engineering evidence rather than copying their repository layouts mechanically. Relevant long-lived patterns include:

- OpenTelemetry: stable API/contract surfaces separated from SDK/reference implementation;
- pytest: explicit fixtures and stable extension contracts rather than hidden test setup;
- Playwright: clear handwritten/generated and public/private implementation boundaries;
- Selenium: browser-specific implementation mechanics isolated behind common contracts;
- Testcontainers: provider-specific optional dependencies instead of forcing every backend into the base installation;
- Kubernetes: explicit API/implementation boundaries and machine-enforced dependency discipline;
- Envoy: typed extension identities and explicit optional extension ownership;
- Python Packaging Authority guidance: entry points are appropriate only after a real extension contract exists.

These projects are references, not AVP authorities. AVP MUST NOT inherit a framework's abstractions merely because that framework is mature.

## 2. Protocol-first implementation

Implementation MUST follow reviewed protocol semantics; it MUST NOT create protocol semantics by precedent.

A reference backend MAY expose additional implementation-private mechanics, but those mechanics:

- MUST NOT alter portable TCK expectations;
- MUST NOT become required for independent AVP implementations unless standardized through the protocol process;
- MUST NOT leak vendor-native handles into portable public contracts;
- MUST NOT be used to justify a normative requirement after the fact.

Portable conformance code MUST NOT branch on implementation or vendor names to change expected semantics.

## 3. Responsibility-driven modules

Modules and packages MUST be created around reviewed responsibilities, not around an aesthetic directory tree.

Prefer names that state a domain responsibility, such as `resource`, `projection`, `control`, `evidence`, `state`, or `driver`, when those responsibilities actually exist.

Generic buckets such as `utils`, `helpers`, `common`, `base`, `manager`, `factory`, or `misc` SHOULD NOT be introduced without a narrow, documented responsibility.

AVP follows this rule:

> Split responsibilities; do not abstract protocol semantics.

Or, equivalently: **拆职责，不抽象协议。**

Do not create empty future-facing packages merely to make the repository look layered.

## 4. Evidence before abstraction

Shared abstractions MUST follow demonstrated stable semantics, not apparent code similarity.

In particular:

- composition SHOULD be preferred before inheritance;
- a generic `Base*Backend`, `Base*Adapter`, or cross-provider framework MUST NOT be introduced only because two current implementations look similar;
- a shared abstraction SHOULD have at least two real consumers or another concrete interoperability reason;
- a new abstraction MUST preserve the protocol authority boundary and MUST be removable without changing normative semantics.

Protocol portability is proven by specification and TCK behavior, not by inheritance from the same Python base class.

## 5. Public and internal API boundaries

Public interfaces MUST expose AVP-governed types rather than driver/vendor-native objects.

Cross-module and public boundaries MUST be typed. Stable boundary models SHOULD avoid unstructured `dict` and unconstrained `Any` when a precise representation exists.

Implementation-private types MAY use native library objects internally, but those objects MUST NOT become portable identity, serialized protocol state, or conformance evidence merely because they are convenient.

Public API additions require documentation, compatibility analysis, and tests. Internal pre-release layouts do not receive compatibility shims merely because they once existed on `main`.

## 6. Optional implementation dependencies

Backend/provider dependencies MUST be optional when the base AVP distribution does not require that backend.

The base distribution MUST remain installable and usable for its advertised capabilities without optional database, browser, container, cloud, or provider dependencies.

Optional backends SHOULD:

- use explicitly named dependency extras;
- import heavy/provider dependencies lazily at the implementation boundary;
- produce a precise dependency-unavailable error when invoked without the extra;
- avoid downloading runtime binaries during unrelated base-package import or installation;
- receive built-wheel installation and smoke/conformance coverage when packaging changes.

## 7. Subject, Evaluator, and privileged control separation

Subject-visible capabilities MUST remain separate from evaluator-only or fixture-control authority.

Privileged fixture/reset/snapshot mutation seams MUST NOT be exposed merely because the reference implementation can access them.

A module that owns privileged control SHOULD be structurally distinct from subject-facing operations so review and dependency checks can detect authority leakage.

Security boundaries MUST fail closed: missing authority, ambiguous ownership, stale resource identity, or unsupported capability MUST NOT silently degrade into broader access.

## 8. TCK and implementation tests

The portable TCK tests protocol-observable behavior. Backend-specific integration tests test implementation mechanics. They are different artifacts.

TCK/conformance logic MUST NOT:

- import a vendor backend to determine expected semantics;
- skip a mandatory requirement simply because one backend cannot implement it;
- accept metadata self-declarations instead of executing behavior where the requirement is behavioral;
- depend on production services, private infrastructure, or hidden evaluator data.

Backend integration tests MAY exercise backend-native failure modes, launch options, drivers, or provider-specific cleanup behavior outside the portable TCK.

## 9. Deterministic fixtures and real execution

Conformance fixtures MUST be deterministic, synthetic, reproducible, and safe to publish.

Mandatory behavioral cases MUST execute real behavior at the boundary being certified. Mocks are appropriate for isolated unit tests and controlled failure injection, not as substitutes for mandatory conformance behavior.

Public fixtures MUST NOT depend on:

- production credentials or accounts;
- customer data;
- proprietary prompts or private corpora;
- hidden benchmark answers required for protocol compliance;
- private DNS names, internal service addresses, or private platform topology;
- mutable public Internet services when a controlled local fixture can provide the same portable behavior.

## 10. State, projection, and evidence discipline

State mutation/control, evaluator projection/observation, and retained evidence SHOULD remain separate responsibilities when the protocol distinguishes their authority.

Implementation-specific evidence capture MUST NOT redefine canonical protocol state. Paths, process IDs, native handles, and backend tokens are implementation details unless a normative contract explicitly says otherwise.

Canonicalization MUST be defined by the normative surface before an implementation relies on a digest for conformance.

## 11. Cleanup and failure semantics

Resource cleanup MUST preserve the primary failure. A secondary cleanup failure MUST NOT overwrite the conformance or runtime failure that triggered cleanup.

Cleanup SHOULD be idempotent and retry-safe where the underlying resource permits it.

Public errors SHOULD distinguish materially different conditions, such as:

- dependency unavailable;
- invalid fixture/configuration;
- unsupported capability;
- stale or foreign resource;
- projection/observation failure;
- restore/reset verification failure;
- backend protocol/driver failure;
- cleanup failure.

Do not collapse unrelated trust-boundary failures into a generic success/failure boolean or one catch-all exception at the public boundary.

## 12. Generated code

Generated files MUST identify their source of truth and MUST NOT be hand-edited to make tests pass.

When code generation is used, CI SHOULD verify that regeneration from the reviewed source produces no unexpected diff.

AVP MUST NOT introduce code generation solely for perceived architectural sophistication; generation requires a concrete maintenance or interoperability benefit.

## 13. Compatibility and deprecation

Compatibility policy protects released public contracts, not every historical internal implementation shape.

A compatibility shim, alias, or deprecation path MUST have an identified released consumer/API contract or an explicit protocol interoperability reason.

Unreleased experimental APIs MAY be changed directly when governance and release policy allow it, with focused migration notes where useful.

## 14. Extension and plugin policy

Dynamic plugin discovery MUST NOT be introduced before the extension contract is stable enough to support independent implementations.

An entry-point/plugin design becomes appropriate only with evidence such as:

- a second independent backend/provider;
- a real third-party extension contributor;
- a stable extension contract already exercised by multiple implementations; or
- a separately approved interoperability requirement.

Explicit construction/registration is preferred while the contract is still evolving.

## 15. Dependency direction and architecture tests

Architecture constraints that can be checked mechanically SHOULD become CI checks.

Examples include:

- normative surfaces do not import reference implementation code;
- portable conformance code does not import backend-specific implementations;
- subject-facing code does not depend on privileged fixture/control modules;
- optional backend dependencies are absent from the base dependency set;
- repository policy documents and machine-readable boundaries remain present and internally consistent;
- generated outputs reproduce from source when generation is adopted.

A Markdown rule that is cheap and reliable to automate SHOULD NOT remain documentation-only indefinitely.

## 16. Comments and maintainability

Comments SHOULD explain invariants, authority, security consequences, portability constraints, cleanup guarantees, or non-obvious backend workarounds.

Comments SHOULD NOT narrate obvious syntax.

A workaround tied to a backend/version MUST state why it exists and which observable invariant it preserves. It MUST NOT silently change portable semantics.

## 17. Pull-request engineering evidence

Every implementation PR MUST remain one coherent work unit and provide evidence appropriate to its risk.

Review MUST be able to answer:

| Dimension | Required evidence |
|---|---|
| Authority | implementation does not redefine protocol semantics |
| Scope | one reviewable work unit |
| Architecture | dependency direction remains valid |
| Packaging | base and optional distributions remain truthful |
| Security | Subject/Evaluator/control boundaries are preserved |
| Conformance | mandatory behavior is executed where applicable |
| Portability | backend workarounds stay out of portable expectations |
| Failure handling | negative and cleanup paths are covered |
| Compatibility | only released/public contracts receive compatibility burden |
| Documentation | public behavior and known limitations are discoverable |
| CI | exact-head evidence is attributable to the reviewed commit |

A PR SHOULD remain Draft while a required row is unresolved.

## 18. Security-safe openness

AVP is an open protocol project. All normative semantics necessary for an independent implementation to interoperate and conform MUST be publicly reviewable.

Security confidentiality MUST NOT be used to create hidden protocol requirements. If conformance depends on a private implementation detail, private corpus, secret service, or unpublished rule, that requirement is not a valid portable AVP requirement.

At the same time, openness does not require publishing operational secrets or sensitive data. The public repository MUST NOT contain real credentials, signing secrets, production/customer data, proprietary prompts, hidden private benchmark corpora, private infrastructure coordinates, or embargoed exploit details. `SECURITY.md` governs disclosure handling.

A security fix MAY be developed under coordinated private disclosure. Any resulting normative protocol change MUST be reconciled into the public normative surfaces before it is treated as a released interoperability requirement.

Commercial/private platform implementations MAY remain private provided they do not define hidden semantics required for AVP conformance.

## 19. Supply-chain and repository security alignment

AVP uses external security frameworks as reference controls, not as protocol authority and not as automatic certification claims.

Current reference points include:

- OpenSSF Open Source Project Security Baseline: <https://baseline.openssf.org/>;
- OpenSSF Scorecard: <https://scorecard.dev/>;
- SLSA specification: <https://slsa.dev/spec/v1.2/>;
- GitHub Actions secure-use guidance: <https://docs.github.com/actions/security-guides/security-hardening-for-github-actions>.

Repository controls SHOULD prefer publicly auditable evidence: protected primary branches, least-privilege workflow tokens, full-SHA-pinned third-party Actions, deterministic/reproducible build checks where practical, dependency review/update automation, private vulnerability reporting, and attributable release provenance.

The project MUST NOT claim OpenSSF, SLSA, Scorecard, or similar compliance/certification solely because this document references those standards. Any future conformance statement must name the exact external version, assessment date, scope, and evidence.

## 20. Change control

Changes to this engineering standard are repository-governance changes, not protocol changes by themselves.

They MUST:

1. use a focused governance PR;
2. explain the maintenance/security/interoperability risk being addressed;
3. update machine-readable enforcement when a rule is suitable for automation;
4. preserve `GOVERNANCE.md`, `SECURITY.md`, and protocol authority boundaries;
5. avoid bundling unrelated protocol semantics or backend implementation work.

The authoritative repository-policy relationships are declared in `repository-boundaries.json` and validated by CI.
