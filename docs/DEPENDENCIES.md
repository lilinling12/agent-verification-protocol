# Dependency Management Policy

AVP separates **consumer compatibility** from **repository reproducibility**.

## Consumer compatibility

`pyproject.toml` is the public installation contract for `avp-reference`.
Runtime and optional dependencies use a tested lower bound and an upper bound
that prevents an unreviewed breaking major version from entering downstream
installations. They are intentionally not pinned to one exact patch release.

The build backend is different: it is repository/build tooling rather than a
runtime dependency, so its version is pinned exactly to reduce source-build
variance.

## Repository reproducibility

`constraints/ci.txt` records the exact dependency resolution used by repository
quality jobs. CI installs the editable project with this constraints file on all
supported Python versions.

The constraints file is not a promise that every transitive package is part of
AVP's public API. It is an execution-environment identity input for tests and
TCK/reference-runtime validation.

If a dependency resolves differently on one supported Python version because of
an environment marker, split the constraints into version-specific files rather
than weakening an exact pin or hiding the difference.

## Downstream compatibility check

The package job deliberately installs the built wheel into a fresh virtual
environment **without** repository constraints. This verifies that the public
ranges in `pyproject.toml` remain independently installable.

Therefore AVP tests both questions:

1. Can maintainers reproduce the repository validation environment?
2. Can a downstream consumer install the published wheel from declared ranges?

Neither check replaces the other.

## Updating dependencies

Dependency updates must be isolated from unrelated protocol/runtime changes.
A dependency update should:

1. update the relevant compatibility bound only when support policy changes;
2. refresh exact CI constraints intentionally;
3. run the full Python matrix, TCK, package build, and clean-wheel smoke checks;
4. review security and behavioral impact, especially for JSON Schema,
   OpenTelemetry, HTTP boundary, and build-tool dependencies;
5. avoid combining unrelated major upgrades in one pull request.

Dependabot may propose updates, but a green resolver is not sufficient evidence
for merging: AVP's full quality/conformance gates remain authoritative.
