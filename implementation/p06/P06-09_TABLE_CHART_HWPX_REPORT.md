# P06-09 TABLE-006 direct HWPX chart report

- Result: `integration_pass`
- Direct stage: `integration_passed`
- Actual product HWPX: `true`
- Actual Hangul 2020 open/save/reopen: `true`
- Actual Hangul PDF export: `true`
- Render page inspected: `true`
- Required `render_diff`: `not_run`
- Automation runtime: `not_run`
- Release differential: `not_run`
- P06-09: `in_progress`
- Product complete: `false`

## Implemented

- Added `hwpx-agent.table-chart-hwpx/v1` for the complete admitted 3-by-3 native table profile.
- Bound section/table/run/cell spans, complete grid and typed value/provenance state, domain plan,
  document flow, deterministic IDs and chart resource path at request and build time.
- Added one closed chart relationship, one OPF manifest item, one `hp:chart` anchor and one bounded
  chart XML part with exact 3D vertical-bar series/category/data caches.
- Preserved the source table, all unrelated package parts and the Hangul 2020 preview-text profile
  through preserving writer build and reopen.
- Added a product fixture builder that reads a hash-locked native source, writes only a separate
  normalized source and product HWPX, and publishes through create-new staging.
- Added a target worker/watchdog for exact input open, new HWPX save, close/reopen, visible-text hash
  comparison, PDF export and exact process cleanup. No Computer Use click or input is invoked.

## Verification completed

- Domain table-chart tests: 12/12 PASS.
- Direct HWPX adapter tests: 6/6 PASS.
- The adapter suite includes happy, boundary, negative, preservation, formula-display-cache origin,
  duplicate/unknown JSON, stale flow, allocation tamper, custom limits and writer-profile reopen.
- Native source harness static tests: 24/24 PASS.
- Product lifecycle harness static tests: 19/19 PASS.
- Native source attempt `20260913-04`: PASS with 18 progress events and zero remaining Hwp process.
- Product build `20260913-01`: PASS. The immutable native input SHA-256 is
  `7ed2006c862be671eba82c1a3648c2a30ce7176fef8a6ceb58469b167a5e4929`; the published product SHA-256
  is `f9f7baa1f2aa975bd2d7fd63f268176e4cfa6121772e95b1893b9873b05bcf12`.
- Exact-target lifecycle attempt `20260913-01`: PASS. Hangul saved and reopened
  `28faf18103332b617cc9f3706b003bd0d927e5ac67cf91fde776130cf8c31af4`; visible source-text digests
  match, PDF export passed, the watchdog observed 12 valid progress events and no Hwp process remains.
- Independent ZIP readback finds one table, nine cells, one chart anchor and one chart XML part in
  both product and saved output. Both contain `bar3DChart`, `barDir=col` and all four labels.
- Native-source and saved-product chart caches have the identical ordered values:
  two series names, each series' two categories and its two numeric values.
- The 98,655-byte PDF has one A4 page and is created by the exact Hwp build. The 150-DPI review shows
  the full table and correctly labelled blue/orange 3D vertical bars for values 1/2 and 3/4 without
  clipping or overlap.

## Matrix effect

- `cataloged`: remains 0.
- `unit_passed`: 1 to 0.
- `integration_passed`: 35 to 36.
- `oracle_verified`: remains 25.
- Green rows: remains 0/61.

TABLE-006 gains direct HWPX, target-build, actual Hangul 2020 open/save/reopen and actual PDF-render
evidence. `schema`, `semantic_reopen`, formula-free source readback and one-page placement are
verified. The required native-reference geometry/text/object `render_diff` is still `not_run`, as are
rollback/retry, product automation binding/runtime and release exact differential. No broader Gate is
promoted.

## Next exact step

Export the immutable native-source chart `after.hwpx` through the same exact-target lifecycle into a
new attempt, render it with the same pipeline, compare native-reference and product geometry/text/
object output within the declared threshold, and run a fresh retry before considering TABLE-006
`oracle_verified`.
