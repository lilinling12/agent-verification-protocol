# AEP-0011 — Browser Resource Profile v0.1

- Status: Draft
- Authors: AVP maintainers and contributors
- Created: 2026-08-27
- Parent: AEP-0009 — Environment Fabric Composition and Capability Contract (`Accepted`)
- Target AVP version: Unselected future protocol version
- Alpha phase: Alpha 3 — Environment Fabric / Browser Resource

## Summary

AEP-0011 starts the portable design for the browser resource domain required by
AVP Alpha 3 Environment Fabric.

The core design constraint is inherited from AEP-0009:

> AVP must define browser-resource semantics before a Playwright adapter is
> treated as an official Alpha 3 implementation, and Playwright behavior must
> never become protocol authority by implementation precedent.

The base Environment Fabric contract already recognizes `browser` as a coarse
Resource Kind. That classification is not a Browser Resource Profile. It does not
define an isolation unit, authoritative browser-state surface, snapshot/restore
meaning, browser execution identity, cross-origin storage semantics, evaluator
projection model, or conformance-bearing browser capability.

This Draft therefore does **not** implement Playwright and does not yet create a
normative specification, schema, capability registration, or TCK profile. Its
purpose is to establish the problem boundary, standards alignment, candidate
scope, security constraints, and the design blockers that must be resolved before
AEP-0011 can advance to `Proposed`.

A working capability/profile identity may be discussed during design, but no
identifier in this Draft is an accepted protocol claim until the AEP lifecycle
and downstream authority chain approve it.

## Problem

A browser is not one serializable state object and an isolated browser automation
context is not automatically a portable AVP snapshot primitive.

Real browser execution combines multiple independently specified and differently
scoped surfaces, including:

- HTTP cookies and partitioned cookie state;
- origin/storage-key scoped local storage;
- top-level-session scoped session storage;
- IndexedDB databases and transactions;
- Cache Storage and other storage buckets;
- service-worker registrations, lifecycle state, and controlled clients;
- browsing-context/page/tab/popup topology;
- navigation and history state;
- DOM and JavaScript heap state;
- workers, timers, pending tasks, dialogs, permissions, and device/emulation
  settings;
- virtual WebAuthn credentials or other credential material when enabled;
- downloads and uploaded-file effects;
- browser engine/build, platform, headless/headful mode, rendering inputs, fonts,
  locale, timezone, viewport, and other execution-relevant configuration;
- network, DNS, TLS, external-service, and wall-clock dependencies that may be
  controlled by other Environment Resource profiles or may remain uncontrolled.

Different automation mechanisms expose different subsets of these surfaces.
Treating one implementation's `storageState` object, profile directory, DevTools
session, or browser-process checkpoint as "the AVP browser state" would create
backend-first semantics and would make cross-implementation conformance
unreviewable.

The Browser Resource Profile must instead specify exactly what portable claim is
made, which surfaces are authoritative for that claim, which surfaces are only
Evidence, which surfaces are explicitly out of scope, and how omitted surfaces
limit restore/replay fidelity.

## Existing AVP authority reused

AEP-0011 specializes existing contracts and must not create competing concepts.

### Environment v0.1

Reused unchanged:

- authoritative Environment ownership and ScenarioInstance binding;
- actor-scoped Subject observations;
- evaluator-authoritative projections and projection digests;
- reset target honesty;
- Environment-owned SnapshotRef identity and stale/foreign fail-closed behavior;
- restore fidelity vocabulary `EXACT | STATE_EQUIVALENT | NON_EQUIVALENT`;
- semantic diff binding where a selected profile defines meaningful diff
  semantics;
- logical-time and fault semantics without claiming control over clocks or
  networks that remain outside Environment authority;
- released-handle failure.

### Environment Fabric

Reused unchanged:

