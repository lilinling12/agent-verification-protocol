# Alpha 3 Browser Cookie Expiry Capability Audit

Status: **DESIGN READY — NO AEP SEMANTIC CHANGE REQUIRED**

Parent provider foundation: `#117`  
Parent corrected head at audit start: `4cf681e7284597e1940a34666b56264b118741eb`  
AEP lifecycle: **AEP-0011 Accepted, not Final**

## 1. Question

The first real Playwright/Chromium Browser provider correctly demonstrated that Chromium does not retain the synthetic fixture expiry:

```text
unixSeconds = 1800000000
nanoseconds = 123456789
```

exactly.

The key governance question is not whether Chromium can store every value representable by BrowserStateImage. The actual question is:

> Does Browser v0.1 require every conforming provider to materialize arbitrary nanosecond expiry values, or does it require lossless projection of the expiry instant actually present in the selected browser state?

The reviewed answer is the latter.

## 2. Authority-chain reading

AVP-BROWSER-007 requires selected persistent cookies to preserve their expiry instant. AVP-BROWSER-008 requires every required selected-cookie state field to be established without ambiguity and requires fail-closed behavior when a provider cannot establish that state losslessly.

Neither requirement says that a browser implementation must be capable of storing every instant expressible by the portable `(unixSeconds, nanoseconds)` serialization.

The portable TCK reinforces the separation:

- `AVP-TCK-BROWSER-STATE-IMAGE-001` is `schema-and-semantic`. Its `123456789ns` value exercises the closed wire representation and canonical StateImage semantics.
- `AVP-TCK-BROWSER-COOKIE-001` is `semantic-and-execution-sensitive`. It requires a persistent expiry to be preserved losslessly and requires rounded/truncated provider behavior to be rejected, but it does not require the concrete execution path to materialize the exact arbitrary-nanosecond StateImage vector.

Therefore:

```text
wire-domain representability != mandatory native-browser storage domain
```

A provider conforms by projecting the browser's actual selected state exactly when it can and failing closed when it cannot. It must never replace the portable state model with provider precision.

## 3. Chromium native expiry resolution

Current Chromium stores `CanonicalCookie::expiry_date_` as `base::Time`.

Chromium's current `base::Time` documentation states that wall-clock time is internally represented in **microseconds** since the Windows epoch.

Consequences:

1. Chromium cannot natively represent arbitrary nanosecond cookie expiry instants.
2. A Chromium cookie expiry that is representable exactly has nanoseconds divisible by `1000` when converted to the BrowserStateImage `(unixSeconds, nanoseconds)` form.
3. Asking Chromium to materialize `123456789ns` necessarily changes the requested value before or at native storage admission.
4. A conforming adapter must detect that change if it is attempting to establish that requested fixture value and must not report the requested value as authoritative state.
5. This does not invalidate the BrowserStateImage nanosecond wire representation; that representation remains capable of encoding browser engines or future implementations with different time domains and avoids using JSON floating point as normative identity.

Authoritative external references reviewed:

- Chromium `CanonicalCookie`: <https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/cookies/canonical_cookie.h>
- Chromium `base::Time`: <https://chromium.googlesource.com/chromium/src/base/+/master/time/time.h>

## 4. Playwright transport capability

Playwright BrowserContext cookie APIs expose `expires` as a floating-point Unix time in seconds.

This transport does not itself define Browser expiry semantics and does not promise arbitrary-nanosecond retention. It can nevertheless be usable for a Chromium implementation if real execution proves that the transport can establish and re-observe Chromium's **actual native expiry** without ambiguity at the browser's supported resolution.

The implementation must therefore compare provider observation with the intended browser-representable value after a real browser round trip. It must not take the Python float value or successful `add_cookies()` completion as proof.

Reference:

- Playwright Python BrowserContext cookies/add_cookies: <https://playwright.dev/python/docs/api/class-browsercontext>

## 5. CDP transport capability

Chrome DevTools Protocol represents cookie expiry as `Network.TimeSinceEpoch`, a JSON `number` containing seconds since the Unix epoch. `Network.setCookie` accepts that representation and `Network.Cookie.expires` returns a numeric seconds value.

CDP therefore does not provide a separate normative seconds-plus-nanoseconds cookie field. Moving from Playwright to raw CDP would not increase Chromium's native storage resolution beyond `base::Time`.

A CDP seam could still be useful later for concrete controls Playwright does not expose, but **CDP must not be introduced merely to simulate arbitrary-nanosecond cookie storage that Chromium does not possess**.

Reference:

- Chrome DevTools Protocol Network domain: <https://chromedevtools.github.io/devtools-protocol/tot/Network/>

## 6. WebDriver BiDi capability

Current WebDriver BiDi defines cookie expiry as `js-uint` for both observed `network.Cookie.expiry` and `storage.PartialCookie.expiry` used by `storage.setCookie`.

That gives a protocol-level integer Unix timestamp and is therefore coarser than Chromium's internal microsecond time domain. The specification also notes that the remote end may further limit expiry.

A BiDi-only Browser backend can still behave correctly for selected state whose expiry is exactly observable through that path, and must fail closed for selected state whose required expiry cannot be recovered without loss. BiDi's coarser transport is not permission to redefine BrowserStateImage expiry to integer seconds.

Reference:

- W3C WebDriver BiDi: <https://www.w3.org/TR/webdriver-bidi/>

