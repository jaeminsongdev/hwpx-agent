# P06-09 TABLE-020 table style HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-style-hwpx.hancom-2020/1`
- Model profiles: `hwpx-agent.table-style-definition/v1`, `hwpx-agent.table-style/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-020 now has preserving direct-HWPX integration evidence for the full admitted table-style
plan. Domain precedence and merged-cell resolution produce the authoritative per-master mutations;
the adapter materializes complete typed table/cell styles, four borders, background and visible
diagonal semantics without a raw-XML or unresolved-digest escape hatch.

Request and build boundaries both bind the complete source style/property state, grid, package
parts, document flow, definition, request and plan. Output is published only after strict semantic
reopen reproduces every planned visual style and the complete target property state.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-020 adapter tests | 4/4 PASS |
| Complete table and per-master cell style materialization | exact static readback PASS |
| Header/whole region plan with distinct typed properties | PASS |
| Four borders, background and table-property changes | PASS |
| Truthful unified diagonal preservation/normalization | PASS |
| Formula owner/AST/cache and payload preservation | PASS |
| Pagination attributes and physical grid/extents | preserved |
| Part/style-state/grid/definition/request/plan/flow drift | fail closed |
| Missing and unused-invalid typed catalog values | fail closed |
| Closed package graph, sibling table and non-target parts | exact preservation PASS |
| Determinism and Debug redaction | PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 30 to 29
- direct `integration_passed`: 16 to 17
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-020 gains static `semantic_reopen`, `formula_readback` and `page_split` evidence. It still
lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

The native formula profile remains zero-or-one exact supported formula. Synthetic XML/package
evidence is not licensed Hangul or render evidence. Automation remains unverified and differential
state remains `not_run`. P06-09, P06, production and the product remain in progress.

The next exact step is another bounded unit-only semantic group or a licensed current-target oracle
for an integration-only row. Recommended reasoning remains `max`.
