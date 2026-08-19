# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-009 UNDER REMEDIATION**

Audit baseline: `main@042d891bbe02f3c3d81a7e419de1d140d0bf5511`

## Purpose

This audit checks the non-normative Python reference implementation against the current governed authority chain:

`Normative Spec -> Schema -> TCK -> Reference Runtime`

It does not permit Python behavior, convenience APIs, historical helpers, or implementation metadata to create protocol obligations.

## Acceptance rule

Reference Runtime Alignment is READY only when:

1. consumer-visible reference behavior does not contradict current normative requirements;
2. implementation identity is bound to the installed distribution identity;
3. runtime discovery metadata does not self-assert TCK conformance that is not represented by validated `ConformanceReport` evidence;
4. mandatory TCK behavior is exercised by the reference adapter rather than manufactured by expectation rewriting or implementation-only table inspection where the case requires execution behavior;
5. conditional TCK cases are skipped only when their explicit capability condition is not declared;
6. built-wheel identity, reference smoke, full registered TCK profiles, and release-evidence gates pass on the exact candidate head;
7. development and published distribution identities cannot ambiguously bind one public version to multiple source revisions;
8. no implementation correction changes normative spec, schemas, or TCK expectations merely to make the reference runtime pass.

## Findings

### RRA-001 — HTTP release identity drift

Status: **RESOLVED**

PR #54 bound the optional FastAPI application version to the distribution single source of truth and merged as `4376dde904d37925bf6cf2970922748629ca567c` after its required gates passed.

### RRA-002 — ambiguous runtime profile claims

Status: **RESOLVED**

PR #55 removed legacy runtime profile self-claims from the public discovery boundary. Conformance remains represented by validated `ConformanceReport` output. The remediation merged as `de8fa1c61d94924f63c173fe4f8ea1cdaff73899`.

### RRA-003 — OpenTelemetry release identity drift

Status: **RESOLVED**

PR #56 bound public OpenTelemetry bridge description and tracer instrumentation-scope identity to the `avp-reference` distribution version without changing telemetry mapping semantics or TCK expectations. The remediation merged as `7666c9b04922bbc5696f1983393d8a9247f0238c`.

### RRA-004 — runtime discovery claim levels

Status: **RESOLVED**

PR #57 separated static implementation support from actual instance configuration and removed profile-like/broad isolation self-claims from consumer discovery. The remediation merged as `c65ab1a3400ed6513eab68c4999164d95fcb1aae`.

### RRA-005 — public discovery version scope drift

Status: **RESOLVED**

PR #58 removed the ambiguous top-level `version: avp.spec/v0.1` runtime claim and scoped the value correctly as Scenario API vocabulary metadata. The remediation merged as `abee72c93c5caf5ccb9d66d67e60b2dad9e1d1f5`.

### RRA-006 — Episode manifest version-label identity drift

Status: **RESOLVED**

PR #59 renamed the identity-bearing reference manifest field/key from `protocol_version` to `scenario_api_version` and preserved replay source binding to the exact active manifest digest. The remediation merged as `883109ac19481076e24bb65383ecba0798298b61`.

### RRA-007 — Oracle runner release identity drift

Status: **RESOLVED**

PR #60 bound the bundled Oracle runner implementation version to the `avp-reference` distribution single source of truth while preserving `avp.oracle/v2` as the independent interoperability identifier. It merged as `f41a409e6296c7590bbedaa7e2157ec3176d5b1b` after exact-head CI #440, Governance #475, Ready Governance #476, installed-wheel full TCK conformance, and release-evidence gates passed.

### RRA-008 — post-RC development distribution provenance

Status: **RESOLVED**

PR #61 established the fail-closed blocker: published `v0.3.0-rc.1` / `avp-reference==0.3.0rc1` is immutable evidence for exact source `ef199124017b0dcc8c4a966d00c4f407760f9a06`, while materially later source must not continue producing different artifacts under that already-published distribution version.

PR #62 adopted the governed post-RC development identity policy:

```text
0.3.0rc1 < 0.3.0rc2.dev0 < 0.3.0rc2 < 0.3.0
```

