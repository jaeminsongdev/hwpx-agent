# P06 TABLE-006 HWPX v1 to render-diff v1

Before this profile, TABLE-006 had actual direct-HWPX and Hangul 2020 lifecycle evidence but no
declared native-reference render threshold. The render-diff v1 profile adds an exact-target-only,
bounded comparison over PDF identity, extracted table-word geometry, 150-DPI pixels, ink bounds and
saved-HWPX chart semantics.

The first native/product pair is calibration only. Its measured values freeze the comparison rule;
the same pair may not be reused to satisfy `required_render_diff`. Only a fresh independently
exported pair created after this profile is committed may qualify. Any difference outside the
locked automatic default-title region fails closed, as does table text, anchor, chart type, series,
cache, page or ink-bound drift.

This migration neither rewrites source artifacts nor changes TABLE-006 from
`direct_hwpx / integration_passed`. Rollback/retry, automation runtime, release differential,
P06-09/P06 completion, production and product completion remain separate Gates.