## 7. Three distinct resolution domains

Future implementation and TCK work MUST keep these layers separate:

### 7.1 Portable wire resolution

BrowserStateImage uses:

```text
expiry = {
  unixSeconds: signed canonical decimal string,
  nanoseconds: integer 0..999999999
}
```

This is the portable representation domain and is independent of a provider.

### 7.2 Browser native storage resolution

A concrete browser owns the state actually stored. Chromium currently uses a microsecond `base::Time` domain. Other browser engines may use different internal representations.

The adapter must not invent finer state than the browser possesses.

### 7.3 Control/observation transport resolution

Playwright, CDP, BiDi, native APIs, or another test-control mechanism may expose less, equal, or differently encoded precision than the native browser store.

If the transport cannot establish the native selected state losslessly, authoritative projection fails closed.

## 8. Fixture-role correction

The repository currently has a shared Browser fixture source containing `123456789ns`. It is used successfully by the backend-neutral in-memory harness and is valuable because it exercises the full portable canonical representation.

That fixture should not be treated as the mandatory concrete-browser execution baseline merely because it is shared.

The next implementation slice SHOULD make fixture roles explicit:

### 8.1 Canonical/serialization fixture

Purpose:

- exercise full BrowserStateImage representability;
- retain arbitrary nanosecond values;
- test JCS/canonical digest identity;
- remain provider-free.

The existing arbitrary-nanosecond vector belongs here.

### 8.2 Provider-neutral executable fixture

Purpose:

- exercise real Browser behavior through a concrete provider;
- remain free of provider names and provider branching;
- choose persistent expiry values that are intentionally representable by the claimed execution set;
- retain positive exact-expiry observation;
- pair with negative controls that prove rounded/truncated or unobservable expiry is rejected.

For the current Chromium-first reference implementation, an integer-second expiry is the safest portable positive baseline. A separate real capability probe SHOULD also exercise a non-zero Chromium-representable microsecond value to prove that the observer is not accidentally truncating every persistent expiry to whole seconds.

The executable fixture is not a narrower BrowserStateImage schema. It is simply one valid state selected for execution.

## 9. Required Chromium expiry capability probes

Before the Browser TCK evaluator is activated, real Chromium acceptance SHOULD prove at least:

1. **whole-second positive** — seed a persistent expiry with `nanoseconds = 0`; independent observation returns the exact same instant;
2. **non-zero microsecond positive** — seed a Chromium-representable value such as `nanoseconds = 123456000`; independent observation returns exactly that actual stored instant;
3. **non-representable nanosecond negative** — request a value such as `123456789ns`; the implementation must not claim that exact requested state was stored; it must fail closed or explicitly observe the browser-normalized different value before any authoritative claim;
4. **integer-truncation broken control** — an implementation that converts every observed persistent expiry to integer seconds must be rejected even when metadata is identical;
5. **provenance-only broken control** — an implementation that ignores current browser expiry and merely replays requested provenance must be rejected;
6. **session/persistent distinction** — session cookies continue to omit expiry and persistent cookies require an observed expiry.

These probes establish the capability boundary without adding provider-specific semantics to the portable TCK.

## 10. TCK design consequence

No change is required to:

- AEP-0011;
- BrowserStateImage schema;
- `AVP-BROWSER-007` / `AVP-BROWSER-008`;
- `AVP-TCK-BROWSER-STATE-IMAGE-001` arbitrary-nanosecond serialization vector;
- the requirement that rounded/truncated persistent expiry be rejected.

The executed-TCK adapter should instead distinguish:

```text
schema/canonical vector evaluation
    from
real provider execution fixture/control evaluation
```

The portable case remains provider-neutral. Provider setup may decide whether a requested control is representable, but an unsupported/lossy state cannot be converted into PASS by normalization.

## 11. No CDP/BiDi abstraction authorization

This audit does not justify a generic Browser transport abstraction, a CDP adapter hierarchy, or a BiDi plugin framework.

The current Playwright implementation should first prove the concrete Chromium capability probes above. CDP or another privileged transport should be introduced only for a specific missing control/observation responsibility that Playwright cannot satisfy and only behind the existing backend-neutral evaluator/control boundary.

## 12. Decision

The earlier hypothesis:

```text
Chromium cannot store arbitrary nanoseconds
=> Browser v0.1 cannot be conformed to by Chromium
```

is **REJECTED**.

The correct rule is:

```text
portable model can represent arbitrary expiry instants
+
concrete browser has a native expiry domain
+
provider must project the actual selected browser state losslessly
+
provider must fail closed when requested/observed state cannot be established exactly
```

Result:

- Browser v0.1 nanosecond wire representation: **RETAIN**.
- Chromium microsecond native resolution: **IMPLEMENTATION FACT, NOT PROTOCOL SEMANTICS**.
- Playwright floating-second transport: **potentially sufficient for Chromium actual-state observation, subject to real microsecond round-trip evidence**.
- WebDriver BiDi integer-second expiry: **not sufficient for fractional selected expiry; fail-closed required when loss would occur**.
- AEP-0011 semantic amendment: **NOT REQUIRED by current evidence**.
- Browser TCK activation: **NOT YET AUTHORIZED**.
- Next implementation slice: **provider-neutral executable fixture + real Chromium expiry-resolution probes**, then the remaining Browser execution controls.
