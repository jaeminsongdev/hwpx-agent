# P06-09 TABLE-001 exact table-create target readback report

Date: 2026-09-13

Decision: **PASS for TABLE-001 direct HWPX creation on the exact current-PC Hangul 2020 target**.

## Exact target and lifecycle

Successful create-only attempt `20260913-05` used deterministic manifest SHA-256
`6595f8fa69798459f58aea01a18c954f8c39852be5c5b310aef4f5efa3c61263`. The two immutable inputs
cover an arbitrary 3x4 blank unmerged table with nonuniform explicit row/column tracks and the 1x1
minimum boundary.

Exact `HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 file version
`11.0.0.9136`, locale `ko-KR`, and executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce` completed both cases through
37 bounded progress events and `terminal/pass`. Every input was opened/read, saved to a new HWPX,
closed, reopened/read, exported to a signed PDF, and closed. Canonical visible-text SHA-256 stayed
exact; no input changed, raw text was not retained, and no Hwp process remained.

## Defect correction and independent typed readback

The first target runs correctly remained failed. They exposed a non-native `hp:ctrl` table wrapper,
missing native defaults on newly generated empty cell paragraphs, a copied watchdog case-count
constant, and one transient same-session reopen race. The adapter now rejects the control-wrapped
template, publishes native empty-cell defaults only for the exact created cells, derives case count
from the manifest, and waits a bounded 250ms after each document close.

The independent Rust oracle rejects unknown manifest fields, path/hash drift, package-part drift,
malformed renderer caches, table/formula count drift, or typed state/grid/pagination/exterior drift.
It removes only validated renderer `linesegarray` caches. Both exact outputs passed:

| Case | Output HWPX SHA-256 | Typed result | Renderer caches |
|---|---|---:|---:|
| 3x4 nonuniform | `95dbabfa...a743e` | 3x4, 12 unmerged masters, exact | 22 |
| 1x1 boundary | `6d37e47b...79d06` | 1x1, 1 unmerged master, exact | 11 |

The original 2x4 formula table, selected-table placement/pagination, zero created payload/formula
state, five immutable package parts, and all section bytes outside the selected table remain exact
after the admitted renderer-cache removal.

## PDF render oracle

Hangul produced two unencrypted, JavaScript-free, one-page A4 PDFs through
`IXHwpDocument.SaveAs/PDF`; producer is `Hancom PDF 1.3.0.550`. Both pages were rendered with
`pdftoppm 26.07.0` at 144 DPI to 1190x1682 RGB pixels and inspected at original detail.

- The 3x4 page shows the preserved original 2x4 formula table and a separate blank grid with four
  visibly nonuniform columns and three visibly nonuniform rows.
- The 1x1 page shows the preserved original table and a separate blank single-cell table.
- Neither page has clipping, overlap, blank output, unreadable glyphs, or black boxes.

The exact PDF and ephemeral rendered-PNG digests are recorded in
`p06-table-create.current-2020.attempt05.v2.json`. PNGs are QA intermediates, not product inputs.

## Retry and historical failure boundary

Attempts 01-04 remain immutable failed evidence and are not promoted. Attempt 03's inner process
completed but its outer wrapper rejected the evidence; attempt 04's saved HWPX files pass the typed
oracle but the lifecycle stopped at the second output reopen. Attempt 05 reused the exact manifest
and input hashes with new create-only outputs, completed every phase, and left no process behind.
This qualifies the admitted retry path without rewriting earlier results.

## Gate boundary

Contract `hwpx-agent.p06-09-table-create-target-contract/v2` promotes only TABLE-001 to
`direct_hwpx / oracle_verified` on this exact target, adding `target_build`, `render_diff`, and
`rollback_or_retry` evidence. Automation runtime and direct/automation differential remain
`not_run`. Nonblank/merged creation, arbitrary native templates or user documents, other PCs or
versions, P06-09/P06 completion, production, and product completion are not claimed.
