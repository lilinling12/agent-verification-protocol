# AVP Governance

This document defines how the Agent Verification Protocol (AVP) repository makes technical and project decisions. AVP is currently an experimental open-source protocol project; this governance model is intentionally lightweight enough for the current maintainer count while establishing rules that can scale.

## Principles

AVP governance is guided by:

- **vendor neutrality** — protocol semantics must not privilege one model, runtime, cloud, or framework;
- **observable verification** — conformance depends on observable behavior, state, evidence, and explicit contracts, not private chain-of-thought;
- **upstream ownership** — AVP does not redefine concerns already owned by standards such as MCP, A2A, OpenTelemetry, JSON Schema, or OCI without a documented interoperability gap;
- **evidence before preference** — normative changes require motivating cases, tradeoffs, and conformance evidence;
- **secure evaluator boundaries** — changes must preserve separation among Subject, Environment, Evaluator, and privileged verification capabilities;
- **reviewable evolution** — protocol changes are versioned, documented, tested, and attributable to a proposal or pull request.

## Roles

Roles are responsibilities, not permanent titles. One person may hold multiple roles while the project is small.

### Contributor

Anyone who reports an issue, proposes protocol semantics, improves documentation, adds tests, or submits code.

### Maintainer

A contributor trusted to review and merge changes in one or more repository areas. Maintainers are expected to enforce project quality and conflict-of-interest rules even on their own proposals.

### Protocol maintainer

A maintainer responsible for consistency of normative AVP semantics, schemas, conformance requirements, and AEP decisions.

### Release manager

A maintainer responsible for release readiness, version selection, release notes, tags, and release artifact verification.

### Security maintainer

A maintainer responsible for private vulnerability triage and coordinated remediation. Security-sensitive changes may receive restricted review before public disclosure.

## Decision process

Routine, non-normative changes are decided through normal pull-request review.

A change requires the protocol proposal/AEP path when it introduces or removes a normative requirement, changes observable verification semantics, changes a conformance requirement, creates an incompatible schema/API contract, or materially changes a trust boundary.

A normative decision must have:

1. a written problem statement and scope;
2. documented alternatives and compatibility impact;
3. security analysis;
4. conformance or test strategy;
5. recorded maintainer decision in the proposal/PR history.

The project prefers consensus. When consensus is not possible, the protocol maintainer records the decision and rationale. As the maintainer group grows, repository rulesets may require multiple non-author approvals for normative areas; the repository settings policy documents the current enforcement target.

## AEP lifecycle

AVP Enhancement Proposals use these states:

- `Draft` — active design work; not normative;
- `Proposed` — sufficiently complete for protocol review;
- `Accepted` — approved direction; implementation may proceed;
- `Final` — normative text and required conformance coverage are merged and released;
- `Rejected` — reviewed and not accepted, with rationale preserved;
- `Withdrawn` — withdrawn by its authors;
- `Superseded` — replaced by a later AEP.

An implementation merged before an AEP becomes Final is reference behavior, not automatically a protocol requirement.

## Maintainer changes

New maintainers are nominated by an existing maintainer based on sustained, high-quality contribution and demonstrated understanding of AVP's protocol and trust boundaries. The nomination and decision are recorded publicly unless security/privacy concerns require otherwise.

Maintainers may step down voluntarily. Maintainer access may be removed for prolonged inactivity, repeated disregard of project policy, or security/conduct reasons. Changes to maintainer access must be documented.

## Governance changes

Changes to this file use `chore(governance): ...` or `docs(governance): ...`, require an explicit rationale, and must not be bundled with unrelated protocol changes.
