# Alpha 3 Browser Cross-Engine Acceptance Evidence

Status: **PARTIAL — PLATFORM EVIDENCE ESTABLISHED; AVP EXECUTABLE EVIDENCE REQUIRED**

Parent protocol PR: #108  
Parent protocol exact head: `4da88bd5fdbaca8fa479b6128e20511e8355d207`  
Evidence branch baseline: `4da88bd5fdbaca8fa479b6128e20511e8355d207`  
AEP: `rfcs/AEP-0011-browser-resource-profile.md` (`Proposed`)

## 1. Purpose

This record separates two kinds of evidence needed to close the Browser Resource Profile acceptance gate:

1. **Web-platform evidence** showing that the protocol decisions are grounded in standards and interoperable browser semantics rather than one automation product; and
2. **AVP executable evidence** showing that the proposed projection, restore, reset, settlement, and fail-closed rules can be implemented and verified without weakening those semantics.

This document does not make AEP-0011 Accepted and does not authorize Browser normative Spec, Schema, TCK, backend-neutral harness, Playwright/reference runtime, release selection, publication, signing, attestation, repository split, or plugin-framework work.

The authority direction remains:

```text
AEP decision
  -> future normative Spec
  -> future Schema where required
  -> future language-neutral TCK
  -> future conformance harness
  -> future reference runtime
```

External standards, WPT, browser-engine documentation, and automation libraries are evidence inputs. They do not become AVP protocol authority by citation or precedent.

## 2. Evidence classes

### Class A — Standards evidence

Use final/living standards to establish the web-platform semantic model that AVP must not contradict.

Primary sources:

- RFC 10025 — Cookies: HTTP State Management Mechanism: <https://www.rfc-editor.org/rfc/rfc10025.html>
- WHATWG HTML: <https://html.spec.whatwg.org/>
- WHATWG Storage: <https://storage.spec.whatwg.org/>
- WHATWG Web IDL: <https://webidl.spec.whatwg.org/>
- WHATWG URL: <https://url.spec.whatwg.org/>
- RFC 8785 — JSON Canonicalization Scheme: <https://www.rfc-editor.org/rfc/rfc8785.html>

### Class B — Cross-browser WPT evidence

Use Web Platform Tests to establish browser-facing platform behavior where an existing portable test already owns the question.

Relevant existing WPT assets include:

- `webstorage/localstorage-basic-partitioned.sub.html`
- `webstorage/localstorage-cross-origin-iframe.https.window.js`
- `webstorage/storage_string_conversion.window.js`
- `cookies/attributes/domain/domain.sub.html`
- `cookies/samesite/fetch.https.html`

WPT source: <https://github.com/web-platform-tests/wpt>  
WPT result archive: <https://wpt.fyi/>

Existing WPT assets should be reused where they test the same web-platform statement. AVP must not clone WPT merely to rename upstream platform behavior as an AVP test.

### Class C — Engine-family implementation evidence

Use browser-engine documentation to identify shipping storage models, privacy partitioning, configuration assumptions, and known family-specific constraints.

Primary sources currently reviewed:

- Chromium/Chrome storage partitioning: <https://developer.chrome.com/docs/extensions/develop/concepts/storage-and-cookies>
- Chrome 127 storage-partitioning release notes: <https://developer.chrome.com/release-notes/127>
- Mozilla State Partitioning: <https://developer.mozilla.org/en-US/docs/Web/Privacy/Guides/State_Partitioning>
- WebKit Tracking Prevention: <https://webkit.org/tracking-prevention/>
- WebKit Storage Access API guidance: <https://webkit.org/blog/11545/updates-to-the-storage-access-api/>

Engine documentation is implementation evidence. Product-specific terminology must not leak into portable BrowserStateManifest or BrowserStateImage semantics.

### Class D — AVP executable acceptance evidence

AVP must execute controlled evidence cases that are not answered by standards/WPT alone, especially:

