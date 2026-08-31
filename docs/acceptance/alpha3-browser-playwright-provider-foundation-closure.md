# Alpha 3 Playwright Browser Provider Foundation Closure Audit

Status: **FOUNDATION REVIEW-CLOSED — FULL BROWSER PROFILE SUPPORT BLOCKED BY EXACT COOKIE EXPIRY FIDELITY**

Provider foundation semantic head: `208bed15f8c6bae9278171495313a94f6262031f`  
Owning pull request: `#117`  
Base harness pull request: `#116`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

Governing authority remains, in order:

1. AEP-0011 Browser Resource Profile v0.1 (`Accepted`)
2. Browser normative state/serialization specifications
3. Browser requirement index and closed schemas
4. provider-neutral Browser TCK profile and eight mandatory cases
5. backend-neutral Browser conformance harness
6. this Playwright/Chromium provider implementation

This audit closes the first concrete provider **foundation** only. It does not alter portable Browser semantics, declare Browser profile conformance, activate Browser TCK case ownership, authorize merge, or advance AEP-0011 to Final.

## 1. Closure decision

The Playwright/Chromium foundation is sufficiently implemented and independently exercised to serve as a concrete backend for the next provider investigation work.

The foundation has demonstrated, against a real installed Chromium build:

- one independently isolated `BrowserContext` per Browser Resource;
- execution-input binding to the running Playwright engine/browser version before fixture materialization;
- browser-backed WHATWG origin/domain canonicalization checks;
- exact UTF-16 code-unit localStorage observation;
- evaluator/control-owned cookie provenance instead of provider serialization as protocol authority;
- selected-cookie observation independent of selected localStorage origins;
- sibling selected-state isolation;
- selected-state reset without deleting excluded cookie state;
- snapshot/reset/restore mechanics with independent harness reprojection;
- fail-closed execution-binding drift and temporal-eligibility controls;
- fail-closed detection when provider cookie expiry transport cannot preserve exact portable expiry.

The foundation is therefore **review-closed for these responsibilities**.

It is **not eligible to claim the complete `avp-browser-unpartitioned-cookie-localstorage-v0.1` profile** because the current Playwright/Chromium cookie transport cannot losslessly round-trip the shared portable fixture's persistent expiry value with non-zero nanoseconds.

## 2. Exact-head validation evidence

At semantic head `208bed15f8c6bae9278171495313a94f6262031f`:

- CI `#740`: **SUCCESS**
- Governance `#822`: **SUCCESS**
- Browser Reference `#6`: **SUCCESS**
- Relational Parity `#133`: **SUCCESS**

Browser Reference `#6` used:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision `1234`;
- Python `3.13` on Ubuntu `24.04`;
- wheel-installed optional Browser dependency path rather than the repository source environment.

The real Browser integration suite executed eight tests and reported:

```text
Ran 8 tests in 18.908s
OK
```

The suite explicitly proved:

1. cookie selection remains independent from localStorage selection;
2. execution-binding and temporal controls fail closed;
3. the materialized fixture binds the running browser identity;
4. provider-compatible baseline state independently reprojects to canonical identity;
5. reset preserves excluded cookie state;
6. the unchanged shared portable fixture fails closed when exact expiry precision is lost;
7. snapshot/reset/restore use real browser state and independent reprojection;
8. sibling Browser resources do not share selected authoritative state.

Green automation is necessary evidence for this closure but is not, by itself, the closure authority.

## 3. Provider authority boundary review

### 3.1 Playwright does not define Browser semantics

PASS.

Playwright concepts remain implementation mechanics. `BrowserContext`, Page objects, launch configuration, provider cookie presentation syntax, and provider enumeration order do not appear in the portable TCK vocabulary or BrowserStateManifest/BrowserStateImage representation.

The implementation binds its concrete engine/version into an existing execution-binding slot as a `version` identity. It does not originate a new protocol field or provider capability identity.

### 3.2 BrowserContext isolation is implementation evidence, not protocol identity

PASS.

One Browser Resource is backed by one independently created Playwright `BrowserContext`, but the context object is not exposed as the Fabric Resource identity. Sibling resources are exercised as separate contexts and their selected state is independently reprojected.

