# P06-09 TABLE-054 nested-table HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-nested-table-hwpx.hancom-2020-inline-template/1`
- Scope: current repository, bounded synthetic Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-054 now has an exact preserving direct-HWPX insertion adapter. It replaces one bound empty
direct paragraph in an explicitly selected parent master cell with a caption-free inline table
wrapper. The nested table retains its complete typed grid, merged spans, ruling edges, cell
properties, ordered text payloads, formula/cache state, pagination and placement.

The parent table is also reopened as a complete typed state. Only one ordered wrapper payload is
added; parent grid, spans, edges, properties, formulas/caches, pagination and all other payloads are
unchanged. Nearest-table formula ownership fixes the previous ambiguity where a nested formula
could be counted as a formula of its parent.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-054 adapter tests | 8/8 PASS |
| Complete nested state and formula/cache reopen | PASS |
| Complete parent state with one ordered payload insertion | PASS |
| Merged covered-cell selector and non-inline/resource-bearing template | fail closed |
| Logical/native table, cell, payload and formula ID collisions | fail closed |
| Part/state/grid/content/wrapper/count/flow/plan drift | fail closed |
| Parent and nested pagination/placement | preserved |
| Closed package graph, compression and non-target parts | exact preservation PASS |
| Strict bounded JSON and redacted Debug | PASS |
| P06 Python full suite | 214/214 PASS |
| Workspace all-target/all-feature locked offline suite | PASS; existing isolated P17 PostgreSQL test 1 ignored |
| Workspace Clippy `-D warnings`, fmt and diff checks | PASS |
| Conformance contract/source locks | 289/289 PASS |

The fixtures are synthetic in-memory HWPX XML and ZIP packages. No user document, Hangul process,
UI, COM/HAction call, saved target file, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 5 to 4
- direct `integration_passed`: 41 to 42
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-054 gains static `semantic_reopen`, `formula_readback` and `page_split` evidence. It still
lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence. Aggregate missing validation instances fall from 83 to 80; direct backend
unbound rows fall from 5 to 4.

## Preserved boundaries

Synthetic XML/package success is not licensed Hangul or render evidence. External resource-bearing
payload portability is not claimed. P06-09, P06, production and the product remain in progress.
The next exact step is another remaining unit-only row or the prepared current-target TABLE-032/033
source run when the user can approve Hangul file access. Recommended reasoning remains `max`.
