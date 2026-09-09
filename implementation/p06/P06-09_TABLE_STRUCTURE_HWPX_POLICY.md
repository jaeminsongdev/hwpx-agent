# P06-09 TABLE-012/013/014/015 exact structure HWPX policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## One exact four-operation model

TABLE-012 `table.insert_rows`, TABLE-013 `table.insert_columns`, TABLE-014 `table.delete_rows` and
TABLE-015 `table.delete_columns` share `hwpx-agent.table-structure/v1`. No row is promoted through an
easier subset. Every request binds one complete ruling state and grid, an exact contiguous edit
interval, authoritative target state/grid, and before/after document flow. Request admission and
build independently recompute and compare source state, source grid and document-flow digests.

Insertion is legal only at a whole-grid boundary that does not cross a merged master. It introduces
one empty, formula-free 1x1 master for every new slot, with distinct bounded logical IDs and explicit
positive track geometry. Deletion removes only masters fully contained by the interval, rejects a
partial merged span and never deletes the final row or column. Surviving masters retain their exact
identity, projected span, ordered payload blocks and complete cell properties.

## Geometry, edge and formula semantics

Unedited row heights and column widths remain exact; inserted track sizes are explicit and the frame
is the exact new boundary extent. At insertion, the source boundary is duplicated onto both sides of
the new band. New internal band edges are explicit in the authoritative target. At deletion, each
surviving boundary is mapped structurally; if two source edges collapse onto one target shared edge,
their line identities must match. Different identities cannot both survive and therefore fail closed.
Background, diagonal and table-property identities are never reconstructed from a visual guess.

Formula owners and every supported reference follow the same `FormulaGridEdit` as the grid. The
caller must select preserve, clear or update for the display cache and provide any updated value
explicitly. Deleting the formula-owning cell retires that formula and is counted; deleting a referenced
range endpoint is unsupported. The native adapter admits at most one existing `SUM(LEFT)` left-prefix
formula in the exact Hancom wrapper with decimal cache. It does not create formulas or generalize this
native syntax. A merged formula master has a dedicated regression proving its span survives while its
owner/reference coordinates rebase.

## Exact HWPX binding and preservation

The HWPX profile accepts one unambiguous top-level `hp:sec/hp:p/hp:run/hp:tbl` wrapper with numeric
paragraph/table IDs. Nested or ambiguous wrappers fail closed. The request binds header, section,
wrapper, domain source state/grid/flow and the complete target transition. The builder relifts source
state before rebuilding the plan. The lowerer relifts again, rebuilds the authoritative plan, renders
only the existing wrapper, reuses exact native formula content, applies formula/pagination lowering,
and publishes only after semantic reopen matches full state, grid, formula/cache, page-split,
repeat-header, caption, native identities and document flow.

Page-split and caption remain exact. Inserting rows before the repeat-header prefix extends it;
deleting rows subtracts the overlap. A zero-to-nonzero or nonzero-to-zero repeat-header transition is
rejected because the current complete table-property digest binds the native flag. This boundary is
explicit rather than guessed. One known caption child is preserved as raw source XML and checked by
the strict pagination reader. Sibling wrappers, tables and formula state, trailing flow and every
non-target package part remain byte exact. Failure returns no partial header, section, binding or
receipt.

JSON is deterministic, bounded and rejects empty, oversized, malformed, unknown and recursive
duplicate keys. Debug omits hashes, logical/native IDs, payloads, formulas, cache values, caption
content and raw XML. Receipts bind input/output parts, wrapper, complete state/grid, request, plan,
pagination/caption and before/after flow plus exact inserted/deleted/preserved cell, edge and formula
counts.

## Evidence boundary

Passing seven domain tests, eight adapter tests and the private tamper suite promotes all four rows
only from `component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, `formula_readback` and `page_split`. The fixture classes are happy-path, boundary,
negative, preservation and security. The matrix moves `unit_passed` from 25 to 21 and
`integration_passed` from 21 to 25; `cataloged` stays 0, `oracle_verified` stays 15 and green stays
0/61.

This evidence does not prove a saved real HWPX, render identity, licensed Hangul 2020 execution,
target build, repeat-header enable/disable, new or non-native formulas, insertion inside a span,
partial-span deletion, rollback/retry, automation runtime, differential exact match, arbitrary user
documents, another PC/version, P06-09/P06 completion, production or product completion.
