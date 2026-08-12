# Release Process

## Versioning

AVP follows semantic versioning.

Format:

```
MAJOR.MINOR.PATCH
```

## Meaning

### MAJOR

Breaking protocol changes.

Examples:

- incompatible schema changes
- changed verification semantics
- removed public interfaces

### MINOR

Backward-compatible capability additions.

Examples:

- new adapters
- new optional evidence types
- new TCK cases

### PATCH

Bug fixes and non-semantic improvements.

## Release requirements

A release requires:

- green CI
- updated changelog
- migration notes when required
- protocol documentation updates
- reproducible build verification

## Tags

Releases use annotated tags:

```
v0.1.0
v0.2.0
```
