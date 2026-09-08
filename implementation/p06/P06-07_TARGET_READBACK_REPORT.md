# P06-07 exact table-pagination target readback report

Date: 2026-09-09

Decision: **PASS for the exact current-PC Hangul 2020 P06-07 target**.

## Corrected deterministic target

The successful target is a create-only successor to every failed or superseded attempt recorded in
`P06-07_TARGET_ATTEMPTS_DIAGNOSTIC.md`. Its five top-level tables explicitly clear native
`treatAsChar`; the one nested table remains inline. This is required for Hangul to paginate a table
instead of laying an inline object outside the page. The adapter's exact native policies remain
unchanged: `CELL` permits cell-content splitting, `TABLE` splits only at cell/row boundaries, and
`NONE` keeps a whole table together.

The target SHA-256 is
`44cfcd14d867e6b53f4a015061666fe3b9ac990d3b3c321faae863d172fe8316`, size 17,171 bytes. It
contains 11 package parts, five top-level tables, one nested table, five captions, one equation and
zero renderer line caches. Its section SHA-256 is
`e252881632e066080d9fd3db2b97f630f80c34201e8033815311ff5df8bc00f1`. The source package and
all failed predecessors remain unchanged.

## Licensed Hangul 2020 lifecycle

The exact current-PC target `HWPFrame.HwpObject.2`, 32-bit registry view, file version
`11.0.0.9136`, and executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce` completed all 21 bounded
progress events through `terminal/pass`. Open, input read, HWPX save, close, output reopen, output
read, PDF export, close and quit all passed. The input stayed byte-exact; before/after text SHA-256
was `19e2e32f32ce5238e72ffafdca368a7ebba92bb60b9ed514a40719305b5a8855`; no raw document text
was retained; no user document, network, registry write or Computer Use input was used; and no
`Hwp.exe` process remained.

The saved HWPX SHA-256 is
`8e32f37df5af2b8aaee70cbd0c5cbed30150528f2022952c4dbb012fd58106ed`, size 44,597 bytes. The
post-save oracle again finds the exact six typed tables, five captions and one equation, with 115
renderer-produced line caches. Its section SHA-256 is
`62059a8ad174e39863e24ab381bfd9dbd1ac62b2b773617b0f85afd529d63788`.

After removing exactly those cache elements, the remaining section drift is limited to renderer
normalization: the two paginated top-level table heights become 61,764 and 61,264 HWPUNIT, the
nested table width is normalized to its 15,000-HWPUNIT cell width, and empty text sentinels are
inserted after the nested table and equation. The strict validator reverses only these exact known
normalizations and then requires byte equality with the target section. Header drift is exactly the
removal of unused paragraph-property IDs 20 and 21 with item count 22 to 20; `content.hpf` changes
only modified time and spine `linear` values. Six other package parts are byte-identical, while the
preview text/image are exact-artifact bound.

## Ten-page PDF oracle

The PDF SHA-256 is
`249ad3e14716b9a55898c03ae424a34419cfbb7db8a2d3ab12ad7b362d70da1a`, size 38,042 bytes. It is
an unencrypted, JavaScript-free, ten-page A4 PDF produced by `Hwp 2020 11.0.0.9136` and
`Hancom PDF 1.3.0.550`. All ten pages were rendered at 144 DPI and inspected at original detail;
every extracted glyph lies inside its page box.

- Pages 1-4 split the `CELL` long cell while repeating its two-cell header on every continuation
  page. Items 001-064 remain visible in order with no blank, clipped or overflow page.
- Pages 5-6 split the `TABLE` case only between complete rows. The 18-paragraph merged cell remains
  whole on page 5; page 6 repeats the header and preserves rows 024-030, the nested table, the
  equation row and the bottom caption as intact blocks.
- The 34- and 35-line `NONE` candidates and their top captions stay on pages 7 and 8. The 36-line
  candidate leaves only its fillers on page 9 and moves the whole table plus bottom caption to page
  10. This is the required before/exact/after boundary separation.

The PDF, all ten PNGs and page-by-page findings are digest-bound by
`target-readback-pdf-visual-oracle-01.json`. Hash, trace, progress, HWPX topology, known renderer
normalization, PDF page count, PNG dimensions and negative tamper cases all fail closed.

## Gate boundary

Contract `hwpx-agent.p06-07-table-pagination-target-contract/v2` adds this exact external target
oracle without altering the historical pure or static adapter contracts. P06-07 is complete for
this exact current-PC Hangul 2020 scope. It does not prove arbitrary documents, caption
creation/removal, left/right captions, another PC, Hangul 2022/2024, automation/direct
differentials for the full table matrix, P06 completion, production or product completion.
