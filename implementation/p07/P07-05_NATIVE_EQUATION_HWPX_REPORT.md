# P07-05 native equation HWPX report

## Result

Result: `component_pass` / direct stage `integration_passed`.

`hwpx-package` now lowers a normalized `MathAst` through the P07-04 EqEdit engine into one typed
Hangul 2020 native equation object. It binds the complete expanded package graph, exact section,
top-level paragraph/run, package-wide native object IDs and document flow, then performs strict
native object and semantic readback before returning a preserving patch.

## Evidence

- Focused native equation Rust tests: 10/10 PASS. They cover display and inline insertion,
  EqEdit/AST semantic readback, script/style/baseline/color/extent/anchor inspection, closed-package
  writer reopen, request/build source and flow drift, ID collisions, provisional extent policy,
  strict JSON/limits, native tampering, deterministic receipts and redacted Debug.
- P03 ID-index tests: 8/8 PASS. The new `equation/v4` profile types equation IDs while
  `formula/v3` continues to reject them; duplicate equation IDs fail closed.
- `hwpx-package` all-target/all-feature tests: PASS, including every existing preservation,
  writer, table and package test.
- Focused `hwpx-package` Clippy with `-D warnings`: PASS.
- P07 Python contracts: 20/20 PASS. Workspace Rust FULL passed in 61.6s with only the
  pre-existing explicitly ignored environment qualifications; workspace Clippy passed in 9.4s
  and `cargo fmt --check` passed in 1.8s through the live bounded journal runner.
- The lowerer removes the inserted object from its private output by the exact parsed span and
  requires byte-for-byte source equality. The patch changes exactly one section and retains every
  other expanded part SHA.
- The package writer now validates with the immutable ID profile carried by `PatchResult`, closing
  a latent stronger-profile-to-core validation mismatch without weakening any older profile.
- STRICT preservation/privacy/non-promotion review: blocker/major/minor `0/0/0` after the writer
  profile-propagation correction. `git diff --check` also passed.

## Exact boundary

The tests create synthetic but structurally closed HWPX packages. The installed Hangul 2020 build
and prior P06-07 licensed save/reopen qualify the current native equation vocabulary and predecessor
shape; they do not attest execution of this new lowerer. P07-07 estimator evidence is absent, so
only `provisional + render_required` extent is admitted.

Actual new-lowerer Hangul execution, save/reopen, editor smoke, render, automation, differential,
other Hangul versions, P07 completion, production readiness and product completion remain
`false` / `not_run`.

## Next exact task

Generate one disposable target fixture through this lowerer, then obtain a separate licensed
Hangul 2020 open/save/reopen and native semantic readback record without relabeling the component
tests. After that, implement P07-06 automation binding at `max`.
