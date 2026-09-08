# Protocol catalog v4 to v5

`catalog-v5` adds the public P06 table automation-projection, direct-evidence and conformance-report
schemas without changing any v1, v2, v3 or v4 schema/catalog bytes.

- Existing consumers may continue to pin `schema-catalog-v4.json` unchanged.
- P06 conformance tooling opts into `schema-catalog-v5.json`.
- The public projection and report contain semantic feature/capability identities only. Raw Hancom
  Action, ParameterSet, probe values, document content and absolute private paths remain excluded.
- All three schemas are target-scoped and fail closed when evidence, runtime qualification or
  direct/automation differential proof is missing.
