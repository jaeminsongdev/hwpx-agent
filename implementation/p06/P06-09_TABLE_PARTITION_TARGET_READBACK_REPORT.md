# P06-09 TABLE-010/011 exact table-partition target readback report

Date: 2026-09-13

Decision: **PASS for TABLE-010 whole-table split and TABLE-011 whole-table join on the exact
current-PC Hangul 2020 target**.

## One chained batch

One create-only fixture derives a formula-free 4x2 table from immutable P06-06 ancestor SHA-256
`6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5`. TABLE-010 splits
before row 3 into two 2x2 tables with one separator paragraph. TABLE-011 consumes that exact split
state and joins it back into one 4x2 table. This chains both operations over the same eight master
cells, eight payload blocks, row/column geometry, table properties, edge identities and `CELL`
page-split state instead of qualifying unrelated fixtures.

The fixture manifest SHA-256 is
`f7c25806e82e2f809d6d6dfde0fc2620493a5cf237fbb9913c9782713db33c25`.

- TABLE-010 target SHA-256:
  `8bab0736c9deb47fa577a68b40223087efcbee3560c700dc97456f777c83e9c3`.
- TABLE-011 target SHA-256:
  `a5a7a475d33fc82c729c2a39b028925a4bb4d528161f36c040d4d3c6204eeecb`.

Two independent batch builds were byte-identical. Reusing the existing destination failed before
publication. The immutable ancestor remained byte-exact.

## Target-calibrated native wrapper fix

The first target pass exposed two native canonicalization rules rather than a semantic mismatch.
Hangul uses signed-range native object IDs and serializes table wrappers with a trailing empty
`hp:t`. It serializes the split separator as a self-closing empty `hp:run`. The fixture now uses a
bounded native-ID range, the split lowerer emits the native table-wrapper and separator forms
directly, and the join reader admits that exact native empty-run separator as one paragraph break.

The existing five split and seven join adapter tests still pass. The join negative test now also
binds the actual native empty-run separator while preserving rejection of missing separators,
non-whitespace content, comments and hidden content.

## Licensed Hangul 2020 lifecycle

Both targets independently completed all 21 bounded events through `terminal/pass` using
`HWPFrame.HwpObject.2`, 32-bit registry view, x86 STA client, Hangul 2020 build `11.0.0.9136`, and
executable SHA-256
`7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce`.
Open, input read, save to a new HWPX, close, reopen/read, PDF export, close and quit passed for both.
Every input remained byte-exact and no `Hwp.exe` process remained.

The save/reopen output SHA-256 values are:

- TABLE-010: `7229ccccd1bfb98dfa3d6a57f4575033718d3644c785103407d8e17795d8db67`
- TABLE-011: `28fddc01a7d224f4d79b15e960483a7c754c2acbde518505148364b75c086c95`

Input/output visible-text SHA-256 values match within each case. The split and join hashes differ,
as expected, because Hangul exposes the whole-table separator through its text projection.

## Independent typed and render oracles

The Rust batch oracle validates both closed 11-part packages, the immutable package boundary, exact
table count, each complete grid/ruling/partition/pagination state, master-cell and payload identity,
and zero formulas. Hangul adds 13 renderer `linesegarray` caches to TABLE-010 and 11 to TABLE-011.
Their ordered raw SHA-256 values are respectively
`6c2aed93776177cfcd1b8935b2417f84c51bce0088d0ebcc8be24171759bbcc2` and
`683f76ab4736256762f04ca371ac0206431d3f496e17b607b2daefa20358d516`.
Removing only those structurally validated caches makes each output section byte-equal to its
target.

Both PDFs are unencrypted, JavaScript-free, one-page A4 outputs from the exact Hangul build. The
144-DPI 1190x1682 pages were inspected at original detail. TABLE-010 visibly contains two separate
2x2 tables holding rows 1-2 and 3-4. TABLE-011 visibly contains one contiguous 4x2 table with all
eight values. No value is clipped or overlapped, and there are no blank pages or black boxes.

## Gate boundary

Contract `hwpx-agent.p06-09-table-partition-target-contract/v2` promotes TABLE-010 and TABLE-011
from `integration_passed` to `direct_hwpx / oracle_verified` for this exact target. It binds the
target build, render diff and retry evidence for the chained batch. It does not claim formula,
caption or repeat-header split/join semantics. Automation runtime, direct/automation differential,
arbitrary documents, other PCs or versions, P06-09/P06 completion, production and product
completion remain unclaimed.
