# AEP-0011 — Browser Resource Profile v0.1

- Status: Proposed
- Authors: AVP maintainers and contributors
- Created: 2026-08-27
- Portability audit: `docs/design/alpha3-browser-resource-portability-audit.md`
- Proposed-readiness evidence: `docs/design/alpha3-browser-resource-proposed-readiness-audit.md`
- Lifecycle decision: `docs/acceptance/alpha3-aep-0011-proposed-decision.md`
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Browser Resource

## Summary

AEP-0011 defines the review-ready portable direction for the first browser resource profile under AVP Environment Fabric.

The core rule is:

> AVP standardizes the observable browser-session state boundary and the identity/evidence required to verify it; browser products, automation libraries, native handles, profile directories, and engine-private mechanics remain implementation details.

The reconciled v0.1 design is deliberately narrow. One independently isolated browser-session resource owns a closed authoritative logical state surface consisting of selected **unpartitioned HTTP cookies** and selected **origin-scoped `localStorage`**. A successful restore may report exactly `STATE_EQUIVALENT`; `EXACT` is not a valid successful fidelity claim for this base profile.

A working capability identity for downstream normative review is:

```text
capabilityId: browser.session-state
profile: avp-browser-state-v0.1
revision: "0.1"
```

The exact spelling remains a candidate until formal protocol review and downstream normative authority approve it. The capability is one cohesive portable claim rather than a transitional collection of `supports_*` flags.

AEP-0011 is **Proposed** for formal protocol review. This lifecycle state means the design is sufficiently complete to receive protocol review; it does not make the Browser profile Accepted, normative, released, or authorized for Browser Spec/Schema/TCK/runtime implementation.

## Problem

A browser is not one serializable state object, and an automation context is not automatically a portable AVP snapshot primitive.

Real browser execution combines independently scoped surfaces such as cookies, Web Storage, IndexedDB, Cache Storage, Service Workers, browsing-context topology, navigation history, DOM/JavaScript execution, credentials, downloads, rendering state, browser build/configuration, networking, and time.

Different automation mechanisms expose different subsets of those surfaces. Treating Playwright `storageState`, a profile directory, a DevTools session, a WebDriver handle, or a browser-process checkpoint as "the AVP browser state" would create backend-first semantics.

A portable Browser Resource Profile must therefore state exactly:

- what resource boundary AVP owns;
- which state is authoritative and restorable;
- which data is Evidence or runtime observation only;
- which state is excluded from the base profile;
- what identity must remain immutable for execution;
- when projection is trustworthy;
- what restore fidelity can honestly be claimed;
- how an implementation proves the behavior without self-certification.

## Existing AVP authority reused

AEP-0011 specializes existing contracts and does not create competing concepts.

### Environment

Reused unchanged:

- authoritative Environment/resource ownership and ScenarioInstance binding;
- evaluator-authoritative projection identity;
- reset target honesty;
- Environment-owned SnapshotRef identity and foreign/stale rejection;
- restore fidelity vocabulary `EXACT | STATE_EQUIVALENT | NON_EQUIVALENT`;
- released-handle failure;
- Artifact identity for retained exact bytes.

### Environment Fabric

Reused unchanged:

- `resourceKind: browser` as coarse classification only;
- Resource Capability declaration and semantic-revision binding;
- REQUIRED/OPTIONAL participation from the materialized execution contract;
- Resource Capability versus Subject Capability separation;
- resource identity and profile-required identity Artifacts;
- fail-closed per-resource/composite result semantics;
- aggregate restore-fidelity non-inflation;
- no implicit cross-resource atomicity;
- Security/Evidence composition;
- execution-sensitive conformance;
- retry-safe cleanup.

`resourceKind: browser` alone does not claim Browser v0.1 semantics.

### Scenario and Core

Reused unchanged:

- unresolved required execution inputs fail before Episode execution;
- materialized execution semantics remain immutable during an Episode;
- Subject capabilities derive from the materialized actor projection;
- Core lifecycle remains the only Episode lifecycle;
- `QUIESCING` closes admission of new Subject side effects;
- already accepted work may settle;
- lifecycle, infrastructure condition, Validity, and Task Verdict remain separate.