- lossless selected-cookie projection at the AVP boundary;
- restore eligibility when historical cookie temporal behavior cannot be preserved;
- independent post-restore/reset re-projection;
- positive settlement witness and fail-closed `unsettled` behavior;
- excluded-state residual noninterference assumptions;
- AVP's lossless `DOMString` representation round trip.

Only Class D evidence can close AVP-specific implementation-boundary obligations. Class A/B/C evidence cannot substitute for it.

## 3. Standards findings retained as acceptance premises

### 3.1 Cookie identity includes `hostOnly`

RFC 10025 stores `host-only-flag` as cookie state and includes it in cookie uniqueness together with name, domain, and path.

The storage algorithm distinguishes:

```text
(name, domain, host-only-flag, path)
```

A cookie created without a `Domain` attribute is host-only; a domain-scoped cookie is eligible for matching subdomains according to domain-match semantics.

Acceptance implication:

- AEP-0011 is correct to retain `(name, domain, hostOnly, path)`.
- A backend projection that cannot establish `hostOnly` is lossy for AVP purposes.
- Lossy automation output must not cause AVP to weaken cookie identity.

### 3.2 `SameSite=Default` is not the same stored state as explicit `Lax`

RFC 10025 defines a stored `same-site-flag` whose values include `Default`. `Lax-allowing-unsafe` is not a separate SameSite attribute value; it may apply only to cookies whose stored same-site flag is `Default`.

Acceptance implication:

- `Default -> Lax` normalization is not acceptable projection or restore behavior.
- A provider API that reports only an effective policy but loses stored Default-versus-explicit state is insufficient by itself.

### 3.3 Cookie creation time can change observable behavior

RFC 10025 stores `creation-time`. It can affect at least:

- eligibility for the optional recent-cookie `Lax-allowing-unsafe` compatibility mode; and
- cookie ordering when equal-length paths are serialized, where earlier creation time is the recommended ordering rule.

Acceptance implication:

- image-field equality without historical temporal evidence cannot be promoted into an unbounded browser-behavior equality claim;
- Browser v0.1 may remain narrow, but restore must fail closed where creation-time-dependent behavior is material and cannot be preserved or proven equivalent.

### 3.4 Modern `localStorage` cannot be described globally by tuple origin alone

Shipping browser families partition third-party state:

- Chrome partitions storage in third-party contexts from Chrome 115;
- Firefox State Partitioning double-keys client-side state by resource origin and top-level site, with Dynamic Partitioning enabled by default from Firefox 103;
- WebKit documents third-party LocalStorage as partitioned per first-party website and subject to tracking-prevention policy.

Acceptance implication:

- tuple `(scheme, host, port)` is valid only inside the deliberately admitted **unpartitioned** Browser v0.1 context;
- partitioned third-party state must not be projected into the base profile under tuple-origin identity;
- a Scenario depending on partitioned state requires fail-closed insufficiency or a future partition-aware capability.

### 3.5 `DOMString` can contain unmatched surrogates

Web IDL explicitly permits `DOMString` values containing unmatched surrogate code points and defines JavaScript conversion as preserving the same sequence of code units.

RFC 8785/JCS requires compliant implementations to terminate on lone surrogates because they are invalid Unicode scalar-value data for that canonicalization model.

Acceptance implication:

- raw host-language JSON strings cannot be the AVP authority for exact Web Storage values;
- the AEP-0011 UTF-16 code-unit representation is justified because it preserves the exact Web IDL value while keeping canonical JSON input ASCII-safe.

## 4. Cross-engine platform evidence matrix

