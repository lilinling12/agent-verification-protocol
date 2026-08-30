# AEP-0011 — Browser Resource Profile v0.1

- Status: Proposed
- Authors: AVP maintainers and contributors
- Created: 2026-08-27
- Portability audit: `docs/design/alpha3-browser-resource-portability-audit.md`
- Proposed-readiness evidence: `docs/design/alpha3-browser-resource-proposed-readiness-audit.md`
- Lifecycle decision: `docs/acceptance/alpha3-aep-0011-proposed-decision.md`
- Formal Proposed review: `docs/design/alpha3-browser-resource-formal-proposed-review.md`
- Proposed-review blocker ledger: `docs/design/alpha3-browser-resource-proposed-review-blockers.md`
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Browser Resource

## Summary

AEP-0011 defines the portable direction for the first browser state resource profile under AVP Environment Fabric.

The core rule is:

> AVP standardizes the observable browser-session state boundary and the identity/evidence required to verify it; browser products, automation libraries, native handles, profile directories, and engine-private mechanics remain implementation details.

The v0.1 design is deliberately narrow. One independently isolated browser-session resource owns a closed authoritative logical state surface consisting of selected **unpartitioned HTTP cookies** and selected **unpartitioned `localStorage`** for exact tuple origins admitted by the profile. A successful restore may report exactly `STATE_EQUIVALENT`; `EXACT` is not a valid successful fidelity claim for this base profile.

The protocol-facing Resource Capability identity is:

```text
capabilityId: state.browser
profile: avp-browser-unpartitioned-cookie-localstorage-v0.1
revision: "0.1"
```

The capability is a Browser **state** capability. It does not imply a complete browser-profile checkpoint and does not grant a universal Browser Agent action API. Partition-aware storage, richer browser state, actions, and observations require separately governed capabilities.

AEP-0011 remains **Proposed**. Proposed status makes these decisions reviewable; it does not make the Browser profile Accepted, normative, released, or authorized for Browser Spec/Schema/TCK/runtime implementation.

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
- how state selection and exact values are represented;
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

- WHATWG HTML/Web Storage establishes `localStorage` string semantics and its relationship to origin and browsing context.
- WHATWG URL/HTML define tuple-origin components and origin serialization; AVP reuses those semantics instead of inventing a second URL/origin canonicalizer.
- WHATWG Storage distinguishes storage endpoints and storage keys; deployed browser privacy models may further partition state by top-level site or related context.
- Web IDL defines `DOMString` in terms of UTF-16 code units, including code-unit sequences that are not Unicode scalar-value strings.
- the HTTP cookie storage model distinguishes cookie name, domain, host-only flag, path, persistence/expiry, Secure, HttpOnly, SameSite, and temporal metadata such as creation time.
- IndexedDB, Cache Storage, and Service Worker state have independent semantics and are not reducible to an unspecified JSON map.
- WebDriver BiDi demonstrates implementation-neutral browser-control concepts but does not define AVP Environment identity or snapshot fidelity.
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
2. selected **unpartitioned `localStorage` key/value entries** for exact admitted tuple origins.

This surface is closed. An implementation cannot silently omit selected state it cannot project or restore, and it cannot project partitioned state into the base image under an unpartitioned identity.

### Unpartitioned cookies

Each projected cookie is one unpartitioned cookie-store entry. Its portable entry identity is:

```text
(name, domain, hostOnly, path)
```

No two projected cookies in one BrowserStateImage may have the same entry-identity tuple.

The canonical cookie state preserves at least:

- `name` and `value` as the exact cookie data in the selected browser state boundary;
- canonical domain/host text and the explicit `hostOnly` boolean;
- `path`;
- persistent versus session semantics;
- expiry instant when persistent;
- `Secure`;
- `HttpOnly`;
- `SameSite`, including a distinct user-agent `Default` state where the stored-cookie model distinguishes it from an explicitly governed value.