### Security and Evidence

Reused unchanged:

- Subject, Evaluator, and privileged Control authority remain separated;
- evaluator/control credentials and automation handles do not enter Subject context;
- evaluator-private state is protected from Subject visibility;
- Artifact digest is identity, not retrieval authority or declassification;
- Evidence classification governs handling without changing exact-byte identity;
- technology labels such as `incognito`, `BrowserContext`, `headless`, container, or browser sandbox do not automatically establish `SecurityAssurance`.

## Standards and interoperability basis

The profile reuses upstream web-platform concepts where they own semantics and adds only the AVP verification-facing boundary.

- WHATWG HTML/Web Storage establishes the distinction between origin-scoped `localStorage` and session/topology-scoped `sessionStorage`.
- WHATWG URL/HTML define tuple-origin components and origin serialization; AVP reuses those semantics instead of inventing a second URL/origin canonicalizer.
- WHATWG Storage exposes multiple distinct storage endpoints rather than one universal browser-state map.
- IndexedDB has database, object-store, index, key, version, transaction, and structured-clone semantics that cannot be reduced to an unspecified JSON object.
- Service Worker and Cache Storage have independent registration/lifecycle/cache semantics.
- the HTTP cookie storage model distinguishes cookie name, domain, host-only flag, path, persistence/expiry, Secure, HttpOnly, and SameSite semantics; AVP preserves the portable subset needed by the selected unpartitioned-cookie state claim.
- WebDriver BiDi demonstrates implementation-neutral concepts such as user contexts, browsing contexts, cookie storage, and storage partition keys without defining AVP Environment identity or snapshot fidelity.
- Playwright is useful reference-implementation evidence but is not AVP protocol authority.

AVP does not copy an automation-library serialization format into the protocol.

## Portable resource boundary

One Browser v0.1 resource represents one independently owned **isolated browser session resource**.

The portable resource is not:

- one page/tab;
- one whole browser process;
- one browser profile directory;
- a Playwright `BrowserContext` object;
- a WebDriver BiDi user-context handle;
- a CDP target/session identifier.

A conforming implementation may realize the resource using any mechanism that preserves the observable isolation and state semantics. A process may host multiple independent resources. Backend process IDs, profile paths, and native handles are not portable resource identity.

Sibling resources must not silently share selected authoritative state.

## Authoritative v0.1 state surface

The base profile authoritative restorable state is exactly:

1. selected **unpartitioned HTTP cookies**; and
2. selected **origin-scoped `localStorage` key/value entries**.

This surface is closed. An implementation cannot silently omit selected state it cannot project or restore.

### Mandatory authoritative state

#### Unpartitioned cookies

Each projected cookie is one unpartitioned cookie-store entry. Its portable entry identity is the tuple:

```text
(name, domain, hostOnly, path)
```

No two projected cookies in one BrowserStateImage may have the same entry-identity tuple.

The canonical cookie state must preserve at least:

- `name` and `value` as the exact cookie data exposed by the selected browser state boundary;
- canonical domain/host text and the explicit `hostOnly` boolean;
- `path`;
- persistent versus session semantics;
- expiry instant when persistent;
- `Secure`;
- `HttpOnly`;
- `SameSite` state, including the distinction between an explicitly governed value and the user-agent default state where that distinction affects the stored cookie state.

Creation time and last-access time are not part of Browser v0.1 portable state identity. Browser eviction policy, cookie-store capacity, and retrieval ordering are not standardized by this profile.

An expired cookie is not a valid retained BrowserStateImage entry: the projected authoritative image represents the browser's current selected cookie store after expired entries have been removed according to browser cookie-store semantics. A session cookie records session persistence semantics rather than inventing an expiry instant.

Domain text must represent the canonical host/domain value associated with the stored cookie; AVP does not preserve whether an input `Domain` attribute originally contained presentation-only syntax such as a leading dot. Host-only versus domain-scoped behavior is preserved by `hostOnly`.

