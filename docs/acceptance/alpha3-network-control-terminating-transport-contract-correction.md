# Alpha 3 Network Control Terminating Transport Contract Correction

Status: **IMPLEMENTATION CORRECTION UNDER REVIEW — TEL-003 EVIDENCE NOT YET PRODUCED OR ADOPTED**

Prepared: 2026-09-04

## 1. Purpose

This record captures the end-to-end correction required after trusted-main `Network Control Privileged Evidence` run `33840868116` reached the real Toxiproxy data plane and exposed a deterministic incompatibility between the shared exact-byte fixture/client implementation and the pinned terminating intermediary.

The correction is intentionally broader than a one-line failure fix. It addresses the concrete transport contract, failure-evidence retention, and the missing provider-transport qualification gate while preserving the existing provider-neutral comparator and AEP-0012 semantics.

## 2. Triggering trusted-main evidence

Run `33840868116` executed from exact:

```text
main@9924c538d9d75ab33287135940a165f4766b9a79
```

The following boundaries passed before the failure:

- exact default-branch checkout guard;
- constrained Python environment and dependency check;
- runner/Docker provenance capture;
- exact helper-image materialization;
- pinned Toxiproxy v2.12.0 version verification;
- AF_PACKET qualification v0.3;
- all four reviewed `CaptureAssurance` assertions;
- duplicate-SYN normalization canary.

The positive terminating run then materialized the real topology and executed certified attempts. The provider-neutral comparator returned:

```text
SEMANTIC_VIOLATION
primary: C2:baseline:exact-exchange-not-completed
```

with additional positive-path completion failures for pre-trigger, non-target control, recovery, and stability phases.

Retained transport evidence showed the important common pattern:

- each affected attempt had exactly one front initiation;
- each affected attempt had exactly one corresponding upstream initiation;
- no alternate initiation was normalized away;
- no byte mismatch was observed by the Subject client;
- the attempts did not report evaluator-budget expiry;
- exact exchange completion was false.

This ruled out the earlier helper/version prerequisites and focused the audit on the concrete stream framing between Subject, Toxiproxy, and Fixture.

Run `33840868116` is **not** TEL-003 evidence and must not be adopted as such.

## 3. Root cause: implementation framing diverged from reviewed design

### 3.1 Shared implementation before correction

The shared exact-byte client sent the exact materialized request and then called:

```text
shutdown(SHUT_WR)
```

The Fixture read the exact request byte count, then required a further read to observe EOF before it was allowed to emit the expected response. This made client TCP half-close a hidden prerequisite for every successful exchange.

### 3.2 Pinned Toxiproxy behavior

The reviewed Toxiproxy artifact remains v2.12.0 from exact source commit:

```text
3ccd6a79cbc6c6a72b884d295ad314b75cdf3962
```

At that source revision, the Toxiproxy stream relay closes the destination side when the corresponding copy direction reaches EOF rather than preserving the connection as an application-transparent TCP half-close boundary.

Therefore the previous sequence was structurally incompatible:

```text
Subject exact request
  -> Subject SHUT_WR
  -> Toxiproxy observes client EOF
  -> Toxiproxy closes upstream destination
  -> Fixture observes EOF
  -> Fixture no longer owns a usable upstream connection on which to return response
```

The resulting evidence matches run `33840868116`: both front and upstream initiation occurred once, but the exact response could not complete.

### 3.3 Why this is not an AEP change

AEP-0012 requires the governed exact request to be emitted once and the exact expected response to be observed for successful exchange phases. It does not make native FIN/RST behavior portable Network Control semantics.

The reviewed NPR-011 evidence-contract detailed design is even more explicit about the deterministic Fixture protocol:

1. accept one connection;
2. read the exact request byte count;
3. validate exact request bytes/current challenge;
4. on a valid request, emit the exact materialized expected response once;
5. record the fixture exchange event;
6. finish according to fixture-local hygiene.

The pre-response EOF barrier was therefore an implementation deviation introduced after the design baseline, not a protocol requirement that the provider must emulate.

## 4. Corrected exact-byte exchange boundary

The Subject client still performs:

- exactly one TCP connection initiation;
- exactly one governed request-byte send sequence;
- no reconnect;
- no fallback destination;
- no application retry loop;
- evaluator-owned finite monotonic observation budget;
- exact expected-response comparison.

It no longer requires `SHUT_WR` before reading the response.

The Fixture now follows the reviewed contract order:

1. read exactly the governed request byte count;
2. reject truncation or exact-byte mismatch;
3. emit the exact expected response immediately after exact request validation;
4. perform bounded post-response request-stream hygiene;
5. retain trailing-byte evidence if additional request bytes were supplied.

