# P06-09 TABLE-002/003 table ruling HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope

This profile maps the complete `hwpx-agent.table-ruling/v1` state for `TABLE-002 / table.draw` and
`TABLE-003 / table.eraser` into the reviewed current-Hangul-2020 HWPX table shape. It covers outer
rectangle creation, full row/column strokes, local cell split, slash/back-slash diagonals,
shared-edge structural merge, and nonstructural transparent-line erasure through one physical
grid/edge/cell model.

The strict reader admits one selected `hp:tbl`, its direct `hp:tr` rows, master `hp:tc` cells,
`hp:cellAddr`, `hp:cellSpan`, `hp:cellSz`, `hp:subList`, and referenced header `hh:borderFill`
definitions. These mappings follow Hancom's table drawing/eraser semantics and HWPML revision 1.2:

- <https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(draw).htm>
- <https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(eraser).htm>
- <https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D3.0_HWPML_revision1.2.pdf>

## Exact admission and identity

HWPX merged cells do not encode every internal physical boundary needed by the domain model. The
caller therefore supplies the logical table/master-cell/payload identities and the complete row
and column HWPUNIT boundaries. The adapter verifies each native cell's address, span, width and
height against that binding. It never infers hidden boundaries from equal-sized cells or UI
defaults.

Every master-cell side resolves to one semantic line identity derived from the referenced
`hh:borderFill`. Opposite sides of adjacent cells must agree. Internal edges covered by one merged
master cell become explicit transparent domain edges. Slash and back-slash identities are distinct
even though HWPX stores their visible line through one diagonal-line definition. Non-ruling cell
attributes, margins, background, table attributes and unowned table children are hashed separately
and rebound on readback.

Formula paragraphs are excluded from ordinary payloads and lifted through the existing strict
formula adapter. All other nonempty direct cell paragraphs retain ordered logical IDs and exact raw
paragraph SHA-256 identities. Empty scaffold paragraphs are represented as an empty payload, not as
invented user content.

## Existing-table lowering

Immediately before mutation, the adapter relifts the selected table and requires exact equality
with the caller's complete source state and grid. It independently verifies the plan receipt's
before/after state and grid SHA-256 values, the planned-grid digest, table identity and current
document-flow SHA-256. Any drift returns no bytes.

Topology changes rebuild only the selected table's row/cell region from preserving source
templates. The original top-left component retains raw ordered payloads; new empty components use
one canonical empty paragraph; structural merge concatenates source paragraphs in domain row-major
order. Non-ruling/background properties must have a preserving source template. Line-only edits
retain the complete original cell content bytes, including formula AST and cache.

The desired sides and diagonals resolve only through reviewed header identities. An existing
`hh:borderFill` is reused by semantic equality; otherwise one dense sequential definition is
appended and the header count is patched. One native master-cell side cannot express multiple line
styles, and HWPX cannot express two simultaneous diagonals with different line styles, so those
states fail closed rather than being flattened.

The current native formula profile supports exact read/preservation of one unmerged formula but not
general structural formula rebasing/cache serialization. A topology-changing plan that contains a
formula therefore returns `UnsupportedFormulaMutation`. This is an explicit nonclaim, not a partial
successful lowering.

## Outer-rectangle creation

Outer creation never treats an existing table as absent. The caller first selects an exact empty
top-level `hp:p`; its context digest binds the complete source section, paragraph ordinal and raw
placeholder bytes. The plan carries that digest and the lowerer recomputes it immediately before
mutation.

A separate reviewed template section supplies one empty, formula-free 1x1 native table wrapper.
Its bound cell extents, physical frame, table-property digest and cell-property identities must
match the domain target exactly. The wrapper may use only empty `hp:p/run/ctrl/t` structure outside
the table, and its native table ID must not collide with another destination table. Only the bound
placeholder is replaced. The inserted table is then selected at its exact resulting ordinal and
relifted to the planned state/grid.

## Package preservation, bounds and privacy

The closed synthetic package oracle coordinates header and section changes, reopens the package
graph, and checks formula/cache plus pagination readback for an unselected sibling table. Every
other expanded package part keeps its exact SHA-256; selected-table-exterior section bytes and
source package bytes remain exact; repeated rebuilding is deterministic.

All XML, layout, paragraph-style, formula, grid and ruling limits remain finite. Allocation and
output growth use checked/fallible paths. Receipts bind source/output header and section, optional
template/source state and grid, target state/grid, document flow and optional insertion context.
Custom `Debug` omits all hashes, logical IDs, payloads, formulas, caches and raw XML.

## Evidence promotion rule

Passing the fifteen adapter tests and private tamper suite promotes only TABLE-002/003 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, `formula_readback` and `page_split`. It does not prove renderer identity,
licensed Hangul 2020 save/reopen or target-build behavior, general structural-formula native
lowering, rollback/retry, automation runtime, differential exact match, arbitrary user documents,
another PC/version, P06-09/P06 completion, production or product completion.