Partitioned/CHIPS-style cookie state is excluded from the base profile. A future separately governed capability may add storage-partition semantics once portable identity and executable cross-engine behavior are sufficiently bounded.

#### Origin-scoped localStorage

`localStorage` is represented per selected **tuple origin**. A flat global key/value map is forbidden.

For Browser v0.1, a selected `localStorage` origin must be a non-opaque tuple origin whose identity is `(scheme, host, port)` under WHATWG origin semantics. Its portable canonical text is the WHATWG serialization of that origin:

```text
scheme://serialized-host[:non-null-port]
```

The serialization therefore uses the parsed/canonical host form and includes a port only when the origin tuple's port is non-null. URL path, query, fragment, username, and password never participate in `localStorage` origin identity.

Opaque origins and `file:` origin behavior are outside the base v0.1 portable `localStorage` state claim because they do not provide the stable tuple-origin interoperability boundary this profile requires. A Scenario that materially requires them needs separately governed semantics.

Within one selected origin, `localStorage` state is a map from exact string key to exact string value. A key appears at most once. Canonical ordering is by the exact string-key representation defined by the downstream normative canonical JSON model, not browser enumeration order, locale, or insertion order.

For every selected origin, all selected `localStorage` entries participate in the authoritative state claim. Missing, extra, scope-shifted, or transformed selected entries are non-equivalent.

Browser profile paths, vendor storage-key tokens, native partition IDs, automation object IDs, or product-specific handles are not AVP origin/state identity.

## Explicitly excluded base state

The following do not participate in the base Browser v0.1 state digest or restore-equivalence claim:

- partitioned cookies/storage-partition state;
- `sessionStorage`;
- pages/tabs/popups and browsing topology;
- navigation history and current live page state;
- DOM and JavaScript heap;
- workers, timers, pending tasks, and dialogs;
- IndexedDB;
- Cache Storage;
- Service Worker registrations/lifecycle/runtime state;
- WebAuthn/passkey private credential state;
- downloads;
- screenshots, accessibility trees, traces, console logs, page errors, network events, and rendering output.

Some excluded surfaces are candidates for separately governed future capabilities. They are not implicitly optional parts of the base capability.

If a materialized Scenario depends on an excluded surface for reproducible verification, base Browser v0.1 alone is insufficient for that dependency and the execution must not falsely claim that the omitted state was restored.

## Evidence and runtime observation boundary

Evidence/observation is separate from authoritative state.

Potential Evidence includes current URL/navigation events, selected DOM or accessibility projections, screenshots, console/page errors, network traces, downloads, and execution diagnostics.

Capturing an Evidence surface does not make it restorable state. Equal screenshots do not prove equal Browser v0.1 state; unequal screenshots do not by themselves prove the selected cookie/`localStorage` state differs.

Retained Evidence continues to use AVP Artifact identity. Redacted bytes are distinct bytes with distinct identity from an original retained Artifact.

## Browser state identity direction

Downstream normative closure should define two acyclic logical resources analogous to AVP's existing content-addressing discipline:

```text
BrowserStateManifest
  profile/revision
  selected origin set / selection rules
  selected cookie scope rules
  canonical representation revision

BrowserStateImage
  manifestDigest
  cookies[]
  origins[]
    origin
    localStorage[]
```

The exact field names and schema spelling are downstream work; the semantics above are not.

The Manifest defines the interpretation/selection rules and does not point to the baseline StateImage. The baseline StateImage binds the Manifest digest. Runtime snapshot StateImages are generated Environment/Evidence state bound through SnapshotRef and do not mutate the resource's immutable baseline identity inputs.

The downstream normative specification must define one closed selection grammar: it must identify the complete set of unpartitioned cookie entries and tuple origins whose state participates in the resource without relying on a vendor query language or runtime-only callback. Selection identity is immutable for the materialized resource.

Canonical ordering and exact representation must be protocol-owned before schema/TCK closure. No automation-library export format becomes canonical authority.

## Execution-relevant immutable identity

Logical browser-state equality is not complete execution identity.