| Evidence question | Standards/WPT | Chromium family | Gecko family | WebKit family | AVP-specific evidence still required? |
| --- | --- | --- | --- | --- | --- |
| Host-only and domain-scoped cookie behavior differ | RFC 10025; WPT cookie domain tests | Required engine run | Required engine run | Required engine run | **Yes** — AVP projection must preserve identity |
| Cookie uniqueness includes host-only state | RFC 10025 | Standards premise | Standards premise | Standards premise | **Yes** — prove AVP can establish it or fail closed |
| `SameSite=Default` is distinct stored state | RFC 10025 | Required engine run | Required engine run | Required engine run | **Yes** — projection/restore boundary |
| Creation-time can affect Default SameSite behavior | RFC 10025 | Required engine run | Required engine run | Required engine run | **Yes** — temporal restore eligibility |
| First-party/unpartitioned localStorage is origin scoped | HTML/Storage + WPT | Required engine run | Required engine run | Required engine run | **Yes** — AVP canonical projection/reprojection |
| Third-party storage may be partitioned beyond tuple origin | WPT + engine docs | Shipping partitioning | Shipping partitioning | Shipping partitioning | **Yes** — base-profile rejection/non-admission |
| LocalStorage string conversion uses DOMString semantics | Web IDL/HTML + WPT | Required engine run | Required engine run | Required engine run | **Yes** — AVP UTF-16 representation round trip |
| Browser globally idle after network quiet | No such platform guarantee | Not proven | Not proven | Not proven | **Yes** — AVP positive settlement witness required |
| Equal selected state reproduces excluded Service Worker/cache/IDB state | No | No | No | No | **Yes** — noninterference or insufficiency proof |

The table deliberately distinguishes browser-platform evidence from AVP conformance evidence. A green WPT result does not prove an AVP restore implementation.

## 5. Mandatory AVP evidence cases

The executable evidence phase should use one immutable logical fixture definition across Chromium, Gecko, and WebKit. Engine names are matrix metadata, not expectation branches.

### BAE-001 — Host-only versus domain-scoped behavioral distinction

Seed two controlled cookie cases using HTTP `Set-Cookie` semantics:

1. host-only cookie created without `Domain`;
2. domain-scoped cookie created with an exact admitted domain.

Required observations:

- host-only cookie is not sent to a qualifying subdomain;
- domain-scoped cookie is sent where domain-match permits;
- AVP projection records the correct `hostOnly` identity;
- an intentionally lossy projector that erases `hostOnly` must be rejected.

### BAE-002 — SameSite Default versus explicit Lax projection

Seed one cookie with no SameSite attribute and one with explicit `SameSite=Lax` under otherwise controlled attributes.

Required observations:

- AVP projection distinguishes stored Default from explicit Lax where the engine exposes/proves the distinction through the accepted evidence path;
- if the implementation cannot establish the distinction, projection fails closed;
- no adapter may rewrite Default to Lax to obtain a passing image.

### BAE-003 — Temporal restore eligibility

Exercise a Default-SameSite cookie in a controlled cross-site unsafe top-level navigation scenario around the engine's recent-cookie compatibility behavior.

The portable expectation must **not** require every engine to implement the optional compatibility mode identically. Instead:

- record whether the bound engine/build applies a creation-time-sensitive behavior;
- where the Scenario relies on that behavior and restore cannot preserve/prove it, AVP restore must fail closed;
- explicit Lax/Strict/None cases that do not depend on unpreserved historical creation time may remain eligible if all other requirements are satisfied.

### BAE-004 — Exact selected-cookie complete-set projection

Use an exact selected stored-domain list and include multiple cookie names and paths, including dynamic names not enumerated by the manifest.

Required observations:

- every in-scope cookie participates;
- no extra in-scope cookie can be silently omitted;
- cookies outside exact selected domains do not enter the image;
- no suffix/glob/vendor-filter behavior is accepted.

### BAE-005 — First-party unpartitioned localStorage projection

For multiple exact tuple origins, seed complete localStorage maps and independently project them.

Required observations:

- exact tuple-origin separation;
- complete map semantics, including empty map;
- missing/extra/transformed values fail equality;
- path/query/fragment do not alter origin identity.

### BAE-006 — Partitioned third-party non-admission

