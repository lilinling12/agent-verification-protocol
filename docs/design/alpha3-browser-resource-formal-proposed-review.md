# AEP-0011 Browser Resource Profile — Formal Proposed Protocol Review

Status: **REVIEWED — ACCEPTANCE BLOCKERS OPEN**

Reviewed baseline: `main@ccd05b71635b46218dfa14043320a60376339dc2`

Review date: 2026-08-30

Decision target: `rfcs/AEP-0011-browser-resource-profile.md`

Lifecycle result: **KEEP `Proposed`; NOT READY for `Proposed → Accepted`**

Implementation authorization: **NONE**. This review does not authorize Browser normative Spec, Schema, language-neutral TCK, backend-neutral conformance harness, Playwright/reference runtime, release selection, publication, signing, attestation, repository split, or plugin-framework work.

## 1. Executive decision

AEP-0011 remains directionally sound and should not be redesigned from scratch. The protocol-first architecture, narrow authoritative state, Subject/Evaluator/Control separation, execution-identity separation, independent re-projection, and refusal to let an automation framework define AVP semantics remain correct foundations.

The review nevertheless finds that the current Proposed text is not precise enough for acceptance. The Draft-to-Proposed work closed portability questions at a level adequate for formal review, but several browser-standard and cross-engine semantics still require explicit protocol decisions before the AEP can be Accepted.

The acceptance gate is therefore closed until BPR-001 through BPR-009 below are resolved and an acceptance-oriented re-review finds no remaining semantic blocker.

## 2. Review authority and method

The review preserves the repository authority chain:

`Normative Spec -> Schema -> language-neutral TCK -> conformance harness -> reference runtime`

No Playwright, WebDriver BiDi, browser-specific protocol, reference implementation, CI fixture, or existing runtime behavior gains normative authority by precedent.

Evidence priority for this review is:

1. final or living web standards and standards-track specifications;
2. browser-engine documentation and standards-conformance behavior;
3. cross-browser interoperability/conformance practice;
4. mature automation-library behavior as implementation evidence only;
5. agent/browser-agent security guidance where it informs AVP trust boundaries.

Primary research inputs include RFC 10025, WHATWG HTML/Storage/Web IDL/URL, WebDriver BiDi, Web Platform Tests/Interop practice, Chromium storage partitioning, Firefox State Partitioning, WebKit storage policy, Playwright browser-context/storage APIs, MCP/A2A security direction, and current computer-use/browser-agent safety guidance.

## 3. Design decisions retained

The following Proposed design directions survive formal review:

- one Browser resource represents one independently isolated logical browser-session resource rather than one page, browser process, profile directory, Playwright `BrowserContext`, WebDriver BiDi user context, or vendor handle;
- `resourceKind: browser` remains coarse Fabric classification and does not by itself claim Browser-profile conformance;
- Browser v0.1 remains deliberately narrow rather than expanding toward a product-specific full browser profile snapshot;
- authoritative state remains based on selected unpartitioned HTTP cookies plus a narrowly defined unpartitioned `localStorage` surface;
- partitioned cookies/storage, IndexedDB, Cache Storage, Service Workers, sessionStorage, DOM/JS heap, page topology, history, workers, rendering state, downloads, WebAuthn private credential state, and automation handles remain outside the base state image unless separately governed later;
- cookie identity retains `(name, domain, hostOnly, path)`; `hostOnly` must not be removed merely because mainstream automation APIs do not expose it directly;
- `SameSite=Default` must not be silently normalized to explicit `Lax`;
- successful base restore may claim `STATE_EQUIVALENT`, never `EXACT`;
- restore/reset success requires independent evaluator re-projection of the complete selected authoritative surface;
- no universal `network idle`, arbitrary sleep, Playwright-specific idle state, or vendor event queue becomes protocol semantics;
- Resource Capability support does not grant Subject page automation, navigation, script, click, typing, locator, credential-read, or evaluator-control authority;
- credentials and privileged browser-control handles remain evaluator/control private unless a separate Subject contract explicitly grants an action or observation;
- browser state/evidence/execution identity remain separate concepts;
- no generic `BaseBrowserBackend`, browser plugin framework, or implementation hierarchy is introduced at this stage.

## 4. Required protocol corrections before acceptance