When the materialized Scenario relies on them, execution-relevant browser inputs must bind through existing Scenario/Fabric immutable execution-input mechanisms. Relevant inputs may include:

- browser engine family;
- exact browser version/build/revision sufficient to distinguish behavior;
- executable/package Artifact identity where stronger deployment identity is required;
- operating system/platform/architecture where behavior depends on it;
- headless/headful mode;
- locale and timezone;
- viewport and device scale factor;
- touch/mobile/device emulation configuration;
- JavaScript enablement;
- permissions and geolocation when relied upon;
- Service Worker policy;
- proxy/TLS/HTTPS policy when not owned by another Resource;
- preload scripts, extensions, or browser configuration when relied upon;
- font/rendering inputs when visual verification depends on them.

Relevance is Scenario-specific. The profile does not require hashes of every backend configuration field merely because a backend exposes them.

Labels such as `chromium`, `firefox`, `webkit`, `playwright`, or `selenium` alone are not sufficient immutable execution identity.

Missing or drifted required execution identity fails closed even when the logical state Manifest remains structurally satisfiable.

## Snapshot semantics

A snapshot captures the complete selected authoritative cookie + `localStorage` state as a canonical BrowserStateImage and binds it to the existing Environment/resource-owned SnapshotRef semantics.

Successful snapshot creation requires an evaluator-authoritative projection of the complete selected surface after the profile-relevant settlement boundary. Backend command success or an automation-library export object alone is insufficient.

A foreign, stale, corrupted, incompatible, or wrong-resource SnapshotRef fails closed under existing Environment semantics.

## Restore fidelity

Browser v0.1 successful restore reports exactly:

```text
STATE_EQUIVALENT
```

`EXACT` is forbidden as a successful base-profile restore fidelity.

A successful restore requires:

1. any conforming backend restore/reseed mechanism;
2. independent evaluator reprojection of the complete selected authoritative cookie + `localStorage` surface;
3. canonical equality with the target snapshot under the same profile/Manifest/resource identity binding;
4. failure if selected authoritative state is missing, extra, scope-shifted, transformed, or otherwise non-equivalent.

Context recreation, storage import success, navigation success, profile-directory restoration, or backend command success does not establish fidelity by itself.

`EXACT` is excluded because v0.1 does not standardize live JavaScript execution, page topology, `sessionStorage`, navigation history, worker lifecycle, caches, pending operations, browser-process continuation, or rendering/runtime timing state.

## Reset semantics

Reset establishes the immutable bound baseline BrowserStateImage and then independently reprojects the complete authoritative surface.

An implementation may recreate an isolated session and reseed state, clear/repopulate state safely, or use another mechanism. The protocol tests the observable result rather than prescribing automation commands.

Successful reset requires canonical post-reset equality with the bound baseline under the same Manifest/profile identity. An implementation cannot silently downgrade or drop an unsupported selected item.

## Operation settling and observation consistency

The browser profile defines no universal `network idle` condition and no arbitrary sleep-based correctness rule.

An accepted authoritative-state observation is produced only after:

1. Core has entered the side-effect admission boundary that prevents new Subject mutations from being accepted;
2. browser mutations accepted before that boundary have reached a profile-relevant terminal outcome or settlement fails;
3. selected cookie/`localStorage` writes relevant to the authoritative state no longer have unresolved accepted mutations;
4. the Evaluator can project the complete selected authoritative state without mixing known pre/post mutation fragments.

For base v0.1, this settlement rule concerns only the selected authoritative storage claim. It does not imply that all animations, timers, workers, rendering, or network activity are idle.

If trustworthy settlement cannot be established under the bound policy, no accepted final state projection is produced. The condition composes with existing infrastructure/Validity semantics and is not converted automatically into Agent Task Verdict failure.

## Subject capability boundary

Resource Capability support never grants arbitrary browser automation authority to the Subject.

The base profile does not define a universal page/locator/click/script API.

The materialized Scenario/Security actor projection separately governs any Subject browser actions or observations. Privileged browser/session provisioning, baseline seeding, reset, snapshot, restore, credential injection, hidden instrumentation, and evaluator-only diagnostics remain Evaluator/Control operations unless a separately governed Subject contract grants specific authority.

