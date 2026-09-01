# Alpha 3 Playwright Browser Provider Foundation Closure Audit

Status: **FOUNDATION REVIEW-CLOSED — FULL BROWSER PROFILE SUPPORT NOT YET ESTABLISHED**

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

The Playwright/Chromium foundation is sufficiently implemented and independently exercised to serve as a concrete backend for the next executed-provider work.

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
- fail-closed detection when a requested synthetic cookie expiry is not representable by the concrete browser/provider path.

The foundation is therefore **review-closed for these responsibilities**.

Complete `avp-browser-unpartitioned-cookie-localstorage-v0.1` conformance is **not yet established**, because the remaining mandatory execution controls and provider-neutral Browser TCK evaluator are not implemented. The previously recorded conclusion that arbitrary-nanosecond cookie expiry alone blocks the entire profile was too broad and is corrected below.

## 2. Exact-head validation evidence

At semantic head `208bed15f8c6bae9278171495313a94f6262031f`:

- CI `#740`: **SUCCESS**
- Governance `#822`: **SUCCESS**
- Browser Reference `#6`: **SUCCESS**
- Relational Parity `#133`: **SUCCESS**

The subsequent closure-record head also passed its complete validation set before this correction.

Browser Reference used:

- Playwright Python `1.62.0`;
- Chrome for Testing `151.0.7922.34` / Playwright Chromium revision `1234`;
- Python `3.13` on Ubuntu `24.04`;
- wheel-installed optional Browser dependency path rather than the repository source environment.

The real Browser integration suite executed eight tests and reported `OK`. It explicitly proved:

1. cookie selection remains independent from localStorage selection;
2. execution-binding and temporal controls fail closed;
3. the materialized fixture binds the running browser identity;
4. a browser-representable baseline independently reprojects to canonical identity;
5. reset preserves excluded cookie state;
6. an intentionally non-representable synthetic expiry fails closed rather than being rounded and falsely reported as exact;
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

Domain-scoped cookies use a leading-dot domain only as Playwright seeding syntax. Portable stored-domain identity remains the canonical provenance value without the presentation dot. `hostOnly` is never inferred from provider domain text.

## 4. Cookie observation and provenance review

### 4.1 Cookie selection is independent from localStorage selection

PASS after closure fix.

The first provider implementation queried cookies only through selected `localStorageOrigins`. That incorrectly coupled two independent Browser Manifest selections and could omit a selected cookie domain with no corresponding selected localStorage origin.

The corrected implementation enumerates current context cookies and filters their normalized observed domain against Manifest `cookieDomains`. A real Chromium regression materializes localStorage only for `b.test` while keeping selected cookies for `a.test`; the selected `a.test` domain cookie remains observable and participates in canonical projection.

### 4.2 Lossy cookie identity/state uses current observation plus provenance

PASS for foundation scope.

Current browser observation is correlated with evaluator/control-owned provenance. Missing, ambiguous, conflicting, or untracked selected cookies fail closed.

The provider does not reconstruct `hostOnly`, `SameSite=Default`, or expiry merely from Playwright's exported cookie object.

### 4.3 Expiry representation versus browser representability

PASS after correction of the closure interpretation.

The BrowserStateImage wire model represents persistent expiry as:

```text
(unixSeconds, nanoseconds)
```

That representation can losslessly describe an expiry instant independently of any particular browser's native resolution. It does **not** imply that every conforming browser must be capable of storing every mathematically representable nanosecond value.

The Browser normative requirement is that every **selected cookie actually admitted into authoritative browser state** have its required state, including its actual persistent expiry instant, established without ambiguity. If a requested seed value is rounded or truncated before becoming browser state, an evaluator must not claim that the requested value was stored exactly.

The provider therefore correctly fails closed when asked to seed the synthetic fixture value:

```text
unixSeconds = 1800000000
nanoseconds = 123456789
```

through Chromium when that value is not representable by Chromium's actual cookie time model.

That fail-closed result demonstrates provider honesty. It does **not by itself establish a profile-level blocker**.

The portable TCK reinforces this distinction:

- `AVP-TCK-BROWSER-STATE-IMAGE-001` is `schema-and-semantic` and uses `123456789ns` to exercise the closed serialized StateImage representation;
- `AVP-TCK-BROWSER-COOKIE-001` is `semantic-and-execution-sensitive` and requires persistent expiry to be preserved losslessly, but does not mandate that real browser execution materialize that specific arbitrary-nanosecond vector.

For a real provider execution, the positive expiry control may use a browser-representable persistent expiry as long as the evaluator independently proves that the browser's actual stored expiry is projected exactly and any rounded/truncated requested value is rejected.

No Browser Spec, Schema, or TCK weakening is required for this interpretation.