### 4.1 Scope `localStorage` explicitly to the unpartitioned base profile

The current AEP describes selected `localStorage` in terms of tuple origin. That is not sufficient as a general modern-browser storage identity statement.

WHATWG Storage still describes storage keys through origin-oriented machinery but explicitly anticipates evolution, while deployed browsers partition third-party storage using top-level-site and related context. Chromium, Firefox, and WebKit have materially different partitioning and storage-access policies.

Browser v0.1 should therefore define its authoritative surface as selected **unpartitioned `localStorage`** only. Tuple `(scheme, host, port)` identity is valid only inside that bounded base profile.

A scenario that depends on partitioned third-party storage must not be projected into this profile as ordinary tuple-origin state. Such state is either unsupported/fail-closed for v0.1 or belongs to a future separately governed partition-aware capability.

### 4.2 Keep correct cookie identity even when automation APIs are lossy

RFC 10025 preserves the host-only flag as part of cookie storage identity. The AEP's `(name, domain, hostOnly, path)` tuple is therefore correct.

Current WebDriver BiDi cookie representations and mainstream Playwright cookie APIs do not directly expose all of this storage identity. That is an implementation/projection limitation, not a reason to weaken AVP semantics.

A conforming implementation must prove lossless projection/restoration for selected cookies or fail closed for state it cannot faithfully establish. AVP must not infer conformance merely from an automation-library cookie export.

### 4.3 Close the cookie temporal-semantics gap

RFC 10025's stored cookie model includes creation time. Creation time can be observably relevant, including SameSite default compatibility behavior and cookie ordering in request construction.

The current BrowserStateImage direction does not retain creation time, while mainstream portable automation surfaces do not generally expose and restore arbitrary historic creation time. Consequently, two re-projections can be field-equal under the current Proposed image while post-restore HTTP behavior still differs.

Browser v0.1 must explicitly resolve this before `STATE_EQUIVALENT` can be accepted as a protocol claim. The preferred direction is not to add an unportable creation-time field simply to make the image larger. Instead:

- preserve `SameSite=Default` as distinct stored state;
- define the equivalence domain honestly;
- where a selected cookie's temporal semantics cannot be preserved or proven, generic restore must fail closed rather than silently manufacturing an apparently equivalent fresh cookie;
- no implementation may normalize `Default` to `Lax` as a workaround.

### 4.4 Make state selection grammar closed and protocol-owned

Selection is part of semantics, not merely schema syntax.

The v0.1 manifest should use a finite explicit grammar. Recommended direction:

- `localStorage`: exact canonical tuple-origin list, with each selected origin contributing its complete base-profile unpartitioned map;
- cookies: exact canonical stored-domain list, with every selected unpartitioned cookie entry for those exact stored domains participating in the authoritative state.

The base grammar should not contain regexes, globs, suffix matching, vendor query callbacks, Playwright filters, backend-native partition selectors, or runtime code. Dynamic cookie names remain capturable because selection chooses a domain-scoped complete set rather than a hard-coded cookie-name allowlist.

### 4.5 Define `STATE_EQUIVALENT` over an explicit equivalence domain

A successful Browser v0.1 restore should mean:

> under the same immutable BrowserStateManifest/profile revision/resource binding and compatible required execution identity, independent evaluator re-projection yields exactly the same complete selected authoritative state, including required absence and no extra in-scope entries.

It must not imply equality of excluded surfaces such as DOM, page history, browser-internal metadata, caches, workers, rendering, or process continuation.

The protocol must explicitly state any selected cookie class that is not restorable with the required behavioral fidelity and therefore cannot produce successful `STATE_EQUIVALENT` under the base profile.

### 4.6 Replace implicit settling with a positive portable settlement witness

There is no standards-level universal point at which a live browser is globally "settled". Network-idle windows and sleeps are not protocol-grade evidence.

The base profile should require a positive scenario-bound/profile-bound settlement witness or barrier:

1. Core closes admission of new Subject side effects;
2. all accepted pre-boundary mutations relevant to the selected authoritative surface reach a terminal outcome known to the evaluator/control plane;
3. the evaluator establishes that no accepted profile-relevant mutation remains unresolved;
4. only then may authoritative projection be accepted.