Automation/control handles and credentials must not be exposed merely because the reference implementation can access them.

## Service Worker and Cache policy

Service Worker registrations/lifecycle/runtime state and Cache Storage are excluded from base authoritative state.

A conforming implementation may run with Service Workers enabled or disabled as execution configuration. When that policy materially affects the Scenario, it must be identity-bound. The policy does not prove that Service Worker state itself is restorable.

The base capability must not claim state equivalence for behavior whose correctness materially depends on restoring Service Worker or Cache Storage state.

A future Service Worker/cache capability requires separate semantics and real cross-engine conformance evidence.

## Credential-bearing state

Cookies and `localStorage` remain authoritative even when selected values contain authentication material. Confidentiality changes visibility and handling, not identity.

Rules:

1. evaluator-private selected state remains authoritative;
2. Subject-visible observations must not disclose evaluator-private values;
3. retained secret-bearing snapshot bytes require appropriate Evidence classification and access control;
4. a digest does not grant retrieval authority or make secret bytes safe to publish;
5. public TCK fixtures use synthetic credentials only;
6. WebAuthn/passkey private credential export/import is not mandatory base behavior;
7. private keys/authenticator secrets must not become public TCK prerequisites.

## Relationship to Network and Time profiles

Browser v0.1 does not imply deterministic networking or time control.

Browser proxy/offline/interception options are implementation mechanics unless a governed Network Resource owns the portable claim. Browser clock overrides do not imply host/database/remote-service time virtualization.

Browser-local configuration relied upon by a Scenario may be identity-bound without absorbing future Network-Control or Time-Control semantics.

## Security analysis

A browser resource creates substantial control and data-exposure surface.

### Origin and state isolation

Origin boundaries must be preserved. Cross-origin `localStorage` must not be flattened into a Subject-readable global map. Evaluator authority to project or restore state does not expand Subject same-origin authority.

### Privileged automation channel

Remote-debugging, browser launch, extension/preload, browser-context management, and hidden fixture-control channels may grant powers beyond Scenario-authorized behavior. They remain privileged Control/Evaluator authority.

### Network exposure

Browser Resource conformance does not imply verified egress isolation. Access to local/private/metadata endpoints is governed by actual SecurityAssurance and/or a Network Resource, not by the browser capability label.

### Downloads and file interaction

Downloads are untrusted output. When retained, exact bytes use Artifact identity and may require limits, quarantine, and path isolation. Browser-supplied paths are never Artifact identity.

### Evidence leakage

Screenshots, traces, console output, DOM projections, network events, and state snapshots can contain secrets. Evidence visibility/access classification must be explicit.

### SecurityAssurance non-inflation

`Chromium sandbox`, private/incognito mode, `BrowserContext`, headless mode, a container, or another technology name does not by itself establish any `SecurityAssurance` dimension as verified.

## Backward compatibility

Browser v0.1 is additive under AEP-0009.

Existing Environment/Fabric implementations need not claim the Browser capability. Existing Fabric manifests may contain `resourceKind: browser`, but that coarse kind alone must not be interpreted as Browser v0.1 support.

No Alpha 2 semantics change. No release version is selected. The currently planned `0.3.1` maintenance release is not assigned Browser semantics by this AEP.

## Conformance strategy

Browser-profile conformance must be language-neutral, backend-name-neutral, and execution-sensitive.

Mandatory behavioral cases execute a real browser runtime through the implementation under test. Metadata declarations, mocks, or self-certification cannot substitute for behavior at the certified boundary.

Mandatory conformance families should cover at least:

