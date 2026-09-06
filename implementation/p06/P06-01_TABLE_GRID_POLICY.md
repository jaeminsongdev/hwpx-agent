# P06-01 TableGrid policy

- Contract: `hwpx-agent.table-grid/v1`
- Contract record: `protocol/private/p06-table-grid-v1.json`
- Implementation: `domain_ir::TableGrid`
- Scope: current-PC pure IR, personal local development only

## Source boundary

The locked product-design sources are `docs/03_document_model/06_table_model.md`,
`docs/12_implementation_guides/05_page_table_layout_algorithms.md`, the 61-feature table contract and
the P06 roadmap. Their UTF-8 text is line-ending-normalized to LF before the exact SHA-256 values are
recorded in the private contract, so LF and CRLF checkouts remain equivalent while content drift still
fails closed. The sources require a logical grid
that preserves pre-merge coordinates, maps each slot to one master cell and permits only rectangular
spans. P06-01 does not infer direct HWPX element or attribute names from those requirements.

The official KS X 6101 source and current Hangul 2020 runtime remain available to later table
lift/lower and differential tasks, but neither is promoted to P06-01 execution evidence. No user
document, generated table package, COM action or raw XML is an input to this task.

## Typed invariant

`TableGrid` owns nonzero bounded row/column dimensions, canonical master-cell rectangles and a dense
private slot-to-master index. Each `TableCellSpan` has a unique bounded backend-neutral `LogicalId`, a
top-left logical coordinate and nonzero checked row/column spans. Construction succeeds only when
every logical slot is covered exactly once. Input cell ordering is not semantic.

`TableCellSpan::from_covered_slots` accepts an explicit coordinate set only to prove the rectangular
shape. It sorts the set, rejects duplicates, computes the checked bounding rectangle and requires the
rectangle area to equal the complete unique coordinate count. The rectangle's top-left slot becomes
the master coordinate; it does not choose an arbitrary source order winner.

Lookup is total inside the validated dimensions and returns the exact master cell for both master and
covered coordinates. Out-of-bounds coordinates are a typed error. Debug output exposes counts and
dimensions, not logical IDs.

## Limits, canonicalization and failure policy

Default limits are 10,000 rows, 1,024 columns, 1,000,000 logical slots, 1,000,000 master cells,
256-byte logical IDs and 32 MiB serialized input/output. Absolute ceilings remain finite. Slot count,
span endpoints and flat indexes use checked arithmetic; backing storage uses fallible reservation.

Canonical JSON is compact UTF-8 with exact schema version and master cells sorted by row, column and
logical ID. Unknown or duplicate struct fields, malformed JSON and wrong versions are rejected. The
validated model can produce a stable SHA-256 over canonical bytes. Bounded serialization distinguishes
limit, allocation and serializer failures without embedding source values in errors.

Stable failures distinguish invalid limits/version/JSON, empty or oversized dimensions, slot
capacity/limit, master-cell and identifier limits, duplicate IDs, empty/overflowing/out-of-bounds
spans, duplicate/nonrectangular explicit coverage, overlaps, uncovered slots, invalid lookup and
bounded serialization/allocation failures. There is no repair, clipping, implicit filler cell,
last-writer-wins overlap or partial result.

## Gate boundary

Passing P06-01 proves only the pure logical grid invariant, canonical mapping and deterministic
property/negative corpus. It does not implement table create/insert/delete, merge/split content
policy, cell formatting, sizing, formulae, pagination, selectors, HWPX XML, Hangul execution,
rendered fidelity, arbitrary documents, another PC, or Hangul 2022/2024 compatibility.
