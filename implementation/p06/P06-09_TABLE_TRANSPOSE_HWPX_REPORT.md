# P06-09 TABLE-021 table transpose HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-transpose-hwpx.hancom-2020-wrapper/1`
- Model profile: `hwpx-agent.table-transpose/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-021 now has preserving direct-HWPX integration evidence for the complete admitted native
transpose profile. A 2x3 fixture with both vertical and horizontal merged masters becomes 3x2;
nonuniform row/column tracks, frame axes, all unit edges, ordered multi/empty payloads, complete cell
properties, slash/back-slash diagonals, page-split policy and caption all reopen as the exact target
state. Transposing the result again restores the original complete grid and ruling state.

The request, builder and lowerer independently bind or recheck source header, section, ruling state,
grid and current document flow. The domain plan is rebuilt before mutation. Output is returned only
after target binding regeneration, strict header/section semantic reopen and table-count,
pagination, payload and formula-free verification.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-021 adapter tests | 7/7 PASS |
| Rectangular 2x3 to 3x2 dimensions and frame | exact static readback PASS |
| Vertical/horizontal merged spans | axes swapped PASS |
| Nonuniform physical boundaries and complete unit edges | axes swapped PASS |
| Master/payload IDs, ordered multi/empty payloads and cell properties | preserved |
| Slash and back-slash diagonals | preserved with each master |
| Page-split policy, zero repeat headers and caption | preserved |
| Double transpose | exact original grid/state PASS |
| Header/section/state/grid/flow/cell/plan drift | fail closed |
| Formula-bearing and repeat-header sources | fail closed |
| Duplicate/unknown/oversized JSON and Debug privacy | fail closed / redacted |
| Closed package graph and opaque non-target part | exact preservation PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 13 to 12
- direct `integration_passed`: 33 to 34
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-021 gains static `semantic_reopen`, formula-free `formula_readback` and `page_split` evidence.
It still lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

The domain formula-transpose contract remains implemented and tested, but formula-bearing native
HWPX lowering is not claimed here. Nonzero repeat-header rows are rejected because transpose would
require a native repeat-header-column semantic that this profile cannot represent. Synthetic
XML/package evidence is not licensed Hangul or render evidence. Automation remains unverified and
differential state remains `not_run`. P06-09, P06, production and the product remain in progress.

The next exact step remains the licensed current-target aggregate oracle batch once the user accepts
the visible Hangul access prompt, or another bounded unit-only row while that approval is pending.
Recommended reasoning remains `max`.