1. isolated-resource ownership and sibling isolation;
2. execution-identity binding and incompatible-identity rejection;
3. baseline materialization and independent reprojection;
4. exact tuple-origin `localStorage` separation and canonical origin identity;
5. complete unpartitioned-cookie entry identity and stored attribute semantics;
6. exact canonical state identity for the selected surface;
7. SnapshotRef ownership/integrity and stale/foreign rejection;
8. mutation -> snapshot -> restore -> independent reprojection;
9. reset -> independent baseline reprojection;
10. restore fidelity exactly `STATE_EQUIVALENT` and rejection of false `EXACT`;
11. Resource Capability versus Subject Capability separation;
12. evaluator-private credential non-disclosure;
13. operation-settlement enforcement;
14. released-resource and cleanup behavior;
15. explicitly excluded required state failing closed;
16. metadata-identical negative implementations that break real behavior.

Negative controls should include at minimum implementations that:

- omit selected `localStorage` state;
- flatten cross-origin state;
- collapse host-only and domain-scoped cookies with otherwise matching fields;
- report restore success without independent reprojection;
- falsely report `EXACT`;
- expose evaluator-private credential values;
- admit new Subject mutation after the settlement boundary;
- self-certify support without real-browser execution.

Mandatory TCK fixtures use deterministic controlled local origins/resources. Portable expectations must not branch on Playwright, Chromium, Firefox, WebKit, Selenium, or other product names.

### Multi-engine portability evidence

A conforming third-party implementation is not required to implement multiple browser engines merely to claim one implementation of the portable profile.

However, before AVP treats the **reference semantics** as adequately protected against one-engine precedent, the reference acceptance gate should execute the same portable behavioral cases across at least two materially independent browser-engine families. A three-engine matrix is desirable where practical.

A single Chromium-only run is useful implementation evidence but is insufficient by itself to prove that an unresolved semantic choice is implementation-independent.

Engine product names remain test-matrix metadata, not protocol identity.

## Reference implementation gate

A Playwright adapter may begin only after:

1. AEP-0011 reaches the lifecycle state required by governance for downstream normative closure;
2. Browser normative semantics are encoded in the public specification;
3. serialized state/projection resources receive reviewed schemas where required;
4. the language-neutral execution-sensitive Browser TCK is reviewable;
5. any backend-neutral conformance harness/fixture-control prerequisites identified by readiness review are closed.

The base AVP distribution must remain usable without a browser provider dependency unless separate packaging governance decides otherwise. Browser provider dependencies should be optional, lazily imported at the implementation boundary, and must not download browser binaries during unrelated base-package import/install.

Implementation-private packages may use native browser objects internally, but portable public boundaries and TCK semantics must not expose those objects.

No generic `BaseBrowserBackend`, plugin framework, or provider abstraction is justified before a stable multi-consumer extension contract exists.

## Alternatives considered

### Implement Playwright first and generalize later

Rejected. It reverses the AEP-0009 authority direction and turns implementation limits into protocol semantics.

### Define browser state as Playwright `storageState`

Rejected as portable authority. It is an implementation mechanism for selected state surfaces, not a standards-level complete browser checkpoint.

### Make IndexedDB mandatory in base v0.1

Rejected for the base profile. IndexedDB semantics are materially richer than the selected cookie/`localStorage` boundary and require separately governed canonical serialization and transaction semantics.

### Include `sessionStorage` and page topology

Rejected for base v0.1. Session storage depends on browsing-session/topology identity that the base profile intentionally does not standardize.

### Include Service Worker / Cache Storage state

Rejected for base v0.1. Cross-engine lifecycle/control behavior is not sufficiently bounded for the initial portable state claim.

### Support partitioned cookies in the base profile

Rejected for v0.1. Storage-partition identity and cross-engine automation support require separate governance rather than a backend-shaped compatibility layer.

### Snapshot the whole browser profile directory

Rejected. Profile bytes contain engine/version-private formats, caches, locks, secrets, and unrelated state and cannot be portable equality.

### Make a live page the resource

Rejected. A page is too narrow to own shared cookie/origin storage and encourages native automation objects to become protocol identity.

### Make the whole browser process the resource

Rejected. Multiple independently isolated sessions may share one process, and process identity is an implementation concern.

### Omit snapshot/restore and standardize browser actions only

Rejected for this resource profile. A universal Subject automation API does not solve Environment state/reset/identity/replay honesty.

