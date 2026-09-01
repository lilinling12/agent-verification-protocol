# AVP Browser State Resource Contract v0.1

Status: draft normative candidate

## 1. Scope

This specification defines the portable Browser State Environment Fabric Resource Capability selected as:

```text
capabilityId: state.browser
profile: avp-browser-unpartitioned-cookie-localstorage-v0.1
revision: "0.1"
```

It specializes the existing AVP Environment, Environment Fabric, Scenario, Core, Security, and Evidence contracts. It does not define a browser automation API, browser-product profile, WebDriver/CDP/BiDi protocol, Playwright/Selenium contract, browser-process checkpoint, profile-directory format, second Episode lifecycle, second Artifact identity system, or second security model.

A conforming implementation MUST satisfy all applicable upstream AVP requirements selected for the Episode.

Normative keywords MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are interpreted as conformance requirement terms.

## 2. Portable resource model

One Browser State Resource represents one independently owned isolated browser-session state boundary within one owning Environment.

The portable resource is not a page/tab, whole browser process, browser profile directory, automation-library context object, WebDriver/BiDi user-context handle, CDP target/session, process identifier, filesystem path, or other provider-native object.

The mandatory v0.1 authoritative restorable state surface is closed to:

1. selected **unpartitioned HTTP cookies**; and
2. selected **unpartitioned `localStorage` key/value entries** for admitted exact tuple origins.

Partitioned cookies/storage, `sessionStorage`, IndexedDB, Cache Storage, Service Workers, browsing topology/history, DOM/JavaScript heap, workers/timers, WebAuthn/passkey private state, downloads, rendering state, traces, console/network diagnostics, and other richer browser state are outside the mandatory base state identity unless separately governed.

The profile uses two acyclic logical state-identity resources:

1. one immutable `BrowserStateManifest` defining interpretation, selection, canonical representation revision, and profile-required identity/policy bindings; and
2. one immutable baseline `BrowserStateImage` binding the exact Manifest digest and the complete selected authoritative state.

The Manifest MUST NOT reference the baseline StateImage identity. The baseline StateImage MUST bind the exact Manifest Artifact digest.

Canonical Browser Manifest/Image identity bytes are profile-ordered RFC 8785 JCS UTF-8 bytes. Artifact identity remains SHA-256 over exact retained bytes under the AVP Evidence contract.

## 3. Profile and resource identity

<a id="avp-browser-001"></a>
### AVP-BROWSER-001 — Resource capability and identity Artifact binding

A resource claiming `state.browser @ avp-browser-unpartitioned-cookie-localstorage-v0.1 / 0.1` MUST bind exactly one BrowserStateManifest Artifact and exactly one baseline BrowserStateImage Artifact as Browser state-identity material required by this profile. Their roles MUST be determined by governed media/type identity rather than array position.

The Manifest MUST NOT contain or reference the baseline StateImage Artifact identity. The baseline StateImage MUST bind the exact Manifest Artifact digest. Browser product names, automation-library objects, native browser handles, process ids, profile paths, provider export bytes, or transport/session identifiers MUST NOT substitute for the portable state identities.

<a id="avp-browser-002"></a>
### AVP-BROWSER-002 — Immutable BrowserStateManifest semantics

BrowserStateManifest MUST immutably bind the selected capability/profile/revision, the complete localStorage origin-selection set, the complete cookie stored-domain selection set, the canonical representation revision, and every profile-required execution-policy or identity input whose meaning is part of the resource binding.

Selection membership and representation semantics MUST remain immutable for the bound resource lifetime. A mutable provider configuration object or native automation context MUST NOT be treated as Manifest identity.

## 4. State selection

<a id="avp-browser-003"></a>
### AVP-BROWSER-003 — Closed localStorage selection grammar

The Manifest localStorage selection MUST be a finite duplicate-free set of exact canonical non-opaque tuple-origin strings. Each selected origin selects the complete admitted **unpartitioned** `localStorage` map for that origin, including meaningful empty-map state.

