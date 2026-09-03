# Alpha 3 Network Control Terminating Evidence Foundation Main Adoption

Status: **MAIN-ADOPTED — TEL-001 AND PROVIDER-NEUTRAL TERMINATING-EVIDENCE PREREQUISITES STABLE**

Reconciled main baseline: `498488420223704c3522b60d1ca0e2a95e98d3eb`

Prepared: 2026-09-03

## 1. Purpose

This record reconciles the Network Control terminating-evidence implementation status after the reviewed TEL-001 foundation and its two provider-neutral follow-up prerequisites were adopted into `main`.

It is a project-status and evidence-provenance record only. It does not change AEP-0012 semantics or lifecycle state, authorize normative Network Control Spec/requirement-index/Schema/TCK work, authorize a generic provider/backend abstraction, authorize privileged GitHub Actions, or select/publish/sign/attest a release.

## 2. Governing authority and boundaries

The current authority direction remains:

```text
AEP-0012 Proposed semantics
  -> NPR-011 project acceptance evidence
  -> acceptance-oriented protocol re-review
  -> explicit Proposed -> Accepted decision
  -> normative Spec
  -> Schema where required
  -> provider/language-neutral TCK
  -> backend-neutral conformance harness
  -> reference implementation
```

AEP-0012 remains **Proposed**. The terminating evidence lab is project acceptance-evidence infrastructure and must not define portable protocol semantics by provider precedent.

The reviewed implementation boundary remains `TEL-001 -> TEL-002 -> TEL-003`:

- TEL-001: provider-neutral evidence core, deterministic fixture/client, independent initiation witness;
- TEL-002: concrete pinned Toxiproxy terminating mechanism binding against those adopted evidence responsibilities;
- TEL-003: reviewed terminating-class live evidence execution/adoption record.

The independent non-terminating packet-path class remains required before NPR-011 cross-mechanism evidence can be complete.

## 3. Main-adopted evidence foundation

### 3.1 PR #144 — TEL-001 evidence core and witness

PR #144, `test(alpha3): add terminating evidence core and witness`, was squash-merged into `main` at:

`4ff4a8eaa2c1f876538fc641a0f2cd7bdb2a9b38`

It established the provider-neutral terminating evidence foundation, including:

- immutable/sealed evidence-plan inputs and exact-byte identity;
- fresh attempt/challenge materialization without future challenge exposure;
- deterministic exact-byte TCP fixture and single-initiation attempt client;
- independent Linux transport-initiation witness collection;
- retransmission-versus-new-initiation normalization;
- fail-closed capture-integrity handling;
- content-addressed raw evidence retention.

It did not add Toxiproxy/provider control code, a generic Network backend/provider SPI, privileged CI, normative Network Control Spec/Schema/TCK, or an AEP lifecycle transition.

### 3.2 PR #145 — fixture evidence publication stabilization

PR #145, `test(alpha3): synchronize fixture evidence publication`, was squash-merged into `main` at:

`4b2bdef29773737c6a734f0385cf91997c64375d`

It closed the TEL-001 event-publication race with a bounded `Condition`-based publication barrier. The fix does not introduce sleep-based settlement, reconnect/retry behavior, or reinterpret fixture publication as transport settlement.

Exact-main post-merge validation on that commit passed CI #867, Relational Parity #260, and Browser Reference #133.

### 3.3 PR #146 — provider-neutral portable comparator

PR #146, `test(alpha3): close portable network evidence comparator`, was squash-merged into `main` at:

`44f5e4884835fbb7e5c7d98960d7cbd6cce6f798`

It added the provider-neutral C1-C12 assessment layer and optional non-target control endpoint binding without allowing provider mechanics to own portable outcomes. The comparator fail-closes evidence-integrity ambiguity before semantic conclusions and preserves predicate/failure ordering across baseline, activation settlement, active cut, target isolation, recovery/stability, initiation integrity, cleanup, and security projection.

Exact-main post-merge validation on that commit passed CI #869 (`33752164276`), Relational Parity #262 (`33752164370`), and Browser Reference #135 (`33752164390`).

### 3.4 PR #147 — non-target control logical-path identity

TEL-002 no-rewrite review identified one remaining provider-neutral attribution gap: the optional control endpoints were sealed, but a control attempt could still inherit the selected logical path identity.

PR #147, `test(alpha3): bind non-target control path identity`, closed that gap and was squash-merged into `main` at the current reconciled baseline:

`498488420223704c3522b60d1ca0e2a95e98d3eb`

The adopted change:

- derives a distinct evaluator-owned non-target logical path identity;
- seals that identity with the optional control binding;
- binds control-attempt challenge/attempt materialization to that logical path;
- carries logical path identity into normalized attempt observations;
- makes the portable comparator reject selected/control path-attribution drift;
- fails closed if a control attempt is requested without a materialized control path.

The path identity remains provider-neutral and does not use proxy/toxic/container/provider-native names or handles.

## 4. Exact-main post-merge validation

Current `main@498488420223704c3522b60d1ca0e2a95e98d3eb` is GitHub-verified and passed all push-triggered post-merge suites:

| Gate | Run | Result |
|---|---:|---|
| CI | #871 (`33754189308`) | SUCCESS |
| Relational Parity | #264 (`33754189292`) | SUCCESS |
| Browser Reference | #137 (`33754189318`) | SUCCESS |

No open pull request was present when this reconciliation Work Unit was started.

## 5. Current no-rewrite disposition

With PRs #144-#147 main-adopted and post-merge stable, no additional provider-neutral prerequisite is currently identified before TEL-002.

The next legal implementation Work Unit is therefore **TEL-002 — pinned Toxiproxy terminating mechanism binding**, constrained by `docs/acceptance/alpha3-network-control-terminating-evidence-lab-implementation-readiness.md`:

- exact reviewed Toxiproxy artifact/platform identity;
- concrete run-scoped data/admin topology;
- selected and non-target proxy paths;
- explicit upstream `timeout` toxic with `timeout = 0` for the selected cut;
- distinct activation-settlement and Subject active-cut attempts;
- non-target control during the selected cut;
- clear followed by exactly two recovery probes and one stability witness;
- independent initiation witness evidence for every certified attempt;
- positive and required negative mechanism assembly against the already-adopted provider-neutral comparator;
- explicit admin-plane isolation and Subject/control authority separation;
- run-scoped, idempotent cleanup plus residual-state/noninterference evidence;
- no arbitrary sleep, unbounded retry, silent fallback, provider-owned portable verdict, or generic provider base class.

Ordinary CI remains unprivileged. Any privileged evidence workflow remains a separate TEL-RB-003 security/workflow Work Unit.

TEL-RB-004 documentation drift in the older cross-mechanism architecture remains separately reconcilable and does not authorize weakening the later independent initiation-witness requirement.

## 6. Non-authorizations

This reconciliation does **not** authorize or claim completion of:

- TEL-002 live evidence acceptance;
- TEL-003 terminating-class adoption evidence;
- the independent packet-path mechanism class;
- NPR-011 cross-mechanism acceptance closure;
- AEP-0012 `Proposed -> Accepted`;
- Network Control normative Spec, requirement index, Schema, TCK, conformance harness, or released reference implementation;
- privileged GitHub Actions/networking changes;
- release selection, tags, package publication, signing, or attestation.

Those remain separate governed decisions and Work Units.