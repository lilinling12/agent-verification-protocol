# Alpha 2 RC1 Published Release Acceptance

Status: **IN VALIDATION**

Release under test:

- GitHub tag: `v0.3.0-rc.1`
- Exact source commit: `ef199124017b0dcc8c4a966d00c4f407760f9a06`
- Distribution: `avp-reference==0.3.0rc1`
- Release class: prerelease

## Purpose

This audit validates the public release object as consumed outside the build workspace. It is intentionally distinct from pre-publication CI evidence.

The acceptance question is not merely whether commit `ef199124...` once passed CI. The question is whether the bytes and metadata currently published under `v0.3.0-rc.1` remain bound to that exact verified source and continue to satisfy the same consumer/conformance gates when downloaded from the GitHub Release.

## Acceptance gates

The published release MUST satisfy all of the following:

1. `refs/tags/v0.3.0-rc.1` resolves directly to the exact release commit.
2. The GitHub Release is published (`draft=false`) and remains a prerelease (`prerelease=true`).
3. `target_commitish` equals the exact release commit, not a branch name or different revision.
4. The release contains exactly four authoritative assets:
   - `avp_reference-0.3.0rc1-py3-none-any.whl`
   - `avp_reference-0.3.0rc1.tar.gz`
   - `MANIFEST.json`
   - `SHA256SUMS`
5. Every downloaded asset matches GitHub's recorded SHA-256 digest and byte size.
6. `MANIFEST.json` uses `avp-release-evidence/v1` and binds the repository, exact commit, distribution name, version, filenames, sizes, and distribution digests.
7. `SHA256SUMS` exactly matches the downloaded wheel, sdist, and manifest bytes.
8. The published base wheel installs into a clean environment without repository constraints or editable-source access and passes `pip check`.
9. Installed distribution version, `avp_ref.__version__`, and ReferenceRuntime implementation identity all equal `0.3.0rc1`.
10. The published wheel passes the base reference conformance smoke command.
11. The same published wheel, installed with its non-normative `[conformance]` extra in a separate clean environment, passes every registered TCK profile.

## Fail-closed design

`scripts/validate_published_release.py` rejects release-object or asset ambiguity rather than trying to repair it. In particular it rejects:

- a tag that points to another commit or an annotated-tag object when direct commit binding is expected for this RC;
- draft/stable-class substitution;
- a release target that differs from the exact source commit;
- missing, duplicate, or extra release assets;
- missing GitHub SHA-256 asset digests;
- downloaded asset digest/size mismatches;
- manifest source/distribution substitution;
- manifest artifact metadata that does not match the downloaded bytes;
- checksum-file substitution.

The validator does not infer protocol correctness from GitHub metadata alone. Full conformance is re-executed from the downloaded wheel.

## Governance boundary

Passing this audit demonstrates that the public RC is internally consistent and consumable as the current Alpha 2 release candidate. It does **not** by itself:

- make the prerelease a stable conformance target;
- publish the package to PyPI or another package index;
- authorize `v0.3.0` stable release;
- transition AEP-0001 through AEP-0008 from `Accepted` to `Final`;
- authorize Alpha 3 implementation changes.

Any later stable-release or AEP lifecycle transition remains a separate governed decision.