Creation time and last-access time are not portable BrowserStateImage identity fields. Their omission does **not** mean that temporal cookie semantics are irrelevant. Creation time can affect observable HTTP behavior, including default-SameSite compatibility behavior and cookie ordering. Browser eviction policy, cookie-store capacity, and retrieval ordering are likewise not standardized by the image.

An expired cookie is not a valid retained BrowserStateImage entry. A session cookie records session persistence semantics rather than inventing an expiry instant.

Domain text represents the canonical host/domain value associated with the stored cookie; presentation-only input syntax such as a leading dot is not preserved. Host-only versus domain-scoped behavior is preserved by `hostOnly`.

Partitioned/CHIPS-style cookie state is excluded from the base profile. A future separately governed capability may define partition-aware identity and restoration.

#### Lossless cookie projection requirement

The portable identity above remains authoritative even if a browser-control API is lossy. A backend API that omits `hostOnly`, `SameSite=Default`, or another required selected field does not redefine AVP semantics.

An implementation may successfully project a selected cookie only when evaluator/control authority can establish the required identity and state through an independently reviewable mechanism. It MUST fail closed for selected cookie state whose required identity or state cannot be established without ambiguity. Inferring `hostOnly` from a convenience serialization, normalizing unknown state, or treating backend export success as projection proof is insufficient.

Acceptance of this AEP additionally requires cross-engine evidence that the identity/projection rule is implementable and behaves as claimed for Chromium, Gecko, and WebKit engine families.

#### Cookie temporal restore eligibility

A selected cookie is eligible for a successful Browser v0.1 `STATE_EQUIVALENT` restore only when the implementation can establish that recreating/restoring the cookie preserves the profile-relevant behavior required by the materialized Scenario under its bound execution policy.

In particular:

1. `SameSite=Default` MUST remain distinct from explicit `Lax`; `Default -> Lax` normalization is forbidden.
2. If creation-time-dependent behavior can materially affect the verification claim and historical creation time cannot be preserved or its behavioral effect otherwise proven equivalent, restore MUST fail closed for the resource.
3. Reprojection equality of image fields is necessary but is not, by itself, proof of unbounded HTTP behavioral equivalence.
4. A Scenario or fixture used to claim successful restore MUST make the admitted temporal-behavior assumptions reviewable and bind any execution policy on which that eligibility relies.
5. A backend MUST NOT manufacture a fresh field-equal cookie and report `STATE_EQUIVALENT` when a material creation-time distinction remains unresolved.

This rule keeps the portable image narrow while preventing image-field equality from overstating browser behavior.

### Unpartitioned localStorage

Browser v0.1 standardizes only **unpartitioned** `localStorage` whose selected storage identity can be proven to be the tuple origin itself in the controlled execution context. Tuple-origin identity is not a claim that all modern browser storage is unpartitioned.

A selected origin must be a non-opaque tuple origin `(scheme, host, port)` under WHATWG origin semantics. Its portable canonical text is the WHATWG serialization:

```text
scheme://serialized-host[:non-null-port]
```

The parsed/canonical host form is used and a port appears only when the origin tuple's port is non-null. Path, query, fragment, username, and password never participate in `localStorage` origin identity.

Opaque origins and `file:` origin behavior are outside the base v0.1 claim. Partitioned third-party storage, top-level-site-keyed storage, or another storage-key variant MUST NOT be aliased to ordinary tuple-origin `localStorage` in this profile. If a Scenario materially depends on such partitioned state, Browser v0.1 is insufficient and execution fails closed unless a separately governed partition-aware capability owns that dependency.

For each selected origin, the complete admitted unpartitioned `localStorage` map participates in authoritative state. Missing, extra, transformed, or scope-shifted entries are non-equivalent.

### Exact Web Storage string representation

Web Storage keys and values are exact Web IDL `DOMString` values. Browser v0.1 therefore defines equality over the exact ordered sequence of unsigned 16-bit UTF-16 code units, not over a host-language Unicode scalar-value string abstraction.

For protocol serialization, each `DOMString` is encoded as follows:

1. take its UTF-16 code units without repairing or replacing unmatched surrogates;
2. encode each unsigned code unit as exactly two bytes in network byte order (most-significant byte first);
3. concatenate those bytes in code-unit order;
4. encode the resulting bytes with unpadded base64url as defined by RFC 4648 URL-safe alphabet.

This representation is lossless for all `DOMString` values, including unmatched surrogates. Downstream canonical JSON carries this ASCII representation; a JSON library is never asked to preserve the original potentially non-scalar-value string directly.

Equality is byte-for-byte equality of the decoded UTF-16 code-unit sequence. Canonical key ordering is lexicographic ordering by unsigned UTF-16 code units; if one sequence is an exact prefix of another, the shorter sequence sorts first. Browser enumeration order, insertion order, locale collation, host-language string ordering, and JSON-library behavior are not authoritative.

The BrowserStateManifest binds the canonical representation revision so a future representation change cannot silently reinterpret existing state identity.

## Closed state-selection grammar

Browser v0.1 fixes one finite, vendor-neutral selection grammar. The schema may choose field spelling later, but MUST preserve these semantics.

### localStorage selection

The Manifest contains a finite, duplicate-free list of exact canonical tuple-origin strings. Each listed origin selects its **complete admitted unpartitioned `localStorage` map**. An empty map is meaningful state and participates in equality.

### Cookie selection

The Manifest contains a finite, duplicate-free list of exact canonical stored-cookie domain strings. A cookie is selected iff it is unpartitioned and its canonical stored domain is exactly equal to one listed domain. Every selected cookie entry participates, including cookie names not known when the Manifest was authored.

### Selection restrictions

Selection lists are canonicalized and immutable for the materialized resource. The grammar has no regex, glob, suffix/subdomain matcher, vendor callback, backend-native query expression, runtime code, Playwright filter, CDP predicate, or partition selector.

Selection semantics are complete-set semantics. Missing selected state, extra in-scope state, transformed values, changed cookie scope, or state projected under a different storage identity is non-equivalent.

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

### Residual-state noninterference

Excluding a surface from BrowserStateImage does not establish that the surface is behaviorally irrelevant. For every excluded surface that can materially affect the Scenario verification claim, the materialized execution MUST establish at least one of:

1. isolation or configuration that makes the surface noninterfering for the claimed verification boundary;
2. immutable execution-identity/policy binding through existing Scenario/Fabric mechanisms sufficient to make the relied-upon condition explicit and drift-detectable; or
3. fail-closed insufficiency: Browser v0.1 alone is declared unable to reproduce that Scenario dependency.

This rule applies to, among other things, Service Worker state, Cache Storage, IndexedDB, permissions, extensions, preload scripts, browser-profile residue, network policy, credential state, and other excluded state that can change execution behavior.

A successful base restore never claims reproduction of excluded state merely because selected BrowserStateImage state is equal.

## Evidence and runtime observation boundary

Evidence/observation is separate from authoritative state.

Potential Evidence includes current URL/navigation events, selected DOM or accessibility projections, screenshots, console/page errors, network traces, downloads, and execution diagnostics.

Capturing an Evidence surface does not make it restorable state. Equal screenshots do not prove equal Browser v0.1 state; unequal screenshots do not by themselves prove the selected cookie/`localStorage` state differs.

Retained Evidence continues to use AVP Artifact identity. Redacted bytes are distinct bytes with distinct identity from an original retained Artifact.

## Browser state identity

Downstream normative closure defines two acyclic logical resources analogous to AVP's existing content-addressing discipline:

```text
BrowserStateManifest
  capability/profile/revision
  exact localStorage origin selection
  exact cookie stored-domain selection
  canonical representation revision
  profile-required execution policy/identity bindings

BrowserStateImage
  manifestDigest
  cookies[]
  origins[]
    origin
    localStorage[]
```

The exact schema field names remain downstream work; the selection and equality semantics do not.

The Manifest defines interpretation and selection rules and does not point to the baseline StateImage. The baseline StateImage binds the Manifest digest. Runtime snapshot StateImages are generated Environment/Evidence state bound through SnapshotRef and do not mutate immutable baseline identity inputs.

