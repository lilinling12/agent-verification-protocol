# AEP-0011 Browser Resource Portability / Proposed-Readiness Audit

Status: **PORTABILITY DECISIONS RECORDED — AEP RECONCILIATION REQUIRED BEFORE PROPOSED**

AEP: `rfcs/AEP-0011-browser-resource-profile.md`
Parent: AEP-0009 (Accepted)
Audit date: 2026-08-28
Baseline: `main@7a02e5724b001d39e54acc3a26a4e05543161d53`

## 1. Audit purpose

This audit resolves the design direction for BR-BR-001 through BR-BR-010 sufficiently to constrain the next AEP-0011 reconciliation work unit.

It does **not** change AEP-0011 from Draft, does not itself close the Draft → Proposed lifecycle gate, does not create normative Browser schemas/TCK, and does not authorize a Playwright implementation.

The audit applies the repository authority rule:

```text
Normative Spec -> Schema -> TCK / Conformance -> Reference Implementation
```

Browser automation products and browser-engine APIs are implementation evidence only.

## 2. Portability conclusion

The v0.1 Browser Resource profile should be deliberately narrow.

The base portable claim should cover one independently isolated browser-session resource with a closed logical storage state surface that can be reproduced across browser engines without depending on one automation library's export format.

The base v0.1 authoritative restorable state should contain:

1. **unpartitioned HTTP cookie state** selected for the resource; and
2. **origin-scoped `localStorage` key/value state** selected for the resource.

The following should **not** be part of the mandatory v0.1 authoritative restore surface:

- `sessionStorage`;
- page/tab/popup topology;
- navigation history;
- live DOM or JavaScript heap;
- IndexedDB;
- Cache Storage;
- Service Worker registrations/lifecycle/runtime state;
- WebAuthn/passkey private credential state;
- downloads;
- screenshots, accessibility trees, traces, console output, network events, current URLs, or rendering artifacts.

Some of these may become separately governed optional capabilities later. Evidence-only surfaces remain governed by AVP Evidence/Security without becoming state merely because an implementation can capture them.

This narrow base is intentional. A profile that claims a larger state boundary without cross-engine executable semantics would be less portable, not more complete.

## 3. BR-BR-001 — authoritative v0.1 state surface

**Decision: CLOSED FOR AEP RECONCILIATION**

Base v0.1 authoritative restorable state is exactly:

- selected unpartitioned cookies; and
- selected origin-scoped `localStorage` entries.

The state surface is closed. An implementation cannot silently omit an entry it cannot faithfully project or restore.

Classification for v0.1:

| Surface | v0.1 classification |
|---|---|
| unpartitioned cookies | mandatory authoritative state |
| origin-scoped `localStorage` | mandatory authoritative state |
| partitioned cookies / partition-key state | excluded from base; future separately governed capability |
| `sessionStorage` | excluded from base |
| IndexedDB | excluded from base; future optional capability candidate |
| Cache Storage | excluded from base |
| Service Worker registrations/runtime state | excluded from base |
| page/tab/popup topology | runtime observation only |
| navigation/history | runtime observation/evidence only |
| DOM / JS heap / workers / timers | excluded from authoritative state |
| WebAuthn/passkey credential state | excluded from base |
| downloads | Evidence Artifact only when retained |
| screenshots / accessibility / traces / console / network events | Evidence/observation only |

A Scenario that materially requires an excluded surface for reproducible verification cannot claim base Browser v0.1 state equivalence for that dependency.

## 4. BR-BR-002 — origin and storage-partition identity

**Decision: CLOSED FOR AEP RECONCILIATION**

Portable `localStorage` identity is origin-scoped and must preserve web-platform origin separation. A flat global key/value map is forbidden.

The base profile should use a protocol-owned canonical origin representation derived from standards-level origin components rather than browser profile directories or automation handles.

For v0.1 cookies, the portable model is deliberately restricted to unpartitioned cookie state. Cookie identity and canonical comparison must preserve the fields required to distinguish cookie scope and behavior, including at minimum:

- name;
- value;
- domain / host-only semantics as represented by the eventual normative model;
- path;
- expiry/session semantics;
- secure;
- HttpOnly;
- SameSite where applicable.

Partition-key / CHIPS-style cookie state is excluded from base v0.1 because cross-engine storage-partition representation and automation support are not yet sufficiently stable to make it a mandatory portable state claim.