### 3.3 Provider cookie presentation syntax is non-authoritative

PASS.

Domain-scoped cookies use a leading-dot domain only as Playwright seeding syntax. Portable stored-domain identity remains the canonical provenance value without the presentation dot. `hostOnly` is never inferred from the provider's domain text.

## 4. Cookie observation and provenance review

### 4.1 Cookie selection is independent from localStorage selection

PASS after closure fix.

The first provider implementation queried cookies only through selected `localStorageOrigins`. That incorrectly coupled two independent Browser Manifest selections and could omit a selected cookie domain with no corresponding selected localStorage origin.

The corrected implementation enumerates current context cookies and filters their normalized observed domain against the Manifest `cookieDomains`. A real Chromium regression test materializes localStorage only for `b.test` while keeping selected cookies for `a.test`; the selected `a.test` domain cookie remains observable and participates in the canonical projection.

### 4.2 Lossy cookie identity/state uses current observation plus provenance

PASS for foundation scope.

Current browser observation is correlated with evaluator/control-owned provenance. Missing, ambiguous, conflicting, or untracked selected cookies fail closed.

The provider does not reconstruct `hostOnly`, `SameSite=Default`, or exact expiry merely from Playwright's exported cookie object.

### 4.3 Persistent expiry is not overstated

PASS after closure fix; **full-profile blocker remains**.

The shared provider-neutral fixture intentionally includes a persistent cookie with:

```text
unixSeconds = 1800000000
nanoseconds = 123456789
```

The original provider foundation compared only integer expiry seconds and then reused provenance nanoseconds. That could falsely report a lossless BrowserStateImage even if Playwright/Chromium truncated the fractional expiry.

The corrected provider converts the actual observed Playwright expiry into an exact `(unixSeconds, nanoseconds)` pair and compares it against provenance before admitting the cookie into authoritative state.

Real Chromium evidence confirms that the unchanged shared fixture does not preserve the exact non-zero nanosecond value through this provider path. Provisioning therefore fails closed, as required.

The portable fixture, schema, specification, and TCK were **not changed** to accommodate Playwright.

## 5. Provider-compatible lifecycle fixture boundary

PASS, with explicit non-authority status.

The integration suite derives a test-only copy of the portable fixture whose persistent cookie expiry uses `nanoseconds = 0`. This copy exists only to exercise the implemented provider foundation lifecycle under a value the provider can independently observe exactly.

It is not a portable fixture replacement, is not TCK authority, and cannot be used to claim support for the unchanged portable Browser profile.

The distinction is intentional:

```text
portable shared fixture
    -> exact non-zero-nanosecond expiry
    -> Playwright provider loses fidelity
    -> FAIL CLOSED

provider-compatible foundation fixture
    -> provider-observable exact expiry
    -> lifecycle/isolation foundation smoke may execute
    -> NO full-profile conformance claim
```

## 6. Selected versus excluded state review

### 6.1 Reset/restore must not globally clear excluded cookies

PASS after closure fix.

The initial provider implementation used global `clear_cookies()`, which could delete cookies outside the Manifest selected authoritative state.

The corrected implementation clears only selected cookies represented by evaluator provenance and clears only selected localStorage origins. A real Chromium regression seeds an excluded `b.test` cookie, executes verified reset, and confirms that the excluded cookie remains while selected authoritative state returns to its canonical baseline.

### 6.2 Ambiguous cookie deletion remains fail-closed territory

PASS for foundation boundary.

Playwright's clear-cookie filter does not expose `hostOnly` as an independent deletion discriminator. The implementation therefore does not claim it can safely resolve every possible host-only/domain-scoped identity collision through provider filters.

Such collision handling must remain fail closed unless a later controlled mechanism can prove precise deletion without turning provider syntax into protocol semantics.

## 7. LocalStorage exactness review

PASS.

Observation iterates JavaScript strings by `text.length` and `charCodeAt(i)`, preserving UTF-16 code units rather than Unicode code points. This is necessary for unmatched surrogate values and remains aligned with Browser v0.1 canonical DOMString encoding.

