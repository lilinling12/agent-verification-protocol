# AEP-0002 — Security Boundary Contract v0.1

- Status: Final
- Authors: AVP maintainers
- Created: 2026-08-13
- Accepted: 2026-08-16
- Acceptance decision: Approved by the protocol maintainer during the Alpha 2 readiness review. This approves the protocol direction only; the AEP is not Final and this decision does not authorize merge, tag, or release.
- Finalized: 2026-08-17
- Final decision: Explicitly approved by the protocol maintainer for `Accepted` → `Final` on 2026-08-17, based on the merged Alpha 2 Final-eligibility audit and released evidence at `v0.3.0-rc.1` / `ef199124017b0dcc8c4a966d00c4f407760f9a06`; the published release bytes passed external-consumer and full TCK validation, no post-release protocol-semantic drift invalidated that evidence, and this Finalization does not authorize stable `v0.3.0` publication.
- Target AVP version: 0.1

## Problem

AVP separates an untrusted Subject Agent Plane from privileged Evaluator and Control Planes. The historical threat model identifies evaluator credentials, hidden state, Oracle logic, benchmark holdout data, snapshots, production traces, and artifact registry identity as protected assets.

The existing reference runtime demonstrates API-plane separation through a narrow Subject gateway. It must not claim hardened process, network, tenant, or sandbox isolation from an in-process implementation.

## Motivation / interoperability case

Independent AVP implementations need a shared security vocabulary for observable verification boundaries:

- what capabilities a Subject may receive;
- what privileged evaluator material must never cross the boundary;
- what a conformance result actually proves.

This AEP standardizes observable security semantics rather than one sandbox technology.

## Existing standards analysis

AVP does not define operating-system sandbox primitives, network policy engines, container formats, secret managers, or identity protocols. Deployments MAY use containers, microVMs, WebAssembly, isolated services, OAuth/OIDC, mTLS, or other mechanisms.

The protocol requirement is the resulting trust boundary.

## Proposed semantics

### AVP-SECURITY-001 Plane separation

A conforming implementation MUST represent Subject Agent capabilities separately from privileged Evaluator capabilities. Subject execution MUST NOT receive unrestricted evaluator interfaces.

### AVP-SECURITY-002 Capability fail-closed

A Subject invocation MUST fail closed when requesting a capability not granted by the Scenario capability projection. Hidden evaluator APIs MUST NOT become discoverable Subject capabilities.

### AVP-SECURITY-003 Credential separation

Evaluator credentials, signing material, Oracle secrets, and private benchmark secrets MUST NOT be inherited by the Subject execution context.

### AVP-SECURITY-004 Hidden material protection

Hidden evaluator artifacts, answer keys, private fixtures, and non-declared snapshots MUST NOT be exposed through Subject observation, tool results, or public artifact references.

### AVP-SECURITY-005 Fault secrecy

Future fault schedules and inactive evaluator-only perturbation metadata MUST remain unavailable to the Subject until the Scenario explicitly makes an activation observable.

### AVP-SECURITY-006 Assurance honesty

A Security conformance result MUST identify the isolation layer it proves. API capability separation MUST NOT be represented as process, network, tenant, or sandbox isolation.

## Protocol/schema changes

This AEP introduces the AVP Security profile contract, `SecurityAssurance` schema, requirement index, and TCK mapping. It intentionally does not introduce a generic security token schema, sandbox API, or deployment-isolation mechanism.

## Security considerations

This AEP defines the security boundary. Implementations remain responsible for selecting appropriate deployment isolation for their threat model.

## Conformance tests

The mandatory `avp-security-v0.1` TCK maps one executable case to each normative requirement:

- `AVP-TCK-SECURITY-CAPABILITY-SEPARATION-001` verifies that the Subject capability surface excludes privileged Evaluator and Control operations (`AVP-SECURITY-001`).
- `AVP-TCK-SECURITY-CAPABILITY-DENY-001` verifies deny-before-side-effect behavior for an undeclared Subject capability while preserving an allowed control capability (`AVP-SECURITY-002`).
- `AVP-TCK-SECURITY-CREDENTIAL-CONTEXT-001` verifies that evaluator-only environment credentials are absent from an AVP-managed Subject child context while an explicitly allowlisted public value remains available (`AVP-SECURITY-003`).
- `AVP-TCK-SECURITY-HIDDEN-MATERIAL-001` verifies that evaluator-only Scenario material and a hidden sentinel are absent from Subject projection and runtime-observable Subject inputs (`AVP-SECURITY-004`).
- `AVP-TCK-SECURITY-FAULT-SECRECY-001` verifies that a future hidden fault remains unavailable before its configured occurrence and only its observable effect activates when due (`AVP-SECURITY-005`).
- `AVP-TCK-SECURITY-ASSURANCE-HONESTY-001` validates the machine-readable baseline `SecurityAssurance` declaration and verifies that the base `ReferenceRuntime` does not advertise full Security profile conformance (`AVP-SECURITY-006`).

Passing these cases demonstrates the baseline Security profile semantics only. It does not by itself demonstrate process, network, tenant, filesystem, or hardened sandbox isolation.

## Reference implementation

The Python reference implementation provides separate witnesses for API-capability enforcement, managed credential-context separation, hidden-material projection boundaries, future-fault secrecy, and assurance declaration validation. The base `ReferenceRuntime` remains an in-process reference runtime and does not claim hardened multi-tenant sandbox security.

## Alternatives

### Standardize one sandbox technology

Rejected. AVP requires interoperable semantics, not one deployment mechanism.

### Treat API separation as full sandbox isolation

Rejected. This would create false security claims.
