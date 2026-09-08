# P06 table-ruling v0 to v1 migration

`hwpx-agent.table-ruling/v1` replaces the catalog-generated generic TABLE-002/003 argument shapes
with one private, bounded semantic model for table drawing and erasing.

Existing documents and public capability catalogs are unchanged. The internal model introduces a
physical table frame and ruling lattice, one normalized record for every horizontal and vertical
unit edge, complete master-cell payload/property/formula/cache state, and exact state/grid/flow
bindings. It does not expose raw HWPX XML, COM action names, parameter-set identifiers, UI
coordinates, or arbitrary file paths.

Callers creating a table with an outer rectangle now provide exact table/cell identities, frame,
line and initial property identities, insertion-context SHA-256, and current document-flow SHA-256.
Existing-table draw and eraser callers provide the complete state, exact grid, current flow, and a
typed stroke or diagonal operation. Draw strokes must provide the exact deterministic new-cell IDs
needed by the resulting rectangular partition. Eraser strokes must follow existing ruling
coordinates.

The v1 builder separates visual line state from structural topology. Full row/column and local
draw strokes split rectangular cell components; diagonals remain cell-local. Erasing a shared edge
merges a rectangular connected cell set, while nonshared edges become explicitly transparent.
Ordered payloads are retained, merge property conflicts and multiple formulas reject, formula moves
rebase under an explicit policy, and topology-stale formula caches are cleared only when explicitly
authorized. Existing-lattice merged-cell splits with formula state reject as semantically ambiguous.
Any failure returns no partial state, plan, or receipt.

Direct HWPX lowering, package preservation, semantic reopen, licensed Hangul 2020 execution,
automation and differential parity remain separate Gates and require independent migration
evidence.
