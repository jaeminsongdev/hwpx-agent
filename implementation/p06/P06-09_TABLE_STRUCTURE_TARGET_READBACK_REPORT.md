# P06-09 TABLE-012/013/014/015 exact table-structure target readback report

Date: 2026-09-13

Decision: **PASS for TABLE-012 insert row, TABLE-013 insert column, TABLE-014 delete row and
TABLE-015 delete column on the exact current-PC Hangul 2020 target**.

## One structural batch

One create-only fixture derives four independent operations from the same formula-free 3x3 source.
The immutable P06-06 ancestor SHA-256 is
`6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5`, and the prepared
source section SHA-256 is
`ad25a9853990d2e249f3a26c8d87aa4cd3717bf40ecd795de9667af45ee47dd8`.

- TABLE-012 inserts row 2: 4x3, 12 masters, 9 preserved payload blocks and 3 empty masters.
- TABLE-013 inserts column 2: 3x4, 12 masters, 9 preserved payload blocks and 3 empty masters.
- TABLE-014 deletes row 2: 2x3, 6 masters, 6 preserved payload blocks and 3 deleted masters.
- TABLE-015 deletes column 2: 3x2, 6 masters, 6 preserved payload blocks and 3 deleted masters.

The fixture manifest SHA-256 is
`4f02027b798d0c8e3c805ac9be766280421b30a941ed2fc49cfede16b1f4fa09`. Two independent
builds were byte-identical, an existing destination was rejected before overwrite, and the ancestor
remained byte-exact.

## Target-calibrated fixes

The first licensed target pass exposed Hangul's native empty-cell canonical form. An inserted empty
cell is saved as a paragraph with explicit `pageBreak`, `columnBreak` and `merged` zero attributes
and one self-closing `hp:run`; it does not retain an empty `hp:t`. The row/column-structure render
profile now emits that exact form while other table creation profiles retain their existing form.

The same batch exposed a receipt-only overclaim: delete operations reported all nine source payload
blocks as preserved even though only six survive. The lowering receipt now checked-sums payloads
from the authoritative after-state. Adapter tests explicitly require 9 for insertion and 6 for
deletion. Neither correction relaxes invalid-grid, span, edge, formula, pagination, package or
publication checks.

## Licensed Hangul 2020 lifecycle

All four targets independently completed 21 bounded events through `terminal/pass` using
`HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 build `11.0.0.9136`, and
executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce`.
Open, input read, save to a new HWPX, close, reopen/read, PDF export, close and quit passed. Every
input remained byte-exact, input/output visible-text SHA-256 matched within its case, and no
`Hwp.exe` process remained.

The save/reopen output SHA-256 values are:

- TABLE-012: `04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c`
- TABLE-013: `1f9c5e40a164d59715547e22b858690504b3bb9895fb6a0e57d887842fe35add`
- TABLE-014: `c449bb856589c78a7c80b93bc700e407cff85f3744dd266787bcf03a3fa3b0fe`
- TABLE-015: `bd0ffb108bf35289c742bd400a74d3d95f0a69574f3279c3b363f8475a38dce1`

## Independent typed and render oracles

The Rust oracle and independent Python contract validator bind all four closed 11-part packages,
immutable package parts, exact dimensions and cell order, logical master/payload identities,
formula-free state, `CELL` page split, no repeat header or caption, native empty-cell scaffold and
the exact insertion/deletion counts. Hangul adds respectively 15, 15, 9 and 9 renderer
`linesegarray` caches. Their ordered raw SHA-256 values are:

- TABLE-012: `44d9a1d66c172f530f561438c38c67b6530bf994332fa4ccddd5c84982b434ad`
- TABLE-013: `23eb6840733c3b4c748f9192ee54b9ffb88f04c85ab2eff182bb9657f347adda`
- TABLE-014: `a5491d59a064546751144e7d9df920737505cc0698e0838acb59968aa2dd05a4`
- TABLE-015: `71928c8f51a481142c90e09243c511df8206180c297dfd656725653c13b7d927`

Removing only those structurally validated caches makes every output section byte-equal to its
target.

All PDFs are unencrypted, JavaScript-free, one-page A4 outputs. The 144-DPI 1190x1682 renders were
inspected at original detail. TABLE-012 visibly has one empty inserted second row; TABLE-013 one
empty inserted second column; TABLE-014 contains only source rows 1 and 3; TABLE-015 contains only
source columns 1 and 3. All expected labels are visible. There is no clipping, overlap, blank page
or black box.

## Gate boundary

Contract `hwpx-agent.p06-09-table-structure-target-contract/v2` promotes TABLE-012 through
TABLE-015 from `integration_passed` to `direct_hwpx / oracle_verified` for this exact target. It
binds target build, render diff and retry evidence for the combined batch. Formula-bearing,
repeat-header and caption-bearing structural transformations remain unclaimed. Automation runtime,
direct/automation differential, arbitrary documents, other PCs or versions, P06-09/P06 completion,
production and product completion remain unclaimed.
