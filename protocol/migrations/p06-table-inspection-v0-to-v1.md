# P06 table inspection v0 to v1

Date: 2026-09-08

`v0` had no table-specific immutable snapshot. Callers could combine a table index and a physical
row/column position without binding the document revision, merged-cell master, nested-table path,
or logical table/cell fingerprint.

`hwpx-agent.table-inspection/v1` is additive and strict. A caller must build a bounded snapshot from
one validated `DocumentGraph`, obtain a `TableSelector` or `TableCellSelector` from that snapshot,
and resolve it with the exact `TableInspectionExpectation`. Persisted selectors bind logical ID,
structural path, and fingerprints; cell selectors additionally bind the requested pre-merge
coordinate and canonical master-cell identity.

Legacy numeric table indexes, backend object IDs, cursor positions, and row/column pairs without
these anchors are not coerced. Unknown fields or versions are not accepted by protocol adapters.
HWPX and automation adapters may translate the stable result only through their own versioned
contracts and may not promote this pure snapshot into backend selection or renderer evidence.
