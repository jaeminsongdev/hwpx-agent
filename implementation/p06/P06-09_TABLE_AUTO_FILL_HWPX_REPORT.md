# P06-09 TABLE-057/058 table auto-fill HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-auto-fill-hwpx.hancom-2020-single-run/1`
- Model profiles: `hwpx-agent.table-auto-fill/v1`, `hwpx-agent.table-auto-fill-series/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-057/058 now have preserving direct-HWPX integration evidence for the complete admitted native
profile. Exact explicit-cycle, linear-number and linear-date series fill arbitrary merge-free
rectangles in row-major or column-major order. The adapter rewrites only selected run content and
reopens the complete target ruling state, unchanged grid, scalar state, formula count, payload
identities, page policy, repeat headers, caption and table count.

The request, builder and lowerer independently recheck source parts, table content, ruling state,
grid, selected scalar/style/formula state, payload identities, pagination, series and current flow.
Existing nonempty payload IDs are retained and new IDs for blank/formula-to-nonempty transitions are
explicit, distinct and collision checked. A target-typed text collision is a byte-exact no-op.

STRICT review found a preservation risk beyond the original happy path: changing a selected source
of an unselected formula would preserve a stale visible cache. The final adapter recursively checks
cell/range/unary/binary/function dependencies and fails closed in that case. Unrelated formulas are
preserved byte-for-byte; selected formulas are rejected or exactly removed only under
`ReplaceBound`.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-057/058 adapter tests | 8/8 PASS |
| Explicit cycle, linear number and extended date generation | exact static readback PASS |
| Row-major, column-major and start index | domain-rebuilt PASS |
| Selected run content only; paragraph/run/cell style | exact preservation PASS |
| Complete grid, edges, table/cell properties and unselected payloads | preserved |
| Selected formula reject/replace and cache parity | fail closed / exact reopen |
| Unselected dependent formula cache | fail closed |
| Unselected unrelated formula | byte preserved |
| Target payload identity creation/reuse/collision | exact / fail closed |
| Part/state/grid/scalar/series/pagination/current-flow/plan drift | fail closed |
| Merged, multi-paragraph/run, inline-style and opaque input | fail closed |
| Duplicate/unknown/oversized JSON and Debug privacy | fail closed / redacted |
| No-op parts and flow | byte exact / unchanged |
| Closed package graph and opaque non-target part | exact preservation PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 8 to 6
- direct `integration_passed`: 38 to 40
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-057/058 gain static `semantic_reopen`, `formula_readback` and `page_split` evidence. They still
lack render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence. Aggregate missing validation instances fall from 92 to 86; direct backend
unbound rows fall from 8 to 6.

## Preserved boundaries

Synthetic XML/package success is not licensed Hangul or render evidence. The adapter does not
recalculate formula caches and therefore refuses dependent unselected formulas. Automation remains
unverified and differential state remains `not_run`. P06-09, P06, production and the product remain
in progress. The next exact step is another remaining unit-only row or the already prepared licensed
current-target oracle run. Recommended reasoning remains `max`.