No automation-library export format becomes canonical authority.

## Execution-relevant immutable identity

Logical browser-state equality is not complete execution identity.

When the materialized Scenario relies on them, execution-relevant browser inputs bind through existing Scenario/Fabric immutable execution-input mechanisms. Relevant inputs may include:

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
- font/rendering inputs when visual verification depends on them;
- cookie temporal-behavior assumptions/policy when relied upon;
- storage-partitioning/isolation policy needed to establish the admitted unpartitioned state boundary.

Relevance is Scenario-specific. The profile does not require hashes of every backend configuration field merely because a backend exposes them.

Labels such as `chromium`, `firefox`, `webkit`, `playwright`, or `selenium` alone are not sufficient immutable execution identity.

Missing or drifted required execution identity fails closed even when the logical state Manifest remains structurally satisfiable.

## Snapshot semantics

A snapshot captures the complete selected authoritative cookie + `localStorage` state as a canonical BrowserStateImage and binds it to existing Environment/resource-owned SnapshotRef semantics.

Successful snapshot creation requires evaluator-authoritative lossless projection of the complete selected surface after the profile-relevant settlement witness. Backend command success or an automation-library export object alone is insufficient.

A foreign, stale, corrupted, incompatible, or wrong-resource SnapshotRef fails closed under existing Environment semantics.

## Restore fidelity

Browser v0.1 successful restore reports exactly:

```text
STATE_EQUIVALENT
```

`EXACT` is forbidden as a successful base-profile restore fidelity.

A successful restore means that, under the same immutable BrowserStateManifest/profile/revision/resource binding and compatible required execution identity:

1. the target selected state is restored by any conforming backend mechanism;
2. every selected cookie satisfies the temporal restore-eligibility rule;
3. the profile-relevant settlement witness is established;
4. independent evaluator reprojection yields exactly the complete target selected authoritative state;
5. required absence is preserved and no extra in-scope state exists.

Missing, extra, scope-shifted, transformed, ambiguously projected, or temporally ineligible selected state fails closed.

`STATE_EQUIVALENT` is intentionally scoped. It does not claim equality of DOM, page topology, `sessionStorage`, navigation history, browser-internal metadata, worker lifecycle, caches, excluded storage, process continuation, rendering, or other excluded surfaces.

Context recreation, storage import success, navigation success, profile-directory restoration, backend command success, or image-field equality without the required eligibility/witness conditions does not establish fidelity by itself.

## Reset semantics

Reset establishes the immutable bound baseline BrowserStateImage and then independently reprojects the complete authoritative surface.

An implementation may recreate an isolated session and reseed state, clear/repopulate state safely, or use another mechanism. The protocol tests the observable result rather than prescribing automation commands.

Successful reset requires the same restore-eligibility, settlement, independent-reprojection, complete-set, and residual-noninterference rules as successful restore. An implementation cannot silently downgrade or drop an unsupported selected item.

## Operation settling and observation consistency

The browser profile defines no universal browser-idle state. An accepted authoritative projection requires a **positive profile-relevant settlement witness**.

The witness exists only when all of the following are established by evaluator/control authority:

1. Core has closed admission of new Subject side effects for the Episode boundary being observed;
2. every accepted pre-boundary mutation that can affect selected authoritative browser state has a known terminal outcome;
3. no accepted profile-relevant mutation remains unresolved;
4. the authoritative projection begins only after items 1–3 are true and is obtained without knowingly mixing pre/post mutation fragments.

The implementation must expose enough control/evidence for the witness to be independently reviewable at the conformance boundary. A timeout may terminate waiting, but elapsed time alone does not prove settlement. Arbitrary sleeps, `networkidle`, quiet-window heuristics, browser-vendor event queues, and backend command completion are insufficient by themselves.

If the witness cannot be established, the operation fails closed as **unsettled** and no accepted final authoritative projection is produced. This condition concerns infrastructure/Validity semantics and is not automatically converted into Agent Task Verdict failure.

