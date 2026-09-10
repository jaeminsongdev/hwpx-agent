# P06-09 TABLE-022/023/024/026/027/028/029/030 exact aggregate target report

Date: 2026-09-10

Decision: **PASS for the eight aggregate rows on the exact current-PC Hangul 2020 target**.

## Exact target and lifecycle

Create-only attempt `20260910-02` used manifest SHA-256
`b58c3b68d156550512674d894427bc94dcb26d014f687d3e32e8918a37acc363` and the fixed feature
order TABLE-022, 023, 024, 026, 027, 028, 029 and 030. One licensed `HWPFrame.HwpObject.2`
session through the 32-bit registry view and x86 STA client ran Hangul 2020 `11.0.0.9136`,
`ko-KR`; executable SHA-256 is
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce`.

All eight cases completed open, text read, save to a new HWPX, close, reopen, second text read, PDF
export and close. The 133-event progress journal ended at `terminal/pass`. Every input digest and
visible-text digest stayed exact, every output and PDF was newly created, and zero owned HWP
processes remained. No raw document text was retained, no user document was scanned, no network or
system-setting change occurred, and Computer Use supplied no click or keystroke.

## Independent typed HWPX oracle

The independent Rust oracle passed all eight target/output pairs. It reopens the complete package,
typed ruling state, logical grid, formula AST/cache, pagination/caption, layout and preview before
allowing any renderer normalization. Each output preserved a 2x4 unmerged table with eight masters,
seven ordered payload blocks and one formula. Formulas and visible unverified caches were:

| Feature | Formula | Visible cache | Output HWPX SHA-256 |
|---|---|---:|---|
| TABLE-022 | `SUM(A1:B2)` | 32 | `91735b23...31dadc` |
| TABLE-023 | `AVG(A1:B2)` | 8 | `fca2c3f2...2a6783` |
| TABLE-024 | `PRODUCT(A1:B2)` | 1020 | `d1a3dde8...4dd53` |
| TABLE-026 | `SUM(D1:D1)` | 5 | `0f7dfd81...0abc6` |
| TABLE-027 | `AVG(A2:B2)` | 13.5 | `46ef052d...3dcd1` |
| TABLE-028 | `AVG(D1:D1)` | 5 | `54b43642...fb855` |
| TABLE-029 | `PRODUCT(A2:B2)` | 170 | `784d90c6...c1ba0` |
| TABLE-030 | `PRODUCT(D1:D1)` | 5 | `da1db896...bb793` |

Hangul added exactly ten validated renderer `linesegarray` caches, regenerated the table height from
564 to 2564 HWP units, and reissued exactly one positive matching formula field-identity pair. The
oracle replaces only those validated differences. The resulting complete `section0.xml` equals the
target bytes for every case. The renderer-cache digest is `4fe319c0...b9c8d`; the raw field IDs are
not retained, and their domain-separated relation digest is `68bbc31e...03bb0`.

## PDF render review

The eight retained PDFs are unencrypted, JavaScript-free, one-page A4 documents produced by
`Hancom PDF 1.3.0.550` with PDF version 1.4. Every page was rendered using `pdftoppm 26.07.0` at
144 DPI to 1190x1682 pixels and inspected at original detail. Each shows the expected 2x4 values and
the exact visible aggregate result. There are no blank pages, clipping, overlap, black boxes or
unreadable glyphs. PDF and ephemeral PNG digests are fixed in the v2 evidence receipt; PNGs remain
review intermediates, not product inputs.

## Retry and evidence boundary

Attempt 01 remains the immutable failed 900-second access-approval timeout. It completed zero
cases, created no HWPX/PDF, preserved every input and cleaned its one owned process. Attempt 02 used
the same manifest and inputs with separate create-only outputs, so rollback/retry passes without
relabeling the failed trace.

Contract `hwpx-agent.p06-09-table-aggregate-target-contract/v2` promotes only the eight named rows
to `direct_hwpx / oracle_verified` on this exact target and adds `target_build`, `render_diff` and
`rollback_or_retry`. The displayed formula values remain explicit unverified caches; actual formula
evaluation or verified refresh is not claimed. Automation runtime and differential remain
`not_run`; arbitrary documents, merged or existing-formula sources, another PC, Hangul 2022/2024,
P06-09/P06 completion, production and product completion remain unproven.
