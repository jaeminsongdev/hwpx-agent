# P06-09 table and cell properties policy

- Features: TABLE-007 table.properties, TABLE-008 table.cell_border_each,
  TABLE-009 table.cell_border_unified, TABLE-047 table.cell_diagonal
- Model contract: hwpx-agent.table-properties/v1
- Scope: pure bounded semantic component for the current-PC local-development branch
- Current direct stage: component_only / unit_passed

## Source meaning and feature boundary

The catalog requires these operations to bind TableNode/CellProperties/FormulaAst and an exact
TableCellSelector. Hancom's official help distinguishes per-cell application from treating one
contiguous rectangular cell block as one logical selection. It also states that non-rectangular or
non-contiguous multi-cell blocks cannot use the unified operation. The current Hangul 2020 help
states that cell backgrounds remain cell-unit properties rather than a single table-wide image.

References:

- https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/cellborder/cellborder(each).htm
- https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/cellborder/cellborder(many).htm
- https://help.hancom.com/hoffice110/ko-KR/Hwp/table/cellborder/cellborder(background).htm
- https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/cellborder/cellborder(diagonal).htm

## Complete state and exact binding

A TablePropertiesState contains one canonical record for every TableGrid master cell. Each record
binds its logical ID and top-left coordinate to payload, optional formula, non-border cell
properties, four border sides, background and diagonal semantic identities. The state also binds the
table-properties digest and exact canonical grid digest. Missing, duplicate, extra or coordinate-
mismatched master cells fail before a request exists.

A request binds the current state SHA-256 and exact grid. A selected cell operation consumes an
explicit set of logical slots. Slot order is canonicalized, while duplicates, out-of-grid slots and
a selection that contains only part of a merged master cell are rejected. TABLE-007 and TABLE-008
accept an exact non-contiguous cell set. TABLE-009 additionally requires that the selected slots form
one contiguous rectangle. A fully selected merged cell is addressed once through its master identity.

## TABLE-007 properties semantics

SetProperties may replace the table-properties identity, the non-border property identity of every
exactly selected master cell, or both. A table-only mutation requires an empty selection; a cell-property
mutation requires a non-empty valid selection. Border, background, diagonal, payload and formula
identities are preserved. Empty operations and ambiguous table-only selections fail closed.

The digest-bound table and non-border property values are backend-neutral identities for separately
validated semantic records. They do not admit arbitrary raw XML or desktop action parameters.

## TABLE-008 each-cell semantics

BorderEach has four independent per-cell side patches. Each side and background patch is exactly one
of preserve, clear or set-to-validated-SHA-256. The same top/right/bottom/left intent is resolved for
every exactly selected master cell independently, including non-contiguous cells and merged cells
whose complete covered-slot set is selected.

## TABLE-009 unified-selection semantics

BorderUnified models the rectangular selection as one frame with outer top/right/bottom/left and
separate inner-horizontal and inner-vertical patches. For each selected master cell, an edge touching
the selection boundary receives its corresponding outer patch; every other real master-cell edge
receives the applicable inner patch. Covered slots inside one merged span do not create fictitious
internal edges. Background remains a cell property and the declared background patch is applied to
each selected master cell.

## TABLE-047 diagonal semantics

CellDiagonal explicitly chooses each-cell or unified-selection application. Each-cell mode accepts
an exact non-contiguous slot set and repeats one semantic value in every selected master cell.
Unified mode requires one rectangular slot region and gives all selected master cells one shared
region identity; this prevents a later adapter from silently treating the request as independent
per-cell diagonals.

The semantic value records OWPML `slash` and `backSlash` topology (`none`, `center`,
`center_below`, `center_above`, or `all`), their independent crooked/counter flags,
horizontal/vertical/cross center-line intent, and a validated digest for the line type/width/color
tuple. No undocumented flag normalization is invented; a set operation with no slash or center line
is rejected. Clear is distinct from set. The identity also binds table, grid, application mode and
unified region.

## Determinism, preservation and receipts

Validated state, request and plan representations use deterministic compact bounded JSON and
SHA-256. A plan carries before/after property values for every selected master cell plus explicit
per-cell, selection-outer or selection-inner edge roles. Receipts distinguish assignment counts from
actual semantic changes, so clearing an already absent side or diagonal is not counted as a change.
Diagonal receipts separately record target assignments and actual changes.

Unselected master cells and every payload, formula and untargeted diagonal identity are included in
the before/after state hashes and preservation counts. Invalid limits, versions, JSON, identifiers,
digests, state/grid drift, selection topology, merged-cell containment, output size or allocation
return typed errors with no partial plan or receipt. Debug surfaces redact document IDs and digests.

No user document, HWPX package, Hangul process, registry, printer, trust store, network service or
system setting is read or changed by this component.

## Evidence boundary

This slice proves only the bounded logical planner for TABLE-007/008/009/047. It does not prove HWPX
borderFill catalog materialization, package mutation/preservation, semantic reopen, formula
readback, pagination, rendering, licensed Hangul 2020 execution, desktop automation or differential
equivalence. The four rows therefore move only from cataloged to unit_passed; they remain non-green
and P06-09, P06 and the product remain in progress.

The next HWPX/preservation/oracle work remains at reasoning level max.
