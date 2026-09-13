# P06-09 TABLE-008/009/047 exact border, fill and diagonal target readback report

Date: 2026-09-13

Decision: **PASS for TABLE-008, TABLE-009 and TABLE-047 direct HWPX operations on the exact
current-PC Hangul 2020 target**.

## One batch, three capability targets

One create-only batch derives all three 2x4 formula-bearing targets from immutable P06-06 ancestor
SHA-256 `6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5`.
The fixture manifest SHA-256 is
`05387606ca02cd9e06d44556d8ea50aaf5d80d238dbdc41f68b9c9551026bab0`.

- TABLE-008 applies four independent top/right/bottom/left line values and a background to the
  selected 2x2 region. It records 4 changed cells, 16 side changes and 16 per-cell edge
  assignments. Target SHA-256:
  `5ec86c45cbb1df724827b5126220643bf37a647d58307bbb8f4840bfe89acc30`.
- TABLE-009 applies six unified outer/inner line roles and a background to the same region. It
  records 4 changed cells, 16 side changes, 8 outer assignments and 8 inner assignments. Target
  SHA-256: `c83d13e508fd78cbaa3e65a01ea2d5b7b668a4dce87188c972484c2e8223b0d8`.
- TABLE-047 applies both center diagonals to cell `(0,2)` using `each_cell`. It records one
  diagonal change and one assignment. Target SHA-256:
  `26ab01ea8ba2b02430afbe2173af52bf106dbb251b23ab3a320a3d78361f36ea`.

All targets preserve the other cells, seven payload blocks, the formula owned by `(1,3)`, canonical
formula `SUM(A2:C2)`, visible result `52`, and `CELL` page splitting. Two independent batch builds
were byte-identical. Reusing the existing destination failed before publication and did not change
the manifest or any target. Refactoring the shared generator also reproduced the prior TABLE-007
manifest and target byte-for-byte.

## Licensed Hangul 2020 lifecycle

Each target independently completed all 21 bounded events through `terminal/pass` using exact
`HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 build `11.0.0.9136`, and
executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce`.
Open, input read, save to a new HWPX, close, reopen/read, PDF export, close and quit passed for all
three. Every input remained byte-exact; visible-text SHA-256 remained
`ff9c3868c05d5171931304c7fdc722ad8f99278af1d83e4abb4662a6026f3a3e`; no raw user document
text, network, registry mutation or Computer Use input was used; no `Hwp.exe` process remained.

The save/reopen output SHA-256 values are:

- TABLE-008: `d97d7c1faafc2973484fbc379db8ade16267f46f3ed6ec4b66394e94284254b9`
- TABLE-009: `546560ec33d7ab2a1a28057f377ee747ca6aa6d17491cf531e2e192a2ed42e83`
- TABLE-047: `ff831710d4a0823105578596a96e46c3a81c0040ea8d34a9e91bf269c0163262`

## Independent typed and render oracles

The Rust batch oracle validates each closed 11-part package, immutable package boundary, exact
grid, selected-cell semantics, border-role assignment, diagonal identity, payloads, formula and
pagination. Hangul adds exactly ten renderer `linesegarray` caches to each section. The three cache
sets have SHA-256
`72864168e174956d51a0f33d9e4be3226215c2993a5216644671b81e12ccecd2`; removing only those
validated caches makes each output section byte-equal to its target.

Hangul 2020 also materializes `hatchColor="#000000"` when a solid `winBrush` has no `hatchStyle`.
The color cannot affect rendering without a hatch style. The adapter now excludes only that inert
native default from background identity; an explicit active hatch remains identity-bearing. A
regression test binds the rule. Both the new batch oracle and the pre-existing TABLE-007 oracle pass
after this correction.

All PDFs are unencrypted, JavaScript-free, one-page A4 outputs from the exact Hangul build. The
144-DPI 1190x1682 pages were inspected at original detail:

- TABLE-008 visibly retains independent colored top/right/bottom/left styles on all four selected
  cells;
- TABLE-009 visibly retains the distinct unified outer and inner line roles;
- TABLE-047 visibly retains both purple center diagonals as an X in cell `(0,2)`; and
- all eight values remain visible with no clipping, overlap, blank page or black boxes.

## Gate boundary

Contract `hwpx-agent.p06-09-table-properties-target-contract/v3` promotes TABLE-008, TABLE-009 and
TABLE-047 from `integration_passed` to `direct_hwpx / oracle_verified` for this exact target. It
preserves the v2 TABLE-007 result and binds target-build, render-diff and retry evidence for the
batch. Automation runtime, direct/automation differential, arbitrary documents, other PCs or
versions, P06-09/P06 completion, production and product completion remain unclaimed.
