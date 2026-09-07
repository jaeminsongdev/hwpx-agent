# P06 table formula pure v1 to HWPX adapter v1

Date: 2026-09-07

This is an additive adapter boundary, not an in-place migration of
`hwpx-agent.table-formula/v1`. The pure model remains immutable and locale neutral.

The current Hangul 2020 adapter admits only the exact formula field shape observed in the named
synthetic current-PC capture. Its directional left-sum representation lifts to a relative
`SUM(A1:owner-left)` range. Lowering is permitted only when the AST still denotes the complete
relative left prefix of the owner row. Any other native spelling, range, parameter set, field-ID
relationship, cache shape, or number format fails closed.

Native command strings and automation action identifiers are adapter-private. Public callers pass
only `FormulaCell`, exact grid dimensions, a table ordinal, and finite limits. Cached results remain
`unverified`; this adapter component cannot promote them to verified oracle evidence.

There is no automatic migration and no fallback to guessed syntax. P06-06 remains open until a
structural row/column differential and an exact product-target licensed Hangul 2020 save/reopen
oracle both pass. Other PCs and Hangul versions remain unclaimed.
