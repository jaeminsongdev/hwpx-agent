# P06-03 Merge/split policy

- Contract: `hwpx-agent.table-merge-split/v1`
- Contract record: `protocol/private/p06-table-merge-split-v1.json`
- Implementation: `domain_ir::TableGrid` merge/split engine and bound content ownership state
- Scope: current-PC pure IR, personal local development only

## Source and representation boundary

The P06 table model, table-layout implementation guide, 61-feature table contract and P06 roadmap are
the only product-design sources used by this task. Their UTF-8 text is normalized to LF before exact
SHA-256 comparison. P06-03 does not infer HWPX XML names or desktop automation identifiers.

`TableCellContent` contains only ordered `LogicalId` references to content blocks. It does not copy,
parse or expose paragraph/text bytes. `TableContentState` requires exactly one entry per current
master cell, globally unique content-block ownership, finite identifier/count limits, canonical
master-coordinate order and an exact binding to the grid's canonical SHA-256. Its private ID index
provides bounded `O(log n)` lookup. Debug output exposes only counts.

## Merge geometry and identity

The caller supplies every logical slot in the requested merge area. The engine sorts the set and
requires a nonempty, duplicate-free, in-bounds, complete axis-aligned rectangle. Every existing
master span that intersects the rectangle must be fully contained. Partial-master, nonrectangular
and single-master no-op selections fail before publication.

At least two master cells become one span. The master covering the region's top-left slot keeps its
logical identity; the other selected identities retire in canonical pre-merge coordinate order.
Unselected master cells and their content ownership are unchanged.

## Explicit merge content policy

- `concatenate`: preserve every selected cell's block IDs in canonical pre-merge cell order and
  original intra-cell order.
- `distribute`: a merge has one destination, so this is explicitly equivalent to lossless canonical
  concatenation rather than guessing another destination.
- `reject_if_multiple`: fail with `MultipleNonemptyCells` when more than one selected source cell is
  nonempty; otherwise move the only nonempty cell's ordered blocks to the survivor.
- `first`: retain only the canonical top-left source cell's blocks. Every block from later selected
  cells is listed in `discarded_content_block_ids`; loss is never silent. Public authorization for
  this lossy mode is outside P06-03.

There is no default policy. A caller must choose one explicitly.

## Split geometry, identity and content

Split partitions one existing master span inside the unchanged logical grid. Requested row and
column part counts must be nonzero, produce at least two parts and evenly divide the source span.
The top-left result keeps the source identity; the caller supplies exactly one unique bounded ID for
each remaining part in row-major order. A 1x1 logical cell cannot be subdivided without a separate
row/column insertion plan.

`distribute` assigns source block IDs to result cells as stable contiguous balanced chunks: each
part receives the quotient count and the earliest remainder parts receive one additional block.
`concatenate`, `first` and `reject_if_multiple` keep every source block in the preserved top-left
result because split has exactly one source content owner. Split never discards content.

## Atomic result and receipt

Both operations borrow the source grid and content state, build a new grid, rebuild and revalidate
the exact content ownership state, then validate a bounded deterministic receipt before returning.
Failure mutates neither source. The receipt binds before/after grid digests, operation, policy,
region, preserved/retired/created identities, content transfers and explicit discarded block IDs.
Receipt and content fields are private with read-only getters.

Validation is content/grid binding, selection or subdivision geometry, existing-span containment,
policy conflict, exact new-ID count, finite allocation, P06-01 grid invariant, content ownership and
bounded receipt serialization. Stable typed errors retain underlying `TableGridError` codes.

## Deferred semantics

This pure IR layer does not validate actual `Flow` bodies, style inheritance, border/fill,
FormulaAst movement, table split/join, logical row/column insertion during cell split, HWPX
lift/lower, desktop automation, semantic reopen or rendering. It does not qualify a public tool,
arbitrary documents, another PC/version, production, the P06 phase or the product.
