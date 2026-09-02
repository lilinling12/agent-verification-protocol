# Alpha 3 Browser Cross-Engine Evidence — Slice 1

Status: **EXECUTED — PARTIAL ACCEPTANCE EVIDENCE**

Parent evidence PR: #109  
Protocol parent PR: #108  
Evidence branch source head: `3cfc1710d719c8fe221de13788e9fa5d53f755f8`  
GitHub pull-request merge head executed by Actions: `011c7117d7e0fddf672b978dfcabf9046cb6c49c`

## Scope

This record captures the first executable Chromium/Gecko/WebKit evidence slice for AEP-0011. It is non-normative acceptance evidence and does not close BPR-003, BPR-004, or BPR-009 by itself.

Executed cases:

- BAE-001 — host-only versus domain-scoped cookie behavior and projection sufficiency;
- BAE-005 — admitted first-party/unpartitioned tuple-origin `localStorage` behavior;
- BAE-007 — lossless Web IDL `DOMString` UTF-16 code-unit round trip.

## Exact execution identity

Workflow:

```text
Browser Acceptance Evidence #1
run: 33312289466
job: 99259411169
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

Execution platform:

```text
Ubuntu 24.04 GitHub-hosted runner
Python 3.13.15
headless: true
controlled loopback hosts:
  a.test
  sub.a.test
  b.test
```

No browser privacy/storage flag was changed to force cross-engine parity.

## Retained artifact

Artifact:

```text
name:
  browser-pre-acceptance-evidence-011c7117d7e0fddf672b978dfcabf9046cb6c49c
artifact id:
  9732363667
artifact digest:
  sha256:1156d9ae1d3ec779be72de3d5cc6562104bca2e8bff3034a3c0cde2ec4142049
size:
  1143 bytes
retention expiry:
  2026-09-29T12:45:39Z
```

The artifact is execution evidence, not protocol authority.

## Case matrix

| Engine | BAE-001 | BAE-005 | BAE-007 |
| --- | --- | --- | --- |
| Chromium 151.0.7922.34 | **PARTIAL** | **PASS** | **PASS** |
| Firefox 153.0 | **PARTIAL** | **PASS** | **PASS** |
| WebKit 26.5 | **PARTIAL** | **PASS** | **PASS** |

No case returned `fail` in this slice.

## BAE-001 finding — behavior is portable; Playwright projection is insufficient

The controlled HTTP fixture created:

1. a host-only cookie by omitting the `Domain` attribute; and
2. a domain-scoped cookie with `Domain=a.test`.

For all three engine families:

- the host-only cookie was not sent to `sub.a.test`;
- the domain-scoped cookie was sent to `sub.a.test` where domain-match permitted it.

This establishes the browser-observable behavioral distinction expected by RFC 10025 across the tested engine families.

However, Playwright 1.62.0 `BrowserContext.cookies()` did not expose a `hostOnly` field in any of the three tested families. The runner therefore returned `BAE-001=partial`, not `pass`.

The correct AVP interpretation is:

```text
browser behavior proves host-only/domain distinction
+
Playwright convenience cookie serialization does not expose required AVP identity
=
a projector relying only on that serialization must fail closed
```

The evidence MUST NOT be converted into an inference rule such as leading-dot inspection, URL provenance guessing, or `Domain` presentation heuristics. Such inference would make the transport serialization define protocol identity.

### BPR-003 effect

BPR-003 remains **OPEN FOR EXECUTABLE PROJECTION EVIDENCE**.

This slice strengthens, rather than weakens, the AEP decision to retain:

```text
(name, domain, hostOnly, path)
```

A future accepted implementation requires another independently reviewable projection mechanism or an explicit unsupported/fail-closed result for selected cookie state whose `hostOnly` identity cannot be established.

## BAE-005 finding — admitted first-party tuple-origin localStorage behavior passes

Across Chromium, Firefox, and WebKit in the controlled first-party context:

- `a.test` state remained visible across path/query/fragment changes;
- `b.test` did not observe `a.test` localStorage state;
- mutation under `b.test` did not alter `a.test` state.

This provides initial executable evidence for the AEP's admitted **unpartitioned first-party tuple-origin** state model.

It does **not** prove that third-party or partitioned state can be represented by tuple origin. BAE-006 remains required.

## BAE-007 finding — exact DOMString code units pass across all three families

The browser-side fixture constructed values from explicit UTF-16 code units using `String.fromCharCode` and read them back using `charCodeAt`, avoiding accidental transport repair of malformed surrogate sequences.

Tested values included:

- empty string;
- U+0000;
- ASCII;
- non-ASCII BMP text;
- valid surrogate pair;
- unmatched high surrogate;
- unmatched low surrogate;
- composed Unicode sequence;
- canonically decomposed Unicode sequence.

All three engine families preserved the exact code-unit sequences in localStorage.

The test-only AVP evidence codec then round-tripped each exact unsigned 16-bit sequence through:

```text
UTF-16 code units
  -> two network-byte-order bytes per code unit
  -> unpadded base64url
  -> exact decoded code units
```

No normalization, U+FFFD repair, or scalar-value coercion was observed in the tested path.

### BPR-007 effect

This is positive implementation evidence for the already incorporated BPR-007 protocol decision. It does not independently promote the AEP lifecycle.

## Engineering gate results on source head

The same evidence source head completed the existing repository gates successfully:

```text
CI #650
run 33312289415
SUCCESS

Governance #720
run 33312289447
SUCCESS

Relational Parity #43
run 33312289425
SUCCESS

Browser Acceptance Evidence #1
run 33312289466
SUCCESS
```

This demonstrates that the test-only Browser evidence boundary did not require Browser dependencies in the base package and did not regress existing Relational/quality gates.

## What this slice does not prove

This slice does not establish:

- a lossless accepted cookie projector;
- `SameSite=Default` versus explicit Lax projection;
- creation-time-sensitive restore eligibility;
- partitioned third-party localStorage non-admission;
- snapshot/restore `STATE_EQUIVALENT` evidence;
- reset evidence;
- settlement witness behavior;
- residual-state noninterference;
- completion of BPR-003, BPR-004, or BPR-009.

## Next evidence slice

The next executable slice should cover:

```text
BAE-002 — SameSite Default vs explicit Lax
BAE-003 — temporal restore eligibility diagnostics
BAE-006 — partitioned third-party localStorage non-admission
```

The portable expectation must remain fail-closed and must not require optional SameSite compatibility behavior or partitioning implementation details to be identical across browser families.

## Current conclusion

```text
BAE-001: PARTIAL across Chromium/Gecko/WebKit
BAE-005: PASS across Chromium/Gecko/WebKit
BAE-007: PASS across Chromium/Gecko/WebKit
BPR-003: OPEN
BPR-004: OPEN
BPR-009: OPEN
AEP-0011: Proposed
Proposed -> Accepted: not authorized
```
