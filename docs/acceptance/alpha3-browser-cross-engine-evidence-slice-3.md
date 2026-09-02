# Alpha 3 Browser Cross-Engine Evidence — Slice 3

Status: **EXECUTED — POSITIVE SETTLEMENT-WITNESS EVIDENCE**

Parent evidence PR: #109  
Protocol parent PR: #108  
Evidence branch source head: `9a5872775cb1370abd3472472aa977e5c894e109`  
GitHub pull-request merge head executed by Actions: `30b260f422e39ccf278422e14f97075155b64b2e`

## Scope

This record captures executable Chromium/Gecko/WebKit evidence for:

- BAE-010 — positive Browser v0.1 settlement witness.

The case tests the AEP-0011 rule that authoritative projection may be accepted only after all already-accepted profile-relevant mutations have a known terminal outcome. It also provides a direct negative control against treating browser `networkidle` as settlement proof.

This is non-normative acceptance evidence. It does not itself promote AEP-0011 or authorize Browser Spec/Schema/TCK/runtime work.

## Exact execution identity

```text
Browser Settlement Evidence #1
run: 33312757843
job: 99260645559
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
Ubuntu 24.04.4 GitHub-hosted runner
Python 3.13.15
headless: true
controlled loopback origin:
  a.test
```

## Retained artifact

```text
name:
  browser-settlement-evidence-30b260f422e39ccf278422e14f97075155b64b2e
artifact id:
  9732503800
artifact digest:
  sha256:bc514045d81514031ecb9fa62f5ec159c5867a49de5032a3dec3b533ddbad237
size:
  811 bytes
retention expiry:
  2026-09-29T12:56:13Z
```

The artifact is evidence identity only and does not become protocol authority.

## Case matrix

| Engine | BAE-010 | `networkidle` proved settlement? |
| --- | --- | --- |
| Chromium 151.0.7922.34 | **PASS** | **No** |
| Firefox 153.0 | **PASS** | **No** |
| WebKit 26.5 | **PASS** | **No** |

## Fixture design

The controlled page starts with no selected `settlement_probe` value. Evaluator/control authority then:

1. accepts one profile-relevant mutation, `mutation-1`;
2. schedules a browser timer that will later write:

   ```text
   localStorage["settlement_probe"] = "terminal-value"
   ```

3. closes new Subject side-effect admission;
4. waits for Playwright's `networkidle` observation;
5. verifies the accepted mutation is still unresolved;
6. attempts authoritative projection;
7. rejects that projection as `unsettled` because evaluator/control still has unresolved accepted work;
8. verifies a new Subject mutation cannot be accepted after admission closes;
9. waits on the explicit browser terminal predicate `window.__mutationDone === true`;
10. records `mutation-1` terminal;
11. re-projects and accepts the final selected state.

The timer delay creates an observation window; **elapsed time is not the correctness witness**. The accepted/unresolved/terminal ledger state and explicit terminal predicate are the witness.

## Positive finding — network idle is not selected-state settlement

In all three engine families, `networkidle` became observable before the accepted localStorage mutation had reached its terminal outcome.

At that point:

```text
accepted projection: false
condition: unsettled
unresolved:
  - mutation-1
```

This directly demonstrates that a provider/network quiet condition cannot prove Browser v0.1 storage settlement.

The evidence therefore supports the AEP prohibition against using:

- `networkidle`;
- arbitrary sleep;
- quiet-window timing;
- provider command completion;
- vendor event-queue inspection alone

as sufficient protocol settlement evidence.

## Positive finding — the settlement witness is mechanically testable

After the explicit terminal predicate became true and evaluator/control marked the already-accepted mutation terminal, the selected-state projection was accepted and contained:

```text
settlement_probe = "terminal-value"
```

The fixture also verified that a new Subject mutation offered after admission closure was rejected.

Therefore the proposed settlement rule is not merely descriptive prose; its core invariant can be evaluated mechanically:

```text
admission closed
AND
all accepted profile-relevant pre-boundary mutations terminal
AND
no unresolved accepted profile-relevant mutation
THEN
projection may begin
ELSE
unsettled / no accepted final projection
```

## BPR-006 effect

BPR-006's protocol decision was already incorporated in AEP-0011. Slice 3 now provides positive executable evidence across Chromium, Gecko, and WebKit-family test transports that:

- network-idle is insufficient;
- unresolved accepted work can be distinguished from settled work;
- projection can fail closed as `unsettled`;
- admission closure is independently enforceable;
- projection may proceed only after evaluator/control observes terminal completion.

This evidence does not turn the test-only `_MutationLedger` into a runtime abstraction or prescribe how a future conforming implementation must internally track accepted work.

## Architecture boundary

The fixture ledger lives only under `tests/acceptance/browser/`. It is intentionally not moved to `src/avp_ref`, `conformance/`, or a Browser provider package.

The evidence validates an externally testable invariant, not an implementation class hierarchy.

## What this slice does not prove

Slice 3 does not establish:

- a lossless selected-cookie projector;
- cookie temporal restore eligibility;
- partitioned-storage shipping-policy evidence;
- complete cookie selection semantics;
- snapshot/restore `STATE_EQUIVALENT`;
- reset reprojection;
- residual-state noninterference;
- complete BPR-009 closure.

## Current conclusion

```text
BAE-010: PASS across Chromium/Gecko/WebKit-family evidence transports
networkidle as settlement oracle: REJECTED by executable evidence
BPR-006 protocol decision: positively supported
BPR-003: OPEN
BPR-004: OPEN
BPR-009: OPEN
AEP-0011: Proposed
Proposed -> Accepted: not authorized
```
