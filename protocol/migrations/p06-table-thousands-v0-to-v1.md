# P06 table thousands planner migration: v0 to v1

`v0` had no independently versioned thousands-format operation. Callers must now emit
`hwpx-agent.table-thousands/v1` with an explicit `add` or `remove` mode and exact selected-cell
coordinates.

## Required migration

1. Bind the request to exact nonzero table dimensions.
2. Supply a nonempty finite selection without duplicate coordinates.
3. Supply exactly one validated `FormulaCell` per selected coordinate.
4. Admit only an existing `Number` format; do not infer from visible text or another format.
5. Preserve decimal places, owner, formula AST and cache while changing only `use_grouping`.
6. Treat every validation or output-limit error as atomic failure with no partial plan.

There is no backward-compatible native-HWPX mapping in this migration. HWPX lowering and licensed
Hangul 2020 behavior require a separately versioned, source-backed adapter and oracle evidence.