- `resourceKind: browser` as coarse resource classification;
- Resource Capability declaration and semantic-revision binding;
- REQUIRED/OPTIONAL participation from the materialized execution contract;
- Resource Capability versus Subject Capability authorization separation;
- resource identity and profile-required `identityArtifacts`;
- per-resource/composite operation-result honesty;
- aggregate restore-fidelity non-inflation;
- no implicit cross-resource atomicity;
- Security/Evidence composition;
- execution-sensitive capability conformance;
- retry-safe cleanup.

The base Fabric capability model is necessary but insufficient: no currently
registered Fabric requirement defines browser-domain state or behavior.

### Scenario and Core

Reused unchanged:

- unresolved required execution inputs fail before Episode execution;
- materialized execution semantics remain immutable for the Episode;
- Subject capability exposure derives from the materialized actor projection;
- Core lifecycle remains the only Episode lifecycle;
- `QUIESCING` remains the side-effect acceptance boundary;
- lifecycle, Validity, infrastructure health, and Task Verdict remain separate.

### Security and Evidence

Reused unchanged:

- Subject, Evaluator, and privileged Control authority remain separated;
- evaluator/control credentials never enter Subject execution context;
- evaluator-private material is protected from Subject visibility;
- `SecurityAssurance` remains multi-dimensional and must not be inflated because
  a browser runs in an incognito/private context, container, process sandbox, or
  other named technology;
- exact retained bytes use AVP Artifact identity;
- locators, file paths, browser-context IDs, DevTools IDs, and automation handles
  are not substitutes for Artifact content identity;
- Evidence classification governs visibility/handling without changing content
  identity.

## Why the base Fabric contract is not enough

The base Fabric normative candidate deliberately defines only composition-level
semantics. Its closed `browser` Resource Kind means "this resource belongs to the
browser interoperability domain". It does not mean any of the following:

- the resource has an isolated session boundary;
- cookies, local storage, IndexedDB, caches, or service workers can be captured;
- a browser snapshot can be restored;
- a page or DOM is authoritative state;
- a browser build or execution configuration is identity-bound;
- screenshots or traces are state rather than Evidence;
- navigation, clicking, locator APIs, or JavaScript evaluation are Subject
  capabilities;
- a Playwright `BrowserContext` or WebDriver BiDi user context is the protocol
  object.

A browser adapter that claimed portable behavior from `resourceKind: browser`
alone would therefore violate AEP-0009 capability honesty and backend-first
implementation rules.

## Standards and interoperability analysis

The Browser Resource Profile should reuse web-platform and browser-automation
standards where they own the underlying concepts. AVP should specify only the
verification-facing gap: state/evidence identity, Environment ownership,
reset/snapshot/restore honesty, capability binding, and conformance semantics.

### HTML browsing and origin model

The WHATWG HTML Standard defines browsing-context/navigation concepts and the
origin security model. Origin boundaries are fundamental to browser storage and
script authority. AVP must not replace same-origin/site rules with an
implementation-specific URL grouping model.

For Web Storage, the HTML Standard distinguishes `localStorage` and
`sessionStorage`. Local storage is associated with an origin/storage area, while
session storage is tied to a browsing session/top-level traversable relationship.
Those scoping differences matter directly to any AVP snapshot/restore claim.

A portable browser profile must therefore avoid a flat map such as:

```text
storage[key] = value
```

that loses origin/storage-key and session/topology boundaries.

### IndexedDB

Indexed Database API defines databases under storage keys, object stores, indexes,
key semantics, transactional behavior, upgrade/version behavior, and structured
clone value semantics.

A portable AVP claim cannot treat an IndexedDB database as merely a JSON object
without defining how database names, versions, object stores, indexes, keys,
values, key generators, and ordering are represented. It also cannot assume that
an automation library's export format is a standards-level serialization format.

Whether IndexedDB is mandatory in Browser Profile v0.1, optional under a separate
capability, or excluded from the first portable state surface remains a Draft
question. Whatever decision is made must be explicit and TCK-testable.

### Service Workers and Cache Storage

