# P06-09 TABLE-006 render-diff qualification report

- Date: 2026-09-13
- Target: licensed Hancom Hangul 2020 `11.0.0.9136`, x86, `ko-KR`
- Feature: `TABLE-006 table.chart_from_table`
- Frozen profile: `701248eec6ef0b5fd1524a718d7b18dd2e2077009e74cdacb0fdba34c2a5ba0b`
- Decision: direct `oracle_verified`; release row remains non-green

## Exact-target lifecycle

Four fresh post-freeze runs completed: qualification native reference, qualification product, retry
native reference and retry product. Each run passed actual HWPX open, save-as, close/reopen and PDF
export on the named Hangul build. Input and output visible-text digests match. Watchdog and delegated
worker traces agree, each progress log contains the required twelve ordered events, and each
finalizer reports zero remaining Hwp processes. No user document, network, registry/system setting,
Computer Use click/type, raw document payload or raw chart payload was involved.

## Frozen render and semantic oracle

Both independent pairs pass the frozen v1 operational profile. Each PDF is one unencrypted A4 page
from the exact Hwp/Hancom PDF identity and contains the same eight words at the frozen positions.
Both comparisons produce the same bounded metrics: 1,980 differing pixels, ratio
`0.0009108808862226966`, mean absolute channel delta `0.04153708849345822`, maximum channel delta
193, diff box `[450,324,575,355]`, zero pixels outside the allowed default-title box, identical ink
bounds `[176,212,1057,690]` and ink-count delta 443.

All four saved HWPX packages relift to the frozen one-table, nine-cell, one-chart, 3D vertical-bar,
two-series/two-category/four-value semantics, exact ordered caches and exact chart-anchor properties.
The PDFs were also inspected at original detail and showed the 3x3 source table and linked chart
without clipping, overlap, broken glyphs or black boxes; this review is supplementary to the frozen
machine oracle.

## Decision

The first post-freeze pair satisfies direct `render_diff`; the second distinct pair satisfies
`rollback_or_retry`. TABLE-006 can advance from `integration_passed` to `oracle_verified`.

Automation runtime was not exercised and the direct/automation release differential remains
`not_run`. This report does not make TABLE-006 green and does not claim P06-09, P06, production,
other-PC/version or product completion. Photos and user screenshots are not required.