A client may therefore receive the exact response before the Fixture finishes its supplemental trailing-byte hygiene check. Such a completed client exchange is **not sufficient evidence by itself**: the canonical trusted live binding requires the corresponding exact Fixture event to show:

- `requestValid=true`;
- `responseEmitted=true`;
- no Fixture problem.

Trailing request bytes, request mismatch, missing Fixture evidence, or malformed Fixture evidence become evidence-validity problems before portable semantic success can be accepted.

This preserves exact-byte integrity without making provider-specific TCP half-close handling a portable condition.

## 5. Failure-evidence retention correction

Run `33840868116` also exposed a diagnostic integrity gap.

The role worker already produced the complete project-local `ExchangeObservation` diagnostics:

- `attemptId`;
- `completed`;
- `mismatchObserved`;
- `observationBudgetExpired`;
- `elapsedNs`;
- `responseSize`;
- `responseSha256`;
- `nativeError`.

The live lab previously discarded these diagnostics after projecting only the provider-neutral fields into `AttemptObservation`. Fixture events were retained only for completed exchanges.

The canonical trusted binding now:

- content-addresses every exchange diagnostic;
- binds its `ArtifactRef` to the exact certified `PhaseExecution`;
- requires completed exchanges to retain and pass exact Fixture integrity evidence;
- performs only a short, bounded, non-authoritative Fixture diagnostic lookup for incomplete exchanges;
- records unavailable incomplete Fixture diagnostics without turning their absence into a portable cut predicate.

Native socket/provider diagnostics remain project-local and cannot establish portable PASS.

## 6. Pinned timeout-toxic semantics

The same pinned Toxiproxy source was audited for the active-cut mechanism.

For the reviewed upstream `timeout` toxic with `timeout=0`, Toxiproxy drops data without scheduling an immediate connection close. Therefore the expected concrete compatibility signal for the active-cut qualification is evaluator-owned observation-budget expiry/non-completion, not a provider-native FIN/RST or specific socket error.

The provider-neutral comparator remains unchanged and continues to judge completion/non-completion from reviewed normalized evidence rather than native connection termination details.

## 7. Process correction: provider transport qualification before full matrix

The privileged workflow previously performed:

```text
AF_PACKET qualification
  -> full positive/negative terminating matrix
```

That allowed helper identity, admin-version parsing, and stream-framing integration defects to surface serially inside the expensive full matrix.

The corrected workflow adds an explicit project-local concrete transport qualification:

```text
trusted exact main
  -> AF_PACKET capture qualification
  -> pinned Toxiproxy transport qualification
       * pass-through exact exchange
       * timeout=0 active cut
       * clear + fresh recovery
       * exact 1/1 front/upstream initiations
       * exchange/Fixture evidence retention
       * clean teardown
  -> full provider-neutral C1-C12 positive/negative matrix
```

The transport qualification does **not** issue a C1-C12 verdict and cannot replace the full matrix. Its responsibility is only to prove that the exact reviewed concrete provider/runtime can carry the evidence mechanics that the full matrix is about to exercise.

## 8. Canonical concrete binding boundary

The executable scripts continue to use the narrow trusted concrete bindings in `verified_live_labs.py`. These bindings are the canonical execution boundary for the current Proposed evidence work and apply:

- exact helper-image materialization;
- strict pinned Toxiproxy version parsing;
- exact exchange diagnostic retention;
- completed-Fixture integrity checks.

The older base concrete classes are not public provider APIs and are not executable entrypoints. Folding the reviewed prerequisites back into their lower-level owners is intentionally deferred to a separate structural-cleanup Work Unit rather than mixing a large refactor into this behavior/evidence correction.

No generic provider SPI or backend hierarchy is introduced.

## 9. Scope boundary

This correction does not change:

- AEP-0012 lifecycle state;
- C1-C12;
- `compare_portable_evidence`;
- provider-neutral Network Control semantics;
- AF_PACKET SYN normalization rules;
- capture qualification v0.3 requirements;
- HiddenRetry/Fallback portable semantics;
- Spec, Schema, requirement-index, or TCK;
- public runtime APIs;
- release/signing/attestation surfaces;
- provider/backend abstraction policy.

AEP-0012 remains **Proposed**.

TEL-003 evidence adoption remains a separate governed Work Unit. No further privileged rerun should be treated as an adoption candidate until this correction has passed ordinary exact-head gates, focused review, Ready-state Governance, explicit merge authorization, trusted-main adoption, and the new transport qualification plus complete terminating matrix on that exact main revision.