Service Workers have an independent lifecycle and can mediate network fetches,
control browsing contexts, and participate in offline/cache behavior. Cache
Storage is not interchangeable with cookies, local storage, or IndexedDB.

A browser profile must not report restored state as equivalent when the selected
portable state claim requires a service worker/cache effect that was silently
lost or recreated differently.

Conversely, v0.1 must not make service-worker/cache checkpointing mandatory merely
because one browser or automation backend can expose part of it. The profile may
need an explicit exclusion or separately claimable capability.

### WebDriver BiDi

The W3C WebDriver BiDi work provides a useful implementation-neutral automation
reference. It defines, among other concepts:

- browser user contexts;
- browsing contexts and their lifecycle/events;
- navigation and download events;
- screenshot capture;
- network events/interception;
- script realms;
- cookie storage commands and storage partition keys;
- browser/emulation controls.

These concepts are evidence that browser control can be described independently
of Playwright. They do not by themselves solve AVP's verification problem:
WebDriver BiDi does not define an AVP Environment Resource identity, baseline
state Artifact, reset target, snapshot/restore fidelity, Scenario binding,
Evaluator/Subject authority model, or ConformanceReport semantics.

AEP-0011 should align terminology with standards where practical rather than
inventing Playwright-shaped public names, while keeping AVP-specific lifecycle
and evidence semantics in AVP.

### Playwright as reference implementation evidence

Playwright `BrowserContext` is a strong candidate implementation boundary because
it provides isolated non-persistent browser sessions and context-scoped browser
operations.

Current Playwright documentation also demonstrates why its API must not be copied
into the protocol:

- `storageState()` documents cookies and local storage as captured state;
- IndexedDB capture is an explicit option rather than an inseparable universal
  property;
- virtual WebAuthn credential capture is an explicit option and can include
  credential private-key material;
- service-worker behavior has engine/backend limitations and interacts with
  network routing;
- pages, JavaScript heap, service-worker lifecycle, Cache Storage, downloads, and
  every other browser effect are not thereby proven to be part of one complete
  portable snapshot.

The AVP profile must define the claim first. A Playwright adapter may then prove
that a selected Playwright/engine configuration satisfies it.

## Candidate portable resource boundary

The preferred design direction is one independently owned **isolated browser
session resource**, not one global browser process and not one page object.

The session resource should be capable of containing one or more browsing
contexts/pages while preserving an isolation boundary from sibling browser
resources.

This is a design direction, not yet accepted semantics. The forthcoming
portability audit must determine whether "browser session" can be specified
without depending on the lifecycle details of Playwright `BrowserContext`,
WebDriver BiDi user contexts, or one browser engine.

### Browser process versus resource identity

A shared browser process may host multiple independently isolated resources. The
browser process handle is therefore not necessarily the Environment Resource.

Conversely, a persistent browser profile directory may contain more state than a
single portable resource is allowed to claim. A filesystem directory or process
PID must not become AVP resource identity.

### Page topology

Pages/tabs/popups are dynamic children of the browser-session boundary. The Draft
does not yet decide whether page topology participates in authoritative snapshot
state, is evaluator-observable runtime state only, or is excluded from v0.1
restore semantics.

This decision materially affects `sessionStorage`, navigation history, open
popups, pending dialogs, and live JavaScript state and therefore cannot be left to
the adapter.

## State, Evidence, and execution identity must be separate

AEP-0011 must not create one ambiguous "browser state" digest that conflates
three different verification concerns.

### 1. Authoritative restorable state

This is the surface for which the profile makes reset/snapshot/restore and state
identity claims. Candidate surfaces include cookies, selected origin-scoped Web
Storage, and selected IndexedDB state, subject to the unresolved blockers below.

Only surfaces explicitly selected by the eventual profile may contribute to a
`STATE_EQUIVALENT` claim.

### 2. Evidence/observation surfaces

Potential browser Evidence includes:

