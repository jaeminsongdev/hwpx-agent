# P06 table geometry v0 to v1

Date: 2026-09-08

`v0` had no dedicated table-track state or receipt. Row heights, column widths and content minima
could be carried as unrelated arrays without an exact logical-grid binding, atomic operation rule,
or deterministic evidence of what changed.

`hwpx-agent.table-geometry/v1` is additive and strict. A caller supplies one validated `TableGrid`
and exactly one positive bounded height/width and minimum for every logical track. The canonical
grid SHA-256 binds the state. Equal-row, equal-column and row-minimum operations accept nonempty
contiguous `TableTrackRange` values and return a new state plus a source/output-bound receipt.

Legacy arrays, zero or negative dimensions, values below their content minimum, unsupported
versions, unknown or duplicate JSON fields, mismatched grids and empty/out-of-range selections are
not coerced. Failed operations do not mutate the source state.

Direct HWPX and automation adapters may translate this component only through their own validated
contracts. Pure component PASS may not promote a capability to HWPX integration, licensed Hangul
2020 oracle, differential exact match, release-enabled, P06-09/P06 PASS, production, or product
completion.
