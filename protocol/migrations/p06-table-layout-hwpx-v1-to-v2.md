# P06 table layout HWPX v1 to v2

P06-05 v2 activates `hwpx-agent.table-layout-hwpx.hancom-2020/2` while preserving exact
`hwpx-agent.table-layout-hwpx.hancom-2020/1` and its SHA-256 as an immutable predecessor. The v1 contract described layout and
content readback but did not expose the inherited table `hp:inMargin` values in the public typed
readback. Adding that Rust structure field is an explicit contract change; there is no automatic
profile detection and callers must rebuild against v2.

The v2 reader requires exactly one `hp:inMargin` and returns its `left`, `right`, `top`, and
`bottom` values as unsigned HWPUNIT scalars. Zero is valid. Each value must be no greater than the
configured `dimension_hwpunit` limit. The lowerer does not edit those attributes: it carries all
four source values into the expected readback and fails closed if any value changes after lowering.
Only existing `hp:sz` and `hp:cellSz` width and height value spans remain mutable.

The exact current-PC product fixture additionally binds the source HWPX digest, current installed
`함초롬바탕` 10 pt font-metric receipt digest, four target text hashes, verified layout plan, and
create-new deterministic package digest. The solver receives the exact inherited table inner
margin instead of a guessed default. `Preview/PrvText.txt` is refreshed to the target strings;
the preserved source `Preview/PrvImage.png` is explicitly not renderer evidence.

This migration does not claim that the target has passed Hangul 2020 save/reopen, wrapping,
geometry, or PDF visual review. It also does not migrate Hangul 2022, Hangul 2024, another build,
arbitrary documents, pagination, formulas, production, or product completion. Those remain
separate actual-evidence Gates.
