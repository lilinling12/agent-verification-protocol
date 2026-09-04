# Alpha 3 Network Control Toxiproxy Version Response Correction

Status: **IMPLEMENTATION FIX UNDER REVIEW — TEL-003 EVIDENCE NOT YET PRODUCED OR ADOPTED**

Prepared: 2026-09-04

## 1. Triggering trusted-main evidence

After PR #153 was squash-merged to exact `main@938935adf4b9579f3a8d38bde357507f7090cb85`, maintainer workflow dispatch started `Network Control Privileged Evidence` run `33833695091` on that exact `main` revision.

The trusted boundary checks passed. Capture qualification also passed completely, including the strengthened duplicate-SYN normalization canary:

- format `avp-project-network-capture-qualification-v0.3`;
- all four `CaptureAssurance` facts true only after non-circular qualification;
- duplicate-SYN canary retained `rawSynPackets=2`;
- duplicate-SYN canary normalized to `totalInitiations=1`;
- `retransmittedSynPackets=1`;
- zero capture drops;
- raw qualification artifacts retained.

This confirms the helper-image correction adopted through PR #153 reached and passed the privileged AF_PACKET qualification boundary.

The terminating matrix then failed before the positive case could produce portable observations. The exact error was:

```text
ToxiproxyControlError: unexpected Toxiproxy runtime version '{"version": "2.12.0"}'; expected '2.12.0'
```

The workflow failed closed, built its manifest, and uploaded artifact ID `9922559198`. The positive result file is empty and no negative cases ran, so run `33833695091` is **not** TEL-003 evidence.

## 2. Root cause

The pinned Toxiproxy source is commit:

```text
3ccd6a79cbc6c6a72b884d295ad314b75cdf3962
```

At that exact source revision, `GET /version` is a JSON endpoint. Its implementation sets JSON content type and emits exactly:

```json
{"version":"<runtime-version>"}
```

The project concrete verifier instead treated the response body as legacy plain text and attempted to remove a `toxiproxy-server version ` prefix before comparing it with the reviewed version.

That parser did not match the exact reviewed provider contract and therefore rejected a correct pinned Toxiproxy v2.12.0 runtime.

## 3. Correction

The trusted concrete execution binding now parses the reviewed Toxiproxy v2.12.0 version response as strict JSON.

Accepted shape:

```json
{"version":"2.12.0"}
```

The parser requires:

1. valid JSON;
2. a JSON object;
3. exactly one member named `version`;
4. a non-empty string version value;
5. exact equality with the reviewed artifact version `2.12.0`.

The following fail closed:

- legacy plain text;
- `toxiproxy-server version ...` text;
- malformed JSON;
- non-object JSON;
- missing `version`;
- additional fields;
- non-string version values;
- version drift.

The existing bounded admin-readiness loop is retained. The raw `ControlSnapshot.response_bytes` remains unchanged and available as project-local control-plane provenance.

## 4. Scope boundary

This correction is limited to trusted concrete Toxiproxy execution plumbing and regression tests. It does not change:

- AEP-0012 lifecycle state;
- C1-C12;
- `compare_portable_evidence`;
- portable Network Control semantics;
- AF_PACKET witness normalization;
- capture qualification requirements;
- HiddenRetry/Fallback semantics;
- Spec, Schema, requirement-index, or TCK;
- workflow permissions or triggers;
- release, signing, or attestation surfaces;
- provider/backend abstraction policy.

Provider API acknowledgement and provider version response still cannot establish portable PASS.

AEP-0012 remains **Proposed**. TEL-003 evidence adoption remains a separate governed Work Unit and requires a later successful trusted-main matrix execution plus independent artifact review.