The witness concerns only selected authoritative state. It does not imply that animations, rendering, unrelated timers, workers, or network activity are globally idle.

## Subject capability boundary

Resource Capability support never grants arbitrary browser automation authority to the Subject.

The base profile does not define a universal page/locator/click/script API.

The materialized Scenario/Security actor projection separately governs any Subject browser actions or observations. Privileged browser/session provisioning, baseline seeding, reset, snapshot, restore, credential injection, hidden instrumentation, and evaluator-only diagnostics remain Evaluator/Control operations unless a separately governed Subject contract grants specific authority.

Automation/control handles and credentials must not be exposed merely because the reference implementation can access them.

## Service Worker and Cache policy

Service Worker registrations/lifecycle/runtime state and Cache Storage are excluded from base authoritative state.

A conforming implementation may run with Service Workers enabled or disabled as execution configuration. When that policy materially affects the Scenario, it must satisfy the residual-state noninterference rule and, where relied upon, be identity-bound. The policy does not prove that Service Worker state itself is restorable.

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

Partitioned state must not be relabeled as unpartitioned tuple-origin state merely to make it serializable through a backend API.

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

No Alpha 2 semantics change. No release version is selected. The currently planned maintenance release is not assigned Browser semantics by this AEP.

## Conformance and acceptance-evidence strategy

Browser-profile conformance must be language-neutral, backend-name-neutral, and execution-sensitive.

Mandatory behavioral cases execute a real browser runtime through the implementation under test. Metadata declarations, mocks, or self-certification cannot substitute for behavior at the certified boundary.

Mandatory conformance families should cover at least:

1. isolated-resource ownership and sibling isolation;
2. execution-identity binding and incompatible-identity rejection;
3. baseline materialization and independent reprojection;
4. exact admitted unpartitioned tuple-origin `localStorage` separation;
5. lossless Web Storage `DOMString` representation, including unmatched-surrogate cases;
6. complete unpartitioned-cookie identity including host-only/domain differentiation;
7. distinct `SameSite=Default` handling and temporal restore eligibility;
8. closed complete-set selection semantics;
9. SnapshotRef ownership/integrity and stale/foreign rejection;
10. mutation -> snapshot -> restore -> independent reprojection;
11. reset -> independent baseline reprojection;
12. restore fidelity exactly `STATE_EQUIVALENT` and rejection of false `EXACT`;
13. Resource Capability versus Subject Capability separation;
14. evaluator-private credential non-disclosure;
15. positive settlement-witness enforcement;
16. residual-state noninterference/fail-closed behavior;
17. released-resource and cleanup behavior;
18. explicitly excluded required state failing closed;
19. metadata-identical negative implementations that break real behavior.

Negative controls should include implementations that:

- omit selected `localStorage` state;
- flatten or misclassify partitioned storage as tuple-origin unpartitioned state;
- collapse host-only and domain-scoped cookies with otherwise matching fields;
- normalize `SameSite=Default` to explicit `Lax`;
- recreate temporally ineligible cookies and falsely report equivalence;
- corrupt an unmatched-surrogate `DOMString` through host-language JSON handling;
- report restore success without independent reprojection;
- falsely report `EXACT`;
- expose evaluator-private credential values;
- admit new Subject mutation after the settlement boundary;
- use sleep/network-idle as the sole settlement proof;
- self-certify support without real-browser execution.

Mandatory TCK fixtures use deterministic controlled local origins/resources. Portable expectations must not branch on Playwright, Chromium, Firefox, WebKit, Selenium, or another product name.

### Chromium / Gecko / WebKit acceptance evidence

Before an acceptance-oriented review may conclude that AEP-0011 has no remaining portability blocker, reviewable evidence MUST exercise the same portable semantic decisions across Chromium, Gecko, and WebKit engine families.

The acceptance matrix covers at least:

