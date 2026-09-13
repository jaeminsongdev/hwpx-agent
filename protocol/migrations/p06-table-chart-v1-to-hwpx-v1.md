# P06 TABLE-006 table-chart v1 to direct-HWPX v1 migration

## Before this profile

`hwpx-agent.table-chart/v1` proved only the complete logical grid, exact selected rectangle,
series/category/body roles, chart type, formula-display-cache provenance and deterministic plan. It
did not select an HWPX anchor, manifest entry, relationship, chart part or Hangul package dialect.

## Admitted direct profile

The direct profile accepts only the exact complete native table shape described by
`P06-09_TABLE_CHART_HWPX_POLICY.md`. It binds the direct `hp:run`, full table and cell spans, complete
grid and typed state, semantic flow and deterministic resource allocation before mutation.

The source artifact is never rewritten. A distinct normalized fixture repairs the locked native
small-table height inconsistency and removes stale renderer caches. That fixture-specific
normalization may not be inferred for arbitrary packages.

## Owned change

Add exactly one chart anchor, one chart XML part and the corresponding manifest/relationship closure.
Retain the complete source table and every unrelated package part. Recheck the same state, grid,
flow, plan, IDs and part paths before writer publication and semantic reopen.

## Gate effect

The migration raises TABLE-006 only to `direct_hwpx / integration_passed`. Exact-target product
open/save/reopen and PDF export are additional evidence, but native-reference render diff,
rollback/retry, verified automation runtime and release exact differential remain separate Gates.
