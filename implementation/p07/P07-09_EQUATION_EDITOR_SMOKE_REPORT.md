# P07-09 equation editor smoke report

## Result

Result: `implementation_ready / target_not_run`.

The complete fail-closed protocol and target tooling for double-click edit, one-token mutation,
save/reopen and native semantic readback are now implemented. This card is not target-complete
because no manual editor session or licensed-Hangul evidence was executed in this implementation
step.

## Component evidence

- Editor-smoke Rust tests: 10/10 PASS. They cover deterministic one-token plans, trusted plan reload,
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

## Exact boundary

All current happy-path evidence is synthetic component evidence. It demonstrates that a trusted
target evidence file would be checked correctly; it does not demonstrate that Hangul was opened or
that the editor interaction, save/reopen, render or differential occurred.

`editor_target_state=not_run`, `actual_hangul=false`, `save_reopen=false`, `render=false`,
`p07_complete=false` and `product_complete=false` remain explicit.

## Next exact task

With P07 implementation surfaces closed, run the combined P06/P07 exact-current-target campaign at
`max`: P07-07 baseline/ink-box qualification, P07-08 Tier B target corpus, P07-09 user editor smoke,
native save/reopen/render and required direct/automation differential evidence.
