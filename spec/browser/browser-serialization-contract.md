# AVP Browser State Serialization Contract v0.1

Status: draft normative candidate

This companion contract closes the machine-readable Browser v0.1 resource shape required by `browser-state-contract.md`. It does not redefine Browser state semantics, create a browser automation API, or make provider-native data portable authority.

## 1. Resource classification and isolation

<a id="avp-browser-021"></a>
### AVP-BROWSER-021 — Browser resource classification and sibling isolation

A resource claiming `state.browser @ avp-browser-unpartitioned-cookie-localstorage-v0.1 / 0.1` MUST be an Environment Fabric resource with `resourceKind: browser`.

Each such resource MUST represent one independently owned isolated browser-session state boundary. Two sibling Browser resources in the same Environment MUST NOT silently share selected authoritative cookie or selected authoritative `localStorage` state. A conforming implementation MAY host multiple Browser resources in one process only when the required observable isolation is preserved.

A page/tab, browser process identifier, browser profile path, automation-library context object, WebDriver/BiDi user-context handle, CDP target/session, or another provider-native identifier MUST NOT replace the owning Fabric Resource Identifier or the Browser profile's portable state identity.

## 2. BrowserStateManifest serialized shape

<a id="avp-browser-022"></a>
### AVP-BROWSER-022 — Closed BrowserStateManifest serialization

The canonical BrowserStateManifest JSON object MUST contain exactly these fields:

- `apiVersion` = `avp.browser/v0.1`;
- `kind` = `BrowserStateManifest`;
- `profile` = `avp-browser-unpartitioned-cookie-localstorage-v0.1`;
- `revision` = `0.1`;
- `canonicalRepresentation` = `avp-browser-v0.1-rfc8785-jcs`;
- `localStorageOrigins` = the complete selected canonical tuple-origin list governed by AVP-BROWSER-003 and AVP-BROWSER-010;
- `cookieDomains` = the complete selected canonical stored-domain list governed by AVP-BROWSER-004 and AVP-BROWSER-010;
- `executionBindings` = a closed identity-binding map for Browser-profile-required execution policy/reference identities already resolved and identity-bound by the materialized Scenario/Fabric contract.

No other field is permitted in BrowserStateManifest v0.1.

`executionBindings` MUST be a JSON object. Each member name is a non-empty stable binding reference used by the materialized Scenario/Fabric contract. Each member value MUST contain exactly:

- `identity` — the resolved non-empty immutable identity value; and
- `identityType` — exactly one of `content`, `version`, or `symbolic`, reusing the Scenario v0.1 external-reference identity vocabulary.

A Browser Manifest execution binding MUST NOT originate a second independent identity claim. For every `executionBindings` member, the same binding reference, identity value, and identity type MUST already be represented in identity-bound semantic content of the owning materialized Scenario/Fabric execution contract. Missing, unresolved, conflicting, or provenance-only binding material MUST fail before Browser provisioning or Subject execution. Provider names, process ids, mutable paths, native handles, automation objects, or untyped provider property/value records MUST NOT be inserted as Browser execution bindings merely because an implementation exposes them.

The map MAY be empty only when no additional Browser-profile-required execution policy/reference identity is required beyond identity-bound semantic content already sufficient for the selected profile and Scenario. It MUST NOT be used to hide material execution inputs that AVP-BROWSER-013 requires to be identity-bound.

Because `executionBindings` is an object rather than a profile-defined array, its member ordering is canonicalized by RFC 8785 JCS object-member ordering. This avoids inventing a provider-derived or new Browser array-order semantic. `localStorageOrigins` and `cookieDomains` remain set-like semantically but MUST be serialized in the canonical order required by AVP-BROWSER-010 before JCS and digest computation. JSON Schema `uniqueItems` is necessary but does not prove WHATWG/domain canonicality or ordering; semantic conformance MUST verify those rules.

A future need for a different Browser-specific execution-binding identity level or serialized field requires a governed profile/schema revision; it MUST NOT be introduced through an open extension/property bag.

## 3. BrowserStateImage serialized shape

<a id="avp-browser-023"></a>
### AVP-BROWSER-023 — Closed BrowserStateImage serialization

The canonical BrowserStateImage JSON object MUST contain exactly:

- `apiVersion` = `avp.browser/v0.1`;
- `kind` = `BrowserStateImage`;
- `manifestDigest` = the exact SHA-256 Artifact digest of its BrowserStateManifest;
- `cookies` = the complete selected canonical cookie array;
- `origins` = the complete selected canonical origin/localStorage array.

Each `origins[]` member MUST contain exactly:

- `origin` = one selected canonical tuple-origin string;
- `localStorage` = the complete canonical entry array for that selected origin.

Each `localStorage[]` member MUST contain exactly `key` and `value`. Both are the unpadded base64url encodings of the exact UTF-16 code-unit byte sequences defined by AVP-BROWSER-005. These fields MUST NOT carry repaired host-language Unicode strings.

Each `cookies[]` member MUST contain exactly:

- `name`;
- `value`;
- `domain`;
- `hostOnly`;
- `path`;
- `persistent`;
- `secure`;
- `httpOnly`;
- `sameSite` with one of `Default`, `Strict`, `Lax`, or `None`;
- and, only when `persistent` is true, `expiry`.

`expiry` MUST contain exactly `unixSeconds` and `nanoseconds`. `unixSeconds` is a canonical signed base-10 integer string with no plus sign, no leading zero except `0`, and no negative zero. `nanoseconds` is an integer from 0 through 999999999. Together they represent one UTC expiry instant without using a JSON floating-point number. A selected persistent cookie whose authoritative expiry instant cannot be represented losslessly by this pair MUST fail closed rather than be rounded or truncated. A session cookie (`persistent: false`) MUST NOT contain `expiry`.

Cookie `name`, `value`, and `path` preserve the exact RFC cookie octet sequence represented as JSON strings over the corresponding US-ASCII code points. `domain` is the canonical stored-domain text governed by the Browser profile; leading-dot presentation syntax is not retained. The schema does not infer `hostOnly`, SameSite state, domain canonicality, or partition identity from those strings; those remain semantic requirements of AVP-BROWSER-007 through AVP-BROWSER-009.

`cookies[]`, `origins[]`, and every `localStorage[]` MUST be serialized in the canonical orders required by AVP-BROWSER-006 and AVP-BROWSER-010 before RFC 8785 JCS serialization and SHA-256 identity computation.

## 4. Closed-schema boundary

The companion Browser JSON Schemas are structural contracts for AVP-BROWSER-022 and AVP-BROWSER-023. Unknown fields MUST fail validation. Schema acceptance alone MUST NOT establish Browser conformance: canonical origin/domain semantics, set completeness, duplicate portable identities, cookie provenance, partition admission, temporal restore eligibility, settlement, execution-input binding, sibling isolation, and independent reset/restore reprojection require semantic or execution-sensitive TCK coverage.