- selected unpartitioned cookie identity/projection;
- host-only versus domain-scoped cookie behavior;
- `SameSite=Default` and temporal restore restrictions;
- admitted unpartitioned `localStorage` tuple-origin behavior;
- rejection/non-admission of partitioned state into the base profile;
- lossless Web Storage string projection where the engine boundary permits the selected value;
- independent post-restore/reset reprojection;
- settlement fail-closed behavior;
- residual-state isolation assumptions used by the fixture.

This matrix is an **AEP acceptance-evidence gate**. It is not a universal requirement that every future third-party conforming implementation support three engines. Engine product names are evidence metadata, not protocol identity, and an engine-specific API limitation cannot redefine portable semantics.

## Reference implementation gate

A browser provider/reference implementation may begin only after:

1. AEP-0011 reaches the lifecycle state required by governance for downstream normative closure;
2. Browser normative semantics are encoded in the public specification;
3. serialized state/projection resources receive reviewed schemas where required;
4. the language-neutral execution-sensitive Browser TCK is reviewable;
5. backend-neutral conformance harness/fixture-control prerequisites identified by readiness review are closed.

The base AVP distribution must remain usable without a browser provider dependency unless separate packaging governance decides otherwise. Browser provider dependencies should be optional, lazily imported at the implementation boundary, and must not download browser binaries during unrelated base-package import/install.

Implementation-private packages may use native browser objects internally, but portable public boundaries and TCK semantics must not expose those objects.

No generic `BaseBrowserBackend`, plugin framework, or provider abstraction is justified before a stable multi-consumer extension contract exists.

## Alternatives considered

### Implement Playwright first and generalize later

Rejected. It reverses the AEP-0009 authority direction and turns implementation limits into protocol semantics.

### Define browser state as Playwright `storageState`

Rejected as portable authority. It is an implementation mechanism for selected state surfaces, not a standards-level complete browser checkpoint.

### Add creation time to BrowserStateImage merely because the cookie model has it

Rejected for v0.1. Mainstream portable automation surfaces do not expose and restore arbitrary historic creation time reliably enough to make it a portable image field. The profile instead constrains successful restore with explicit temporal restore eligibility and fail-closed behavior.

### Make IndexedDB mandatory in base v0.1

Rejected. IndexedDB semantics are materially richer than the selected cookie/`localStorage` boundary and require separately governed canonical serialization and transaction semantics.

### Include `sessionStorage` and page topology

Rejected. Session storage depends on browsing-session/topology identity that the base profile intentionally does not standardize.

### Include Service Worker / Cache Storage state

Rejected. Cross-engine lifecycle/control behavior is not sufficiently bounded for the initial portable state claim.

### Support partitioned storage in the base profile

Rejected. Storage-partition identity and cross-engine automation support require separate governance rather than a backend-shaped compatibility layer.

### Snapshot the whole browser profile directory

Rejected. Profile bytes contain engine/version-private formats, caches, locks, secrets, and unrelated state and cannot be portable equality.

### Make a live page the resource

Rejected. A page is too narrow to own shared cookie/origin storage and encourages native automation objects to become protocol identity.

### Make the whole browser process the resource

Rejected. Multiple independently isolated sessions may share one process, and process identity is an implementation concern.

### Omit snapshot/restore and standardize browser actions only

Rejected. A universal Subject automation API does not solve Environment state/reset/identity/replay honesty.

### Use `network idle` or sleep as the settlement definition

Rejected. Timing heuristics are not equivalent to a positive witness that accepted mutations affecting selected authoritative state are terminal.

## Proposed-review blocker disposition

The formal Proposed review is authoritative over conflicting Draft-era design wording.

