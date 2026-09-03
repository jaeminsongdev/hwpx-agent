# P05-06 page-setup policy

- Scope: current-PC licensed Hangul 2020 `11.0.0.9136` x86, direct HWPX page setup
- Contract: `hwpx-agent.page-setup/1`
- Source lock: `source-lock-P00-20260901-v9-final-current-scope`
- Locked source SHA-256: `c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`
- Reasoning/review mode: `max`

## Source and target profile

The machine-readable KS X 6101 reform-03 records identify Appendix E `pagePr`, `margin`,
`landscape`, `gutter`, and `gutterType`. The pinned Hancom OWPML model at commit
`1453388472c703a4b299a0834f425cdac16644b9` defines `pagePr` as required unsigned width/height,
`WIDELY|NARROWLY`, `LEFT_ONLY|LEFT_RIGHT|TOP_BOTTOM`, and exactly one margin child carrying
left/right/top/bottom/header/footer/gutter unsigned HWPUNIT values.

The exact current-2020 synthetic section uses `WIDELY`, width `59528`, height `84186`,
`LEFT_ONLY`, and margin values header/footer `4252`, gutter `0`, left/right `8504`, top `5668`,
bottom `4252`. These observed numbers are target evidence, not universal preset constants.

## Public model and normalization

- Public dimensions are positive unrotated sheet width/height in HWPUNIT with `width <= height`.
- Orientation is independent and typed. `WIDELY` maps to landscape and `NARROWLY` to portrait.
- Named presets lower their standards-defined millimetres using exact `7200 / 25.4` conversion and
  checked half-up rounding. The lowering receipt records exact resulting HWPUNIT dimensions.
- Custom dimensions use thousandths of a millimetre. Floating point and implicit locale parsing are
  not admitted.
- `LEFT_ONLY` and `LEFT_RIGHT` consume gutter on the horizontal body axis once. `TOP_BOTTOM`
  consumes it on the vertical axis once. Facing-page parity is P05-07 section behavior; it does not
  double the stored gutter.

## Impossible-layout rules

The implementation rejects instead of shrinking, swapping, or clamping when:

- a dimension is zero, above the configured target ceiling, or not in unrotated order;
- any margin exceeds the target ceiling;
- left + right + horizontal gutter leaves no positive body width;
- top + bottom + vertical gutter leaves no positive body height;
- header distance exceeds top margin or footer distance exceeds bottom margin; or
- checked conversion, span replacement, output sizing, or allocation overflows.

## Preservation and failure boundary

The reader accepts either a standalone namespaced `hp:pagePr` or one exact `pagePr` directly under
`hp:secPr` in a current-2020 `hs:sec`. Missing, duplicate, foreign-namespace, unknown-attribute,
nested-margin, malformed-number, and unknown-enum shapes fail closed.

The section lowerer replaces only the preserving XML `pagePr` outer byte span. It never edits the
source buffer, reparses the complete result, compares the typed model, and returns source/output
digests plus the replaced half-open span. No raw XML or arbitrary path is exposed as a public action.

## Deferred evidence

A3/B4 and other named preset canonicalization, printer feasibility, rendered page geometry,
multi-section selection, columns, headers/footers, borders/backgrounds, and Hangul 2022/2024 are not
proved by this pure slice. They require their P05-06 target fixture, P05-07/P05-08/P05-09 Gates, or a
separately qualified machine. Until then those claims remain unverified.
