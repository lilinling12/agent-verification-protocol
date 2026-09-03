# Alpha 3 Network Control Hidden-Retry Upstream Negative Prerequisite

Status: **TEL-002 EVIDENCE PREREQUISITE — REVIEW REQUIRED BEFORE TEL-RB-003 READY / TEL-003 EXECUTION**

Prepared: 2026-09-04

Baseline: `bc01bc028e8bd37dbff324fb98d4b980aecbf5be`

## 1. Problem

The terminating-lab readiness audit requires at least two independent `HiddenRetry/Fallback` faulty assemblies:

1. one certified Subject attempt performs an additional Subject-facing connection initiation;
2. an intentionally faulty helper in the same Toxiproxy role/network namespace performs an additional upstream initiation during the certified attempt window.

The main-adopted TEL-002 implementation currently materializes the first variant only. Its Subject exchange worker performs a second front-side `connect` when `NegativeMode.HIDDEN_RETRY_FALLBACK` is selected. The same provider-neutral C10 comparator rejects the observed cardinality violation.

That is not sufficient for the readiness requirement. A terminating implementation could preserve one Subject-facing initiation while internally reconnecting/retrying upstream. The independently armed upstream witness must prove that such a fault is also observable and rejected.

TEL-RB-003 PR #150 therefore remains Draft/frozen until this prerequisite is main-adopted and post-merge stable.

## 2. Narrow implementation decision

This Work Unit does not add another portable negative mode and does not modify C1-C12.

`HiddenRetry/Fallback` remains the existing project-local umbrella negative. A new test-only `UpstreamHiddenRetryLiveLab` subclasses the concrete Toxiproxy live lab solely to replace the existing front-side extra connect with the required upstream faulty assembly.

The ordinary positive lab and every other negative mode remain unchanged.

No generic provider base class, provider registry, backend SPI, public API, Schema, or TCK surface is introduced.

## 3. Same-role/namespace helper

When the existing phase runner selects `HiddenRetry/Fallback` for `subject-active-cut`, the upstream variant performs the normal certified Subject exchange with the base `extra_connect` disabled. Before the certified attempt returns — while front and both upstream AF_PACKET witnesses remain armed — it runs one bounded helper with:

```text
--network container:<exact Toxiproxy container>
--read-only
--cap-drop=ALL
--security-opt=no-new-privileges
<exact pinned helper image digest>
```

The helper receives no Docker socket and no `NET_RAW` capability. It uses an ordinary TCP socket only.

The socket explicitly binds the Toxiproxy **data-plane literal source address** before `connect_ex()` to the exact selected fixture endpoint. This prevents route/source ambiguity from silently placing the faulty initiation on the admin-side witness channel.

The helper performs exactly one direct connection initiation and exits. It does not activate or clear the fault, does not inspect provider state, and does not produce a portable verdict.

## 4. Witness and comparator ownership

The certified attempt already arms:

- `W-front` on the Subject/privileged front role;
- `W-upstream-data` in the Toxiproxy namespace for the data source address;
- `W-upstream-admin` in the same namespace for the admin source address.

The helper executes only after those witnesses are ready and before they are closed. Main PR #151's bounded terminal drain is therefore also applied when the attempt seals.

For the upstream negative, expected evidence is:

```text
frontInitiations == 1
upstreamInitiations > 1
```

The existing provider-neutral comparator owns the rejection through C10. The helper's Docker exit code or marker record cannot establish the semantic violation by itself.

Raw witness bytes remain the cardinality evidence.

## 5. Variant provenance

Because both faulty assemblies intentionally use the same `NegativeMode.HIDDEN_RETRY_FALLBACK`, the opt-in execution script gains a project-local `--hidden-retry-variant` selector:

- `front-extra-connect` — default, preserving the already-adopted behavior;
- `upstream-extra-connect` — selects the same-namespace upstream faulty lab.

The selector is rejected for unrelated negative modes.

For the upstream variant the live lab retains an additional project-local phase evidence marker containing the exact attempt, source address, destination endpoint, Toxiproxy namespace container identity, and pinned helper image provenance. This marker is diagnostic provenance; the transport witness still owns the initiation count.

## 6. Failure and lifecycle policy

The injected helper is bounded by the existing evaluator `_run_bounded` process limit and uses a finite socket timeout. A helper execution failure is an execution/infrastructure failure; it is not converted into a C10 PASS or assumed retry evidence.

The helper container is one-shot and `--rm`. Normal lab cleanup remains responsible for the Toxiproxy/fixture/network topology. No arbitrary sleep, reconnect loop, fallback loop, or provider-native retry counter is introduced.

## 7. Regression requirements

Ordinary CI must verify without requiring Docker that:

1. the helper command shares exactly the Toxiproxy network namespace;
2. it is read-only, capability-dropped, has no `NET_RAW`, and has no Docker socket;
3. it uses the exact pinned helper image;
4. it explicitly binds the data-plane source address and exact fixture endpoint;
5. the upstream variant suppresses the base front extra-connect;
6. injection occurs before the overridden exchange method returns, therefore inside the existing witness window;
7. variant provenance is retained as phase evidence;
8. CLI default preserves the front variant and explicit upstream selection chooses only the test-only upstream assembly;
9. variant selection is rejected for unrelated negative modes.

The privileged TEL-RB-003 workflow must later execute **both** variants and require the same C10 rejection before TEL-003 evidence can be considered complete.

## 8. Governance boundary

This prerequisite does not authorize:

- TEL-RB-003 merge;
- TEL-003 evidence adoption;
- AEP-0012 `Proposed -> Accepted`;
- normative Network Control Spec/requirement-index/Schema/TCK work;
- backend/provider abstraction;
- release selection, publication, signing, or attestation.

After this prerequisite is independently reviewed, merged, and post-merge validated, PR #150 must be reconciled onto the resulting exact main and its privileged matrix updated to execute both required HiddenRetry/Fallback variants.
