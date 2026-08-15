# Alpha 2 Cross-Profile Security Composition Review

Status: **PASS on stacked audit baseline**

Audit baseline: `c37ea4746d960f46528a1cabcbd5d06ec302f277` plus the non-normative audit/release-note changes in PR #33.

This review checks whether the Alpha 2 contracts compose without creating conflicting authority, privilege escalation, misleading assurance, or failure-to-verdict collapse. It is an acceptance-audit artifact, not a new source of protocol semantics.

## 1. Authority map

| Concern | Normative owner | Required composition invariant |
|---|---|---|
| Episode lifecycle and terminal phase | Core lifecycle | Lifecycle state remains distinct from Task Verdict and Validity |
| Scenario visibility and actor capability projection | Scenario | Subject-visible material/capabilities derive from identity-bound Scenario semantics |
| Mutable verification state and observation | Environment | Environment retains authoritative mutable state; Subject receives actor-scoped observation only |
| Subject/Evaluator privilege boundary | Security | Undeclared capabilities fail closed before side effects; evaluator secrets remain outside Subject context |
| Runtime ↔ Agent execution boundary | Subject Adapter | Adapter mediates execution but does not become authority for Scenario, Security, Environment, MCP, OTel, Oracle, or Evidence |
| Tool protocol semantics when MCP is used | MCP | MCP remains wire/protocol authority; AVP capability/evidence checks do not replace MCP authorization semantics |
| Telemetry representation | OpenTelemetry / W3C + AVP mapping profile | Telemetry preserves correlation/outcomes but cannot become verdict or evidence authority by itself |
| Immutable verification bytes and Evidence identity | Evidence / Artifact | Exact-byte digest/size establish Artifact integrity; locator/metadata do not redefine identity |
| Evaluator verification result | Oracle | Oracle failure invalidates/inconclusively evaluates; it does not establish Subject task failure |
| Attestation authentication and evaluator trust acceptance | Artifact Trust | Authentication, exact Artifact subject binding, signer identity, and policy remain distinct from Artifact integrity |

No reviewed contract assigns the same authoritative decision to two incompatible owners.

## 2. Subject visibility and capability chain

The intended chain is:

```text
ScenarioInstance
  -> Subject projection / actor capability projection
  -> Security deny-by-default enforcement
  -> Subject Adapter controlled gateway
  -> Environment and/or MCP authorized operation
```

Composition findings:

1. Scenario excludes evaluator-only success criteria, hidden Oracle material, future faults, evaluator credentials, and other private verification state from the Subject projection.
2. Scenario capability projection is identity-bound to the materialized ScenarioInstance or equivalent compiled authorization policy.
3. Security requires undeclared capability requests through AVP-provided routes to fail before the side effect and forbids fallback to broader privileged interfaces.
4. Subject Adapter explicitly delegates authorization to Security and cannot manufacture stronger capabilities through its adapter API.
5. MCP profile independently requires an unauthorized tool call to fail before upstream `tools/call`; it does not claim to replace MCP OAuth or transport authorization.
6. Environment remains the owner of authoritative mutable state and exposes only actor-scoped Subject observations.

Result: **PASS**. No path reviewed permits an AVP adapter/profile to widen Subject authority merely because a downstream implementation exposes a broader API.

## 3. Hidden material and secret containment

Protected material is consistently treated as evaluator/control-private:

- Scenario projection excludes hidden evaluator material and credentials.
- Security forbids evaluator credentials, signing material, Oracle secrets, answer keys, and equivalent authentication material from entering Subject execution context.
- Environment observations must not disclose hidden grader/private security/future-fault material.
- Subject Adapter invocation/gateway must not disclose evaluator-only material.
- OpenTelemetry conformance does not require raw prompts, tool payloads, credentials, hidden Oracle material, or future fault schedules.
- Artifact Trust publication keeps private keys, signing credentials, and KMS authorization outside Subject context.

Result: **PASS**. Telemetry, Artifact locators, adapter metadata, and signing helpers do not create an alternate disclosure authority.

## 4. State, side effects, and verification ordering

Core, Environment, Subject, Security, and MCP preserve one compatible ordering model:

1. Environment owns the mutable resources.
2. Subject-initiated side effects occur only while permitted by lifecycle and capability policy.
3. Security/MCP must reject unauthorized side effects before upstream execution.
4. On entry to Core `QUIESCING`, no new Subject-requested side effect may be initiated.
5. Verification follows in `VERIFYING` against stabilized authorized Evidence/state.