If the implementation cannot establish that witness under the bound scenario policy, final authoritative projection fails closed as unsettled. The rule applies only to profile-relevant state and does not pretend that all rendering, animations, workers, timers, or network activity are globally idle.

### 4.7 Resolve Web IDL `DOMString` canonical representation

Web Storage keys and values are Web IDL `DOMString` values. `DOMString` semantics can contain unmatched UTF-16 surrogate code units, while common canonical-JSON approaches may reject such strings.

Before acceptance the AEP must choose one protocol-owned behavior:

- a lossless representation preserving the exact UTF-16 code-unit sequence; or
- an explicit unsupported/fail-closed rule when selected `localStorage` contains values that cannot be represented by the chosen canonical form.

The result must not depend accidentally on JavaScript, Python, Java, JSON library, operating system, or browser-string conversion behavior.

### 4.8 Add residual-state noninterference requirements for excluded surfaces

Excluding a surface from the authoritative image does not make its effect disappear. Service Workers, cache state, IndexedDB, permissions, browser extensions, preload scripts, profile residue, network policy, credential state, and similar surfaces may affect observable execution even though they are not restored by BrowserStateImage.

The accepted profile must therefore require either:

- isolation/configuration proving an excluded surface cannot materially interfere with the scenario's verification claim; or
- explicit immutable execution identity/policy binding for relevant excluded state; or
- fail-closed declaration that the base Browser profile is insufficient for that scenario.

This preserves a narrow base image without making false reproducibility claims.

### 4.9 Require three-engine-family acceptance evidence

Before AEP-0011 is Accepted, the protocol decisions above should be supported by an evidence matrix spanning Chromium, Gecko, and WebKit engine families.

This is an AEP acceptance-evidence requirement, not a universal requirement that every future third-party AVP implementation support all three engines.

The evidence should test semantic claims rather than vendor API equality, including at minimum:

- selected unpartitioned cookie identity/projection behavior;
- host-only/domain cookie differentiation;
- SameSite default handling and any v0.1 restore restriction arising from temporal semantics;
- selected unpartitioned `localStorage` isolation and tuple-origin behavior within the admitted execution context;
- rejection/non-admission of partitioned state into the base profile;
- independent post-restore/reset projection;
- unsettled/fail-closed behavior;
- residual-state isolation assumptions relied upon by the fixture.

## 5. Acceptance blocker ledger

### BPR-001 — Capability/profile naming closure

**Problem:** `browser.session-state` / `avp-browser-state-v0.1` are still working names and are broader/less explicit than the actual narrow state contract.

**Closure criteria:** Formal review selects stable protocol-facing capability/profile identifiers that describe a browser state resource without implying a universal Browser Agent action API or full browser-profile snapshot. The identifiers are recorded in AEP-0011 before Accepted review.

**Recommended direction:** a generic resource capability such as `state.browser` combined with a narrow versioned profile name describing unpartitioned cookie + localStorage semantics. Exact spelling remains a protocol decision, not an implementation constant.

### BPR-002 — Unpartitioned `localStorage` boundary

**Problem:** tuple-origin wording is insufficiently qualified in a storage-partitioned web platform.

**Closure criteria:** AEP-0011 explicitly defines the v0.1 `localStorage` surface as unpartitioned base-profile state, states the admitted execution-context assumptions, and fails closed for selected partitioned storage rather than aliasing it to tuple origin.

### BPR-003 — Lossless cookie identity/projection proof

**Problem:** required cookie identity includes `hostOnly`, but common automation surfaces are lossy.

**Closure criteria:** AEP-0011 specifies that correct cookie identity remains normative and defines evidence requirements/fail-closed behavior for backends that cannot prove the selected identity and state. Acceptance evidence demonstrates the decision across Chromium, Gecko, and WebKit families.

### BPR-004 — Cookie temporal semantics and restore fidelity

**Problem:** creation-time-dependent behavior can make field-equal restored cookies behaviorally different.

**Closure criteria:** The AEP defines which cookie states are admitted to successful `STATE_EQUIVALENT` restore and how unpreservable temporal semantics fail closed. `SameSite=Default` is never normalized to `Lax` merely to obtain restore success.

### BPR-005 — Closed state-selection grammar and equivalence domain

**Problem:** current Proposed text requires a closed grammar but does not choose it.

