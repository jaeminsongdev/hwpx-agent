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
- Added a fail-closed Hangul 2020 source worker and watchdog for a disposable exact 3-by-3 table,
  whole-table cell block, native chart creation, immutable baseline/chart HWPX outputs, source-text
  preservation and digest-only progress/receipt evidence.
- The worker deliberately emits no guessed chart anchor, chart-part path, manifest relation or chart
  XML. Those native details remain pending inspection of an admitted target artifact.

## Verification

- Focused Rust table-chart tests: 12/12 PASS.
- Happy path: full and partial cell-block category/series projection, formula-display-cache origin,
  exact decimal labels, documented chart type and explicit blank data points.
- Boundary/negative: cursor-only, selected merge, body text, incomplete/duplicate state, non-NFC,
  scale, bad origin digest, ID collision, state drift, flow drift, strict JSON and size limits.
- Preservation: source-state before/after bindings remain exact and source mutation is absent from
  the pure plan.
- Source qualification harness static tests: 24/24 PASS under both PowerShell 7 and x86 Windows
  PowerShell 5.1, including parser, exact-target, exact data/selection, official action path,
  immutable outputs, progress null roundtrip, creation-time/session/command-line ownership,
  timeout/owned-process cleanup, privacy and
  prohibited-side-effect checks.
- Contract validator and tamper tests bind the policy, migration, implementation markers, source
  documents, nonclaims, limits and failure policy.
- P06 Python contract/conformance regression: 214/214 PASS at the latest full checkpoint.
- Workspace `--all-targets --all-features --locked --offline` tests PASS; the one pre-existing
  isolated PostgreSQL qualification test remains explicitly ignored.
- Workspace Clippy with `-D warnings`, formatting and diff checks PASS.

## Matrix effect

- `cataloged`: remains 0.
- `unit_passed`: remains 4.
- `integration_passed`: remains 42.
- `oracle_verified`: remains 15.
- Green rows: remains 0/61.

TABLE-006 still lacks direct HWPX lowering, a disposable chart fixture, linked-data semantic
save/reopen, formula readback, page/render checks, licensed Hangul 2020 target execution, rollback,
reviewed automation binding/runtime evidence, and exact differential evidence. None is promoted by
this component result. The new source harness has not been run and therefore adds no actual HWPX or
Hangul evidence.