No vendor storage-key token, profile path, browser-context identifier, CDP target ID, Playwright object, or WebDriver handle may become AVP state identity.

## 5. BR-BR-003 — page topology and session-scoped state

**Decision: CLOSED FOR AEP RECONCILIATION**

Pages/tabs/popups, navigation history, and `sessionStorage` are excluded from authoritative base v0.1 restore state.

They may be observed as runtime evidence when a selected evaluator projection requires them, but their presence does not participate in the base state digest or `STATE_EQUIVALENT` restore claim.

This avoids falsely standardizing a live browsing-session checkpoint when the base profile only guarantees selected durable logical storage state.

If a future capability standardizes topology/session restoration, it requires separate semantics and real cross-engine TCK evidence.

## 6. BR-BR-004 — snapshot/restore fidelity

**Decision: CLOSED FOR AEP RECONCILIATION**

Base Browser v0.1 successful restore reports exactly:

```text
STATE_EQUIVALENT
```

`EXACT` is not a valid successful fidelity claim for the base profile.

A successful restore requires:

1. restore/reseed using any conforming backend mechanism;
2. independent evaluator reprojection of the complete selected authoritative cookie + `localStorage` surface;
3. re-establishment of the canonical snapshot-state identity under the same profile/resource identity binding;
4. failure if any selected authoritative item is missing, extra, scope-shifted, transformed, or otherwise non-equivalent.

Context creation success, storage import success, navigation success, or backend command success is insufficient by itself.

`EXACT` is excluded because v0.1 does not standardize live JS execution, page topology, session storage, navigation history, worker lifecycle, cache state, pending operations, browser-process identity, or rendering/runtime timing state.

## 7. BR-BR-005 — browser execution identity

**Decision: CLOSED FOR AEP RECONCILIATION**

Logical browser-state equality is not complete execution identity.

Execution-relevant browser inputs must bind through existing Scenario/Fabric immutable execution-input mechanisms when the materialized Scenario relies on them.

Candidate required identities, when relevant, include:

- browser engine family;
- exact browser version/build/revision sufficient to distinguish executable behavior;
- browser executable/package artifact identity when governed deployment requires stronger byte identity;
- operating-system/platform and architecture where behavior depends on them;
- headless/headful mode;
- locale;
- timezone;
- viewport dimensions;
- device scale factor;
- touch/mobile/device emulation settings;
- JavaScript enablement;
- permissions/geolocation where relied upon;
- service-worker policy;
- proxy/TLS/HTTPS policy where not owned by another resource;
- preload scripts/extensions/configuration identity when relied upon;
- font/rendering inputs when visual verification depends on them.

Relevance is materialized-execution-specific. The profile must not require hashes of every browser configuration field merely because a backend exposes them.

Labels such as `chromium`, `firefox`, `webkit`, or `playwright` alone are never sufficient immutable execution identity.

## 8. BR-BR-006 — service-worker/cache semantics

**Decision: CLOSED FOR AEP RECONCILIATION**

Service Worker registrations/lifecycle/runtime state and Cache Storage are excluded from the mandatory base v0.1 authoritative state claim.

The base capability must not claim state equivalence for behavior whose correctness materially depends on restoring those surfaces.

A conforming base implementation may run with Service Workers enabled or disabled as an execution configuration, but that policy is execution identity, not proof that Service Worker state is restorable.

Where the Scenario depends on a particular Service Worker policy, that policy must be bound explicitly. An implementation must not hide network-interception differences behind a generic browser capability claim.

A future Service Worker/cache state capability requires separate cross-engine semantics and TCK coverage.

## 9. BR-BR-007 — credential-bearing browser state

**Decision: CLOSED FOR AEP RECONCILIATION**

Cookies and `localStorage` remain authoritative even when their values contain authentication material. Confidentiality changes handling and visibility, not state identity.

Rules:

1. evaluator-private credential-bearing state remains part of authoritative state when selected;
2. Subject-visible projections must not expose evaluator-private values;
3. retained snapshot bytes containing secrets require appropriate Evidence classification and access control;
4. Artifact digest does not grant retrieval authority and does not make secret bytes safe to publish;
5. public TCK fixtures use synthetic non-production credentials;
6. virtual WebAuthn/passkey credential export/import is not mandatory base behavior;
7. private keys or authenticator secrets must not become a public conformance prerequisite.