- current URL/navigation information;
- selected DOM projection;
- accessibility-oriented projection where a stable contract can be defined;
- screenshot Artifact;
- console/page-error events;
- browser/network event traces;
- download Artifacts;
- execution diagnostics.

Evidence capture does not make these surfaces automatically restorable state.
For example, a screenshot can prove what was rendered without proving that the
browser can restore the underlying DOM/JavaScript heap exactly.

### 3. Execution-relevant immutable identity

Browser behavior can differ even with identical logical storage state. The
materialized execution may rely on identity/configuration inputs such as:

- browser engine family and exact build/revision;
- browser executable/package identity;
- operating-system/platform identity where behavior depends on it;
- headless/headful mode;
- locale, timezone, color scheme, reduced-motion, viewport, device scale factor,
  touch/mobile settings, JavaScript enablement, permissions, geolocation, or
  other emulation configuration when relied upon by the Scenario;
- service-worker policy;
- proxy/network configuration when not separately owned by a Network Resource;
- trusted certificates or HTTPS policy;
- extension/preload-script/configuration identity;
- font/rendering inputs when visual verification relies upon them.

The profile must determine which of these belong in a browser-specific immutable
identity resource versus existing Scenario/Fabric resolved execution-input
bindings. Backend labels such as `chromium` or `playwright` alone are not
sufficient immutable identity.

## Snapshot and restore honesty

The Draft starts from a conservative rule: logical browser storage restoration is
not automatically `EXACT` browser restoration.

Recreating an isolated browser session and reseeding selected storage may restore
the selected authoritative logical state while failing to reproduce:

- live JS heap and tasks;
- exact page/tab topology;
- session storage;
- navigation history;
- active workers/service-worker lifecycle;
- cache state;
- pending downloads/dialogs;
- in-flight network operations;
- rendering/runtime timing state.

If v0.1 defines a logical state surface that intentionally excludes such
components, successful restoration of the complete selected surface is a
candidate for `STATE_EQUIVALENT`, not an excuse to claim process-level `EXACT`.

Whether any conforming v0.1 implementation can legitimately report `EXACT` must
be resolved before Proposed. If the term would be misleading for the entire
portable profile, the normative profile may prohibit `EXACT` for v0.1 just as the
Relational State profile did for its logical restore semantics.

## Reset semantics

Reset must establish a profile-defined target and then independently observe the
post-reset state. Closing a browser context or calling an automation-library
clear-storage method is not sufficient by command success alone.

A likely reference strategy is to dispose the isolated session, create a new
profile-compatible session, seed the bound baseline state, and independently
re-project the selected authoritative state. That is implementation strategy, not
protocol semantics.

The profile must define behavior for omitted/unrestorable required state rather
than allowing an adapter to silently downgrade it.

## Subject capability boundary

Browser Resource Capability support is **not** authority for the Subject to call
arbitrary browser automation methods.

AEP-0011 must preserve the existing Resource Capability / Subject Capability
separation:

- the Resource Capability describes Environment behavior the browser resource can
  satisfy;
- the materialized Scenario/Security actor projection determines which browser
  actions/observations the Subject may invoke;
- privileged reset/snapshot/restore, credential seeding, browser launch/control,
  diagnostic capture, and hidden test instrumentation remain Evaluator/Control
  operations unless separately granted through a governed Subject contract.

The first Browser Resource Profile should not standardize a universal Playwright-
style page/locator API merely to make the reference adapter convenient.

## Relationship to Network and Time profiles

A browser resource observes network and time, but Browser Profile v0.1 must not
silently absorb the future Network-Control or Time-Control profiles.

For example:

- repeating a navigation is not proof of deterministic network behavior;
- setting browser offline mode is not automatically equivalent to a portable
  network fault profile;
- overriding a page clock does not prove host/kernel/database/external-service
  time virtualization;
- request interception semantics may differ when service workers are active.