A selected origin MUST use WHATWG tuple-origin semantics and canonical serialization of `(scheme, host, port)`. Path, query, fragment, username, and password MUST NOT participate in localStorage origin identity. Opaque origins and `file:` behavior are outside the mandatory profile.

Regex, glob, suffix/subdomain matching, provider callback, runtime code, backend-native predicate, top-level-site partition selector, or other open-ended selection grammar MUST NOT define v0.1 localStorage membership.

<a id="avp-browser-004"></a>
### AVP-BROWSER-004 — Closed cookie selection grammar

The Manifest cookie selection MUST be a finite duplicate-free set of exact canonical stored-cookie domain strings. A cookie is selected if and only if it is unpartitioned and its canonical stored domain exactly equals a selected domain.

Every selected cookie entry participates regardless of cookie name. Regex, glob, suffix/subdomain matching, provider query language, runtime code, or partition selector MUST NOT define v0.1 cookie membership.

An implementation MUST NOT relabel partitioned/CHIPS-style state as ordinary unpartitioned cookie state to satisfy this profile.

## 5. Canonical Web Storage representation

<a id="avp-browser-005"></a>
### AVP-BROWSER-005 — Lossless DOMString representation

Every selected localStorage key and value MUST preserve the exact ordered Web IDL `DOMString` UTF-16 code-unit sequence without Unicode repair, scalar-value normalization, replacement of unmatched surrogates, or host-language string coercion.

For protocol serialization, each DOMString MUST be encoded by taking each unsigned 16-bit UTF-16 code unit, writing it as exactly two network-byte-order bytes, concatenating those bytes in code-unit order, and encoding the result as unpadded RFC 4648 base64url.

Equality is equality of the decoded unsigned UTF-16 code-unit sequence.

<a id="avp-browser-006"></a>
### AVP-BROWSER-006 — Canonical localStorage ordering

For each selected origin, localStorage entries MUST be ordered lexicographically by unsigned UTF-16 key code units, with the shorter sequence first when one key is an exact prefix of another.

Browser enumeration order, insertion order, locale collation, provider transport order, host-language string ordering, and JSON-library object ordering MUST NOT define canonical localStorage order.

Duplicate canonical key identity within one selected origin MUST fail closed.

## 6. Cookie state model

<a id="avp-browser-007"></a>
### AVP-BROWSER-007 — Portable cookie identity and required state

Each selected projected cookie MUST represent one unpartitioned stored-cookie entry with portable identity:

```text
(name, domain, hostOnly, path)
```

No two cookies in one BrowserStateImage may share that identity tuple.

The portable state MUST preserve, at minimum, exact cookie name/value data, canonical stored domain text, explicit `hostOnly`, path, session-versus-persistent semantics, expiry instant when persistent, Secure, HttpOnly, and SameSite including a distinct user-agent `Default` state where the stored-cookie model distinguishes it.

Creation time and last-access time are not BrowserStateImage identity fields. Their omission MUST NOT be interpreted as permission to erase material temporal behavior.

<a id="avp-browser-008"></a>
### AVP-BROWSER-008 — Lossless cookie projection fails closed

A selected cookie may be accepted into an authoritative Browser projection only when evaluator/control authority can establish every required portable identity and state field without ambiguity.

A provider API that omits `hostOnly`, collapses `SameSite=Default`, loses domain/path identity, or otherwise cannot establish required selected state MUST NOT redefine the portable model. Guessing from convenience serialization, provider defaults, presentation-only leading-dot syntax, or export success is insufficient.

If required selected cookie identity/state cannot be established losslessly, authoritative projection MUST fail closed.

<a id="avp-browser-009"></a>
### AVP-BROWSER-009 — Cookie temporal restore eligibility

Successful Browser v0.1 restore/reset of selected cookies MUST preserve the profile-relevant behavior required by the materialized Scenario under its bound execution policy.

`SameSite=Default` MUST remain distinct from explicit `Lax`. If creation-time-dependent behavior can materially affect the verification claim and historical creation time cannot be preserved or its behavioral effect otherwise proven equivalent, restore/reset MUST fail closed for the resource.

