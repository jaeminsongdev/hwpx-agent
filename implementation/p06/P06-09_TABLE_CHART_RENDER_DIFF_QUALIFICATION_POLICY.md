# P06-09 TABLE-006 render-diff qualification policy

## Scope

This policy admits a post-freeze exact-target oracle for `TABLE-006 table.chart_from_table`. The
immutable predecessor is `protocol/private/p06-table-chart-render-diff-v1.json`; its calibration pair
remains non-gating.

## Required pairs

Two independent native-reference/product pairs must be created after the frozen profile. Every run
must use licensed Hancom Hangul 2020 `11.0.0.9136`, x86, `ko-KR`, and must pass open, save-as,
close/reopen and PDF export. A watchdog trace, delegated worker trace and exactly twelve ordered
progress events are required for each run. Process identity must be bound and zero Hwp processes may
remain after finalization.

The first pair is the qualification pair. The second pair is a separate retry/rollback witness. A
reused calibration artifact, a reused qualification artifact, a missing trace, an out-of-order event
or a hash/size mismatch fails closed.

## Frozen comparison

Both pairs must be evaluated against the exact v1 profile hash
`701248eec6ef0b5fd1524a718d7b18dd2e2077009e74cdacb0fdba34c2a5ba0b`.
The expected A4 identity, eight words and word boxes, one-table/one-chart semantics, 3D vertical-bar
series/cache order, anchor semantics, 150 DPI dimensions, ink bounds and pixel budgets are unchanged.
Any raster difference outside the frozen default-title box fails. The validator also relifts all four
saved packages and checks basic PDF identity without trusting the receipt alone.

## Privacy and interaction

Receipts contain bounded relative roles, sizes, digests and aggregate observations only. They contain
no absolute path, raw document text, raw chart XML, user identity or secret material. Computer Use
does not click or type. User screenshots and photo evidence are not required; they cannot replace
native lifecycle or machine readback.

## Gate boundary

A passing qualification pair plus a passing independent retry advances TABLE-006 direct evidence to
`oracle_verified` and records direct `render_diff` plus `rollback_or_retry`. Product automation
runtime and the direct/automation release differential remain `not_run`; therefore TABLE-006 remains
non-green and P06-09/P06 remain in progress.