Browser-specific configuration required for a Scenario can be identity-bound,
but broad fault/time capability claims belong to the corresponding portable
resource profiles unless a later cross-resource capability explicitly coordinates
them.

## Security analysis

A browser resource creates a large attack and data-exposure surface. The profile
must preserve at least the following constraints.

### Authentication and storage material

Cookies, local storage, IndexedDB, and WebAuthn credential state may contain
bearer tokens, long-lived secrets, personally identifying information, or private
keys.

- Subject-visible state projections must not expose evaluator-private credential
  material.
- Snapshot Artifacts containing credential material require appropriate Evidence
  classification and access control.
- A digest does not make sensitive snapshot bytes safe to publish.
- Virtual credential export/import must not become mandatory base behavior solely
  because one automation backend can perform it.

### Origin and storage partition isolation

The profile must preserve web-platform origin/storage-key partitioning and must
not flatten cross-origin state into a Subject-readable global map.

Evaluator privileges used to capture/restore state must not be confused with the
Subject's same-origin authority.

### Privileged automation channel

Remote-debugging, automation, browser-launch, extension, preload-script, and
context-management handles can provide powers far beyond Scenario-granted browser
actions. These handles and credentials belong to Evaluator/Control authority and
must not enter the Subject execution context.

### Navigation and network exposure

A browser can reach local, private, metadata, or privileged network endpoints if
network policy permits it. Browser Resource conformance must not imply verified
network isolation. Any egress restrictions must be represented by actual
SecurityAssurance evidence and/or a governed Network Resource capability.

### Downloads and file interaction

Downloads are untrusted output and may need content-addressed Artifact capture,
size/resource limits, quarantine, and path isolation. Uploaded file inputs require
immutable input identity when the Scenario relies on exact bytes.

A browser-supplied path must never be treated as Artifact identity.

### Rendering and screenshots

Screenshots, traces, console output, DOM projections, and network events can leak
secrets. Evidence visibility and redaction policy must be explicit; redaction must
not mutate the identity of retained original evidence while pretending the bytes
are unchanged.

### Sandbox/engine labels

`Chromium sandbox`, `incognito`, `BrowserContext`, `headless`, containerization,
or another technology label must not automatically raise any
`SecurityAssurance` dimension to `verified`.

## Backward compatibility

A Browser Resource Profile is additive under AEP-0009.

Existing AVP implementations that conform to Environment v0.1 or the base
`avp-environment-fabric-v0.1` profile are not required to claim browser-domain
capabilities.

Existing Fabric manifests may contain `resourceKind: browser`, but that Resource
Kind alone must not be interpreted as a claim of the future AEP-0011 capability.
A conforming implementation may claim the browser profile only after the
capability/profile identity, semantics, schemas where required, and TCK obligations
are governed and supported.

No accepted Alpha 2 semantics are changed by this Draft.

## Conformance strategy direction

Browser-profile conformance must be language-neutral and execution-sensitive.

The eventual TCK must operate through an implementation adapter against a real
browser runtime. It must be capable of rejecting an adapter that advertises the
same capability/profile metadata as a conforming adapter but does not establish
the required runtime behavior.

Candidate mandatory conformance families include:

1. isolated-resource ownership and sibling-session isolation;
2. execution-identity binding and incompatible-identity fail-closed behavior;
3. baseline-state materialization and independent post-provision projection;
4. origin/storage-key partition preservation;
5. exact canonical state identity for every surface selected as authoritative by
   the profile;
6. snapshot ownership/integrity and foreign/stale rejection;
7. mutation -> snapshot/restore -> independent reprojection;
8. reset -> independent reprojection to the bound baseline;
9. restore-fidelity non-inflation;
10. Resource Capability versus Subject Capability separation;
11. credential/evaluator-private non-disclosure;
12. stale/released resource failure and retry-safe cleanup;
13. negative implementation controls that preserve metadata while breaking real
    browser behavior;
