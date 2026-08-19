# Alpha 2 RC2 Published Release Acceptance

Status: **PASS — SRD-003 RESOLVED**

Release under test:

- GitHub tag: `v0.3.0-rc.2`
- Exact source commit: `9cfbdb7f72b3418aa960100f33845249db73fbcf`
- Distribution: `avp-reference==0.3.0rc2`
- Release class: prerelease
- Exact-main CI: run `32236927283` / CI #461 — SUCCESS
- Published-release acceptance: run `32294651642` / Release Validation #26 — SUCCESS

## Purpose

This audit records the post-RC1 public-consumer evidence required by SRD-003. It distinguishes pre-publication exact-main CI from validation of the bytes actually published through the GitHub Release.

## Pre-publication evidence

The selected release source `9cfbdb7f72b3418aa960100f33845249db73fbcf` passed the push-triggered `main` CI run `32236927283` (CI #461). The package gate completed successfully, including reproducible wheel/sdist verification, built-wheel metadata validation, unconstrained clean-consumer installation, installed identity checks, the complete registered TCK profile set, and release-evidence build/verification/upload.

The resulting release-evidence artifact was named `avp-release-evidence-9cfbdb7f72b3418aa960100f33845249db73fbcf` and was bound to the same exact source SHA.

## Published release evidence

After explicit maintainer authorization, `v0.3.0-rc.2` was published as a GitHub prerelease bound directly to `9cfbdb7f72b3418aa960100f33845249db73fbcf` with exactly four authoritative assets:

- `avp_reference-0.3.0rc2-py3-none-any.whl`
- `avp_reference-0.3.0rc2.tar.gz`
- `MANIFEST.json`
- `SHA256SUMS`

The repository-owned published-release validator accepted the public object and all four downloaded assets against the exact tag/commit/version/class identity.

The governed `Release Validation` workflow was then dispatched with:

- tag `v0.3.0-rc.2`;
- commit `9cfbdb7f72b3418aa960100f33845249db73fbcf`;
- version `0.3.0rc2`;
- release class `prerelease`.

Release Validation #26 (`32294651642`) completed successfully. Its external-consumer job verified the exact published-source checkout, downloaded and verified the public release bytes, installed the published base wheel in a clean environment, verified installed distribution/runtime identity, installed the conformance extra in a separate clean environment, and passed the complete TCK profile set from the exact published source.

## SRD-003 disposition

**SRD-003 is resolved.**

The blocker required a public post-RC1 artifact to pass the external-consumer download/install/full-TCK acceptance path. `v0.3.0-rc.2` now provides that evidence at exact source commit `9cfbdb7f72b3418aa960100f33845249db73fbcf`.

This closure is release-management evidence only. It does not itself authorize stable `v0.3.0`, PyPI/package-index publication, Alpha 3, or any change to protocol/spec/schema/TCK semantics.

## Post-release transition

Because `0.3.0rc2` is now a published immutable identity, materially different source bytes must not continue to use that version. The governed post-release transition therefore:

1. appends RC2 to `docs/releases/published-releases.json` without rewriting RC1;
2. advances `latestPublished` to RC2;
3. returns the repository to `development` mode;
4. uses `0.3.0rc3.dev0` as an unreleased development identity satisfying `0.3.0rc2 < 0.3.0rc3.dev0 < 0.3.0`;
5. records stable `0.3.0` as the next release-management target without authorizing its selection or publication.

A fresh stable-release decision audit must evaluate the post-RC2 evidence after this transition is merged and green.