A future virtual-authenticator capability may be standardized separately.

## 10. BR-BR-008 — canonical projection and evidence boundary

**Decision: CLOSED FOR AEP RECONCILIATION**

The base profile requires portable canonical bytes only for the authoritative logical browser state surface and any state projection needed to verify it.

A future normative representation should define canonical state objects for:

- selected cookies; and
- selected origin-scoped `localStorage`.

Canonical ordering and exact representation must be protocol-owned before schema/TCK closure.

The following are not part of the base canonical state digest:

- DOM snapshots;
- accessibility trees;
- screenshots;
- traces;
- console logs;
- page errors;
- network events;
- current URLs/navigation events;
- downloads.

Those may be Evidence Artifacts or named observations with their own content identity. Equal screenshots do not prove equal browser state; unequal screenshots do not automatically prove base storage-state inequality.

No automation-library export format is portable canonical authority.

## 11. BR-BR-009 — operation settling and observation consistency

**Decision: CLOSED FOR AEP RECONCILIATION**

The browser profile does not define a universal `network idle` or arbitrary sleep rule.

An accepted authoritative-state observation must be taken only after:

1. Core admission rules prevent new Subject side effects once `QUIESCING` begins;
2. browser mutations accepted before that boundary have reached a profile-relevant terminal outcome or the implementation declares settlement failure;
3. selected browser-storage mutation APIs/transactions relevant to the authoritative state no longer have unresolved accepted writes;
4. the evaluator can project the complete selected authoritative state without mixing known pre/post mutation fragments.

For base v0.1, settlement concerns only the selected cookie + `localStorage` state claim. The profile does not wait for unrelated animation, rendering, network quietness, timers, or worker inactivity unless another governed verification surface requires them.

If trustworthy settlement cannot be established within the bound policy, no accepted final state projection is produced; the condition follows existing infrastructure/Validity semantics rather than becoming Agent Task Verdict failure.

## 12. BR-BR-010 — capability decomposition and real-browser TCK matrix

**Decision: CLOSED FOR AEP RECONCILIATION**

The base profile should expose one cohesive capability rather than many `supports_*` flags.

Candidate identity for downstream review:

```text
capabilityId: browser.session-state
profile: avp-browser-state-v0.1
revision: "0.1"
```

The exact identifier remains subject to AEP reconciliation and later normative review.

The base capability means the implementation can provide the complete mandatory v0.1 semantics: isolated browser-session resource ownership, canonical selected cookie + `localStorage` projection, reset, snapshot, `STATE_EQUIVALENT` restore verification, identity binding, Subject/Evaluator separation, settling, and fail-closed negative behavior.

Future separately governed capabilities may cover, for example:

- IndexedDB state;
- partitioned-cookie/storage-partition state;
- virtual-authenticator/WebAuthn state;
- Service Worker / Cache Storage state;
- browsing topology/session restore;
- visual/accessibility evidence contracts.

### Minimum portability evidence

Portable TCK cases must be language-neutral and backend-name-neutral.

Mandatory Browser conformance must execute a real browser engine through the implementation under test; metadata declarations or mocks are not sufficient for mandatory behavioral cases.

The reference implementation acceptance gate should exercise the same portable cases across at least two materially independent browser-engine families before AVP treats the semantics as portability evidence.

A three-engine Playwright matrix is desirable reference evidence when practical, but Chromium/Firefox/WebKit product names are **not** protocol identity and the portable TCK must not branch expected semantics by engine.

A single Chromium-only implementation can be useful development evidence, but it is insufficient by itself to justify a claim that unresolved browser semantics are implementation-independent.

Negative controls should prove at minimum that a metadata-identical implementation cannot pass when it:

- omits selected `localStorage` state;
- flattens cross-origin state;
- restores command-success without re-projection;
- falsely reports `EXACT`;
- exposes evaluator-private credential values;
- permits new Subject mutation after the settlement boundary;
- self-certifies support without real-browser execution.

## 13. Canonical-state design direction

The next AEP reconciliation should specify semantics sufficient for later schema work without prematurely fixing implementation-language APIs.

A likely logical structure is:

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

This is a design direction, not a normative schema.

The representation must avoid cycles between immutable Manifest identity and baseline StateImage identity, following the same content-addressing discipline used elsewhere in AVP.

