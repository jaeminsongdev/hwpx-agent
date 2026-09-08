# P06-09 table sort component report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-sort/v1`
- Capability: `TABLE-056` / `table.sort_cells`
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now produces a deterministic, bounded whole-cell relocation plan for row or column
sorting over one exact merge-free table region. Ordered multiple keys, stable ties, independent
blank placement, binary/ASCII-case-insensitive text comparison, exact integer/fixed-decimal
comparison and an explicit formula movement policy are represented without raw backend actions.

Every cell relocation binds source/destination coordinates plus its full payload and optional
formula SHA-256. The receipt binds table, grid, request, relocation set, formula policy and whether
the permutation changes any coordinate.

## Verification

| Check | Result |
|---|---:|
| Dedicated sort tests | 14/14 PASS |
| Complete row and column relocation | PASS |
| Multi-key precedence and stable ties | PASS |
| Descending with independent blank placement | PASS |
| Exact integer/fixed-decimal order and equivalent-value canonicalization | PASS |
| Binary and ASCII-case-insensitive text modes | PASS |
| Formula reject/verbatim/rebase policy binding | PASS |
| Merged region, key, cell-set and digest negatives | fail closed |
| Input, cell, key, text, comparison-work and output limits | fail closed |
| Strict JSON duplicate/unknown/version negatives | fail closed |
| Determinism, no-op receipt and 64-row fixed-seed permutation | PASS |
| Debug identifier/value/hash disclosure | redacted |

## Conformance impact

After exact evidence hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 14 to 13
- direct `unit_passed`: 29 to 30
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX package, user document or Hangul process was touched. Native
cell lifting/relocation, formula rebasing/readback, page preservation, rendering, target-build
save/reopen, automation and differential evidence remain open. P06-09, P06, production and the
product remain in progress.
