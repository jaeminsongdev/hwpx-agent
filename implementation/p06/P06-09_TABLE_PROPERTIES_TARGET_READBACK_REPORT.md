# P06-09 TABLE-007 exact properties target readback report

Date: 2026-09-13

Decision: **PASS for TABLE-007 direct HWPX properties on the exact current-PC Hangul 2020 target**.

## Exact target and operation chain

The create-only fixture derives from immutable P06-06 target SHA-256
`6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5`. It prepares a 2x4
formula-bearing table and applies two independently read-back-verified operations: table lock and
no-adjust properties first, then margins, horizontal/vertical alignment, text direction and
protection to cell `(1,0)`. The target HWPX SHA-256 is
`940804c73f6cf83b5f1b37821dd18a731f6ad4927c95fb615d68fa4f48829924`, size 13,167 bytes.
Two independent builds produced identical manifest and target bytes. Reuse of an existing output
directory failed before publication and preserved the existing target.

A development probe that placed table and cell changes into one request returned
`ReadbackMismatch`; that result is not promoted. This qualification covers the exact two-operation
product route only.

## Licensed Hangul 2020 lifecycle

Exact `HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 build
`11.0.0.9136`, and executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce` completed all 21 bounded
events through `terminal/pass`. Open, input read, save to a new HWPX, close, reopen/read, PDF export,
close and quit passed. The input remained byte-exact, visible-text SHA-256 remained
`ff9c3868c05d5171931304c7fdc722ad8f99278af1d83e4abb4662a6026f3a3e`, raw document text was not
retained, no network/registry/Computer Use input was used, and no `Hwp.exe` process remained.

The saved HWPX SHA-256 is
`91ee296a57a4db0933c8f1b870d3c57872b7c75c131adb8e93d45c8a270f225d`, size 15,198 bytes.

## Independent typed and render oracles

The Rust oracle validates the closed 11-part package, exact 2x4 grid, table lock/no-adjust state,
selected-cell properties, `CELL` pagination, all cell values, and the single `SUM(A2:C2)` formula
owned by `(1,3)`. Hangul adds exactly ten renderer `linesegarray` caches. Their exact attribute
profiles and digest are verified; removing only those admitted caches makes the section byte-equal
to the target. Renderer cache bytes intentionally change the payload digest, so semantic typed
facets are compared separately from this exact section relation.

The PDF SHA-256 is
`ea7cab8718d3442d3c60a13ec65c9a16ca864a7704808a17d2c9b33bdc4221c7`, size 10,291 bytes. It is
an unencrypted, JavaScript-free, one-page A4 PDF from `Hwp 2020 11.0.0.9136` and
`Hancom PDF 1.3.0.550`. Its 144-DPI 1190x1682 rendering was inspected at original detail: the 2x4
table, all eight values, and the vertically arranged selected cell are visible with no clipping,
overlap, blank page or black boxes.

## Gate boundary

Contract `hwpx-agent.p06-09-table-properties-target-contract/v2` promotes only TABLE-007 to
`direct_hwpx / oracle_verified` for this exact target, with `target_build`, `render_diff`, and
`rollback_or_retry` evidence. TABLE-008, TABLE-009 and TABLE-047 remain `integration_passed`.
Automation runtime, direct/automation differential, the combined single-request shape, arbitrary
documents, other PCs/versions, P06-09/P06 completion, production and product completion are not
claimed.
