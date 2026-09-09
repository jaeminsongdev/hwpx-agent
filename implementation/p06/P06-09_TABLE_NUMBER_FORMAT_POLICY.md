# P06-09 exact table number-format policy

- Feature: `TABLE-049`
- Capability: `table.number_format`
- Model: `hwpx-agent.table-number-format/v1`
- Contract: `protocol/private/p06-table-number-format-v1.json`
- Scope: pure exact-state planner for current-PC local development

## Exact state and selection

The operation is defined over one complete ordered master-cell snapshot, not a loose list of formula
objects. The snapshot binds the logical table identity, canonical `TableGrid` SHA-256, table-level
properties SHA-256, and every master cell. Each master cell binds its identity, top-left coordinate,
non-formula payload SHA-256 and properties SHA-256. Formula cells additionally carry the complete
validated owner, `FormulaAst`, absent or unverified display cache, and current number format.

Requests select a nonempty, bounded, sorted and unique set of exact formula master-cell coordinates.
Covered non-master slots and cells without formulas fail closed. A merged master cell is admissible
at its exact top-left owner because its grid identity remains unambiguous.

## Mutation and preservation

The target is one closed `FormulaNumberFormat` value: general, fixed number with grouping, percent,
or scientific. Decimal places remain bounded by the formula limits. The builder reconstructs each
selected `FormulaCell` with only `number_format` changed. Formula owner, AST and cache are exact;
unselected formulas and all cell/table digests remain byte-for-byte equal in the typed state.

The request binds the current source-state SHA-256 and document-flow SHA-256. Both request admission
and plan building independently recheck table identity, canonical grid digest, full source-state
digest and document-flow digest. Any intervening change fails before a plan is returned. Output is
deterministic bounded JSON with SHA-256; Debug output redacts identities, digests, formulas, caches
and the complete post-state.

## Official format evidence boundary

The archived machine-readable KS X 6101 source, section `10.7.3.5.2`, defines formula
`ResultFormat` values `%g`, `%.0f`, and `%.1f` through `%.4f`. This source proves only those standard
tokens. It does not prove this PC's Hangul 2020 spelling, the observed trailing comma, grouping,
percent, scientific, rounding, visible cache refresh, or save/reopen behavior. Consequently this
component does not lower or patch HWPX and the conformance row remains `unit_passed`.

## Gate boundary

No actual HWPX was created or changed, and no Hangul process, automation binding, save/reopen,
formula readback, pagination, PDF/render or differential ran. A later direct adapter requires exact
target-native source evidence for every admitted target format and must preserve full package state.
`TABLE-049`, P06-09, P06, production and product completion remain open.
