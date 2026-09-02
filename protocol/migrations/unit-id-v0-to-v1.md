# Unit and typed identity v0 to v1

- Target contract: `hwpx-agent.unit-id/v1`
- Automatic in-place migration: forbidden
- Source document mutation: forbidden

## Unit migration

Older values that carry only a bare integer/float and no unit cannot be migrated automatically.
The adapter must supply an explicit source unit and exact rational value.

| Legacy value | v1 migration |
|---|---|
| millimeter decimal | exact bounded rational -> `LengthMicrometers` + receipt |
| typographic point | exact bounded rational -> `PointMilli`, or physical `LengthMicrometers` when explicitly requested |
| HWP 5/HWPX HWPUNIT | declare `1/7200 inch` -> `HwpUnit` -> micrometers + receipt |
| HWPML legacy hunit | declare `1/1800 inch` in a future legacy adapter; never pass as `HwpUnit` |
| pixel | require explicit positive DPI -> micrometers + receipt |
| percent/ratio | declare which source meaning applies -> `RatioMillionths` |
| degree | exact rational -> `AngleMicrodegrees` |

NaN, infinity, a zero/oversized denominator, unknown DPI, overflow or ambiguous source unit fails.
Rounding uses half-away-from-zero and must preserve the signed reduced delta in the receipt.

## Coordinate migration

A bare x/y pair is invalid. Migration must select one of `page`, `content`, `anchor` or
`object_local` and create the matching anchor. If the old source does not identify the anchor,
migration fails instead of assuming page coordinates.

## Identity migration

String IDs must be assigned to the correct v1 newtype. Empty/control/oversized values fail. A
backend numeric/string ID becomes `BackendOpaqueId` only inside a source anchor and never becomes a
logical node/style/resource ID without an explicit stable mapping receipt.

## Negative verification

- `1/1800 inch` legacy hunit passed as v1 HWPUNIT: caller policy error; no implicit conversion.
- invalid rational/DPI/overflow: stable `unit_*` error.
- mismatched coordinate space/anchor, including through JSON: reject.
- wrong typed identity usage: rejected by the Rust type system; invalid JSON value: reject.
- P04-01 canonical graph digest drift: reject the migration/change until versioned review.
