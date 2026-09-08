# P06-09 table geometry component policy v1

Status: pure bounded component implemented; no HWPX or Hangul 2020 oracle claim

## Scope

This policy covers the first implementation slice for three previously catalog-only P06 table
capabilities:

- `TABLE-018` / `table.equal_row_height`
- `TABLE-019` / `table.equal_column_width`
- `TABLE-050` / `table.row_min_height`

The component operates on validated logical row and column tracks bound to exactly one canonical
`TableGrid` SHA-256. It does not select a table in a package, lower XML, automate Hangul, or claim
that a rendered document matches the licensed desktop application.

## Geometry semantics

Equalization accepts a nonempty contiguous zero-based track range. The target is the ceiling of
the selected total divided by its track count, raised when necessary to the largest selected
content minimum. All selected tracks receive exactly that target. Tracks outside the range,
minimum constraints, grid structure, cell content and unrelated document state are preserved.

Row minimum height sets the selected logical rows' minimum constraint. A row below the requested
minimum grows to it; a larger row never shrinks. The operation does not modify column geometry.

Merged cells do not create independent tracks. Their physical extent is the checked sum of every
row and column track covered by the canonical master-cell span.

## Safety and determinism

- State schema is exactly `hwpx-agent.table-geometry/v1`; unknown fields, duplicate fields and
  unsupported versions fail closed.
- Grid digest, row/column counts, positive finite dimensions, minima and output size are validated
  before an operation is admitted.
- Every operation clones the validated source and returns a new state plus a receipt. Invalid
  ranges or dimensions leave the source state byte-for-byte unchanged.
- State and receipt JSON are compact, deterministic and size-bounded. Receipts bind the exact grid,
  source state, output state, operation and changed row/column indexes.
- Debug output omits grid/state hashes and dimension values.

## Evidence promotion rule

Passing the pure Rust and tamper tests promotes only `TABLE-018`, `TABLE-019` and `TABLE-050` from
`cataloged` to `unit_passed` with backend `component_only`. It cannot promote them to
`integration_passed`, `oracle_verified`, differential `exact_match`, release-enabled, P06-09 PASS,
P06 PASS, production, or product completion.

The next evidence boundary is a direct HWPX adapter with schema and semantic reopen checks. The
licensed Hangul 2020 target-build, page-split and render-diff oracles remain separate later gates.
