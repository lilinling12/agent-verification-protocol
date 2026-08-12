# Branching Strategy

## Goals

AVP uses a lightweight branch model suitable for a long-lived open protocol project.

The branch model optimizes for:

- reviewability
- traceable protocol evolution
- small merge units
- reproducible history

## Long-lived branches

### main

`main` is the only permanent development line.

It must always represent a buildable state.

Protected requirements:

- pull request only
- CI required
- review required for protocol changes

## Short-lived branches

Naming format:

```
<type>/<scope>-<description>
```

Examples:

```
feat/oracle-sandbox-runner
fix/runtime-validation
refactor/evidence-model
test/oracle-tck
docs/protocol-overview
chore/repository-governance
```

## Commit rules

Use conventional commits:

```
<type>(<scope>): description
```

Examples:

```
feat(oracle): add isolated execution
fix(runtime): reject invalid transition
```

## Pull request rules

A PR should:

- solve one coherent problem
- include tests
- explain architecture impact
- avoid unrelated formatting changes

Large protocol changes should be split into reviewable stacked PRs.

## Branch lifecycle

```
create branch
    |
implement
    |
CI + review
    |
merge
    |
delete branch
```

Merged branches should not continue development.
