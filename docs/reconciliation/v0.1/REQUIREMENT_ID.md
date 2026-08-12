# AVP Requirement ID Convention

Every normative AVP requirement receives a stable identifier.

Format:

```text
AVP-{DOMAIN}-{NUMBER}
```

Examples:

```text
AVP-CORE-001
AVP-EVIDENCE-001
AVP-ORACLE-001
AVP-SECURITY-001
AVP-EXT-001
```

## Rules

- IDs are never reused after publication.
- Text changes that preserve semantics keep the ID.
- Semantic breaking changes require a new versioning decision.
- Informative text does not receive normative requirement IDs.
- TCK cases reference requirement IDs, not document line numbers.