### Use `network idle` as the settlement definition

Rejected. Network-idle heuristics are not equivalent to settlement of the selected authoritative storage state and are not portable correctness semantics.

## Draft design-blocker disposition

The portability audit and this reconciliation resolve the original Draft blockers as follows:

- **BR-BR-001 — CLOSED:** authoritative base state is selected unpartitioned cookies + origin-scoped `localStorage` only.
- **BR-BR-002 — CLOSED:** tuple-origin state identity and cookie entry identity are explicitly portable; partitioned-cookie state is excluded from base.
- **BR-BR-003 — CLOSED:** page topology, history, and `sessionStorage` are excluded from base authoritative state.
- **BR-BR-004 — CLOSED:** successful base restore is exactly `STATE_EQUIVALENT`; `EXACT` is forbidden.
- **BR-BR-005 — CLOSED:** logical state is separated from Scenario/Fabric-bound execution identity.
- **BR-BR-006 — CLOSED:** Service Worker/Cache state is excluded from base and requires future separate capability semantics.
- **BR-BR-007 — CLOSED:** credential-bearing selected state remains authoritative with Security/Evidence visibility controls; WebAuthn private state is excluded.
- **BR-BR-008 — CLOSED:** canonical bytes/digests apply to the authoritative logical state surface, not rendering/diagnostic Evidence.
- **BR-BR-009 — CLOSED:** accepted projection requires profile-relevant settlement; no universal network-idle rule exists.
- **BR-BR-010 — CLOSED:** one cohesive base capability; real-browser backend-neutral TCK; reference portability evidence across at least two independent engine families before claiming implementation-independent reference semantics.

No unresolved Draft-design blocker remains from BR-BR-001 through BR-BR-010. Formal protocol review may still challenge these decisions; closure means the decisions are explicit and reviewable rather than predetermined as Accepted.

## Governance boundary

AEP-0011 is **Proposed** for formal protocol review under the explicit protocol-maintainer lifecycle authorization recorded on 2026-08-29. Proposed status is not Accepted or Final protocol authority and does not authorize downstream Browser implementation by itself.

This lifecycle transition does not authorize:

- `Proposed -> Accepted` or `Accepted -> Final`;
- Browser normative specification/requirement-index/schema/TCK adoption;
- browser backend-neutral harness implementation;
- Playwright/Selenium/WebDriver/CDP/BiDi adapter implementation as official AVP behavior;
- changing AEP-0009 or AEP-0010 lifecycle state;
- selecting an Alpha 3 public release version;
- assigning Browser work to `0.3.1`;
- changing release-development mode;
- repository merge without separate authorization;
- tag/GitHub Release/package-index publication;
- signing or attestation publication;
- treating reference implementation behavior as protocol authority.

The next governed Browser work after this lifecycle candidate is adopted into `main` is formal Proposed protocol review. Any semantic blocker discovered there must be resolved before a separate `Proposed -> Accepted` decision can be considered.

## References

- AEP-0009 — `rfcs/AEP-0009-environment-fabric.md`
- Environment Fabric contract — `spec/fabric/environment-fabric-contract.md`
- Browser portability audit — `docs/design/alpha3-browser-resource-portability-audit.md`
- WHATWG HTML — <https://html.spec.whatwg.org/>
- WHATWG URL — <https://url.spec.whatwg.org/>
- WHATWG Storage — <https://storage.spec.whatwg.org/>
- HTTP Cookies (RFC 6265bis work) — <https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/>
- W3C WebDriver BiDi — <https://w3c.github.io/webdriver-bidi/>
- Indexed Database API 3.0 — <https://w3c.github.io/IndexedDB/>
- Service Workers — <https://w3c.github.io/ServiceWorker/>
- Web Authentication Level 3 — <https://www.w3.org/TR/webauthn-3/>
- Playwright BrowserContext — <https://playwright.dev/docs/api/class-browsercontext>
- Playwright Service Workers — <https://playwright.dev/docs/service-workers>

External standards constrain interoperability analysis and mechanisms; they do not become AVP normative semantics merely by citation.
