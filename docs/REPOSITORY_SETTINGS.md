# Repository Settings Policy

This document records the GitHub repository settings AVP expects administrators to enforce. Keeping the target policy in version control makes configuration reviewable even though GitHub rulesets themselves are repository settings.

## `main` branch ruleset

Target the default branch and keep enforcement **Active**.

Required controls:

- require a pull request before merging;
- require all configured status checks to pass;
- require the branch to be up to date when the ruleset has stable required checks;
- block branch deletion;
- block non-fast-forward direct updates unless an explicit emergency bypass applies;
- require conversation resolution before merge;
- require linear history when compatible with the selected merge strategy;
- prevent force pushes to `main`;
- do not allow public release tags to be moved or deleted.

Recommended required checks once this governance change is merged:

```text
Governance / Metadata
CI / Quality / Python 3.11
CI / Quality / Python 3.12
CI / Quality / Python 3.13
CI / Package / Python 3.13
```

Use the actual check names reported by GitHub when configuring the ruleset; GitHub status-check names are an external configuration surface and should be verified after workflow changes.

## Review policy while the maintainer group is small

A one-maintainer project cannot honestly enforce a non-author approval on every maintainer-authored PR without creating a permanent deadlock. During this phase:

- PR + CI is mandatory for normal changes;
- CODEOWNERS provides ownership visibility and future review routing;
- the maintainer should not bypass failing required checks;
- protocol/security changes should remain Draft until the review evidence is sufficient;
- external review is encouraged for normative changes.

When AVP has at least two active maintainers, update the ruleset to require at least one non-author approval, dismiss stale approvals after material changes, and require code-owner review for normative/security-sensitive paths.

## Ruleset bypass

Keep bypass permissions minimal. Emergency bypass is only for repository recovery or an actively exploited security incident when the normal path cannot operate. A bypassed change must receive a follow-up PR or issue documenting why the bypass occurred and adding missing tests/review evidence.

## Actions policy

- workflows use minimum `GITHUB_TOKEN` permissions;
- third-party actions are pinned to full commit SHAs;
- dependency updates for GitHub Actions are managed by Dependabot;
- untrusted pull-request data is passed through environment variables rather than interpolated into shell source;
- workflows do not expose repository secrets to untrusted fork PRs.

GitHub rulesets are preferred over undocumented maintainer convention because they are visible/auditable and can layer with other protections.
