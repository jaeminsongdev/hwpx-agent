# P06 table operations v0 to v1 migration

There was no executable v0 table-operation contract. Version
`hwpx-agent.table-operations/v1` introduces bounded, backend-neutral creation and row/column
insertion/deletion over the validated `TableGrid` prerequisite.

Callers must now provide exact row-major logical IDs for every created or inserted 1x1 master cell.
Insertion indexes address boundaries and deletion indexes address half-open in-bounds intervals.
Requests that cross only part of a merged-cell span fail closed; no legacy behavior may guess span
expansion, shrinkage, splitting, content movement, style inheritance or FormulaAst reference updates.
Those semantics require explicit P06-03 and later migrations.

Successful operations return a new grid and deterministic identity/coordinate receipt. A failed
operation leaves the source grid unchanged and returns a typed error. Existing unversioned operation
payloads are rejected rather than coerced. This migration does not add HWPX lowering, Hangul
automation, public API support or phase completion.
