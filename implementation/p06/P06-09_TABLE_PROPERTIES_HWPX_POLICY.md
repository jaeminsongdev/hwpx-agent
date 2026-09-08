# P06-09 TABLE-007/008/009/047 table properties HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope

This profile maps the complete `hwpx-agent.table-properties/v1` state for TABLE-007
`table.properties`, TABLE-008 `table.cell_properties`, TABLE-009 `table.border_fill`, and
TABLE-047 `table.diagonal` into the reviewed current-Hangul-2020 HWPX table shape. It covers typed
table lock/frame/no-adjust values; typed margins, paragraph alignment, vertical alignment, text
direction and protection; four independent cell borders and background; and each-cell or unified
slash, back-slash and center-line diagonal semantics.

## Exact admission and identity

The strict reader first admits one selected `hp:tbl` through the complete physical table binding.
Every native master cell address, span, width and height must equal the logical grid. Table values
come from `lock`, `borderFillIDRef` and `noAdjust`. Cell values come from `cellMargin`,
`protect/editable`, `subList` direction/alignment and every direct paragraph's `paraPrIDRef` through
the exact `Hangul2020V2` cell-style reader.

Each top/right/bottom/left border and background is lifted independently from the referenced typed
`hh:borderFill`; property editing does not invent ruling-style shared-edge equality. HWPX retains
visible diagonal primitives but not whether the user applied them to each cell or one unified
region. Every visible diagonal therefore requires an explicit logical binding, whose native
slash/back-slash/center/line value is rechecked. Missing, extra, duplicate or mismatched bindings
fail closed.

Formula paragraphs are excluded from ordinary payload identity and lifted separately. The current
profile admits zero or one exact supported formula, including owner, AST and display cache. More
than one formula is unsupported rather than partially preserved.

## Typed lowering and preservation

Immediately before mutation, the lowerer relifts the selected table and requires equality with the
caller's complete source state and grid. The domain request and builder both verify exact state and
grid identities; the HWPX build boundary additionally verifies header/section and current
document-flow SHA-256 bindings. Any drift returns no bytes, updated binding or receipt.

Opaque property digests resolve only through typed table, cell, border-line, fill-brush and
border-fill values. Every supplied value is prevalidated against the current header and finite
limits, including unused entries. There is no raw-XML escape hatch or fallback for an unknown
digest. Semantically equal border fills reuse an existing definition; otherwise a dense definition
is appended and the header count is patched.

Only the selected table/cell attributes and their border-fill references are edited. Payload
paragraph bytes, formula/cache semantics, physical grid/extents, unselected cells/tables and all
other section bytes are preserved. A closed synthetic package test checks deterministic rebuild,
package graph identity, an unselected sibling table's formula and pagination, and exact non-target
part hashes.

Native `cellSpacing` is geometry-coupled. This adapter preserves it and does not expose it as an
independent table-property value because changing only that attribute would contradict the exact
cell widths and heights. That boundary is a fail-closed representability rule, not a partial
implementation claim.

## Bounds and privacy

XML, layout, paragraph-style, cell-style, formula, grid and property limits remain finite. Output
growth and allocations use bounded or checked paths. Receipts bind source/output header and
section, source/target state, grid, plan and current document flow, plus changed-cell, added-style
and preserved-formula counts. Custom `Debug` omits hashes, logical IDs, paragraph-property IDs,
payloads, formulas, caches and raw XML.

## Evidence promotion rule

Passing the twelve adapter tests and private tamper suite promotes only TABLE-007/008/009/047 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, `formula_readback` and `page_split`. It does not prove renderer identity,
licensed Hangul 2020 save/reopen or target-build behavior, rollback/retry, automation runtime,
differential exact match, arbitrary user documents, another PC/version, P06-09/P06 completion,
production or product completion.
