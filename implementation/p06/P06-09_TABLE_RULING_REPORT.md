# P06-09 TABLE-002/003 table ruling and topology report

- Result: `component_pass`
- Direct stage: `unit_passed`
- Actual HWPX: `false`
- Actual Hangul 2020: `false`
- P06-09: `in_progress`
- Product complete: `false`
- Recommended next reasoning: `max`

## Implemented

- Added one `hwpx-agent.table-ruling/v1` model for both `table.draw` and `table.eraser`.
- Added exact outer-rectangle creation with physical frame, insertion-context/document-flow
  bindings, one initial cell, and four explicit visible edges.
- Added a complete physical ruling lattice whose normalized unit edges distinguish visible line
  identity from structural cell topology and retain explicit transparent lines.
- Added one generalized horizontal/vertical draw algorithm. It refines physical row/column
  boundaries, remaps the old grid, and partitions affected master cells by connectivity, covering
  full row strokes, full column strokes, local cell splits, and existing-line style changes.
- Added separate slash/back-slash diagonal operations with no topology side effect.
- Added eraser shared-edge unions with rectangular-result enforcement, plus nonshared outer or
  same-master edges becoming transparent without a structural merge.
- Added ordered payload-block preservation, equal-property admission for merges, deterministic new
  and retired master-cell identities, at-most-one formula merge, formula rebasing, and conservative
  structural-cache invalidation only under an explicitly authorized clear policy.
- Added request/build-time exact table state, grid and document-flow drift rejection, bounded
  deterministic JSON, typed errors, and privacy-redacted `Debug` implementations.

## Verification

- Focused Rust table-ruling tests: 17/17 PASS.
- Happy path: outer rectangle, sequential full row/column strokes, local split, two diagonal
  directions, shared-edge structural merge, payload ordering and single-formula relocation.
- Boundary/negative: non-rectangular split/merge, exact new-ID count, diagonal split/merge conflict,
  mismatched properties, explicit formula policy, missing complete edges, strict/duplicate JSON,
  invalid drift and finite input/output limits.
- Preservation: untouched cells and physical extents remain exact; payload block count remains
  exact; formulas remain present; topology-stale caches clear explicitly; nonshared erasures preserve
  topology and record transparent lines.
- Focused Clippy with `-D warnings`: PASS.
- Private contract/tamper tests: 4/4 PASS; direct validator: PASS.
- P06 Python suite: 137/137 PASS.
- Workspace all-target/all-feature locked offline tests: PASS; the existing isolated P17 PostgreSQL
  qualification test remains the sole ignored test.
- Workspace Clippy with `-D warnings`, `cargo fmt --check`, `git diff --check`, and STRICT
  preservation/privacy/non-promotion self-audit: PASS.
- Conformance source locks: 136/136 PASS.

## Matrix effect

- `cataloged`: 2 to 0.
- `unit_passed`: 41 to 43.
- `integration_passed`: remains 7.
- `oracle_verified`: remains 11.
- Green rows: remains 0/61.

TABLE-002/003 still lack direct HWPX lowering, disposable package preservation, semantic reopen,
formula/cache readback, pagination/render checks, licensed Hangul 2020 target execution, rollback,
reviewed automation bindings/runtime evidence, and exact differential evidence. None is promoted by
this component result.