## 5. Fixture-role boundary

The repository currently uses one shared Browser fixture source for backend-neutral harness/canonicalization work. That fixture legitimately contains a non-zero arbitrary nanosecond value because the in-memory harness can exercise the full portable serialization domain.

A concrete browser execution fixture has a different responsibility: it must choose logical state that the tested browser can actually materialize while still exercising every portable semantic requirement.

Therefore the next provider work should explicitly separate these fixture roles rather than treating either as authority over the other:

```text
serialization/canonical fixture
    -> may exercise full wire-domain values such as 123456789ns
    -> validates canonical model and representation

provider-neutral executable fixture
    -> uses values representable across the claimed browser execution set
    -> still requires exact observation and rejects rounding/truncation
    -> does not narrow the BrowserStateImage wire model
```

A test-only derived zero-nanosecond fixture was sufficient for the foundation smoke, but the executed-TCK slice should replace that ad-hoc derivation with an explicitly governed provider-neutral executable fixture before conformance activation.

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

The concrete provider performs snapshot/reset/restore mechanics, but the shared backend-neutral Browser harness remains responsible for positive settlement gating, independent authoritative projection, SnapshotRef ownership/state binding, reset baseline verification, restore target reprojection, and successful restore fidelity exactly `STATE_EQUIVALENT`.

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

This remains correct because the provider-neutral executable fixture, real partitioned-cookie control, positive delayed-mutation settlement, real excluded-state interference, Subject/evaluator secrecy, metadata-identical negative controls, and provider-neutral Browser TCK evaluator are not yet complete.

The following remain incorrect at this point:

- adding any partial subset of Browser IDs to `supported_case_ids`;
- marking the Browser candidate profile as reference-supported;
- treating successful Browser Reference foundation tests as a Browser profile conformance result;
- weakening expiry representation to provider precision;
- treating Playwright's exported cookie representation as protocol authority.

## 11. Remaining provider work before Browser profile activation

The next governed work is no longer an attempt to make Chromium store arbitrary nanoseconds. It is to close the executable conformance path honestly:

1. **Provider-neutral executable Browser fixture** — separate execution vectors from serialization-only vectors; choose a persistent expiry representable by the claimed browser set while preserving exact-observation and rounded/truncated negative controls.
2. **Expiry capability proof** — document the concrete browser's native expiry resolution and verify that provider observation can recover the browser's actual stored expiry exactly at that resolution.
3. **Partitioned-cookie negative control** — create real partitioned state and prove it is not admitted into unpartitioned authoritative state.
4. **Positive delayed-mutation settlement** — exercise accepted profile-relevant mutation tracking against real browser behavior without reducing settlement to provider idleness.
5. **Excluded-state interference** — create and observe a material excluded-state interference condition rather than relying only on a synthetic flag.
6. **Subject/evaluator secrecy** — prove evaluator-private selected state and privileged controls are not exposed through the Subject surface.
7. **Metadata-identical negative controls** — run behaviorally broken implementations with identical metadata and require portable failures.
8. **Provider-neutral Browser TCK evaluator** — route all mandatory cases through the concrete backend without provider-name branching.
9. **Atomic support activation** — all eight Browser case IDs may be activated only when the complete mandatory profile passes; partial ownership remains forbidden.

## 12. Closure result

Corrected result:

- Playwright Browser provider foundation architecture: **REVIEW-CLOSED**.
- Concrete Chromium selected-state/isolation/lifecycle foundation: **VERIFIED for browser-representable expiry inputs**.
- Current observation/provenance fail-closed behavior: **VERIFIED**.
- Selected/excluded state preservation: **VERIFIED**.
- Synthetic arbitrary-nanosecond seed that Chromium cannot represent: **FAIL-CLOSED VERIFIED**.
- Arbitrary-nanosecond wire representation: **REMAINS VALID PORTABLE SERIALIZATION SEMANTICS**.
- Arbitrary-nanosecond Chromium storage capability: **NOT REQUIRED FOR PROFILE CONFORMANCE**; the actual stored browser expiry must instead be projected losslessly.
- Complete Browser v0.1 reference conformance: **NOT YET ESTABLISHED** for the remaining execution controls/evaluator work.
- Eight Browser TCK case ownership: **MUST REMAIN INACTIVE UNTIL COMPLETE PROFILE EXECUTION PASSES**.
- AEP-0011 Final: **NOT AUTHORIZED**.
- Merge of #117 or its parent stack: **NOT AUTHORIZED**.
- Release/tag/publication/signing/attestation: **NOT AUTHORIZED**.

The next governed work unit is **Browser executable-fixture and expiry-capability closure**, followed by the remaining real execution controls — not an AEP semantic weakening and not immediate Browser TCK activation.
