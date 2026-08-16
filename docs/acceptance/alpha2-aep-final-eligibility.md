# Alpha 2 AEP Final Eligibility Audit

Status: **TECHNICAL EVIDENCE PASS — LIFECYCLE TRANSITION NOT YET AUTHORIZED**

Audit scope: AEP-0001 through AEP-0008  
Published release under evidence review: `v0.3.0-rc.1`  
Release source: `ef199124017b0dcc8c4a966d00c4f407760f9a06`

## Decision

The Alpha 2 AEP set has sufficient **technical finality evidence** to proceed to a separate lifecycle decision: the normative specifications, requirement indexes, applicable schemas, and required TCK profiles for AEP-0001 through AEP-0008 are present in the exact source commit published as `v0.3.0-rc.1`, and the corresponding profiles are registered in the released TCK registry.

The AEPs are **not yet eligible for an automatic `Accepted` → `Final` transition**.

This distinction is intentional. `GOVERNANCE.md` defines `Final` as normative text and required conformance coverage that are merged and released. `docs/RELEASE_PROCESS.md` separately states that a prerelease is not a stable conformance target unless its release notes explicitly say otherwise. The public `v0.3.0-rc.1` release is a prerelease and explicitly records that AEP-0001 through AEP-0008 remain `Accepted`, not `Final`.

Therefore the current lifecycle classification is:

```text
technicalFinalityEvidence = PASS
lifecycleEligibility       = REQUIRES_STABLE_FINALITY_DECISION
```

No interpretation of the generic word “released” may silently override the more specific prerelease/stability boundary or the explicit RC release statement.

## Evidence model

The audit deliberately separates four authorities:

1. **Current governance policy** — `GOVERNANCE.md` and `docs/RELEASE_PROCESS.md` on the audit branch/current main lineage.
2. **Published release object** — the live GitHub Release for `v0.3.0-rc.1`, including `draft`, `prerelease`, target commit, release body, and exact authoritative asset-name set.
3. **Immutable tag binding** — `refs/tags/v0.3.0-rc.1` must resolve directly to release commit `ef199124017b0dcc8c4a966d00c4f407760f9a06`.
4. **Released protocol tree** — a separate checkout of the exact release commit, used to prove that each AEP's normative/conformance artifacts existed in the material that was actually released rather than only on a later `main`.

`scripts/audit_aep_final_eligibility.py` fails closed if any authority changes unexpectedly. The dedicated `Finality Readiness` workflow executes the audit against the live GitHub release and the exact RC source checkout.

## Per-AEP technical evidence

| AEP | Normative authority in RC source | Required TCK profile | Technical evidence | Lifecycle eligibility |
| --- | --- | --- | --- | --- |
| AEP-0001 Oracle Evaluation | `spec/oracle/oracle-evaluation-contract.md`, requirement index, Oracle schema | `avp-oracle-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0002 Security Boundary | `spec/security/security-boundary-contract.md`, requirement index, assurance schema | `avp-security-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0003 Scenario / ScenarioInstance | `spec/scenario/scenario-contract.md`, requirement index, template/instance schemas | `avp-scenario-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0004 Environment | `spec/environment/environment-contract.md`, requirement index | `avp-environment-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0005 MCP Tools Interop | `spec/mcp/mcp-tools-interop-contract.md`, requirement index | `avp-mcp-interop-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0006 OpenTelemetry Mapping | `spec/opentelemetry/opentelemetry-mapping-contract.md`, requirement index | `avp-otel-mapping-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0007 Subject Adapter | `spec/subject/subject-adapter-contract.md`, requirement index | `avp-subject-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |
| AEP-0008 Artifact Trust / Attestation | `spec/trust/artifact-trust-attestation-contract.md`, requirement index, trust schemas | `avp-artifact-trust-v0.1` | PASS | REQUIRES_STABLE_FINALITY_DECISION |

The table is a human-readable summary. The machine audit owns the exact file mapping and rejects missing or unregistered artifacts.

## Already-established release evidence

This audit builds on, but does not replace, the earlier release gates:

- exact release-source CI passed before publication;
- the release evidence bundle binds wheel/sdist bytes to the exact source commit;
- the published-release acceptance re-downloads the public assets and verifies their digests, manifest, and checksum file;
- the public wheel installs in a clean consumer environment;
- the same published wheel passes the complete registered TCK profile set in an independent conformance environment;
- post-merge exact-main CI passed after the published-release acceptance machinery entered `main`.

The final-eligibility audit adds a different proof: it establishes that the AEP-specific normative and conformance authorities themselves were present in the released source tree.

## Fail-closed conditions

The audit fails rather than guessing if any of the following occurs:

- the release tag resolves to a different commit;
- the release target points to a different commit;
- the release changes from the expected prerelease classification;
- the authoritative release asset-name set changes;
- the release body no longer preserves the `Accepted`, not `Final` boundary;
- a current or released AEP has an unexpected lifecycle state;
- a required normative spec, requirement index, schema, or TCK profile is absent from the release source;
- a required TCK profile exists as a file but has no case registration in the released TCK registry;
- the governance definition of `Final` or the prerelease stability rule changes without review.

These conditions intentionally force a new governance review instead of allowing stale automation to bless a changed release model.

## Why this does not make the AEPs Final

A technical evidence result is not itself a lifecycle mutation. `Final` changes the protocol's governance status and downstream expectations. The current RC was explicitly published as a prerelease with AEP-0001 through AEP-0008 remaining `Accepted`.

A later transition therefore requires a separately recorded maintainer decision that resolves the stable/finality boundary. That decision may be coupled to a stable `v0.3.0` release plan, or may explicitly define another stable conformance target through the governance process. It must not be inferred from this audit PR or from the existence of an RC tag.

## Governance boundary

This audit does **not** authorize:

- changing any AEP status to `Final`;
- publishing `v0.3.0` or any other stable release;
- publishing `avp-reference` to PyPI or another package index;
- changing protocol semantics, schemas, requirement meaning, or TCK semantics;
- beginning Alpha 3 implementation work;
- merging the audit PR without the normal explicit maintainer authorization.

## Next governed decision

Once this audit is merged and exact-main gates remain green, the protocol maintainer may consider a separate **Alpha 2 Stable/Finality Decision**. That decision should explicitly answer:

1. which release is the stable conformance target for the v0.1 Alpha 2 protocol surface;
2. whether AEP-0001 through AEP-0008 transition together or require per-AEP exceptions;
3. whether any release-note or compatibility wording must change before stable publication;
4. whether stable release publication and AEP `Final` transition occur in one governed release sequence or as explicitly ordered steps.

Until that decision is recorded, all eight AEPs remain `Accepted`.
