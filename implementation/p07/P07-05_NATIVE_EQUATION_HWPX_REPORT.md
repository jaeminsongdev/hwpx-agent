# P07-05 native equation HWPX report

## Result

Result: exact-current-PC `pass` / direct stage `oracle_verified`.

`hwpx-package` now lowers a normalized `MathAst` through the P07-04 EqEdit engine into one typed
Hangul 2020 native equation object. It binds the complete expanded package graph, exact section,
top-level paragraph/run, package-wide native object IDs and document flow, then performs strict
native object and semantic readback before returning a preserving patch. A separately generated
fixture also passed the licensed target lifecycle and render oracle.

## Evidence

- Focused native equation Rust tests: 11/11 PASS. They cover display and inline insertion,
  EqEdit/AST semantic readback, script/style/baseline/color/extent/anchor inspection, closed-package
  writer reopen, request/build source and flow drift, ID collisions, provisional extent policy,
  strict JSON/limits, native tampering, deterministic receipts and redacted Debug.
- P03 ID-index tests: 8/8 PASS. The new `equation/v4` profile types equation IDs while
  `formula/v3` continues to reject them; duplicate equation IDs fail closed.
- `hwpx-package` all-target/all-feature tests: PASS, including every existing preservation,
  writer, table and package test.
- Focused `hwpx-package` Clippy with `-D warnings`: PASS.
- P07 Python contracts: 20/20 PASS. Final workspace Rust FULL passed in 53.6s with only the
  pre-existing explicitly ignored environment qualifications; workspace Clippy passed in 5.0s
  and `cargo fmt --check` passed in 1.7s through the live bounded journal runner.
- The lowerer removes the inserted object from its private output by the exact parsed span and
  requires byte-for-byte source equality. The patch changes exactly one section and retains every
  other expanded part SHA.
- The package writer now validates with the immutable ID profile carried by `PatchResult`, closing
  a latent stronger-profile-to-core validation mismatch without weakening any older profile.
- STRICT preservation/privacy/non-promotion review: blocker/major/minor `0/0/0` after correcting
  writer profile propagation, the real `hs:sec` namespace, and target line-cache/ID normalization.
  `git diff --check` also passed.

## Licensed Hangul 2020 target evidence

- Exact target: `HWPFrame.HwpObject.2`, Registry32, x86, ko-KR, build `11.0.0.9136`, executable
  SHA-256 `7f009613...72bce`.
- Lowerer fixture SHA-256 `a420d8a0...1e18` remained unchanged. All ten lifecycle phases passed:
  open/read/save/close/reopen/read/PDF/close/quit, with 21-event terminal PASS and no remaining
  `Hwp.exe` process.
- Saved HWPX SHA-256 `f4aa7a95...b5263` reopened through the equation/v4 package index. The strict
  oracle found exactly one display equation and preserved semantic SHA `959ece9e...3986`, script
  SHA `d6e25c88...1596`, style, baseline, color, 17000x6000 extent, anchor and margins.
- Hangul reassigned object ID `2200000001 -> 1192003081` and added one paragraph line cache. The
  corrected reader treats those as recorded target normalization, not as semantic loss.
- Hancom PDF SHA-256 `4a08c5da...a851` is one A4 page. Original-detail inspection of the 180 DPI
  render found the summation/integral expression legible with no clipping, overlap, blank page or
  black box.
- Authority: `implementation/p07/evidence/target/p07-05-native-equation.current-2020.attempt01.v1.json`.

## Exact boundary

The component tests create synthetic but structurally closed HWPX packages; the separate evidence
above attests this exact new-lowerer fixture only. P07-07 estimator evidence is absent, so only
`provisional + render_required` extent is admitted.

Editor smoke, native insertion automation, differential, arbitrary documents, other Hangul
versions, P07 completion, production readiness and product completion remain `false` / `not_run`.

## Next exact task

Implement P07-06 typed native insertion/edit/readback automation binding at `max`, using this
target-normalization record without treating the fixed save/reopen harness as that automation Gate.
