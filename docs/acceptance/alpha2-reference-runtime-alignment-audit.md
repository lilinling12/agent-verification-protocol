# Alpha 2 Reference Runtime Alignment Audit

Status: **BLOCKED — RRA-008 POLICY CANDIDATE UNDER VALIDATION**

Audit baseline: `main@777e3ee50496863f5964257295f5b02ba4ac08db`

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
7. development and published distribution identities cannot ambiguously bind one public version to multiple source revisions;
8. no implementation correction changes normative spec, schemas, or TCK expectations merely to make the reference runtime pass.

## Findings

### RRA-001 — HTTP release identity drift

Status: **RESOLVED**

PR #54 bound the optional FastAPI application version to the distribution single source of truth and merged as `4376dde904d37910e57f4a9d1ccd1e94d05a4d3d6` only after its required gates passed. The authoritative merged commit for the HTTP remediation is `4376dde904d37925bf6cf2970922748629ca567c`.

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

Status: **BLOCKING — POLICY CANDIDATE UNDER VALIDATION**

PR #61 established the blocker on `main` as `777e3ee50496863f5964257295f5b02ba4ac08db`: published `v0.3.0-rc.1` / `avp-reference==0.3.0rc1` is immutable evidence for exact source `ef199124017b0dcc8c4a966d00c4f407760f9a06`, while later repository source must not continue producing different artifacts under that already-published version identity.

The policy candidate uses a PEP 440 development release of the next RC for unreleased repository artifacts:

```text
0.3.0rc1 < 0.3.0rc2.dev0 < 0.3.0rc2 < 0.3.0
```

Candidate implementation:

- `src/avp_ref/_version.py` becomes `0.3.0rc2.dev0`;
- `docs/releases/release-development-state.json` records the immutable latest published release, declared next RC, and active source version;
- `scripts/validate_release_development_state.py` fails closed on published-version reuse, non-canonical PEP 440 forms, source/state drift, tag/version drift, ordering violations, immutable RC1 anchor substitution, and source identities that are not development releases of the declared next RC;
- `tests/test_release_development_state.py` regression-tests the accepted ordering and representative invalid states;
- `scripts/quality.sh` runs the provenance validator before the broader test and conformance gates;
- `docs/RELEASE_PROCESS.md` defines the development identity separately from actual RC/stable publication authorization.

This candidate deliberately does **not** publish `v0.3.0-rc.2`, create or move a release tag, authorize stable `v0.3.0`, publish to a package index, or alter normative protocol/TCK semantics. `0.3.0rc2.dev0` means only "unreleased repository state after rc1 while stabilizing toward a possible rc2".

RRA-008 becomes RESOLVED only after this candidate is independently validated on its exact head and explicitly accepted through the normal PR governance/merge process. A subsequent public `rc2` remains a separate release decision.

## TCK adapter audit notes

The reference TCK architecture dispatches registered cases through domain adapters. Mandatory and mixed cases cannot be reported as `SKIP`; conditional cases require an explicit capability condition. Reviewed Core, Evidence, Subject, MCP, OpenTelemetry, Artifact Trust, Oracle, and replay paths exercise reference behavior rather than rewriting expected results into passes.

`TCKRunner.for_reference()` consumes only runtime implementation identity from discovery. Selected profiles and declared conditional capabilities remain explicit runner inputs, so RRA-008 changes distribution provenance only and does not alter protocol applicability or TCK semantics.

The CI package job must continue installing the built wheel into clean consumer/conformance environments and execute every registered TCK profile on the exact remediation head.

## Remaining scope

After RRA-008 is resolved on `main`, continue independently for:

- any remaining bundled-component identity semantics where evidence demonstrates an actual release-identity defect, without assuming resource/API/component versions must equal the distribution version;
- implementation-only convenience behavior, packaging/runtime boundaries, optional component wiring, and any mandatory normative requirement not genuinely exercised by the reference implementation path;
- final Reference Runtime Alignment acceptance before any separate stable `v0.3.0` release decision.

Reference Runtime Alignment is not yet READY. This audit does not authorize stable `v0.3.0`, publication of `v0.3.0-rc.2`, package-index publication, or merge of its own remediation PR.
