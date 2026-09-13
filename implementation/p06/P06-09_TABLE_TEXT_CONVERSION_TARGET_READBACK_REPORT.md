# P06-09 TABLE-004/005 exact text-conversion target readback report

Date: 2026-09-13

Decision: **PASS for TABLE-004 and TABLE-005 direct HWPX conversion on the exact current-PC Hangul
2020 target**.

## Exact target and lifecycle

Successful attempt `20260913-06` used deterministic manifest SHA-256
`6c32f7ccdaad74ad62a2e32257e203ce2c61dc74dafc11026d9ddfe0f045220a`. Four immutable inputs cover
TABLE-004 and TABLE-005 in both a quoted/multiline/Korean/empty-cell 3x2 case and the 1x1 boundary.

Exact `HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 file version
`11.0.0.9136`, locale `ko-KR`, and executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce` completed all four cases.
The 69-event progress stream ended at `terminal/pass`. Each input was opened/read, saved to a new
HWPX, closed, reopened/read, exported through `IXHwpDocument.SaveAs/PDF`, and closed. Input hashes
and canonical visible-text hashes remained exact, raw text was not retained, and no Hwp process
remained.

## Product corrections and independent typed oracle

The target runs exposed three real integration defects: TABLE-005 rejected the native run-direct
wrapper produced by Hangul 2020, generated TABLE-004 cell paragraphs and TABLE-005 replacement text
carried redundant namespace declarations that Hangul normalized on save, and the copied lifecycle
harness still allowed only two cases. The adapters now admit the exact reviewed native wrapper,
emit native paragraph fragments without the redundant namespace, and bind the harness to all four
manifest cases. Legacy single-control TABLE-005 input remains admitted only under its existing exact
profile; mixed or ambiguous wrappers still fail closed.

The independent Rust oracle parses package graph and typed table/text state, preserves the existing
formula table and all immutable parts, and strips only validated renderer `linesegarray` caches.
TABLE-005 compares parsed typed text flow, so Hangul's XML quote/entity lexical normalization cannot
masquerade as a semantic failure or success.

| Case | Output HWPX SHA-256 | Typed result | Renderer caches |
|---|---|---:|---:|
| TABLE-004 3x2 | `06943bbd...e530fb` | 3x2, 6 masters, 5 payloads, exact text grid | 16 |
| TABLE-005 3x2 | `9a9350e3...20900` | exact CSV typed flow, source grid bound | 10 |
| TABLE-004 1x1 | `3a087f02...1d641` | 1x1, 1 master/payload, exact text grid | 11 |
| TABLE-005 1x1 | `881ed366...1f8a` | exact `only` typed flow, source grid bound | 10 |

All four retain the original formula-bearing 2x4 table, one preexisting formula field, selected
exterior/pagination state, and section bytes outside the admitted conversion after renderer-cache
normalization.

## PDF render oracle

Hangul produced four unencrypted, JavaScript-free, one-page A4 PDFs. Producer is
`Hancom PDF 1.3.0.550`; creator is `Hwp 2020 11.0.0.9136`. Every page was rendered with
`pdftoppm 26.07.0` at 144 DPI to 1190x1682 pixels and inspected at original detail.

- TABLE-004 shows the preserved formula table followed by the expected 3x2 or 1x1 converted table.
- TABLE-005 shows the preserved formula table followed by the expected quoted/multiline CSV or
  boundary text.
- No page has clipping, overlap, blank output, unreadable Korean glyphs, or black boxes.

Exact PDF and temporary rendered-PNG digests are recorded in
`p06-table-text-conversion.current-2020.attempt06.v2.json`. PNGs are QA intermediates, not product
inputs.

## Retry and historical evidence boundary

Attempts 01-05 remain immutable failed or superseded evidence and are not promoted. Attempt 01 was
an incomplete generator output. Attempts 02-03 stopped after the stale two-case bound. Attempts 04
and 05 completed the Hangul lifecycle but independently failed TABLE-004 namespace stability and
TABLE-005 native paragraph stability, respectively. Attempt 06 rebuilt all inputs after the product
fixes and passed the complete lifecycle, typed oracle, and render review.

## Gate boundary

Contract `hwpx-agent.p06-09-table-text-conversion-target-contract/v2` promotes only TABLE-004 and
TABLE-005 to `direct_hwpx / oracle_verified` on this exact target, adding `target_build`,
`render_diff`, and `rollback_or_retry` evidence. Automation runtime and direct/automation
differential remain `not_run`. Merged/formula-bearing source conversion, fields or opaque content,
arbitrary wrappers/templates/user documents, other PCs or versions, P06-09/P06 completion,
production, and product completion are not claimed.
