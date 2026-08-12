# Conformance Reports

TCK runners emit reports that validate against `report.schema.json` in this directory.

Reports are execution artifacts, not normative specifications. The normative authority remains the AVP specification and requirement index; the report schema and TCK resources are machine contracts derived from them.

Every report binds the profile identity, TCK registry version and digest, implementation identity digest, declared conditional capabilities, case results, and an internally consistent summary. `SKIP` is valid only for a non-applicable conditional case and always carries an explicit `skipReason`.

`avp-core-v0.1.example.json` is intentionally non-certifying. It is validated by `scripts/validate_tck_report.py` against both the JSON Schema and current registry/profile semantics so the example cannot silently drift from the executable contract.
