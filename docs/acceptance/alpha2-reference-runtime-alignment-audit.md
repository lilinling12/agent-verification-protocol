# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-002 UNDER REMEDIATION**

Audit baseline: `main@4376dde904d37925bf6cf2970922748629ca567c`

## Purpose

This audit checks the non-normative Python reference implementation against the current governed authority chain:

`Normative Spec -> Schema -> TCK -> Reference Runtime`

It does not permit Python behavior, convenience APIs, historical helpers, or implementation metadata to create protocol obligations.

## Acceptance rule

Reference Runtime Alignment is READY only when:

1. consumer-visible reference behavior does not contradict current normative requirements;
2. implementation identity is bound to the installed distribution identity;
3. runtime discovery metadata does not self-assert TCK conformance that is not represented by validated `ConformanceReport` evidence;
4. mandatory TCK behavior is exercised by the reference adapter rather than manufactured by expectation rewriting;
5. conditional TCK cases are skipped only when their explicit capability condition is not declared;
6. built-wheel identity, reference smoke, full registered TCK profiles, and release-evidence gates pass on the exact candidate head;
7. no implementation correction changes normative spec, schemas, or TCK expectations merely to make the reference runtime pass.

## Findings

### RRA-001 — HTTP release identity drift

Status: **RESOLVED**

The optional FastAPI application previously exposed a stale hard-coded application version while the distribution, `avp_ref.__version__`, and `ReferenceRuntime` implementation identity used `0.3.0rc1`.

PR #54 bound the HTTP application version to the distribution single source of truth and added regression coverage. The PR passed exact-head Quality, Governance, installed-wheel full TCK conformance, and release-evidence gates before squash merge as `4376dde904d37925bf6cf2970922748629ca567c`.

### RRA-002 — ambiguous runtime profile claims

Status: **BLOCKING — REMEDIATION CANDIDATE**

`ReferenceRuntime.capabilities()` exposes a `profiles` array containing legacy implementation labels such as `AVP-Snapshot`, `AVP-Verification`, `AVP-Replay`, and `AVP-Chaos`.

These labels are not the registered TCK profile identifiers and are not consumed by `TCKRunner` as conformance evidence. The TCK runner contract treats profile identity and declared conditional capabilities as explicit inputs, while validated `ConformanceReport` output binds the implementation identity, selected profile, declared capabilities, and PASS/FAIL/SKIP results.

Therefore the consumer-visible `profiles` array is ambiguous: a caller can reasonably interpret it as a self-asserted conformance claim even though it is neither a validated TCK report nor a conditional-capability declaration.

Remediation rule:

- the public runtime discovery surface MUST NOT self-assert TCK profiles;
- implementation identity and non-normative feature descriptions MAY remain discoverable;
- TCK profile conformance remains represented only by validated conformance reports;
- no current TCK profile identifiers are copied into runtime discovery as a substitute claim.

The current remediation candidate implements this at the public `avp_ref.runtime` boundary without changing execution-engine semantics.

## TCK adapter audit notes

The current reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. The reviewed Core, Evidence, Subject, MCP, OpenTelemetry, and Artifact Trust paths exercise reference implementation behavior rather than simply returning portable expectations unchanged.

The current CI package job installs the built wheel into a clean conformance environment and executes every registered TCK profile. This remains a required gate for every runtime-alignment remediation candidate.

## Remaining scope

After RRA-002 is resolved on `main`, continue the audit from the new exact baseline. Remaining review areas include implementation-only convenience behavior, public claim surfaces, packaging/runtime boundaries, and any mandatory normative requirement not genuinely exercised by the reference implementation path.

Reference Runtime Alignment is not yet READY, and this audit does not authorize stable `v0.3.0` publication.