Result: **PASS**. The reviewed contracts do not permit a profile to bypass the Core quiescing boundary or mutate authoritative Environment state through an evaluator-private shortcut.

## 5. Result and failure dimension separation

The reviewed contracts preserve distinct result dimensions instead of collapsing every failure into Agent failure:

- Core: lifecycle terminal state is not Task Verdict.
- Scenario: compilation/configuration failure is not Agent task failure.
- Subject Adapter: transport/protocol/timeout/budget failures remain distinct from successful Subject completion and task verdict.
- MCP: successful result, MCP tool execution error, and pre-result upstream/protocol/authorization failure remain distinguishable.
- OpenTelemetry: mappings must preserve AVP outcomes and cannot flatten failures into success.
- Oracle: Oracle execution failure produces invalid evaluation with `INCONCLUSIVE`, not task `FAIL`.
- Artifact Trust: integrity/authentication/subject/identity/policy failures remain machine-distinct trust outcomes.

Result: **PASS**. No reviewed Alpha 2 profile is allowed to infer task failure solely from infrastructure, verification, trust, or telemetry failure.

## 6. Evidence integrity versus Artifact Trust

Evidence and Artifact Trust remain deliberately layered:

```text
Artifact bytes
  -> exact-byte digest + size integrity (Evidence/Artifact)
  -> attestation bytes integrity (Evidence/Artifact)
  -> attestation authentication + authenticated type (Trust binding)
  -> exact target Artifact subject binding (Trust)
  -> authenticated signer identity (Trust)
  -> evaluator-selected policy acceptance (Trust)
```

Key invariants:

- signer, policy, certificate, transparency, predicate, and trust-result metadata do not change target Artifact digest;
- an integrity mismatch stops before attestation parsing/authentication;
- valid authentication for the wrong Artifact yields `subject-mismatch`;
- valid authentication from a disallowed signer remains `identity-rejected`;
- unauthenticated signer hints cannot establish identity;
- `accepted` does not imply transparency, revocation, timestamp, SLSA, or other unverified properties.

Result: **PASS**. Content integrity is neither weakened nor misrepresented as provenance/trust.

## 7. Telemetry and verdict authority

OpenTelemetry mapping is observational, not adjudicative:

- AVP mappings preserve Episode/event/tool correlation and material outcome differences;
- required telemetry completeness can affect evaluation validity only through the declared AVP lifecycle/validity composition;
- telemetry Evidence must use the AVP Evidence/Artifact integrity model;
- a backend, span status, or trace existence cannot override Environment/Oracle Evidence, lifecycle validity, or Task Verdict.

Result: **PASS**. Observability does not become a second Oracle.

## 8. Assurance honesty

Security, Subject Adapter, Environment, and Artifact Trust use compatible non-inflation rules:

- API capability isolation does not imply process/network/tenant/sandbox isolation;
- Environment conformance does not imply deployment isolation;
- in-process Subject Adapter cannot claim stronger containment merely because it exposes a narrow API;
- Artifact Trust publication is conditional, and same-process API privacy is not sufficient proof of signing-credential isolation;
- Trust verified properties are limited to properties actually established by authoritative evidence.

Result: **PASS**. No reviewed profile upgrades a weaker proof into a stronger assurance dimension.

## 9. External-standard ownership

The composition preserves upstream ownership:

- MCP owns MCP protocol/wire semantics and independent authorization mechanisms;
- OpenTelemetry/W3C owns telemetry/context propagation semantics;
- DSSE/in-toto/Sigstore/X.509/SLSA and deployment PKI/KMS mechanisms retain their own cryptographic/identity semantics;
- AVP standardizes only verification-specific bindings, policy outcomes, evidence relationships, and assurance honesty needed for interoperable verification.

Result: **PASS**. Alpha 2 does not introduce a conflicting AVP substitute for these upstream standards.

## 10. Review conclusion

No release-blocking cross-profile security contradiction was identified on the stacked Alpha 2 audit baseline.

This PASS closes the **cross-profile security composition** audit item only. It does not make Alpha 2 Ready for RC because separate governance/integration gates remain:

1. the Subject and Artifact Trust stack must be integrated into `main` using the authorized squash-merge sequence;
2. Proposed AEPs requiring acceptance before RC must receive explicit recorded governance decisions;
3. the final integrated `main` commit must pass required CI/Governance, clean built-wheel/conformance validation, drift checks, issue review, and review-thread checks.

Any semantic change introduced while resolving those gates invalidates the relevant portions of this review and requires re-audit.
