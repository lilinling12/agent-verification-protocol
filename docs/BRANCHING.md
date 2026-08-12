# Branching and Pull-Request Strategy

AVP uses one permanent branch and short-lived topic branches. The model is designed for a long-lived open protocol: reviewable changes, auditable protocol evolution, and minimal long-term branch drift.

## Permanent branch

`main` is the only permanent branch. It must remain releasable and is protected by pull-request and CI policy. AVP does not use a permanent `develop`, `develop/alpha`, or per-release development branch.

Release branches are temporary stabilization branches only when a release cannot be prepared directly from `main`.

## Topic branch names

Repository-owned branches use one of:

```text
feat/<description>
fix/<description>
refactor/<description>
perf/<description>
test/<description>
docs/<description>
build/<description>
ci/<description>
chore/<description>
security/<description>
hotfix/<description>
release/v<major>.<minor>.<patch>[-<prerelease>]
```

Descriptions are lowercase kebab-case. Branches describe the change, never the developer or tool that created it. New `agent/*`, `codex/*`, personal-name, and generic `tmp/*` branches are not used.

Examples:

```text
feat/oracle-sandbox-runner
fix/runtime-invalid-transition
test/oracle-isolation-tck
docs/protocol-overview
chore/repository-governance
release/v0.3.0-rc.1
```

Fork-based external contributions are not required to rename their fork branch. Branch-name enforcement applies only when the PR head repository is this repository. Dependabot machine branches are also allowed.

## Commit messages

Use Conventional Commit form:

```text
<type>(<scope>): <imperative description>
```

Supported types are `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`, `security`, and `revert`.

Examples:

```text
feat(oracle): add isolated execution
fix(runtime): reject invalid transition
test(tck): cover schema drift
```

Commits should be internally coherent. Do not use commits named `update`, `changes`, `fix stuff`, or similar non-descriptive history.

## Pull requests

A PR should solve one coherent problem and include the smallest code, tests, schemas, documentation, and migration notes necessary to make that problem complete. PR titles follow Conventional Commit form and are treated as release-history input.

The preferred merge method for normal topic PRs is **squash merge**. The PR title becomes the durable commit summary; therefore the title must describe the resulting change, not the review process.

After merge, delete the topic branch. Do not continue development on a merged branch.

## Stacked pull requests

Stacked PRs are allowed when a large change has real dependency layers that can be reviewed independently.

For a stack `A → B → C`:

1. PR A targets the stable parent branch.
2. PR B targets A's head branch.
3. PR C targets B's head branch.
4. Dependent PRs remain Draft while their parent is unstable or materially changing.
5. Each PR describes its parent and downstream dependents in the PR template.
6. Merge strictly from the bottom of the dependency graph: A, then B, then C.
7. After a parent is squash-merged, retarget the child to the parent's target and rebase the child onto the new target so the child diff contains only its own change.
8. Use `--force-with-lease`, never an unconditional force push, when a rebase requires updating a reviewed branch.
9. A material rebase invalidates prior review assumptions; reviewers should re-check changed commits/diffs before approval.

The historical Alpha `agent/*` stack predates this policy and is grandfathered only until that stack is merged or closed. No new `agent/*` branches are created.

## Hotfixes

`hotfix/*` is reserved for urgent fixes against a released line. A hotfix still requires tests, CI, review/ruleset requirements, release notes, and a follow-up version tag. It is not a bypass around normal review.

## Repository rules

The intended GitHub ruleset for `main` is documented in `docs/REPOSITORY_SETTINGS.md`. Repository settings are enforcement; this file explains the policy and expected workflow.