Field-equal reprojection is necessary but is not by itself proof of unbounded HTTP behavioral equivalence. An implementation MUST NOT manufacture a fresh field-equal cookie and report successful state equivalence while a material temporal distinction remains unresolved.

## 7. Canonical collection ordering and identity bytes

<a id="avp-browser-010"></a>
### AVP-BROWSER-010 — Canonical Browser collection ordering

Before RFC 8785 JCS serialization and content-addressed identity computation, all profile-defined Browser collections MUST be put into the profile-defined canonical order.

Canonical tuple-origin strings and canonical stored-cookie domain strings compare lexicographically by unsigned UTF-8 bytes of their canonical text, shorter exact prefix first. Cookie `name` and `path` compare lexicographically by exact RFC cookie octets, shorter exact prefix first. `hostOnly` orders `false` before `true`.

The required collection order is:

1. Manifest selected localStorage origins ascending by canonical origin comparator;
2. Manifest selected cookie domains ascending by canonical stored-domain comparator;
3. BrowserStateImage `origins[]` ascending by canonical origin comparator;
4. each origin's localStorage entries by AVP-BROWSER-006;
5. BrowserStateImage `cookies[]` lexicographically by `(name, domain, hostOnly, path)` using the component comparators above.

Provider/browser enumeration order, insertion order, object iteration order, transport-return order, and automation-library export order are non-authoritative.

<a id="avp-browser-011"></a>
### AVP-BROWSER-011 — Canonical Manifest/Image identity bytes

A BrowserStateManifest or BrowserStateImage claiming this profile MUST be emitted in the required profile-defined collection order before RFC 8785 JCS serialization and SHA-256 identity computation.

A syntactically parseable document with noncanonical collection order MUST NOT be accepted as the canonical identity bytes of the claimed Browser Manifest/Image. An implementation MAY parse noncanonical input and emit a new canonical document as distinct retained bytes, but MUST NOT treat the raw noncanonical Artifact digest as the Browser v0.1 Manifest/Image identity.

Duplicate selection values, duplicate origin identities, duplicate localStorage key identities, or duplicate cookie identity tuples MUST fail closed.

## 8. Authoritative BrowserStateImage

<a id="avp-browser-012"></a>
### AVP-BROWSER-012 — Complete selected StateImage

BrowserStateImage MUST bind the exact Manifest Artifact digest and contain the complete selected authoritative state exactly once: every selected admitted origin with its complete unpartitioned localStorage map, and every selected unpartitioned cookie matching the Manifest domain selection.

Missing selected state, extra in-scope state, transformed values, changed cookie scope, state projected under a different storage identity, unsupported selected partition semantics, or noncanonical identity bytes MUST fail closed.

Evaluator-private authoritative values MAY remain part of the complete StateImage; completeness and Subject visibility are separate concerns governed by Security/Evidence.

## 9. Execution identity and excluded-state noninterference

<a id="avp-browser-013"></a>
### AVP-BROWSER-013 — Execution-relevant browser identity binding

BrowserStateManifest is not the complete Environment execution identity. Any browser build/version, operating system/platform, headless/headful mode, locale/timezone, viewport/device emulation, JavaScript setting, permission/geolocation setting, Service Worker policy, proxy/TLS policy, preload/extension/configuration, rendering input, cookie temporal policy, storage-partition/isolation policy, or other browser execution input outside the logical state image that materially affects the Scenario claim MUST compose through existing Scenario/Fabric immutable execution-input identity binding.

Labels such as `chromium`, `firefox`, `webkit`, `playwright`, or `selenium` alone are not sufficient immutable execution identity. Missing required identity before execution or drift of a bound required identity during the Episode MUST fail closed even when logical BrowserStateImage state remains equal.

<a id="avp-browser-014"></a>
### AVP-BROWSER-014 — Excluded-state noninterference or fail-closed insufficiency