## 14. Reset semantics

Base reset establishes the immutable bound baseline state and then independently reprojects the authoritative surface.

Implementation strategy may dispose/recreate an isolated browser session and reseed state, clear and repopulate state safely, or use another mechanism. The protocol tests the observable result.

Successful reset means canonical post-reset state equals the baseline state under the same Manifest/profile identity.

Reset cannot silently downgrade an unsupported selected state item. Incompatibility fails closed before claiming success.

## 15. Subject capability boundary

Resource Capability support never grants arbitrary browser automation authority to the Subject.

The base Browser Resource profile does not define a universal page/locator/click/script API.

Privileged operations remain Evaluator/Control unless separately authorized:

- browser/session provisioning;
- baseline seeding;
- reset;
- snapshot;
- restore;
- hidden evaluator instrumentation;
- credential injection;
- diagnostic/evidence capture beyond Subject authorization.

Subject browser actions continue to derive from separately materialized Subject capabilities/contracts.

## 16. Relationship to Network and Time

No browser capability implies deterministic networking or time control.

Browser proxy/offline/interception options are backend mechanisms unless a Network Resource owns the corresponding portable claim.

Browser clock overrides do not imply host/database/remote-service time virtualization.

The Browser profile may identity-bind browser-local configuration relied upon by the Scenario without absorbing future Network/Time resource semantics.

## 17. Security conclusion

The narrowed v0.1 state boundary improves security reviewability because the protocol does not require broad export of browser profiles, private keys, cache contents, or live execution state.

The profile must preserve:

- same-origin boundaries;
- Subject/Evaluator/Control authority separation;
- evaluator-private state confidentiality;
- Artifact access control separate from digest identity;
- synthetic public conformance fixtures;
- fail-closed behavior for stale/foreign resource or snapshot references;
- no secret material in Subject-visible diagnostics unless explicitly authorized.

## 18. Compatibility and non-goals

The profile is additive. Existing Environment/Fabric implementations need not claim Browser v0.1.

Base v0.1 does not standardize:

- Playwright, Selenium, WebDriver, CDP, BiDi, or another automation API;
- page/locator/action APIs;
- browser-process checkpointing;
- persistent browser profile directory format;
- session/tab/history restoration;
- IndexedDB serialization;
- Service Worker/cache checkpointing;
- WebAuthn/passkey secret export;
- visual determinism;
- network determinism;
- time determinism;
- extension/plugin framework for browser backends;
- Chromium/Firefox/WebKit product names as portable capability identity.

## 19. Evidence basis

The decisions above are intentionally standards-first.

Relevant external evidence includes:

- WHATWG HTML and Storage standards for origin-scoped Web Storage and distinct storage endpoints;
- W3C IndexedDB for storage-key/database/transaction semantics that exceed a simple JSON-map model;
- W3C Service Workers for independent registration/lifecycle/cache-mediated behavior;
- W3C WebDriver BiDi for implementation-neutral user-context, browsing-context, cookie/storage-partition, navigation, and browser-control concepts;
- Playwright documentation as reference-implementation evidence showing that captured state and browser features are capability-dependent and not one universal browser checkpoint.

None of these external standards replaces AVP's Environment ownership, SnapshotRef, restore fidelity, Evidence, Security, Scenario binding, Resource Capability, or conformance semantics.

## 20. Readiness result

BR-BR-001 through BR-BR-010 now have explicit portability decisions suitable for incorporation into AEP-0011.

However, AEP-0011 itself still contains the original unresolved Draft wording. Therefore this audit does **not** declare the AEP Proposed-ready yet.

Next required work unit:

1. reconcile AEP-0011 with this audit;
2. remove or supersede the unresolved Draft alternatives;
3. make the selected state/capability/fidelity/identity/security/TCK semantics internally consistent;
4. record each BR-BR-001..010 blocker as closed in the AEP text;
5. perform a fresh Draft → Proposed readiness audit against the reconciled exact head.

Only after that review may a separate lifecycle decision advance AEP-0011 to `Proposed`.

This audit does not authorize:

- AEP-0011 Draft → Proposed transition;
- browser normative spec/schema/TCK registration;
- backend-neutral browser harness implementation;
- Playwright/Selenium/WebDriver backend implementation;
- repository merge;
- release/tag/publication/signing/attestation.
