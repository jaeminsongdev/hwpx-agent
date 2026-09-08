# P06-09 TABLE-020 table style HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and complete style identity

This profile maps the full `hwpx-agent.table-style-definition/v1` and
`hwpx-agent.table-style/v1` TABLE-020 plan into the reviewed current-Hangul-2020 HWPX table shape.
The domain resolver remains authoritative for whole-table, header/footer, first/last column,
row/column band and corner precedence plus merged-cell policy. The adapter does not re-resolve or
weaken those rules.

A native visual cell-style identity contains the complete admitted cell surface: typed margins,
paragraph alignment, vertical alignment, text direction and protection; four independent borders;
background; and optional slash, back-slash or center-line diagonal value. The table-style identity
contains typed lock, border fill and no-adjust state. Digests are derived from typed values, not raw
XML or caller labels.

## Exact request/build binding

The reader first applies the strict table-properties profile, including exact logical/physical
grid, cell extent, payload, zero-or-one supported formula and visible diagonal bindings. It then
derives one visual style identity for every master cell. The complete style-state digest includes
the property-state digest, so table/grid/payload/formula and exact diagonal provenance remain bound
even though the reusable visual identity excludes document-specific unified regions.

At request time `TableStyleHwpxPartBinding` binds header, section, current document flow, complete
source style state, definition, request and plan SHA-256. Immediately before mutation the lowerer
relifts the source, compares every master ID/coordinate/payload/formula/current style, rebuilds the
domain plan and checks all hashes again. Any drift returns no output parts, binding or receipt.

## Typed lowering and diagonal provenance

Every definition rule must resolve through the complete typed catalog, including rules inactive on
the current grid. Unused table, cell, line, background and border-fill values are prevalidated
against the current header and finite limits. Semantically equal border fills are interned; an
unknown or ambiguous identity fails closed.

HWPX stores visible diagonal primitives but not each-cell versus unified application intent. A
truthful existing unified binding is preserved only if every member of that exact region retains
the same visual diagonal. If any member changes, all remaining visible members of the group become
explicit each-cell bindings; changed or new diagonals are also each-cell. This preserves visible
style semantics without retaining a false unified label, and the normalization count is recorded.

## Preservation, bounds and privacy

Only the selected table/cell attributes and append-only header border-fill definitions are edited.
Ordered payload paragraph bytes, formula owner/AST/number format/display cache, grid/spans, physical
extents, table spacing, pagination attributes, sibling tables and other package parts remain exact.
The output is reparsed through the same strict reader and compared to the complete target property
and visual-style state before return.

Layout, header catalog, cell style, formula, grid, property and style work/output remain finite.
Custom Debug surfaces omit hashes, logical IDs, paragraph-property IDs, payloads, formulas, caches
and raw XML.

## Evidence promotion rule

Passing the four adapter tests and private tamper suite promotes only TABLE-020 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, `formula_readback` and `page_split`. It does not prove render identity, licensed
Hangul 2020 save/reopen or target build, rollback/retry, automation runtime, differential exact
match, arbitrary user documents, another PC/version, P06-09/P06 completion, production or product
completion.
