# Alpha 3 Browser Partition Evidence — Transport Assessment

Status: **REVIEWED — PLAYWRIGHT-ONLY PARTITION EVIDENCE INSUFFICIENT**

Parent evidence PR: #109  
Relevant executable record: `docs/acceptance/alpha3-browser-cross-engine-evidence-slice-2.md`

## 1. Question

BAE-006 expected the same third-party origin, embedded under two distinct top-level sites, to expose either:

- partitioned state;
- blocked/restricted state; or
- an explicitly observed shared-unpartitioned policy.

Slice 2 observed `shared-unpartitioned` for all three Playwright-managed engine families.

The review question is whether that observation disproves modern storage partitioning assumptions or instead reflects the automation transport/build policy.

## 2. Finding

The observation is explained by the Playwright browser environment and MUST NOT be generalized into a shipping-browser privacy claim.

Playwright's own browser patches and issue history document deliberate deviations from shipping partitioning defaults.

### Firefox

Playwright's Firefox configuration currently includes:

```text
pref("network.cookie.cookieBehavior", 4)
```

with an explicit source comment that first-party-based cookie partitioning is disabled because enabling it would require retaining partition-related permissions in Playwright storage state.

Relevant upstream source:

- `microsoft/playwright/browser_patches/firefox/preferences/playwright.cfg`

Relevant upstream issue:

- `microsoft/playwright#31275` — request to restore Firefox's shipping partitioning default rather than Playwright's overridden value.

### Cross-engine Playwright limitation

Upstream Playwright issue `microsoft/playwright#38455` records that storage partitioning is enabled by default in major shipping browsers but has been disabled in Playwright-managed browser environments, citing Chromium, Firefox, and WebKit behavior and requesting support for storage-key-aware state.

This aligns with Slice 2's three-engine `shared-unpartitioned` observation.

### Product/build distinction

Playwright documentation also states that:

- its Firefox requires Playwright-specific patches and does not operate as the branded Firefox product;
- its WebKit build is derived from WebKit sources and is not branded Safari;
- operating-system/platform behavior may differ.

Therefore the engine-family label is valid implementation metadata, but it is not sufficient evidence that shipping privacy policy is active.

## 3. Protocol consequence

This limitation confirms, rather than weakens, AEP-0011's separation between:

```text
browser engine family
browser build/version
execution configuration/policy
AVP logical selected state
```

A label such as `firefox`, `webkit`, or `chromium` cannot prove storage-partition policy.

If partitioning is material to the evidence claim, the bound execution identity must make the relevant browser build/policy reviewable.

## 4. Evidence consequence

### Slice 2 remains valid

BAE-006 remains `PARTIAL` for all three tested Playwright-managed engines.

It validly proves:

- the evidence runner does not invent a partition key;
- the base-profile disposition remains fail-closed when partition identity is not established;
- engine-family name alone is insufficient to infer partitioning.

It does **not** prove:

- that shipping Chromium/Chrome is unpartitioned;
- that shipping Firefox is unpartitioned;
- that shipping Safari/WebKit privacy policy is unpartitioned;
- that BPR-009 partition-state evidence is complete.

## 5. Prohibited workaround

The acceptance project MUST NOT simply enable vendor-specific partitioning flags in all Playwright engines and call the result portable evidence.

Such a run may be useful as a controlled negative fixture if the exact non-default policy is bound and explicitly labeled, but it cannot substitute for evidence about shipping/default browser-family behavior.

In particular, the project must not:

- change one engine's flags until it matches another engine;
- treat Playwright storage-state partition-key fields as AVP identity;
- infer shipping privacy semantics from an automation build merely because the engine family name matches;
- mark BAE-006 pass by configuration without recording the configuration as execution identity.

## 6. Required next partition-evidence strategy

BPR-009 requires a mixed evidence strategy for partitioning:

1. **standards/WPT evidence** for the cross-browser platform behavior and partitioning expectations;
2. **shipping/default engine-family evidence** where practical, using a transport that does not disable the relevant privacy behavior;
3. **AVP fail-closed evidence** showing that an implementation presented with partitioned/restricted state does not flatten it into Browser v0.1 tuple-origin state.

The same portable AVP expectation applies across all runs:

```text
if tuple origin is not proven to be the complete selected unpartitioned storage identity,
Browser v0.1 projection is not accepted.
```

The transport may differ by engine family when necessary to observe real policy. Transport identity remains evidence metadata, not protocol semantics.

## 7. Candidate transport directions

No provider choice is adopted by this record. Candidate evidence paths include:

- WPT/wpt.fyi results for the platform-level partitioning statement;
- branded/shipping Chromium-family execution through a transport that preserves its default storage-partition policy;
- Firefox execution without Playwright's `network.cookie.cookieBehavior=4` override;
- WebKit/Safari-family evidence on a platform/runtime where the relevant storage privacy policy is active.

Each path requires exact build/policy identity and must be reviewed before being treated as BPR-009 closure evidence.

## 8. Current conclusion

```text
Slice 2 BAE-006: valid PARTIAL evidence
Playwright-managed three-engine matrix: insufficient for shipping partition-policy proof
Playwright-only BPR-009 closure: rejected
Protocol tuple-origin boundary: unchanged
BPR-009: OPEN
```