14. explicitly unsupported state surfaces failing closed when the materialized
    execution contract requires them.

A real-browser CI matrix should eventually cover more than one browser engine
family where the selected portable requirements claim cross-engine semantics.
Passing Chromium alone would be Playwright/Chromium implementation evidence, not
proof that a supposedly engine-neutral semantic boundary is portable.

The TCK must use controlled local test origins/resources for mandatory behavior so
external Internet availability, third-party service drift, and unrelated DNS/TLS
conditions do not become accidental conformance dependencies.

## Reference implementation direction

Only after the portable semantics, schema boundary, and executable TCK are
reviewable may a Playwright adapter be introduced.

A Playwright implementation should be an optional backend dependency rather than
an unconditional dependency of the base AVP package unless packaging governance
later decides otherwise.

The adapter may use Playwright `BrowserContext` and browser-specific APIs behind
implementation-private seams, but portable code and language-neutral TCK vectors
must not branch on `playwright`, `chromium`, `firefox`, or `webkit` product names.

An implementation-specific real-browser fixture/control seam may be needed for
TCK setup, mutations, concurrency/lifecycle forcing, and negative controls. That
seam must remain privileged and must not become a Subject API or portable protocol
resource merely because the reference tests use it.

## Draft design blockers before Proposed

This Draft is intentionally **not Proposed-ready**. The next portability audit
must resolve at least the following blockers with implementation-independent
semantics and an executable conformance strategy.

### BR-BR-001 — authoritative v0.1 state surface

Define the exact closed set of browser state surfaces covered by the base profile
and distinguish mandatory, optional-capability, Evidence-only, and excluded
surfaces. Cookies/local storage/IndexedDB/session storage/service workers/cache
state cannot remain implicit.

### BR-BR-002 — origin and storage-partition identity

Define the portable identity model for origins/storage keys/partitioned cookies
and cross-origin state so state equality does not depend on one browser's internal
profile layout or automation export format.

### BR-BR-003 — page topology and session-scoped state

Decide whether pages/tabs/popups, navigation history, and session storage are part
of authoritative restorable state, runtime observation, or explicit v0.1
exclusions. The decision must remain valid across independent browser engines.

### BR-BR-004 — snapshot/restore fidelity

Define the exact state/evidence required before `STATE_EQUIVALENT` may be reported
and determine whether `EXACT` is forbidden in Browser Profile v0.1. Command
success or context recreation alone cannot establish restore fidelity.

### BR-BR-005 — browser execution identity

Define which browser build, platform, mode, emulation/configuration, preload/
extension, and rendering inputs are materially execution-relevant and how they
bind through existing Scenario/Fabric immutable identity mechanisms without
turning product labels into protocol identity.

### BR-BR-006 — service-worker/cache semantics

Choose a portable v0.1 policy for service workers and Cache Storage: mandatory
state, optional capability, blocked/disabled profile mode, or explicit exclusion.
The choice must address cross-engine support and network-observation interactions.

### BR-BR-007 — credential-bearing browser state

Define how authentication material and optional virtual WebAuthn/passkey state
interact with state identity, snapshot Artifacts, Evidence classification,
Evaluator confidentiality, and restore semantics without making secret export a
base conformance requirement.

### BR-BR-008 — canonical projection and evidence boundary

Define which browser projections, if any, require portable canonical bytes and
digests. DOM/accessibility/screenshot/trace outputs must not be conflated, and
rendering artifacts must not be mistaken for authoritative restorable state.

### BR-BR-009 — operation settling and observation consistency

Define when a browser state observation is accepted relative to navigation,
async tasks, storage transactions, workers, and pre-QUIESCING accepted work. The
profile must reject torn/partially settled state where it claims one logical
observation without inventing a universal "network idle means deterministic"
rule.

### BR-BR-010 — capability decomposition and real-browser TCK matrix

