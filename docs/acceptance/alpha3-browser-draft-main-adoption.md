# Alpha 3 Browser Resource Draft Main-Adoption Reconciliation

Status: **MAIN ADOPTED — DRAFT BASELINE CLOSED**

Main baseline: `8f0c37e34202066ed79f8aa420a9939dd79cc5d1`

## Purpose

This document reconciles repository governance after PR #100 adopted the reviewed
AEP-0011 Browser Resource Profile v0.1 Draft problem/scope and standards-analysis
baseline into `main`.

This is an adoption-evidence record only. It does not advance AEP-0011 beyond
`Draft`, close BR-BR-001..BR-BR-010, create Browser Resource normative semantics,
or authorize a Playwright implementation.

## Adopted work unit

PR #100: `docs(alpha3): draft browser resource profile`

Reviewed exact PR head:

`54ed3f132b4e681362271470d758a58c620a2d07`

Squash merge commit on `main`:

`8f0c37e34202066ed79f8aa420a9939dd79cc5d1`

The adopted source slice contains exactly:

- `rfcs/AEP-0011-browser-resource-profile.md`;
- the Browser Resource sequencing update in `ROADMAP.md`.

No runtime source, Browser normative specification, requirement index, schema,
TCK, release-development state, packaging metadata, or workflow definition was
introduced by PR #100.

## Review evidence

Formal exact-head review `5045672174` was anchored to
`54ed3f132b4e681362271470d758a58c620a2d07` and concluded:

- the AEP-0011 problem/scope + standards-analysis baseline was review-closed for
  that PR scope;
- PR #100 was Ready eligible;
- AEP-0011 remained explicitly **not Proposed-ready**;
- BR-BR-001..BR-BR-010 remained intentionally open;
- no Browser Spec/Schema/TCK, Playwright implementation, AEP lifecycle advance,
  release selection/publication, signing, or attestation was authorized.

The Ready transition preserved the exact head. Ready-state Governance #687
(run `33116629995`) completed successfully on that same head.

## Exact-head pre-merge gates

At reviewed PR head `54ed3f132b4e681362271470d758a58c620a2d07`:

- CI #621 / run `33110630228` — **SUCCESS**;
- Governance #686 / run `33110630221` — **SUCCESS**;
- Release Validation #94 / run `33110630251` — **SUCCESS**;
- Relational Parity #14 / run `33110630259` — **SUCCESS**;
- Ready-state Governance #687 / run `33116629995` — **SUCCESS**.

CI included Python 3.11/3.12/3.13 quality, reproducible package construction,
clean-consumer base-wheel installation, installed-wheel identity and smoke,
installed-wheel full registered TCK conformance, release-evidence verification,
and the real PostgreSQL/MySQL regression lanes. Relational Parity executed both
real PostgreSQL/MySQL canonical-parity matrix pairs.

## Exact-main post-merge gates

The authorized squash merge produced exact `main` commit:

`8f0c37e34202066ed79f8aa420a9939dd79cc5d1`

The GitHub merge commit is signature-verified and has parent
`5ba444e79e7a58a9aa4a7f777c00f1ccdb4b8fb1`.

Exact-main push validation completed successfully:

- CI #622 / run `33116957396` — **SUCCESS**;
- Relational Parity #15 / run `33116957406` — **SUCCESS**.

CI #622 executed all eight expected lanes successfully:

- Quality / Python 3.11;
- Quality / Python 3.12;
- Quality / Python 3.13;
- Package / Python 3.13;
- PostgreSQL 17.11 / Relational TCK;
- PostgreSQL 18.6 / Relational TCK;
- MySQL 8.4.11 / Relational TCK;
- MySQL 9.7.2 / Relational TCK.

The Package lane completed reproducible source/wheel construction, clean
unconstrained consumer installation, installed-wheel identity/smoke,
installed-wheel full registered TCK conformance, and release-evidence
build/verification.

Relational Parity #15 executed both real database pairs successfully:

- PostgreSQL 17.11 + MySQL 8.4.11;
- PostgreSQL 18.6 + MySQL 9.7.2.

This evidence closes the PR #100 main-adoption work unit; it does not create
Browser Resource conformance evidence because Browser Spec/Schema/TCK do not yet
exist.

## Governance interpretation

The first Browser Resource ROADMAP item may now be marked complete because its
precise acceptance condition was adoption of the reviewed AEP-0011 Draft
problem/scope and standards-analysis baseline into `main` with exact-main
validation.

The next ROADMAP item remains:

`browser portability and Proposed-readiness audit`

That audit must independently evaluate BR-BR-001..BR-BR-010 and may narrow,
split, or reject Draft design directions. It must not treat this main-adopted
Draft as accepted normative semantics.

## Open-source implementation-quality boundary

Although PR #100 introduced no runtime code, the downstream Browser Resource work
must preserve an implementation architecture suitable for an independently
maintained open-source project. In particular, future implementation work must
not collapse protocol semantics, TCK orchestration, privileged fixture control,
and Playwright/browser-engine mechanics into one package or one adapter class.

The expected dependency direction remains one-way:

```text
AEP / normative Browser contract
        -> schema / canonical resources
        -> language-neutral TCK
        -> backend-neutral browser conformance harness
        -> Playwright reference adapter
        -> browser-engine-specific private mechanics
```

Future code review should reject:

- Playwright-shaped public protocol objects generalized after implementation;
- browser-engine branches inside portable TCK semantics;
- a generic catch-all `BrowserAdapter` with unrelated lifecycle, state codec,
  fixture mutation, page automation, and evidence capture responsibilities;
- privileged fixture/admin capabilities exposed to Subject-visible APIs;
- direct driver/native handles as portable identity;
- unconditional Playwright/browser binaries in the base package without a
  separately reviewed dependency/packaging decision;
- tests that pass from metadata declarations without executing real browser
  behavior;
- transitional compatibility layers for APIs that have never been released.

Exact package names and directories are intentionally deferred until the
portability/readiness audit determines the authoritative Browser Resource
surfaces. Directory structure must follow reviewed responsibilities; it must not
pre-commit protocol semantics by code layout.

## Lifecycle and release boundary

After this reconciliation:

- AEP-0011 remains **Draft**;
- BR-BR-001..BR-BR-010 remain open;
- AEP-0009 remains **Accepted, not Final**;
- AEP-0010 remains **Accepted, not Final**;
- release provenance remains `development` with source version `0.3.1.dev0`;
- the currently planned `0.3.1` release is not selected for Browser Resource
  publication by this work;
- no tag, GitHub Release, package-index publication, signing, or attestation is
  authorized.

## Acceptance conclusion

**MAIN ADOPTED — DRAFT BASELINE CLOSED.**

PR #100 is fully closed at exact main
`8f0c37e34202066ed79f8aa420a9939dd79cc5d1`.

The next separately governed work unit is the Browser Resource portability and
Proposed-readiness audit. This document does not authorize its outcome, AEP-0011
lifecycle advancement, or any Browser runtime implementation.