The implementation moved repository source identity to `0.3.0rc2.dev0`, added `docs/releases/release-development-state.json`, added a fail-closed development-state validator and regression coverage, and wired the validator into the quality gate. It preserves the immutable RC1 source anchor and keeps publication of `v0.3.0-rc.2` or stable `v0.3.0` as independent release decisions.

Exact-head CI #444 (`32206904808`) passed Python 3.11/3.12/3.13 Quality, reproducible package construction, built-wheel metadata and identity, clean consumer install, reference smoke, installed-wheel full registered TCK conformance, and release-evidence build/verification. Governance #479 and Ready Governance #480 also passed. PR #62 was explicitly authorized and squash-merged as `042d891bbe02f3c3d81a7e419de1d140d0bf5511`.

### RRA-009 — Core mandatory normal-path probe does not execute the runtime lifecycle

Status: **BLOCKING — REMEDIATION CANDIDATE**

`AVP-TCK-LIFECYCLE-NORMAL-001` is a mandatory Core case for AVP-CORE-001, AVP-CORE-008, and AVP-CORE-009. Its vector requires the ordered normal lifecycle path from `CREATED` through `COMPLETED`, and its expectation requires `accepted: true` with terminal state `COMPLETED`.

The current reference adapter validates that case by passing each vector pair to the reference implementation's `assert_transition()` relation and then returning PASS when all pairs are statically allowed. It does not create an Episode, invoke `ReferenceRuntime.provision()`, `run_subject()`, or `verify()`, inspect runtime-produced transition records, or observe the actual terminal state.

That is insufficient conformance evidence for this mandatory positive execution case. A defect in the runtime orchestration path could prevent an Episode from reaching `COMPLETED` while the adapter would still report PASS because the underlying transition table remained unchanged.

Remediation rule:

- the TCK vector and Core requirements remain unchanged and authoritative;
- the reference adapter MUST execute the normal path through the actual reference runtime;
- PASS requires runtime-produced ordered `Episode.transition_records` to match the TCK vector exactly and the actual terminal state to match `expect.terminalState`;
- malformed TCK expectation shape remains a runner/adapter error rather than a protocol FAIL;
- an implementation that executes but terminates on a different legal path must report FAIL;
- runtime resources MUST be released after observation, including FAIL outcomes;
- regression coverage MUST prove that an implementation with an unchanged transition table but a deliberately aborting verification pipeline cannot PASS the normal-path case.

The current remediation candidate reuses the existing `_run_to_completion()` runtime path, compares canonical Episode transition records and terminal state against the case document, and adds a deliberately aborting runtime test double. It does not modify the normative Core specification, requirement index, schemas, TCK case data, lifecycle transition relation, or conformance report semantics.

## TCK adapter audit notes

The runner contract requires mandatory and mixed cases to execute and forbids implementation gaps from being represented as `SKIP`. An adapter translates TCK actions into implementation-specific calls and observations; it does not gain authority to replace an execution assertion with a weaker implementation-internal proxy.

Static relation inspection remains appropriate evidence where a case explicitly tests the implementation's supported state projection or transition relation. RRA-009 is intentionally narrower: the mandatory normal-path positive case declares acceptance and a terminal execution result, so its reference probe must observe execution rather than only the relation that execution is expected to use.

`TCKRunner.for_reference()` continues to consume only runtime implementation identity from discovery. Selected profiles and declared conditional capabilities remain explicit runner inputs. No new conditional capability is advertised by this remediation.

The CI package job must continue installing the built wheel into clean consumer/conformance environments and execute every registered TCK profile on the exact remediation head.

## Remaining scope

After RRA-009 is resolved on `main`, continue independently for:

- whether other mandatory positive TCK cases rely on implementation-internal proxies where their case semantics require observable execution;
- any remaining bundled-component identity semantics where evidence demonstrates an actual release-identity defect, without assuming resource/API/component versions must equal the distribution version;
- implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path;
- final Reference Runtime Alignment acceptance before any separate stable `v0.3.0` release decision.

Reference Runtime Alignment is not yet READY. This audit does not authorize stable `v0.3.0`, publication of `v0.3.0-rc.2`, package-index publication, or merge of its own remediation PR.
