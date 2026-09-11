# P07-08 equation corpus report

## Result

Result: `unit_passed / tier_b_target_not_run`.

`equation-engine` now runs one exact, finite A/B/C corpus across LaTeX, MathML and EqEdit, checks
AST-to-EqEdit-to-AST semantic equality, requires exact negative errors and exposes an opaque
byte-preserving legacy-script boundary. The committed 64-case manifest is raw-byte hash pinned.

## Component evidence

- Current corpus Rust tests: 10/10 PASS.
- Tier A: 44/44 semantic round trips, 1,000,000 pass millionths.
- Tier B component: 14/14 semantic round trips, 1,000,000 component pass millionths.
- Tier C: 2/2 exact preserve and 4/4 exact reject; silent approximation count 0.
- Synthetic HWPX same-part preservation fixture: 1/1 PASS. Adjacent text changes while the full
  output-part digest matches the expected bytes containing the unchanged legacy script.
- Manifest tamper, duplicate/unknown JSON, profile drift, duplicate IDs, incomplete tiers, wrong
  policy, unsupported positives, silently accepted negatives, wrong errors, invalid UTF-8/NUL,
  finite limits, deterministic bounded receipt and redacted Debug are covered.

## Exact boundary

No Tier B case has been executed in Hangul in this card. Therefore `tier_b_target_state` remains
`not_run`, `actual_hangul=false` and `product_complete=false`. The HWPX preservation fixture is
synthetic and cannot be promoted to real HWPX or target evidence.

## Next exact task

Implement P07-09's editor-smoke protocol, request/receipt binding and fail-closed evidence loader at
`max`. After implementation closes, execute the P06/P07 target, save/reopen, render and differential
work together as requested by the user.
