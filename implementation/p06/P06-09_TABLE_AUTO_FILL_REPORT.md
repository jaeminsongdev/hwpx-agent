# P06-09 table auto-fill component report

- Generated: 2026-09-08
- Model schemas: `hwpx-agent.table-auto-fill-series/v1`, `hwpx-agent.table-auto-fill/v1`
- Capabilities: `TABLE-057` / `table.auto_fill`, `TABLE-058` / `table.auto_fill_series`
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now validates reusable scalar fill series and produces a deterministic, bounded
mutation plan for an exact merge-free table region. Explicit cycles, exact linear numbers and
linear date-days are separate typed definitions. Fill order, starting index and replacement of
existing formula cells are explicit rather than inferred from UI state.

Every mutation binds its coordinate, sequence index, prior full payload, optional formula and
preserved style SHA-256 plus the generated typed value. The receipt binds table, grid, series,
request, complete mutation set, formula policy and semantic change count.

## Verification

| Check | Result |
|---|---:|
| Dedicated auto-fill tests | 16/16 PASS |
| Explicit-cycle row-major and column-major generation | PASS |
| Exact fixed-decimal and signed date progression | PASS |
| Start-index and canonical series binding | PASS |
| Existing-formula reject/replace-bound policy | PASS |
| Complete payload/formula/style preconditions | PASS |
| Merged region, cell-set, series and digest negatives | fail closed |
| Numeric, date and sequence-index overflow | fail closed |
| Input, selection, item, text, generation-work and output limits | fail closed |
| Strict JSON duplicate/unknown/version negatives | fail closed |
| Determinism, zero semantic change and 256-cell corpus | PASS |
| Debug identifier/value/index/hash disclosure | redacted |

## Conformance impact

After exact evidence hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 13 to 11
- direct `unit_passed`: 30 to 32
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX package, user document or Hangul process was touched. Rich
content lowering, formula propagation/readback, semantic reopen, page preservation, rendering,
target-build save/reopen, native automation index qualification and differential evidence remain
open. P06-09, P06, production and the product remain in progress.
