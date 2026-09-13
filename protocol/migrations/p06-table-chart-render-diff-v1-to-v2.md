# P06 table-chart render-diff v1 to v2

## Boundary

The v1 contract is an immutable calibration record. It froze the exact Hangul 2020 render profile
but explicitly could not satisfy `required_render_diff`. This additive v2 successor does not edit or
reinterpret that calibration pair.

## Added evidence

- one fresh native-reference/product qualification pair was produced after the v1 profile freeze;
- a second fresh native-reference/product pair repeats the lifecycle and render comparison;
- all four runs bind licensed Hangul 2020 `11.0.0.9136` x86 open, save, close, reopen and PDF export;
- every saved HWPX relifts to the frozen table/chart/anchor semantics;
- both PDF pairs satisfy the frozen word, page, raster, ink and allowed-title-region profile;
- all four watchdog traces and 48 ordered progress events are hash-bound and fail closed.

## Promotion

The fresh qualification pair satisfies TABLE-006 direct `render_diff`. The independent repeated pair
satisfies `rollback_or_retry`. TABLE-006 therefore advances from `integration_passed` to
`oracle_verified` in the direct matrix only.

This migration does not enable an automation route, prove automation runtime, perform the
direct/automation release differential, close P06-09, close P06, or claim production/product
completion. User screenshots and photos are not required and are not machine evidence.
