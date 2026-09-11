# P07-09 equation editor smoke report

## Result

Result: `implementation_ready_v2 / target_incomplete`.

The fail-closed protocol now separates the canonical planned before/after programs from the saved
raw native-editor script. This correction was required because licensed Hangul 2020 sometimes
retained `{x} + {1}` when the editor opened and later saved `x+2`; a deterministic pre-edit raw
serialization cannot be claimed. The card is not target-complete until a fresh v2 manual plus
automated save/reopen run passes.

## Component evidence

- Editor-smoke Rust tests: 11/11 PASS. They cover deterministic canonical one-token plans, exact
  saved-native serialization/semantic binding, trusted v2 plan reload and v1 refusal,
  request/build source drift, no-op/multi-token/cardinality rejection, strict JSON, target and
  evidence identity, failed/effect-unknown state, manual and automation incompleteness, Computer Use
  input rejection, object/semantic/graph/flow/reopen/fallback tampering, limits, stable errors,
  bounded receipts and redacted Debug.
- The target oracle independently validates the exact HWPX SHA, package graph and equation ID index,
  reopens the native equation through the strict automation-current-2020 reader, and emits complete
  artifact/graph/flow/object/semantic/script state.
- The plan builder and final evidence oracle are bounded, reject symlinks, require exact file hashes,
  and use the same Rust planner/verifier as the product boundary.
- Parent and x86 STA child PowerShell harnesses parse successfully. Their exact raw source hashes and
  bundle hash are pinned in the contract and source qualification.

## Target discovery boundary

Attempt 06 is failed evidence because the disposable `before.hwpx` copy was overwritten. Attempt
07 preserved input and exposed the `x+2` saved form. Attempt 08 supplied four screenshots and a
manual attestation, but its provisional v2 plan incorrectly assumed `x+1` was the deterministic
editor-open form; the screenshot instead retained `{x} + {1}`. Attempt 09 used the corrected model,
preserved input and independently read back the requested `x+2` semantic state with the same native
object, anchor and layout, but captured no screenshots for that plan. It therefore cannot satisfy
the manual Gate or proceed to the automated close/reopen receipt. All attempts remain preserved
and none is promoted.

`editor_target_state=incomplete`, `save_reopen=false`, `render=false`,
`p07_complete=false` and `product_complete=false` remain explicit.

## Next exact task

With P07 implementation surfaces closed, run the combined P06/P07 exact-current-target campaign at
`max`: P07-07 baseline/ink-box qualification, P07-08 Tier B target corpus, P07-09 user editor smoke,
native save/reopen/render and required direct/automation differential evidence.
