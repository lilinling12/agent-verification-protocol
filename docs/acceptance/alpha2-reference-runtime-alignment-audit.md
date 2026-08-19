# Alpha 2 Reference Runtime Alignment Audit

Status: **READY — REFERENCE RUNTIME ALIGNMENT CLOSED**

Audit baseline: `main@d122ae6820bfacece1749509b35842cb33069f03`

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

Status: **RESOLVED**

`AVP-TCK-LIFECYCLE-NORMAL-001` is a mandatory Core case for AVP-CORE-001, AVP-CORE-008, and AVP-CORE-009. Before remediation, the reference adapter checked only whether the implementation transition relation allowed the TCK vector and could therefore report PASS without executing an Episode.

PR #63 changed the probe to execute the actual `ReferenceRuntime` normal path, observe canonical `Episode.transition_records`, require an exact match with the authoritative TCK vector, and require the actual terminal state to match `expect.terminalState`. A negative regression runtime preserves the same transition relation but deliberately terminates verification as `ABORTED`; the mandatory normal-path case now reports FAIL for that implementation instead of passing from table inspection alone.

The remediation did not change normative Core requirements, requirement indexes, schemas, TCK case data, lifecycle transition semantics, capability declarations, or conformance-report semantics.

Exact-head CI #446 (`32210596018`) passed Python 3.11/3.12/3.13 Quality, reproducible package construction, clean installed-wheel identity/smoke, installed-wheel full registered TCK conformance, and release-evidence build/verification. Governance #481 (`32210596117`), Ready Governance #482 (`32210691048`), and Release Validation #16 (`32210596244`) also passed. Release Validation re-verified the immutable published `v0.3.0-rc.1` bytes, installed-wheel identity, and full TCK independently of the post-RC source tree. PR #63 was explicitly authorized and squash-merged as `d122ae6820bfacece1749509b35842cb33069f03`.

## Final cross-profile adapter review

After RRA-009 merged, the remaining registered reference adapters were re-reviewed for the same class of false-positive conformance evidence.

- **Core:** execution-sensitive normal path, transition records, QUIESCING, and replay probes exercise runtime behavior; state-projection/transition-matrix/illegal/terminal probes intentionally inspect the implementation lifecycle relation because those cases assert relation semantics rather than orchestration completion.
- **Environment:** mandatory cases invoke real reference adapter lifecycle, reset/time, observation, projection, snapshot/restore, semantic diff, and fault APIs.
- **Evidence:** mandatory cases invoke real ArtifactStore/Evidence identity, representation, integrity, and immutability behavior; controlled corruption exists only as a negative test fixture.
- **Oracle:** runtime-sensitive cases execute `ReferenceRuntime` with a deterministic OracleRunner seam and observe request scope, failure classification, Evidence integrity, and immutable evaluation records. Value-object construction is used only where the case directly asserts identity binding of those protocol objects.
- **Scenario:** mandatory cases execute the real compiler, identity verifier, immutable ScenarioInstance projection, and reference resolver paths.
- **MCP:** mandatory cases invoke the real verification gateway and transport boundary, including pre-side-effect denial, schema drift, call binding, result/error separation, upstream failure, and unsupported-feature fail-closed behavior.
- **Subject:** mandatory cases invoke real Subject Adapter lifecycle, projection, budget, capability mediation, outcome/result validation, and assurance-description behavior.
- **Security:** mandatory cases exercise Subject/Evaluator capability separation, deny-before-side-effect behavior, managed credential context, hidden material, future-fault secrecy, and an explicit machine-readable `SecurityAssurance` resource. The assurance declaration is not required by the normative contract to be embedded in runtime discovery; adding such a binding would invent implementation semantics rather than improve conformance evidence.
- **OpenTelemetry:** mandatory cases exercise the real telemetry bridge/session mapping, correlation, outcome preservation, propagation, data minimization, completeness, and Evidence binding.
- **Artifact Trust:** mandatory trust cases exercise real reference Artifact/attestation verifier/policy/publisher boundaries with a deterministic reference-only authenticated-envelope fixture. The optional privileged publication case remains conditional and is skipped unless `artifact-attestation-publication` is explicitly declared.

No additional implementation-alignment defect meeting the RRA blocker threshold was found in this review. In particular, the review did not mass-normalize component/resource/protocol versions to the distribution version where those identifiers have independent semantics.

## TCK and package gate review

`TCKRunner` fails closed when a registered case lacks an implementation adapter, validates result identity, builds a `ConformanceReport`, and validates that report before returning a conformance result.

The Package CI gate enumerates `conformance/tck/profiles/*.yaml` and executes every registered profile against the freshly built wheel in a clean conformance environment. This is intentionally not a hard-coded profile allowlist. The gate therefore continues to detect adapter coverage gaps or package-only drift as profiles evolve.

Conditional capability behavior remains unchanged:

- Core pause: `pause-capability-advertised` is not declared by the default reference runner because there is no reviewed public pause API claim.
- Artifact Trust privileged publication: `artifact-attestation-publication` is not declared by the default reference runner because the base reference runtime does not claim production publication authority.

Those conditional cases may validly report `SKIP`; mandatory or mixed cases may not use missing implementation support as a skip reason.

## Acceptance conclusion

**READY — REFERENCE RUNTIME ALIGNMENT CLOSED.**

RRA-001 through RRA-009 are resolved. The final cross-profile review found no additional evidence-backed implementation-alignment blocker. The governed authority chain remains one-way:

`Normative Spec -> Schema -> TCK -> Reference Runtime`

This acceptance closes the Alpha 2 reference-runtime implementation alignment audit only. It does **not**:

- publish or authorize `v0.3.0-rc.2`;
- publish or authorize stable `v0.3.0`;
- authorize package-index publication;
- claim implementation support for optional signed/attested Artifact publication that remains intentionally unclaimed;
- make Python reference behavior normative;
- authorize Alpha 3 work by itself.

Any future source or conformance change that alters an accepted premise of this audit must be evaluated under the repository's normal governance and exact-head validation rules.