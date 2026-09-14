# P07-08 equation corpus report

## Result

Result: `target_passed / tier_b_target_pass`.

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

The exact Hangul 2020 11.0.0.9136 x86 ko-KR run passed all 14 Tier B cases. Each case passed native
insertion, immediate readback, save, close, reopen, second native readback and the strict HWPX
oracle. The run used two bounded automation sessions and left zero owned HWP processes. The
redacted target qualification binds the plan, manifest, harness, executable, child trace and full
private target evidence by SHA-256 without publishing formulas or local paths.

This promotes `tier_b_target_state=pass`, `actual_hangul=true`, `save_reopen=true` and
`p07_08=pass`. Render and visual inspection were not executed for P07-08 and remain `not_run`;
the component-only synthetic preservation fixture is still not promoted to real-document evidence.

## Handoff

P07-07's user-attested layout review and the 8/8 direct/automation differential are now separate
passing inputs to the aggregate P07 Gate. This report does not promote P07-08 render or any
other-version claim.