Embed the same third-party origin under two distinct top-level sites and write distinguishable localStorage values where the engine's shipping policy partitions that state.

Required observations:

- the base profile must not flatten the partitioned buckets into one ordinary tuple-origin image;
- the implementation either proves that the observed context is the admitted unpartitioned context or fails closed as unsupported/insufficient;
- engine-specific storage-key tokens never become portable AVP identity.

### BAE-007 — Lossless DOMString representation

Seed localStorage keys and values containing at least:

- empty string;
- U+0000;
- ASCII and non-ASCII BMP text;
- a valid surrogate pair;
- an unmatched high surrogate;
- an unmatched low surrogate;
- canonically composed and decomposed Unicode sequences.

Required observations:

- browser round trip preserves the JavaScript/Web IDL code-unit sequence;
- AVP encodes each UTF-16 code unit as two network-byte-order bytes followed by unpadded base64url;
- decode(encode(value)) reproduces exactly the same unsigned 16-bit sequence;
- canonical ordering is by unsigned UTF-16 code units, shorter prefix first;
- no Unicode normalization or replacement character repair occurs.

### BAE-008 — Snapshot -> mutation -> restore -> independent reprojection

For selected cookies + admitted unpartitioned localStorage:

1. establish baseline;
2. prove settlement;
3. snapshot;
4. mutate selected state;
5. restore;
6. independently re-project complete selected state.

Successful fidelity must be exactly `STATE_EQUIVALENT`, never `EXACT`.

A backend import command returning success is not evidence until independent reprojection matches the target and all temporal restore-eligibility conditions remain satisfied.

### BAE-009 — Reset -> independent baseline reprojection

After selected-state mutation, reset must re-establish the immutable baseline and independently reproduce the complete selected image.

### BAE-010 — Positive settlement witness

Create an accepted profile-relevant mutation whose completion is controlled independently from ordinary network quiet.

Required observations:

- Core admission is closed before final projection;
- evaluator/control authority knows whether every accepted profile-relevant mutation is terminal;
- projection is rejected while one accepted mutation remains unresolved;
- arbitrary sleep, network-idle, quiet-window, provider command completion, or vendor queue inspection does not convert unresolved work into settled state.

### BAE-011 — Residual-state noninterference

Exercise materially relevant excluded state, at minimum one Service Worker/cache case and one additional excluded surface such as IndexedDB or browser permission/configuration.

Required observations:

- selected-state equality alone does not claim reproduction of the excluded surface;
- the fixture demonstrates either isolation/noninterference, immutable execution-policy binding, or fail-closed Browser-v0.1 insufficiency.

### BAE-012 — Negative self-certification controls

At least the following intentionally invalid implementations/paths must fail:

- erase `hostOnly` and infer it from domain text;
- normalize `SameSite=Default` to Lax;
- restore a temporal-sensitive Default cookie as a fresh field-equal cookie and report success without proof;
- flatten partitioned localStorage into tuple-origin state;
- drop one selected localStorage key;
- repair an unmatched surrogate into U+FFFD;
- accept final projection while one admitted mutation is unresolved;
- return restore success without independent reprojection.

## 6. Engine-matrix execution policy

Acceptance evidence must cover:

```text
Chromium family
Gecko family
WebKit family
```

For each run, evidence must retain at least:

- engine family;
- exact product/version/build identifier;
- OS/platform/architecture when behavior can depend on it;
- headless/headful mode;
- relevant privacy/storage policy or non-default flags;
- exact evidence fixture revision/digest;
- exact test-case identifiers;
- machine-readable pass/fail/unsupported outcomes;
- diagnostics sufficient to distinguish protocol failure from unavailable engine capability.

The matrix is an **AEP acceptance gate**. It is not a requirement that every future third-party AVP implementation support all three browser families.

No acceptance result may silently change browser defaults merely to make engines behave alike. Any non-default engine flag must be explicit execution identity and must be justified by the admitted Scenario policy.