**Closure criteria:** AEP-0011 fixes a finite vendor-neutral selection grammar, exact scope semantics, canonical identity inputs, complete-set rules, missing/extra behavior, and the precise Browser v0.1 equivalence domain.

### BPR-006 — Portable settlement witness

**Problem:** the current settlement prose does not yet define an independently testable positive witness/barrier.

**Closure criteria:** AEP-0011 defines the portable requirement for proving all accepted profile-relevant pre-boundary mutations terminal or produces fail-closed unsettled outcome. It explicitly rejects sleep/network-idle/vendor queues as sufficient protocol evidence.

### BPR-007 — Lossless `DOMString` canonical semantics

**Problem:** Web Storage strings and canonical JSON may have incompatible character-domain assumptions.

**Closure criteria:** AEP-0011 chooses a language-neutral exact representation or a precise fail-closed unsupported rule and states ordering/equality over that representation.

### BPR-008 — Excluded-state residual noninterference

**Problem:** excluded browser surfaces can still change verification behavior.

**Closure criteria:** AEP-0011 defines the required isolation, execution-identity binding, or insufficiency/fail-closed rule for material excluded surfaces; a base-state restore must not be described as reproducing dependencies that the profile deliberately excludes.

### BPR-009 — Chromium/Gecko/WebKit acceptance evidence matrix

**Problem:** Proposed portability reasoning is not yet strong enough for acceptance of a browser-state standard claim.

**Closure criteria:** reviewable evidence demonstrates the accepted semantic decisions against Chromium, Gecko, and WebKit engine families without making one vendor API normative. Any engine-specific limitation is recorded as evidence about implementability, not used to redefine the protocol opportunistically.

## 6. Recommended final protocol direction

The accepted direction should remain narrow and capability-oriented:

```text
Browser logical resource
  -> immutable BrowserStateManifest
       - capability/profile/revision
       - exact state-selection grammar
       - canonical-representation revision
       - required execution-identity bindings/policies
  -> BrowserStateImage
       - manifest binding
       - selected unpartitioned cookies
       - selected unpartitioned localStorage maps
```

The base image should not expand to match Playwright `storageState`, browser profile directories, CDP exports, or future product-specific browser-agent memory formats.

Future capabilities may independently govern partition-aware storage, IndexedDB, WebAuthn, Service Worker/cache state, browser actions, page observations, visual evidence, or richer computer-use semantics. They should compose through Environment Fabric rather than being smuggled into v0.1 as optional vendor fields.

## 7. Browser Agent / Computer Use future-compatibility judgment

The rapid evolution of Browser Agents strengthens, rather than weakens, the current responsibility split.

AVP should standardize verification-relevant state and evidence contracts while keeping Subject action authority separately governed. A future agent may operate through DOM APIs, accessibility trees, screenshots, WebDriver BiDi, CDP, native OS input, MCP tools, A2A agents, or mechanisms not yet standardized. BrowserStateImage should not need to change merely because action technology changes.

This separation also supports least privilege. Credential-bearing browser state can remain evaluator/control-owned while the Subject receives only the specific browser actions/observations allowed by the materialized scenario security projection.

## 8. Governance outcome

Formal Proposed Review outcome:

```text
AEP-0011 lifecycle: Proposed
Formal review: REVIEWED — ACCEPTANCE BLOCKERS OPEN
Proposed -> Accepted: NOT READY / NOT AUTHORIZED
Browser normative Spec: NOT AUTHORIZED
Browser Schema: NOT AUTHORIZED
Browser TCK: NOT AUTHORIZED
Browser conformance harness: NOT AUTHORIZED
Playwright/reference runtime: NOT AUTHORIZED
Release/tag/PyPI: NOT AUTHORIZED
Repo split/plugin framework: NOT AUTHORIZED
```

The next protocol work after adoption of this review is blocker-resolution design in AEP-0011, followed by an acceptance-oriented re-review. `Proposed -> Accepted` remains a separate explicit protocol-maintainer decision after all blockers are demonstrably closed.

## 9. Non-authoritative implementation note

This review intentionally does not prescribe how a Playwright, WebDriver BiDi, CDP, WebKit automation, or other backend must be structured. Implementation experiments may later provide evidence, but they cannot precede or redefine the accepted protocol semantics.
