# P06 table auto-fill v0 to v1

- V0 had catalog rows only and no executable domain schema.
- V1 adds `hwpx-agent.table-auto-fill-series/v1` for exact scalar series definitions and
  `hwpx-agent.table-auto-fill/v1` for grid-bound mutation planning.
- Existing documents and operation payloads are not rewritten or implicitly admitted.
- Unsupported rich content, formula generation, native UI indices and merged regions fail closed;
  there is no partial plan or fallback after mutation.
- Future formula-aware, HWPX and native-automation behavior must be separately versioned and must
  preserve V1 canonical bytes and failure semantics.
