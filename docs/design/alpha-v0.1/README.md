# AVP Alpha v0.1 Design Baseline

This directory records the historical AVP design baseline produced before the current protocol-consolidation work.

The baseline is **historical and non-normative**. It is evidence of prior design intent, not the current AVP specification. No requirement becomes normative merely because it appears in this baseline or in the Python reference implementation.

## Source provenance

The source bundle is identified by `SOURCE-MANIFEST.json`, including the source archive SHA-256 and a per-document SHA-256/Git-blob identity. Baseline source text is immutable: corrections belong in reconciliation decisions or promoted specification text, never by silently editing historical source.

## Promotion rule

A statement may move from this baseline into `spec/` only after reconciliation against:

1. current design intent;
2. adjacent standards and ownership boundaries;
3. current schemas;
4. current reference implementation behavior;
5. existing conformance coverage;
6. security and interoperability impact.

The authority direction remains:

```text
historical design -> reconciliation -> spec -> schemas -> conformance -> implementation
```

Implementation behavior and unit tests are evidence during reconciliation, not sources of normative authority.

## Baseline documents

The indexed baseline contains documents 03–21 plus ADR-001. See `CLASSIFICATION.md` for the initial disposition and `SOURCE-MANIFEST.json` for exact source identities.
