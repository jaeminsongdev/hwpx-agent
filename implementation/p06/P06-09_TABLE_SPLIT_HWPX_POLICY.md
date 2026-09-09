# P06-09 TABLE-010 whole-table split HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Exact admitted profile

This profile maps TABLE-010 `table.split_table` from the complete
`hwpx-agent.table-partition/v1` domain result into the reviewed current-Hangul-2020
`hp:sec/hp:p/hp:run/hp:tbl` wrapper shape. The cursor selects the first row of the second table;
row zero, an out-of-grid cursor, or a row-spanning master cell crossing that boundary fails closed.
Both output tables keep the exact source column lattice and width. The first keeps the source table
identity, the second uses the caller-bound distinct logical identity, and one caller-bound separator
paragraph is inserted between them.

The native profile is deliberately exact: the selected table must be formula-free, have no caption,
and have zero repeat-header rows. Formula rebasing, caption ownership after a split, and repeat-header
ownership after a split require separately qualified semantics and are rejected rather than guessed.
All supported page-split values remain byte-preserved and are reopened on both output tables.

## Complete state and preservation

The domain grid is authoritative. Every master cell moves to exactly one output table. Row-spanning
cells wholly below the boundary are rebased; their spans, payload block order and bytes, complete cell
properties, four edge identities and diagonal state remain exact. Physical row boundaries are sliced
and rebased to zero; column boundaries, table width, left/top position and all non-topology table
properties remain bound. The source table, sibling tables, sibling formula owner/AST/number-format/
display-cache state, and every non-target package part are never rewritten outside the selected
wrapper replacement.

The lowerer independently renders both partitions through the reviewed ruling renderer, requires an
identical resulting header catalog, allocates collision-free numeric paragraph/table IDs, and replaces
only the selected top-level wrapper with first table, empty separator paragraph and second table.
Publication occurs only after both output tables reopen through the same strict ruling, partition and
pagination readers.

## Exact request/build/lower binding

`TableSplitHwpxRequest` binds header SHA, section SHA, selected-wrapper SHA, table ordinal, complete
partition-state SHA, grid SHA, table identity, split cursor, output logical identities, formula policy
and document-flow SHA. Request construction and build independently validate source state and flow;
the lowerer relifts the supplied parts and rebuilds the complete plan immediately before mutation.

The plan binds both output grids by SHA, both complete ruling states, the authoritative domain plan
and request SHA. The receipt binds source/output parts, source wrapper, both target states, request,
plan, before/after document flow and exact preservation/creation counts. JSON rejects empty,
oversized, malformed, unknown and duplicate keys, including nested duplicates. Debug output omits
hashes, logical IDs, payloads, formula/cache content and raw XML. Failure returns no partial output.

## Evidence promotion rule

Passing the five adapter tests and private tamper suite promotes only TABLE-010 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, sibling `formula_readback` and `page_split`. TABLE-011 remains component-only.
This evidence does not prove render identity, a saved real HWPX, licensed Hangul 2020 execution,
target build, repeat-header or caption split semantics, formula rebasing, rollback/retry, automation
runtime, differential exact match, arbitrary user documents, another PC/version, P06-09/P06
completion, production or product completion.
