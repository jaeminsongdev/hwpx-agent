# P07-09 equation editor smoke report

## Result

Result: `target_pass_v3 / p07_in_progress`.

The fail-closed protocol separates canonical planned before/after programs from the saved raw
native-editor script. V3 also separates user-observed UI state (`user_attested`) from machine
verification, removes photo collection, and retains exact-target native HWPX/save/reopen proof.
Attempt 14 completed that bounded target Gate on Hangul 2020 11.0.0.9136 x86 ko-KR.

## Component evidence

- Editor-smoke Rust tests: 12/12 PASS. They cover deterministic canonical one-token plans, exact
  saved-native serialization/semantic binding, trusted v3 plan reload and v2 refusal,
  request/build source drift, no-op/multi-token/cardinality rejection, strict JSON, target and
  evidence identity, failed/effect-unknown state, missing/failed checklist items, anomaly and
  Computer Use input rejection, v2 screenshot-field relabel rejection,
  object/semantic/graph/flow/reopen/fallback tampering, limits, stable errors, bounded receipts and
  redacted Debug.
- The target oracle independently validates the exact HWPX SHA, package graph and equation ID index,
  reopens the native equation through the strict automation-current-2020 reader, and emits complete
  artifact/graph/flow/object/semantic/script state.
- The plan builder and final evidence oracle are bounded, reject symlinks, require exact file hashes,
  and use the same Rust planner/verifier as the product boundary.
- Parent, x86 STA child and lifecycle finalizer PowerShell harnesses parse successfully. Their exact
  raw source hashes and the interactive bundle hash are pinned in the contract and qualification.
- Scoped `.gitattributes` exceptions preserve those three evidence-harness byte streams exactly
  across checkout instead of applying the repository-wide PowerShell EOL conversion.
- The full P07 Python suite passes 50/50 after adding finalizer-trace distinction tamper coverage.
  Workspace all-target/all-feature locked-offline tests, Clippy `-D warnings`, fmt and diff checks
  pass; the three pre-existing environment-effect tests remain explicitly ignored.

## Exact target result

Attempt 14 bound the source artifact, plan, checklist, saved artifact, interactive child trace,
lifecycle finalizer trace, target-oracle receipt, combined evidence and verified receipt by SHA-256.
The user attested all eight UI checklist items and reported no anomaly; no photo or visual-oracle
claim is present. The interactive child passed target identity, open, checklist, stable save,
immutable input and confirmed process exit. Its same-apartment reopen failure remains preserved.
The v4 finalizer then passed exact-target preflight, two fresh open/close cycles and quit. The native
oracle read back one equation with preserved object ID and the planned `x+2` semantic and saved
script hashes; artifact, package graph and document flow changed as required, with zero fallback.
The public qualification binds the failed child trace and passing lifecycle-finalizer trace as
distinct identities, so the failed same-apartment reopen cannot be relabeled as the passing trace.

`editor_target_state=pass`, `actual_hangul=true` and `save_reopen=true` are bounded to this exact
target and card. `visual_oracle=false`, `render=false`, `p07_complete=false` and
`product_complete=false` remain explicit.

## Next exact task

After the user-requested goal pause, resume at `max` with the remaining P07-07 baseline/ink-box,
P07-08 Tier B corpus, render and direct/automation differential Gates, coordinated with the
remaining P06 exact-current-target campaign.
