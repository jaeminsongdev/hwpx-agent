# P07-07 equation layout report

## Result

Result: `unit_passed / target_not_run`.

`equation-engine` now contains a bounded structural layout estimator with exact-sample,
qualified-model and conservative-provisional paths. `hwpx-package` accepts non-provisional extents
only when they exactly match an opaque estimator result. The implementation is ready for the later
combined P06/P07 current-target visual run requested by the user.

## Evidence

- Layout Rust tests: 8/8 PASS. They cover provisional simple/fraction estimates, exact target sample
  reuse, in/out envelope behavior, trusted SHA, target/profile/visual/sample/ink-box tampering,
  malformed/duplicate/unknown/oversized qualification, limits, AST/base-unit errors, deterministic
  receipts, stable error codes and redacted Debug.
- Native HWPX tests: 13/13 PASS. The added test binds a real normalized equation semantic,
  inline/display mode, base unit, baseline, extent and source state to an opaque estimate, then
  rejects dimension drift. Forged verified JSON remains rejected.
- Focused `equation-engine` and `hwpx-package` Clippy with `-D warnings`: PASS; format check PASS.

## Exact boundary

No current qualification file exists. The existing P07-06 evidence has two native display
readbacks but zero inline ink-box measurements, so it cannot satisfy the minimum 4+4 sample and
visual thresholds. Consequently the public runtime currently produces only provisional estimates
and always requires render.

No actual target layout calibration, baseline visual, ink-box visual, active verified model,
render PASS, other-version result, P07 completion or product completion is claimed.

## Next exact task

Implement P07-08 Tier A/B/C corpus and lossless legacy preserve fixtures at `max`. The target-bound
P07-07 qualification will be collected in the combined P06/P07 validation run after P07
implementation closes.
