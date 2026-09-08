# P06-09 TABLE-006 table-backed chart report

- Result: `component_pass`
- Direct stage: `unit_passed`
- Actual HWPX: `false`
- Actual Hangul 2020: `false`
- P06-09: `in_progress`
- Product complete: `false`
- Recommended next reasoning: `max`

## Implemented

- Added `hwpx-agent.table-chart/v1` with capability ID `table.chart_from_table`.
- Added a complete exact-grid source snapshot with typed blank/decimal/text values, source digests,
  and literal or formula-display-cache provenance.
- Added an exact rectangular cell-block request bound to table identity, source-state SHA-256, grid
  SHA-256, current document-flow SHA-256, and distinct chart/data-resource IDs.
- Added the documented ignored corner, first-row series labels, first-column category labels,
  numeric/blank body mapping, and three-dimensional vertical-bar initial type.
- Excluded cursor-only/default-sample-data creation and fail closed on selected merged cells,
  nonnumeric body text, stale bindings, malformed digests, non-NFC labels, noncanonical numbers,
  identifier collisions, and finite-limit failures.
- Added bounded deterministic JSON and privacy-redacted `Debug` implementations.

## Verification

- Focused Rust table-chart tests: 12/12 PASS.
- Happy path: full and partial cell-block category/series projection, formula-display-cache origin,
  exact decimal labels, documented chart type and explicit blank data points.
- Boundary/negative: cursor-only, selected merge, body text, incomplete/duplicate state, non-NFC,
  scale, bad origin digest, ID collision, state drift, flow drift, strict JSON and size limits.
- Preservation: source-state before/after bindings remain exact and source mutation is absent from
  the pure plan.
- Contract validator and tamper tests bind the policy, migration, implementation markers, source
  documents, nonclaims, limits and failure policy.
- P06 Python contract/conformance regression: 133/133 PASS.
- Workspace `--all-targets --all-features --locked --offline` tests PASS; the one pre-existing
  isolated PostgreSQL qualification test remains explicitly ignored.
- Workspace Clippy with `-D warnings`, formatting and diff checks PASS.

## Matrix effect

- `cataloged`: 3 to 2.
- `unit_passed`: 40 to 41.
- `integration_passed`: remains 7.
- `oracle_verified`: remains 11.
- Green rows: remains 0/61.

TABLE-006 still lacks direct HWPX lowering, a disposable chart fixture, linked-data semantic
save/reopen, formula readback, page/render checks, licensed Hangul 2020 target execution, rollback,
reviewed automation binding/runtime evidence, and exact differential evidence. None is promoted by
this component result.
