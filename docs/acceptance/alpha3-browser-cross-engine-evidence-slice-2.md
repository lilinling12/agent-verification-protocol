# Alpha 3 Browser Cross-Engine Evidence — Slice 2

Status: **EXECUTED — PARTIAL / DIVERGENT ACCEPTANCE EVIDENCE**

Parent evidence PR: #109  
Protocol parent PR: #108  
Evidence branch source head: `2beae94df4d37514821b96487c6ebc2bf4c00516`  
GitHub pull-request merge head executed by Actions: `a19132e8ce6f081ccd9c834369429a31869cb9ea`

## Scope

This record captures the second executable Chromium/Gecko/WebKit evidence slice for AEP-0011.

Executed cases:

- BAE-002 — `SameSite=Default` versus explicit `Lax` projection evidence;
- BAE-003 — temporal restore-eligibility diagnostics;
- BAE-006 — partitioned third-party `localStorage` non-admission diagnostics.

The run succeeded as evidence infrastructure, but several case outcomes are intentionally `partial`. A green workflow does not convert an inconclusive or lossy observation into protocol closure.

## Exact execution identity

Workflow:

```text
Browser Cookie Partition Evidence #1
run: 33312526951
job: 99260038616
conclusion: success
```

Transport:

```text
playwright-python 1.62.0
```

Installed browser builds:

```text
Chromium family
  Chrome for Testing 151.0.7922.34
  Playwright chromium build v1234

Gecko family
  Firefox 153.0
  Playwright firefox build v1538

WebKit family
  WebKit 26.5
  Playwright webkit build v2336
```

Execution identity retained by the artifact:

```text
platform:
  Linux-6.17.0-1022-azure-x86_64-with-glibc2.39
Python:
  3.13.15
headless:
  true
controlled loopback hosts:
  a.test
  b.test
  c.test
non-default browser flags declared by fixture:
  none
```

The browser products are evidence metadata. Their serialization values are not AVP enum authority.

## Retained artifact

```text
name:
  browser-cookie-partition-evidence-a19132e8ce6f081ccd9c834369429a31869cb9ea
artifact id:
  9732432021
artifact digest:
  sha256:7c0124250674ef568f55e312b082ed4544f8d8e17e09a341f4e0ccd7a6a2dc23
size:
  1393 bytes
retention expiry:
  2026-09-29T12:50:48Z
```

## Case matrix

| Engine | BAE-002 | BAE-003 | BAE-006 |
| --- | --- | --- | --- |
| Chromium 151.0.7922.34 | **PARTIAL** | **PARTIAL** | **PARTIAL** |
| Firefox 153.0 | **PASS** | **PARTIAL** | **PARTIAL** |
| WebKit 26.5 | **PARTIAL** | **PARTIAL** | **PARTIAL** |

No case returned `fail`. That does **not** mean BPR-004 or BPR-009 is closed.

## BAE-002 — provider serialization is not a portable SameSite state model

The fixture created two otherwise controlled cookies:

```text
default_site
  SameSite attribute omitted

explicit_lax
  SameSite=Lax
```

Observed Playwright serialization:

```text
Chromium 151.0.7922.34
  default_site -> "Lax"
  explicit_lax -> "Lax"
  result: PARTIAL

Firefox 153.0
  default_site -> "None"
  explicit_lax -> "Lax"
  result: PASS for transport distinguishability only

WebKit 26.5
  default_site -> "Lax"
  explicit_lax -> "Lax"
  result: PARTIAL
```

### Interpretation

The three-engine evidence directly rejects a provider-first mapping such as:

```text
Playwright cookie.sameSite
  -> AVP SameSite state
```

because the same RFC-level stored-state distinction is represented differently by the transport across engine families, and in two families the convenience serialization collapses Default and explicit Lax.

Firefox's `None` observation is evidence about the Playwright/Firefox path; it is **not** permission to redefine omitted SameSite as AVP `None`.

The portable rule remains:

- `SameSite=Default` is a distinct AVP-relevant stored state where the cookie model distinguishes it;
- provider values require an independently justified mapping/projection mechanism;
- if that distinction cannot be established, projection fails closed;
- `Default -> Lax` normalization is forbidden.

### BPR-004 effect

BPR-004 remains open for the complete temporal/restore evidence boundary. BAE-002 strengthens the fail-closed decision but does not supply a lossless cross-engine cookie projector.

## BAE-003 — fresh Default behavior diverges by engine/build

The fixture seeded fresh Default and explicit-Lax cookies, moved to a controlled cross-site top-level context, then submitted an unsafe POST navigation back to the cookie site.

Observed behavior:

