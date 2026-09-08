# P06-09 TABLE-002/003 table ruling and topology policy

- Scope: `component_only / unit_passed`
- Target context: licensed Hangul 2020 `11.0.0.9136` x86 on the current PC
- Model schema: `hwpx-agent.table-ruling/v1`
- Capabilities: `table.draw`, `table.eraser`
- Reasoning level: `max`

## Official semantics

Hancom's table-drawing help describes four distinct pencil operations: draw an outer rectangle to
create a table, draw from the left edge to the right edge to add a row, draw from the top edge to
the bottom edge to add a column, and draw inside an existing table to add cells, diagonals, or a
different line type. The eraser help defines a topology-sensitive rule: erasing a side shared by
two cells combines them into one cell; a line that is not such a shared side becomes transparent.

Official references:

- <https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(draw).htm>
- <https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(eraser).htm>

## Complete exact state

`TableRulingState` binds one table ID, physical frame, exact `TableGrid` SHA-256, table-properties
SHA-256, every physical row and column boundary, and every normalized horizontal and vertical unit
edge. An edge always exists in the state; `line_sha256: null` means an explicit transparent line
and never means that topology was omitted.

Every master cell occurs exactly once in row-major order. Its state includes ordered payload-block
IDs and content SHA-256 values, complete non-ruling/background and slash/back-slash property
identities, and an optional validated `FormulaCell`. `FormulaCell` carries the typed formula AST,
owner, number format, and separate cache. Duplicate cell, edge, payload, or identity records and any
incomplete coverage fail closed.

## Draw topology

An outer-rectangle request has no pre-existing table state or grid. It binds a document-flow and
insertion-context SHA-256, creates one exact 1x1 cell, and assigns the requested line identity to all
four outer edges. Its frame and initial property identities are finite and explicit.

Horizontal and vertical strokes use local HWPUNIT coordinates. A draw may introduce physical
lattice boundaries at its fixed coordinate and endpoints. Existing cells are first remapped onto
that refined lattice without changing their physical extent. The stroke then acts as a barrier
inside every intersected master cell. Connected slot components become cells only when every
component is rectangular; T-junctions or partial strokes that leave a non-rectangular semantic cell
reject atomically.

This single rule covers full-table row strokes, full-table column strokes, and local cell splits.
The original top-left component keeps its master-cell ID, ordered payload, properties, and formula.
Additional components consume an exact deterministic list of new IDs, start with an empty payload
and no formula, and inherit the source cell's non-ruling/background properties. Splitting a cell
with a diagonal rejects because silently clipping or duplicating that diagonal would not preserve
its meaning. Splitting an already-merged lattice while any formula state exists also rejects:
without target evidence, references to covered coordinates cannot be proven to retain the same
logical-cell meaning. A stroke on an existing boundary changes only its visible line identity.

Slash and back-slash diagonals are separate cell-local operations. They change only the selected
direction's line identity and never change the grid topology or the opposite direction.

## Eraser topology

An eraser stroke must follow existing physical ruling coordinates. Every selected interior unit
edge is resolved against both adjacent logical slots:

- different master cells: union them structurally;
- the same master cell, or an outer edge with no second cell: keep topology and make the line
  explicitly transparent.

All cells connected by one stroke are evaluated atomically. Their union must be a rectangle,
non-ruling/background properties must agree, and cell-local diagonals must be absent. Ordered
payload blocks are concatenated in row-major source-cell order. At most one formula may survive;
if its owner moves, relative references are rebased under the explicit formula policy. Cache bytes
are preserved for line-only edits. A structural merge can change the value reached by any formula
without changing its AST, so all non-absent formula caches are cleared only under the explicit
policy; otherwise the merge rejects. All now-internal edges of the merged rectangle become
transparent.

## Drift, bounds, privacy, and failure

Existing-table request construction verifies the complete state SHA-256, exact grid SHA-256, table
identity, and current document-flow SHA-256. The builder repeats every binding immediately before
planning. Outer creation repeats the exact document-flow check and rejects an existing-state/grid
context. Errors return no partial state, plan, or receipt.

Defaults cap input at 32 MiB, cells at 1,000,000, normalized edges at 2,100,000, payload blocks at
1,000,000, identifiers at 256 bytes, physical dimensions at 1,000,000,000 HWPUNIT, and serialized
output at 128 MiB. Hard ceilings remain finite. Canonical JSON is deterministic and bounded.
Custom `Debug` output redacts table, cell and payload identities, line/property/content digests,
formula content, cache values, and binding digests.

## Gate boundary

TABLE-002 and TABLE-003 advance only from `cataloged` to `unit_passed`. This policy does not prove
direct HWPX lowering, package mutation/preservation, semantic reopen, formula readback, pagination,
rendering, licensed Hangul 2020 execution, UI coordinates, automation bindings/runtime, differential
parity, arbitrary user documents, other PCs or versions, P06-09 completion, production readiness,
or product completion. Every such claim remains a separate evidence Gate.