Determine whether v0.1 should expose one cohesive browser-session capability or a
small set of separately claimable capability revisions, and define the minimum
real-browser execution matrix needed to demonstrate portable semantics without
making a specific engine mandatory protocol identity.

Until these blockers are review-closed, AEP-0011 must remain Draft and no
Playwright adapter should be merged as the official Alpha 3 Browser Resource
implementation.

## Alternatives considered at Draft stage

### Alternative A — implement Playwright first and generalize later

Rejected by AEP-0009.

This would make Playwright's context/storage/export limitations de facto protocol
semantics and recreate the backend-first architecture Alpha 3 explicitly
prohibits.

### Alternative B — define browser state as Playwright `storageState`

Rejected as a portable contract.

It is a useful implementation mechanism for selected storage surfaces but is not
a complete standards-level serialization of browser execution state and evolves
with Playwright capabilities/options.

### Alternative C — snapshot the whole browser profile directory

Rejected as the base portable identity.

Profile directories contain browser-specific files, caches, internal databases,
locks, version-specific implementation details, and potentially unrelated or
sensitive material. Equal portable state cannot depend on byte-identical profile
directories across engines.

### Alternative D — make a live page the resource

Rejected as the default resource boundary.

A page is too narrow for shared cookies/origin storage and cannot naturally own
popups, workers, or session-wide state. It also encourages automation API objects
to become protocol identity.

### Alternative E — make the whole browser process the resource

Rejected as the default resource boundary.

Multiple isolated verification sessions may share one process, while process
identity and crash behavior are implementation concerns. Process-level ownership
would also make independent-session cleanup and isolation unnecessarily
backend-dependent.

### Alternative F — omit snapshot/restore and standardize browser actions only

Rejected for Alpha 3 Browser Resource scope.

AEP-0009 specifically identifies browser state/isolation as an Environment Fabric
resource problem. A universal Subject browser-action API is a separate
interoperability question and does not solve Environment reset, identity,
state/evidence, or replay honesty.

## Governance boundary

AEP-0011 is **Draft**.

This Draft does not authorize:

- `Draft -> Proposed` transition;
- acceptance of any candidate capability identifier or state surface;
- normative Browser Resource specification or schema adoption;
- registration of an `avp-browser-*` TCK profile as accepted authority;
- Playwright, WebDriver BiDi, Chromium, Firefox, WebKit, or another browser
  adapter as an official Alpha 3 implementation;
- changing AEP-0009 or AEP-0010 lifecycle state;
- selecting an Alpha 3 public release version;
- assigning this work to the currently planned `0.3.1` maintenance release;
- changing `docs/releases/release-development-state.json` from development mode;
- tagging, GitHub Release creation, package-index publication, signing, or
  attestation publication;
- treating any Python/reference implementation behavior as protocol authority.

The next governed work unit after this Draft is a **Browser Resource portability
and Proposed-readiness audit** that resolves or explicitly narrows BR-BR-001
through BR-BR-010 before any Proposed transition.

## References

Primary upstream references for portability analysis:

- AEP-0009 — Environment Fabric Composition and Capability Contract:
  `rfcs/AEP-0009-environment-fabric.md`
- AVP Environment Fabric Contract v0.1:
  `spec/fabric/environment-fabric-contract.md`
- WHATWG HTML Standard — browsing/origin and Web Storage:
  https://html.spec.whatwg.org/
- W3C WebDriver BiDi Editor's Draft:
  https://w3c.github.io/webdriver-bidi/
- W3C Indexed Database API 3.0:
  https://w3c.github.io/IndexedDB/
- W3C Service Workers:
  https://w3c.github.io/ServiceWorker/
- Web Authentication Level 3:
  https://www.w3.org/TR/webauthn-3/
- Playwright BrowserContext documentation:
  https://playwright.dev/docs/api/class-browsercontext
- Playwright Service Workers documentation:
  https://playwright.dev/docs/service-workers

These references constrain mechanism and interoperability analysis. They do not
become AVP normative semantics merely by citation.
