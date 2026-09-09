# P06 table create HWPX v0 to v1

Before this profile, `hwpx-agent.table-operations/v1` created a complete blank unmerged semantic
grid and receipt, but no native HWPX adapter materialized that target.

`hwpx-agent.table-create-hwpx.hancom-2020-template/1` adds an exact adapter for one bound empty
top-level destination paragraph and one independently bound blank 2x2 native template. Explicit
row and column tracks determine the frame and every master extent; caller-supplied table and cell
logical IDs remain distinct and authoritative.

The request binds destination header/section, template section plus typed state/grid, empty insertion
context and current/target document flow. The builder and lowerer rebuild the domain create plan independently.
The output binding is regenerated from the target state and grid, and no parts are returned until
semantic reopen proves the exact blank grid/state, formula-free readback, pagination profile and
table-count increment.

Nonblank, merged, formula-bearing, captioned, repeat-header, diagonal or nonuniform-edge templates
have no reviewed exact native creation mapping in v1 and fail closed. Migration is additive and
existing documents are not rewritten in place.

Static synthetic HWPX/package success may not promote TABLE-001 to licensed Hangul 2020, renderer,
target-build, rollback/retry, automation, differential, release, production or product PASS.