Provider enumeration order is not authoritative; the shared harness canonicalizes the resulting BrowserStateImage.

## 8. Lifecycle and independent verification review

PASS for foundation scope.

The concrete provider performs snapshot/reset/restore mechanics, but the shared backend-neutral Browser harness remains responsible for:

- positive settlement gating;
- independent authoritative projection;
- snapshot ownership/state binding;
- reset baseline verification;
- restore target reprojection;
- reporting successful restore fidelity exactly as `STATE_EQUIVALENT`.

Provider command success or provider-produced state is never sufficient by itself.

## 9. Dependency and packaging boundary review

PASS.

Playwright is an optional Browser implementation dependency:

```text
playwright>=1.62,<1.63
```

Repository CI pins the tested implementation to `playwright==1.62.0`.

Importing the packaged Browser provider does not eagerly load Playwright. The base AVP wheel remains usable without Browser dependencies, while a dedicated Browser workflow installs the built wheel with `[browser]` and executes the real provider suite.

Dependency-policy validation requires this optional-wheel Browser integration path to remain present.

## 10. TCK ownership and conformance claim review

PASS — ownership remains intentionally inactive.

`ReferenceConformanceAdapter` has not been modified to own any Browser case IDs. The eight mandatory Browser cases therefore remain unsupported by the default reference implementation.

This is the correct state while full portable-fixture fidelity is not established.

The following would be incorrect at this point:

- adding all eight Browser IDs to `supported_case_ids`;
- marking the Browser candidate profile as reference-supported;
- using the provider-compatible fixture as a substitute for the portable fixture;
- treating the successful Browser Reference foundation workflow as a Browser profile conformance result;
- weakening expiry representation or replacing nanoseconds with provider precision;
- treating Playwright's exported cookie representation as protocol authority.

## 11. Remaining provider work before Browser profile activation

Full Browser profile support remains blocked by at least the following provider-facing work:

1. **Exact persistent cookie expiry** — identify a concrete browser-control/observation mechanism that can establish and independently verify the portable seconds/nanoseconds representation, or demonstrate that the current provider cannot support this Browser profile.
2. **Partitioned-cookie negative control** — create real partitioned state and prove it is not admitted into unpartitioned authoritative state.
3. **Positive delayed-mutation settlement** — exercise accepted profile-relevant mutation tracking against real browser behavior without reducing settlement to provider idleness.
4. **Excluded-state interference** — create and observe a material excluded-state interference condition rather than relying only on a synthetic flag.
5. **Subject/evaluator secrecy** — prove evaluator-private selected state and privileged controls are not exposed through the Subject surface.
6. **Metadata-identical negative controls** — run behaviorally broken implementations with identical metadata and require portable failures.
7. **Provider-neutral Browser TCK evaluator** — only after every mandatory behavior can be executed honestly against the concrete backend.
8. **Atomic support activation** — all eight Browser case IDs may be activated only when the complete mandatory profile passes; partial ownership remains forbidden.

## 12. Closure result

Final result for semantic head `208bed15f8c6bae9278171495313a94f6262031f`:

- Playwright Browser provider foundation architecture: **REVIEW-CLOSED**.
- Concrete Chromium selected-state/isolation/lifecycle foundation: **VERIFIED for provider-compatible exact-expiry inputs**.
- Current observation/provenance fail-closed behavior: **VERIFIED**.
- Selected/excluded state preservation: **VERIFIED**.
- Shared portable fixture exact non-zero-nanosecond expiry: **NOT LOSSLESSLY SUPPORTED; FAIL-CLOSED VERIFIED**.
- Complete Browser v0.1 reference conformance: **NOT ESTABLISHED**.
- Eight Browser TCK case ownership: **MUST REMAIN INACTIVE**.
- Browser profile candidate status in installed-wheel planning: **MUST REMAIN implementation-pending / no conformance claim**.
- AEP-0011 Final: **NOT AUTHORIZED**.
- Merge of #117 or its parent stack: **NOT AUTHORIZED**.
- Release/tag/publication/signing/attestation: **NOT AUTHORIZED**.

The next governed work unit is **exact Browser cookie-expiry capability investigation and provider control/observation design**, not Browser TCK support activation.