- **BPR-001 — PROTOCOL DECISION INCORPORATED:** public identity is `state.browser` / `avp-browser-unpartitioned-cookie-localstorage-v0.1` / `0.1`.
- **BPR-002 — PROTOCOL DECISION INCORPORATED:** localStorage is explicitly unpartitioned and tuple-origin identity is admitted only where that boundary is proven.
- **BPR-003 — PROTOCOL DECISION INCORPORATED; ACCEPTANCE EVIDENCE REQUIRED:** cookie identity remains `(name, domain, hostOnly, path)` and lossy projection fails closed; three-engine evidence remains required before acceptance.
- **BPR-004 — PROTOCOL DECISION INCORPORATED; ACCEPTANCE EVIDENCE REQUIRED:** `SameSite=Default` is distinct and successful restore is limited by temporal restore eligibility; unresolved creation-time-dependent behavior fails closed.
- **BPR-005 — PROTOCOL DECISION INCORPORATED:** finite exact-origin/exact-stored-domain complete-set selection grammar is fixed here.
- **BPR-006 — PROTOCOL DECISION INCORPORATED:** accepted projection requires a positive evaluator/control settlement witness; timeouts and idle heuristics do not prove settlement.
- **BPR-007 — PROTOCOL DECISION INCORPORATED:** exact `DOMString` values use protocol-owned UTF-16-code-unit/base64url representation and code-unit ordering.
- **BPR-008 — PROTOCOL DECISION INCORPORATED:** materially relevant excluded state requires noninterference, immutable policy/identity binding, or fail-closed insufficiency.
- **BPR-009 — OPEN ACCEPTANCE-EVIDENCE GATE:** Chromium/Gecko/WebKit evidence remains required before acceptance-oriented review can close.

These dispositions do not self-approve AEP-0011 and do not close BPR-009 by assertion.

## Draft design-blocker disposition

The prior Draft blockers BR-BR-001 through BR-BR-010 remain historical provenance. Where Draft-era audits or readiness documents conflict with this Proposed-review blocker resolution, this AEP supersedes those earlier design assumptions.

In particular, earlier wording that described tuple-origin `localStorage` without an explicit unpartitioned boundary, deferred selection grammar/canonical string representation downstream, or treated two-engine evidence as sufficient is superseded.

## Governance boundary

AEP-0011 remains **Proposed**. This blocker-resolution edit does not authorize `Proposed -> Accepted` and does not authorize Browser normative Spec/requirement-index/schema/TCK, backend-neutral harness, Playwright/Selenium/WebDriver/CDP/BiDi reference implementation, release selection, publication, signing, attestation, repository split, or plugin-framework work.

The next governed Browser work after adoption of these protocol edits is:

1. produce reviewable BPR-003/BPR-004/BPR-009 cross-engine acceptance evidence against Chromium, Gecko, and WebKit families without letting any provider API define the protocol;
2. perform an acceptance-oriented exact-head protocol re-review against the blocker-resolution head and evidence;
3. only if that review finds no remaining semantic blocker, request a separate explicit protocol-maintainer `Proposed -> Accepted` decision.

Generic continuation does not authorize item 3. Repository merge remains separately authorized.

## References

- AEP-0009 — `rfcs/AEP-0009-environment-fabric.md`
- Environment Fabric contract — `spec/fabric/environment-fabric-contract.md`
- Browser portability audit — `docs/design/alpha3-browser-resource-portability-audit.md`
- Formal Proposed review — `docs/design/alpha3-browser-resource-formal-proposed-review.md`
- Proposed-review blocker ledger — `docs/design/alpha3-browser-resource-proposed-review-blockers.md`
- WHATWG HTML — <https://html.spec.whatwg.org/>
- WHATWG Web IDL — <https://webidl.spec.whatwg.org/>
- WHATWG URL — <https://url.spec.whatwg.org/>
- WHATWG Storage — <https://storage.spec.whatwg.org/>
- HTTP Cookies — RFC 10025
- JSON Canonicalization Scheme — RFC 8785
- W3C WebDriver BiDi — <https://w3c.github.io/webdriver-bidi/>
- Indexed Database API — <https://w3c.github.io/IndexedDB/>
- Service Workers — <https://w3c.github.io/ServiceWorker/>
- Web Authentication — <https://www.w3.org/TR/webauthn-3/>
- Playwright BrowserContext — <https://playwright.dev/docs/api/class-browsercontext>

External standards constrain interoperability analysis and mechanisms; they do not become AVP normative semantics merely by citation.