```text
Chromium 151.0.7922.34
  fresh Default sent: true
  explicit Lax sent: false
  optional recent-cookie behavior observed: true

Firefox 153.0
  fresh Default sent: true
  explicit Lax sent: false
  optional recent-cookie behavior observed: true

WebKit 26.5
  fresh Default sent: false
  explicit Lax sent: false
  optional recent-cookie behavior observed: false
```

### Interpretation

This is positive evidence that the protocol must not define one universal effective behavior for Default cookies.

For the tested Chromium and Firefox builds, fresh Default behavior differs observably from explicit Lax in the controlled unsafe cross-site navigation. For the tested WebKit build, the optional recent-cookie compatibility behavior was not observed.

The difference is compatible with the AEP's temporal restore-eligibility rule:

- engine/build/policy identity matters;
- the optional compatibility mode need not be common across engines;
- if a Scenario relies on a creation-time-sensitive behavior, field-equal recreation cannot establish `STATE_EQUIVALENT` unless the historical temporal effect is preserved or independently proven equivalent;
- absence of the observed compatibility behavior in one test does not prove creation time globally irrelevant to that engine.

### Why BAE-003 remains PARTIAL

This slice did not compare a genuinely aged historical cookie with a fresh recreated cookie under the same bound engine/build. Therefore it establishes **fresh Default versus explicit Lax behavioral divergence**, not complete historical-age restore proof.

The correct result remains `partial`.

## BAE-006 — current automation builds exposed shared third-party localStorage

The same `a.test` third-party iframe was embedded beneath two distinct top-level sites:

```text
b.test
c.test
```

The fixture wrote:

```text
partition_probe = "under-b"
```

under `b.test`, then read the same key from an `a.test` iframe under `c.test`.

All three tested automation builds returned the same value:

```text
Chromium: shared-unpartitioned
Firefox:  shared-unpartitioned
WebKit:   shared-unpartitioned
```

No vendor partition-key value was used as AVP state identity.

### Interpretation

This result is intentionally **inconclusive for the shipping partitioning claim**.

It does not overturn the platform/engine documentation showing that modern shipping browser privacy models may partition or restrict third-party storage. It demonstrates that the specific Playwright-managed engine/build/policy combinations used by this evidence fixture did not expose such partitioning in this controlled path.

Possible reasons include engine-build policy, automation configuration, privacy-feature configuration, or a difference between these test builds and shipping products. Those possibilities must be investigated rather than guessed.

The protocol implication remains fail-closed:

- this run cannot be used to certify partitioned storage support;
- it cannot be used to claim that tuple origin is globally sufficient for third-party storage;
- Browser v0.1 may admit a context only when the implementation can establish that the selected state really is unpartitioned and tuple origin is the complete selected identity;
- if partitioned state is present or materially required, it must not be flattened into v0.1.

### BPR-009 effect

BPR-009 remains **OPEN**. The cross-engine executable matrix exists, but BAE-006 has not yet supplied the required non-admission evidence against an actually partitioned/restricted context.

## Combined significance of Slice 1 and Slice 2

The first two executable slices now establish several valuable boundaries:

```text
hostOnly behavior exists across three engine families
BUT Playwright cookie serialization cannot expose hostOnly

Default/Lax behavior and serialization vary across engines
SO provider SameSite strings cannot define AVP state

fresh Default temporal behavior differs across engines/builds
SO restore eligibility must be execution-identity-aware and fail closed

first-party admitted localStorage tuple-origin behavior passes
BUT third-party partitioned-state non-admission is not yet demonstrated by the current automation builds

exact DOMString UTF-16 code-unit round trip passes across all three families
```

This is precisely why the Browser acceptance phase separates protocol semantics from provider convenience APIs.

## Remaining evidence after this slice

Still required:

- a reviewable BAE-006 path that actually observes partitioned or restricted third-party state without changing protocol expectations to match one vendor;
- a stronger BAE-003 historical temporal comparison or an equally reviewable proof that demonstrates the fail-closed restore boundary;
- BAE-004 exact cookie complete-set selection;
- BAE-008 snapshot -> restore -> independent reprojection;
- BAE-009 reset -> independent reprojection;
- BAE-010 positive settlement witness;
- BAE-011 residual-state noninterference;
- BAE-012 negative self-certification controls.

## Current conclusion

```text
BAE-002: partial/pass/partial by engine transport
BAE-003: partial across all engines; meaningful behavioral divergence observed
BAE-006: partial across all engines; current builds exposed shared-unpartitioned state
BPR-003: OPEN
BPR-004: OPEN
BPR-009: OPEN
AEP-0011: Proposed
Acceptance-oriented review: not ready
Proposed -> Accepted: not authorized
```