## 7. WPT reuse versus AVP fixture ownership

### Reuse WPT for

- browser-platform cookie Domain behavior;
- SameSite platform behavior where existing WPT covers the exact question;
- localStorage origin accessibility and partitioning behavior;
- basic Web Storage string-conversion behavior.

### AVP must own evidence for

- BrowserStateManifest selection semantics;
- BrowserStateImage canonical representation;
- `hostOnly` projection proof at the AVP boundary;
- temporal restore eligibility;
- independent AVP reprojection after restore/reset;
- `STATE_EQUIVALENT` claim honesty;
- settlement witness semantics;
- residual-state noninterference decision;
- AVP fail-closed negative controls.

This prevents both duplication and authority inversion.

## 8. Experimental transport boundary

The future evidence runner may use WebDriver, WebDriver BiDi, Playwright, WPT runner infrastructure, or engine-native automation strictly as **test transport**.

The evidence oracle must be expressed in browser-observable and AVP-defined terms. In particular:

- Playwright `storageState` must not be the expected-state oracle;
- CDP cookie objects must not redefine portable fields;
- a WebDriver/BiDi response lacking `hostOnly` must not cause the field to disappear from AVP identity;
- product-specific partition keys are evidence metadata, not AVP state identity;
- engine-specific branching may provision transport, but portable expected outcomes cannot branch merely on product name.

## 9. Repository-structure decision for the executable phase

No new top-level `browser/`, `experiments/`, `providers/`, or generic adapter hierarchy is authorized by this evidence audit.

Before executable evidence code is added, a focused repository-boundary review must choose the smallest existing responsibility boundary that can host **non-normative acceptance-evidence tooling** without being confused with:

- the future language-neutral Browser TCK;
- the future backend-neutral Browser conformance harness;
- the future reference runtime/provider.

Until that placement is reviewed, this child branch remains documentation/evidence-design only.

## 10. Current blocker disposition

### BPR-003

Protocol decision: **INCORPORATED**.  
Standards/platform evidence: **ESTABLISHED** that host-only state is real cookie identity and must not be erased.  
AVP executable evidence: **OPEN** across Chromium/Gecko/WebKit.

### BPR-004

Protocol decision: **INCORPORATED**.  
Standards/platform evidence: **ESTABLISHED** that Default SameSite and creation-time-sensitive behavior can make field-equal recreated cookies behaviorally different.  
AVP executable evidence: **OPEN** across Chromium/Gecko/WebKit.

### BPR-009

Three-engine acceptance evidence: **OPEN**.

The external research is sufficient to define the required executable matrix, but not sufficient to close BPR-009 by assertion.

## 11. Exit criteria for this evidence phase

The Browser cross-engine acceptance-evidence phase is complete only when:

1. BAE-001..BAE-012 have reviewable outcomes against Chromium, Gecko, and WebKit where the case applies;
2. unsupported cases fail closed rather than becoming silent skips;
3. exact engine/build and fixture identity are retained;
4. the same portable expectation model is used across engine families;
5. independent reprojection proves successful restore/reset claims;
6. negative controls demonstrate rejection of lossy/false-positive implementations;
7. evidence artifacts are reproducible and tied to an exact repository head;
8. BPR-003, BPR-004, and BPR-009 are re-reviewed against those artifacts;
9. an acceptance-oriented exact-head protocol review finds no remaining semantic blocker.

Only after those conditions are satisfied may a separate explicit protocol-maintainer `Proposed -> Accepted` decision be considered.

## 12. Current conclusion

```text
AEP-0011: Proposed
Protocol blocker decisions: incorporated on parent PR #108
Platform/standards evidence audit: established
Chromium/Gecko/WebKit AVP executable matrix: required / not yet executed
BPR-003: evidence open
BPR-004: evidence open
BPR-009: open
Acceptance-oriented review: not ready
Proposed -> Accepted: not authorized
Browser Spec/Schema/TCK/harness/runtime: not authorized
```
