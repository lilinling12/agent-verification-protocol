# Alpha 3 Browser Acceptance-Evidence Tooling Placement

Status: **REVIEWED PLACEMENT DIRECTION — NON-NORMATIVE EVIDENCE ONLY**

Parent evidence PR: #109  
Parent evidence head at review start: `e4dc8d2154f865a2ba1559b50d42fd62cb1f311b`

## 1. Decision

Browser cross-engine acceptance-evidence tooling should be introduced, if needed, under:

```text
tests/acceptance/browser/
```

with fixture assets owned by the same non-normative test responsibility, for example:

```text
tests/acceptance/browser/fixtures/
```

A dedicated GitHub Actions workflow may execute that acceptance evidence.

This placement is intentionally **not**:

- `conformance/` or `conformance/fixtures/`;
- `src/avp_ref/tck_adapter/`;
- `src/avp_ref/browser/`;
- `adapters/`;
- a new top-level `browser/`, `experiments/`, `providers/`, or `drivers/` tree.

## 2. Why this is the correct current boundary

AEP-0011 remains `Proposed`. Browser normative Spec, Schema, language-neutral TCK, backend-neutral conformance harness, and reference runtime are not authorized.

The current work is narrower: produce independently reviewable implementation evidence for BPR-003, BPR-004, and BPR-009 without allowing that evidence mechanism to define portable protocol semantics.

Repository engineering policy already distinguishes portable TCK behavior from backend-specific integration tests. The acceptance-evidence runner belongs to the latter class until the Browser protocol reaches the lifecycle state required for normative downstream closure.

`tests/acceptance/browser/` makes that status visible in the path itself:

- test-only;
- acceptance evidence rather than normative conformance;
- browser-specific mechanics permitted internally;
- not packaged into the reference wheel;
- removable/rewriteable without changing protocol authority.

## 3. Why not `conformance/`

`conformance/` represents implementation-independent protocol conformance artifacts. Placing the current Browser evidence runner or fixture there would imply a language-neutral Browser TCK before AEP-0011 is Accepted and before a Browser normative Spec exists.

The current BAE cases are acceptance evidence derived from a Proposed AEP. They may later inform a separately governed TCK, but must not become the TCK by directory precedent.

## 4. Why not `src/avp_ref/tck_adapter/`

The Relational State parity verifier in `src/avp_ref/tck_adapter/` was introduced after the Relational protocol authority slice was Accepted and after the portable TCK/harness responsibilities existed.

Browser is not at that stage.

Adding a Browser verifier there now would create a misleading dependency direction:

```text
Proposed AEP
  <- implementation/test helper in packaged source
```

rather than the required future direction:

```text
Accepted AEP
  -> normative Spec
  -> Schema where required
  -> language-neutral TCK
  -> conformance harness
  -> reference implementation
```

## 5. Why not `adapters/` or a provider package

The evidence runner may need an automation transport to launch Chromium, Gecko, and WebKit-family engines. That does not make the transport an AVP adapter contract.

No stable Browser provider extension point exists yet. Introducing `BaseBrowserBackend`, `BrowserProvider`, entry points, factories, or plugin discovery would violate the repository's evidence-before-abstraction rule.

Transport construction should remain explicit and local to the acceptance test layer.

## 6. Dependency policy

Browser evidence dependencies must not enter base project dependencies.

If Python package dependencies are required, they should be installed only in the dedicated acceptance workflow or, if repeated local execution later justifies it, through a narrowly named optional development/evidence extra. The base wheel must remain installable and usable without browser tooling.

Browser binaries must not download during ordinary package install, import, CI quality lanes, or non-browser workflows. A dedicated Browser acceptance job may provision exact browser builds as an explicit test step and must record their identities.

## 7. Fixture policy

The fixture must be:

- synthetic;
- deterministic;
- localhost-controlled;
- safe to publish;
- independent of production accounts and credentials;
- independent of mutable public Internet services;
- able to use controlled hostnames mapped locally where origin/subdomain behavior is required.

A suitable execution topology may map reserved test hostnames to loopback within the dedicated CI job, allowing controlled first-party, subdomain, and cross-site cases without external DNS dependency.

Fixture-control authority must remain test/evaluator-private and must not be exposed as Subject capability.

## 8. Transport policy

Playwright, WebDriver, WebDriver BiDi, or another mechanism may be used strictly as test transport.

Portable expectations must be expressed in AVP-defined and browser-observable terms.

Transport APIs may supply diagnostics, but must not redefine:

- cookie identity;
- `SameSite=Default` semantics;
- storage partition identity;
- BrowserStateManifest selection semantics;
- BrowserStateImage canonical representation;
- settlement truth;
- restore fidelity.

If a transport cannot expose enough information to establish an AVP-required field, the evidence result is `unsupported`/fail-closed for that path rather than a reason to delete the field from the protocol.

## 9. Initial module responsibility guidance

The first executable evidence slice should remain small. Prefer explicit test modules such as:

```text
tests/acceptance/browser/
  test_cookie_identity_evidence.py
  test_localstorage_evidence.py
  test_settlement_evidence.py
  fixtures/
    ...
```

Do not start with generic buckets such as:

```text
base.py
utils.py
common.py
manager.py
factory.py
```

If multiple test modules later share a stable fixture-server or transport responsibility, extract that responsibility only after the duplication and invariants are concrete.

## 10. Workflow direction

A future dedicated workflow should:

1. check out the exact repository head;
2. install only the test/evidence dependencies needed by this workflow;
3. provision exact Chromium, Gecko, and WebKit-family builds;
4. record engine/build and relevant execution identity;
5. start only controlled local fixture services;
6. run BAE cases with the same portable expectation model across engine families;
7. retain machine-readable evidence artifacts;
8. fail when a mandatory case fails or is silently skipped;
9. distinguish an explicitly expected fail-closed/unsupported result from an infrastructure failure;
10. avoid changing existing CI, Governance, Relational Parity, or Release Validation semantics merely to host Browser evidence.

The dedicated workflow is evidence infrastructure, not a Browser TCK profile.

## 11. Current authorization boundary

This placement decision authorizes only the **location and engineering shape** of non-normative Browser acceptance-evidence tooling if the evidence phase proceeds.

It does not authorize:

- Browser normative Spec or requirement index;
- Browser Schema;
- Browser language-neutral TCK;
- Browser conformance harness;
- packaged Browser runtime/provider;
- Playwright adapter as official AVP behavior;
- generic Browser backend abstraction;
- AEP-0011 `Proposed -> Accepted`;
- release selection/publication/signing/attestation.

## 12. Conclusion

```text
Acceptance evidence tooling: tests/acceptance/browser/
Fixture ownership: same non-normative test responsibility
Dedicated workflow: permitted as evidence infrastructure
Packaged src Browser code: not authorized
conformance/ Browser artifacts: not authorized
provider/plugin abstraction: not justified
```

This preserves the repository authority chain while allowing the three-engine acceptance question to be answered with real executable evidence.