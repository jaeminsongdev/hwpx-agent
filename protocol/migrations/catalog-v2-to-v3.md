# Protocol catalog v2 to v3

`catalog-v3` adds `AutomationBindingRegistryV1` without changing any v1 or v2 schema bytes.

- Existing consumers may continue to pin `schema-catalog-v2.json` unchanged.
- Consumers that need target-build automation bindings opt into `schema-catalog-v3.json`.
- Registry instances with raw action or ParameterSet identifiers are restricted artifacts and must not be exposed through public or LLM-facing surfaces.
- Every binding remains unroutable and runtime-unverified until a target-matched probe produces separate qualification evidence.
