# P06-09 TABLE-001 table create HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and exact native profile

This profile lowers the complete `TableGrid::create_unmerged` TABLE-001 contract into one new
top-level `hp:tbl` at an explicitly bound empty paragraph. It admits arbitrary nonzero bounded
rectangular dimensions, one distinct caller-supplied logical ID per row-major 1x1 master, and
explicit nonzero row-height and column-width tracks. The result is a blank, formula-free, unmerged
table; cursor-only default dimensions, implicit identities and guessed physical sizes are forbidden.

Native structure and style come from one separately bound blank Hancom-2020-shaped 2x2 template.
The table must be the direct child of its `hp:run`; a synthetic `hp:ctrl` wrapper is rejected.
That template must contain exactly four unmerged masters, no payload or formulas, no caption or
repeat-header rows, identical complete non-ruling cell properties, no diagonals, and uniform top,
bottom, left, right, inner-horizontal and inner-vertical edge bands. The target inherits the exact
table property, page-split policy, cell-property identity and those six edge-band identities. Only
the requested frame dimensions, physical tracks, grid, master identities and necessary
append-only border-fill catalog entries change.

## Exact request and build binding

`TableCreateHwpxRequest` binds header, destination section, template section, exact typed template
state and grid, empty insertion context, placeholder and template ordinals, current and target
document-flow SHA-256, table ID,
dimensions, every row-major master ID and every physical track. The reader proves the destination
paragraph is empty and top-level, the native run-direct template wrapper contains exactly one table, and the
template satisfies the full profile.

Request admission and build independently validate exact source/template/context/current-flow
state. The builder calls the authoritative domain create operation, reconstructs the complete
physical `TableRulingState`, and binds target state, grid, domain receipt, table counts and
before/after flow into a bounded deterministic plan. A create operation always requires a distinct
target document-flow digest. Table and cell logical identities must be distinct.

## Lowering, semantic reopen and preservation

Immediately before mutation the lowerer rereads both destination and template, rechecks current
flow and rebuilds the plan. It materializes the target from the exact template wrapper, rejects a
native table-ID collision in the destination, and replaces only the bound empty paragraph. Border
fills are deduplicated and appended only when the arbitrary rectangular target needs a reviewed
combination not already present in the template catalog.

Output is returned only after strict header/section reopen proves the exact target `TableGrid` and
`TableRulingState`, requested dimensions and tracks, zero payload blocks, zero formulas, preserved
page-split policy, zero repeat-header rows, no caption and an exact table-count increment of one.
Closed-package tests preserve every opaque non-target part and package relationship. Destination,
template and package inputs are borrowed and never mutated. Allocation, XML, JSON, geometry, grid,
ruling, formula and pagination work is finite; duplicate/unknown JSON fails closed; Debug omits all
digests, logical IDs, content and raw XML.

## Evidence promotion rule

Passing the seven adapter tests and private contract tamper suite promotes only TABLE-001 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`. The validations are `schema`,
static `semantic_reopen`, formula-free `formula_readback` and `page_split` preservation.

This evidence does not prove renderer equivalence, a saved real HWPX, licensed Hangul 2020
open/save/reopen, target-build execution, rollback/retry, automation runtime, differential exact
match, nonblank initial content, merged initial cells, repeat headers, captions, arbitrary native
templates or user documents, another PC/version, P06-09 or P06 completion, production readiness or
product completion.
