# Alpha 2 Stable v0.3.0 Published Release Acceptance

Status: **PASS — PUBLISHED AND EXTERNALLY ACCEPTED**

Release under test:

- GitHub tag: `v0.3.0`
- Exact source commit: `7be045f47f59b259b32865be8b30005e4caa40f6`
- Distribution: `avp-reference==0.3.0`
- Release class: stable
- GitHub Release: published, non-prerelease, Latest
- Exact-main CI: run `32435703455` / CI #475 — SUCCESS
- Published-release acceptance: run `32442504868` / Release Validation #32 — SUCCESS

## Purpose

This audit records the stable Alpha 2 publication and distinguishes the exact-main pre-publication gate from validation of the bytes actually published through the GitHub Release.

## Pre-publication evidence

The selected stable source `7be045f47f59b259b32865be8b30005e4caa40f6` passed push-triggered `main` CI #475 (`32435703455`). The package gate covered reproducible wheel/sdist bytes, built-wheel metadata validation, unconstrained clean-consumer installation, installed distribution identity, the complete registered TCK profile set, and exact-commit release-evidence generation and verification.

The authoritative release-evidence artifact was named `avp-release-evidence-7be045f47f59b259b32865be8b30005e4caa40f6` and was bound to that exact source SHA.

The accepted release-evidence byte digests were:

- wheel `avp_reference-0.3.0-py3-none-any.whl`: `62238e30efb669e0b42abe2c6800a427697605424d87ba07dab495cae82762f9`;
- sdist `avp_reference-0.3.0.tar.gz`: `e8bd4ddb6ac7ca1ff689bd446f232ed1e1f9e8195f794c9233afeebeea46166c`;
- `MANIFEST.json`: `de66511a4004c00eb65ecf44106a8927e70393d5197f39b44e7f4490d9167622`.

## Published release evidence

After explicit maintainer authorization, `v0.3.0` was published as a non-prerelease GitHub Release and marked Latest. The lightweight tag resolves directly to exact commit `7be045f47f59b259b32865be8b30005e4caa40f6`.

The release contains exactly four authoritative assets:

- `avp_reference-0.3.0-py3-none-any.whl`
- `avp_reference-0.3.0.tar.gz`
- `MANIFEST.json`
- `SHA256SUMS`

The repository-owned published-release validator accepted the public release as stable and verified the public asset set, GitHub asset digests/sizes, manifest source identity, distribution identity, manifest artifact records, and checksum file against the downloaded bytes.

## External-consumer acceptance

The governed Release Validation workflow was dispatched with:

- tag `v0.3.0`;
- commit `7be045f47f59b259b32865be8b30005e4caa40f6`;
- version `0.3.0`;
- release class `stable`.

Release Validation #32 (`32442504868`) completed successfully. Its external-consumer job:

1. validated the requested stable release identity;
2. checked out the exact published source;
3. unit-tested the published-release validator/workflow contract;
4. downloaded and verified the public release bytes;
5. installed the published base wheel in a clean consumer environment;
6. verified installed wheel identity and smoke behavior;
7. installed the published wheel conformance environment; and
8. passed the complete registered TCK profile set from the exact published source.

## Post-release transition

Because `0.3.0` is now an immutable published identity, materially different source bytes must not continue to use that version. The governed post-release transition therefore:

1. appends stable `0.3.0` to `docs/releases/published-releases.json` without rewriting RC1 or RC2;
2. advances `latestPublished` to stable `0.3.0`;
3. returns the repository to `development` mode;
4. uses `0.3.1.dev0` as a distinct unreleased maintenance-development identity;
5. records `0.3.1` / `v0.3.1` as the next release-management boundary required by the validator, without selecting or authorizing that release.

This maintenance-development lane is deliberately narrower than Alpha 3. It does not authorize Alpha 3 Environment Fabric work, a `0.4.0` line, PyPI/package-index publication, signing/attestation, or any protocol/spec/schema/TCK semantic change.

## Final assessment

**PASS — PUBLISHED AND EXTERNALLY ACCEPTED**

Stable `v0.3.0` is the published Alpha 2 conformance baseline at exact source `7be045f47f59b259b32865be8b30005e4caa40f6`.
