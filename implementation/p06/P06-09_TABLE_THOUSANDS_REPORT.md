# P06-09 table thousands-format planner report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-thousands/v1`
- Scope: current repository, pure local formula-cell format component
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now produces bounded plans for adding or removing thousands grouping on an exact
selection of numeric formula-cell formats. Plans change only `use_grouping`; decimal places, formula
owner, formula AST and absent or explicitly unverified cache remain exact.

Requests canonicalize selection order and reject empty, duplicate, oversized or out-of-bounds
coordinates. The builder requires the supplied cell owner set to equal the request exactly and
revalidates every formula against the bound dimensions. Unsupported formats and any late output
limit fail without returning a partial plan.

## Verification

| Check | Result |
|---|---:|
| Dedicated planner tests | 9/9 PASS |
| Add/remove exact grouping flag | PASS |
| Decimal places, formula AST and cache preservation | PASS |
| Idempotence and deterministic JSON/SHA-256 | PASS |
| Selection/order/bounds/mismatch negatives | fail closed |
| Unsupported number formats | fail closed |
| Strict JSON duplicate/unknown/version negatives | fail closed |
| Debug formatted-cell disclosure | redacted |

## Conformance impact

After hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 22 to 20
- direct `unit_passed`: 21 to 23
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX XML, user document or Hangul process was touched. Native
number-format lowering/readback, pagination/rendering, target-build save/reopen, automation and
differentials remain open. P06-09, P06, production and the product remain in progress.
