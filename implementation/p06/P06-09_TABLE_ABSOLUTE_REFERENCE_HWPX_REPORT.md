# P06-09 TABLE-060 absolute-reference HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-absolute-reference-hwpx.hancom-2020-canonical-field/1`
- Scope: current repository, bounded synthetic Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-060 now has a preserving direct-HWPX adapter for the complete bounded `FormulaAst` grammar.
It selects one formula owner even when the table contains other formula fields and changes only
relative reference axes to absolute axes. Coordinates, literals, operators, functions, argument
structure, owner and General number format cannot drift.

`Preserve`, bound `Update` and `Clear` cache policies reopen exactly. Caches remain absent or
unverified; `recalculate=true` is rejected because no formula engine ran. The adapter handles
independent row/column anchors, recursive formula trees, multiple formula fields and already-absolute
no-ops. Invalid coordinate/operator changes, anchor downgrades, cache-policy mismatches, ambiguous
owners, noncanonical native text and stale source/flow/plan bindings fail closed.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-060 adapter tests | 8/8 PASS |
| Independent row/column anchor upgrades | exact static reopen PASS |
| Full bounded recursive FormulaAst shape | preserved except anchors |
| Other formula fields and caches | opaque bytes preserved |
| Cache preserve/update/clear | exact static reopen PASS |
| Recalculate request | fail closed |
| Part/table/formula/unowned/pagination/count/flow binding | fail closed on drift |
| No-op parts and flow | byte exact |
| Page split, repeat header and caption | preserved |
| Closed package graph and every non-target part | exact preservation PASS |
| Strict JSON and redacted Debug | PASS |

The fixtures are synthetic in-memory HWPX XML and ZIP packages. No user document, Hangul process,
UI, COM/HAction call, saved target file, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 6 to 5
- direct `integration_passed`: 40 to 41
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-060 gains static `semantic_reopen`, `formula_readback` and `page_split` evidence. It still
lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence. Aggregate missing validation instances fall from 86 to 83; direct backend
unbound rows fall from 6 to 5.

## Preserved boundaries

Synthetic XML/package success is not licensed Hangul or render evidence. No cache is recalculated or
verified. P06-09, P06, production and the product remain in progress. The next exact step is another
remaining unit-only row or the prepared current-target TABLE-032/033 source run when the user can
approve Hangul file access. Recommended reasoning remains `max`.