Excluding a browser surface from BrowserStateImage MUST NOT be treated as evidence that the surface is behaviorally irrelevant.

For every excluded surface that can materially affect the Scenario verification claim, the materialized execution MUST establish at least one of:

1. isolation/configuration making the surface noninterfering for the claimed boundary;
2. immutable execution-identity/policy binding sufficient to make the relied-upon condition explicit and drift-detectable; or
3. fail-closed insufficiency declaring Browser v0.1 unable to reproduce that dependency.

This rule applies to Service Workers, Cache Storage, IndexedDB, permissions, extensions/preload scripts, browser-profile residue, network policy, credential state, partitioned storage, and other excluded behaviorally relevant state.

## 10. Settlement and observation consistency

<a id="avp-browser-015"></a>
### AVP-BROWSER-015 — Positive profile-relevant settlement witness

Browser v0.1 defines no universal browser-idle state. An accepted authoritative projection MUST begin only after evaluator/control authority establishes a positive profile-relevant settlement witness proving that:

1. Core has closed admission of new Subject side effects for the observed Episode boundary;
2. every accepted pre-boundary mutation capable of affecting selected authoritative Browser state has a known terminal outcome;
3. no accepted profile-relevant mutation remains unresolved; and
4. the authoritative projection begins only after items 1–3 and does not knowingly combine incompatible pre/post mutation fragments.

Arbitrary sleep, elapsed quiet time, `networkidle`, backend command completion, browser event-queue emptiness, or automation-library export completion MUST NOT by themselves establish settlement.

If the witness cannot be established, the operation MUST fail closed as unsettled and MUST NOT produce an accepted final authoritative projection. This is infrastructure/Validity information and MUST NOT be automatically converted into Agent Task Verdict failure solely by occurrence.

## 11. Snapshot, reset, and restore

<a id="avp-browser-016"></a>
### AVP-BROWSER-016 — Snapshot ownership and canonical state evidence

A successful Browser snapshot MUST establish the profile-relevant settlement witness, losslessly project the complete selected authoritative state into canonical BrowserStateImage bytes, retain or otherwise bind those bytes through AVP Artifact identity, and bind that StateImage identity to an Environment/resource-owned SnapshotRef.

Foreign, stale, wrong-resource, corrupted, incompatible, or noncanonical SnapshotRef/StateImage use MUST fail closed. Provider-native profile snapshots, session handles, export objects, filesystem paths, or browser-internal checkpoint identifiers MUST NOT replace SnapshotRef or BrowserStateImage identity.

<a id="avp-browser-017"></a>
### AVP-BROWSER-017 — Reset requires independent canonical reprojection

Reset success MUST be accepted only after valid immutable bindings are established, the baseline selected state is re-established by any conforming mechanism, the profile-relevant settlement witness is established, and independent evaluator reprojection yields exactly the complete canonical baseline BrowserStateImage identity.

Provider reset/import/clear/reseed command success alone is insufficient. Reset mismatch or inability to establish trustworthy selected state is infrastructure/Validity information and MUST fail closed without being converted directly into Agent Task Verdict failure solely by occurrence.

<a id="avp-browser-018"></a>
### AVP-BROWSER-018 — Successful restore fidelity is exactly STATE_EQUIVALENT

Restore of an owner-valid Browser SnapshotRef MUST independently reproject the complete selected authoritative state after the required settlement witness and compare it with the target snapshot BrowserStateImage under the same Manifest and compatible required execution identity.

A successful v0.1 Browser restore MUST re-establish the target BrowserStateImage identity and satisfy AVP-BROWSER-009 temporal eligibility, and MUST report resource restore fidelity exactly `STATE_EQUIVALENT`.

If equivalence cannot be established, restore MUST fail and MUST NOT report success. `EXACT` MUST NOT be reported for this base capability because excluded browser state, provider-internal metadata, process continuation, browsing topology, worker/cache state, temporal metadata, and other execution state are not standardized by v0.1.

## 12. Security and authority separation

