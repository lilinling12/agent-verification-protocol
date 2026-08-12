# Reference Runtime Boundary

`runtime/` defines the distribution boundary for the open-source reference runtime.

During Alpha, executable Python remains under `src/avp_ref/`; this repository-boundary refactor intentionally does not combine a package/import migration with architectural cleanup.

The runtime demonstrates one conforming implementation of Episode execution, adapters, evidence collection, verification, Oracle isolation, telemetry, replay, and artifact handling.

It is non-normative: implementation behavior cannot become protocol semantics by accident. If code and `spec/` disagree, the discrepancy must be resolved explicitly.

This boundary may later become an independent `avp-runtime` repository.