<a id="avp-browser-019"></a>
### AVP-BROWSER-019 — Subject/Evaluator/Control and Evidence visibility separation

Browser Manifest, StateImage, snapshot, projection, and related Evidence MUST compose with existing AVP Security/Evidence classification, actor, credential, and visibility rules.

Evaluator-private authoritative Browser state MAY remain evaluator-confidential/secret/regulated Evidence. Subject-visible observations, routes, execution context, tool results, and Artifact locators MUST NOT disclose evaluator-private Browser state or grant unauthorized retrieval authority unless the materialized Scenario explicitly authorizes that visibility.

Artifact digest identity MUST NOT be treated as retrieval authorization or declassification. Subject-scoped/redacted bytes are distinct Artifacts and MUST NOT reuse the digest of unredacted evaluator-private bytes.

Browser launch/debugging/session provisioning, baseline seeding, reset, snapshot, restore, credential injection, hidden instrumentation, automation handles, and equivalent privileged operations remain Evaluator/Control authority unless a separately governed Subject contract explicitly grants a narrower capability.

## 13. Executed provider-neutral conformance

<a id="avp-browser-020"></a>
### AVP-BROWSER-020 — Executed provider-neutral conformance

Conformance for `state.browser @ avp-browser-unpartitioned-cookie-localstorage-v0.1 / 0.1` MUST execute an implementation path capable of observing whether required Browser behavior is actually satisfied at the browser boundary for behavior-dependent cases. Metadata declarations, mocks, provider names, capability flags, schema shape, or self-certification alone MUST NOT establish conformance.

Portable TCK expectations MUST NOT branch on Playwright, Selenium, Chromium, Firefox, WebKit, CDP, WebDriver, BiDi, or another provider/product name. Provider-specific setup and privileged fixture-control operations MAY exist behind implementation/test-driver seams but MUST NOT become portable Resource or Subject protocol APIs.

The mandatory TCK MUST be capable of rejecting metadata-identical broken implementations that, as applicable, lose cookie identity, collapse `SameSite=Default`, admit partitioned state under unpartitioned identity, corrupt DOMString code units, preserve provider enumeration order as canonical identity, report restore success without independent reprojection, bypass settlement, leak evaluator-private state, ignore excluded-state interference, or silently accept required execution-input drift.

Cross-engine Chromium/Gecko/WebKit evidence MAY be used as acceptance/reference evidence for portability claims but MUST NOT become a universal third-party requirement to support three engines unless a separately governed conformance claim says so.

## 14. Schema and extension rules

Serialized Browser v0.1 Manifest/Image resources MUST use closed machine-readable schemas derived from this specification where schemas are required. Protocol-owned objects MUST reject unknown fields unless an explicit governed extension field is defined. v0.1 defines no generic untyped implementation-property bag.

Schema validation is necessary but not sufficient. Selection uniqueness, canonical ordering, DOMString losslessness, cookie identity/provenance, partition admission, temporal restore eligibility, settlement, execution-input identity, excluded-state noninterference, SnapshotRef ownership, independent reset/restore reprojection, visibility, and executed-conformance behavior require semantic execution.

Schema definitions MUST NOT invent Browser semantics absent from this specification.

## 15. Implementation freedom

Conforming implementations MAY use Playwright, Selenium/WebDriver, CDP, WebDriver BiDi, native browser APIs, custom control infrastructure, or another mechanism. Those choices remain implementation evidence. They MUST NOT redefine the portable semantics above.

A provider/reference implementation MUST NOT begin by publishing provider-native protocol APIs and generalizing them later. Common interfaces MUST be derived from the reviewed `Spec -> Schema -> TCK` authority slice.

No generic `BaseBrowserBackend`, `Base*Adapter`, plugin framework, broad inheritance hierarchy, or generic `supports_*` property family is justified by this specification. Responsibilities SHOULD be composed explicitly until concrete multi-consumer extension evidence requires a narrower abstraction.

The project rule remains: **拆职责，不抽象协议 / split responsibilities; do not abstract protocol semantics.**