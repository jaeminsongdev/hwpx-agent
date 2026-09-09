# P06-09 TABLE-011 whole-table join HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-join-hwpx.hancom-2020-wrapper/1`
- Model profile: `hwpx-agent.table-partition/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-011 now has a preserving direct-HWPX adapter for the exact admitted whole-table join profile.
It binds two adjacent top-level table wrappers plus the exact intervening whitespace paragraphs,
projects unequal source column layouts onto the domain model's reduced-rational common lattice, uses
the larger source width, retains the leading table identity/properties and removes exactly the
separator plus trailing wrapper.

Every master cell, projected span, ordered paragraph payload, complete cell property, edge and
diagonal identity remains bound. The two source tables are rendered sequentially against one evolving
header catalog and each projected state reopens before combination. A differing bottom/top junction
edge is rejected because both values cannot survive as one native shared edge. After row combination,
all native cell addresses and spans are rewritten from the authoritative joined grid and the final
table reopens through strict ruling, partition and pagination readers.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-011 adapter tests | 7/7 PASS |
| Unequal 2-column/2000 + 3-column/3000 sources | 4-column/3000 common lattice PASS |
| Ten master cells, payload blocks and complete properties | static reopen preservation PASS |
| Exact empty/space paragraph separator token and byte binding | PASS |
| Content/reference/object or missing separator | fail closed |
| Formula-bearing selected table and rebase policy | fail closed |
| Divergent source page-split policy | fail closed |
| Junction edge disagreement | fail closed |
| Request part/wrapper/separator/state/flow and lowering drift | fail closed |
| Unknown and recursive duplicate-key JSON | fail closed |
| Sibling formula owner/AST/cache and agreed page-split | exact preservation PASS |
| Closed package non-section parts and spine | exact preservation PASS |
| Debug redaction, deterministic JSON and finite output | PASS |
| Domain partition regression | 13/13 PASS |
| Existing TABLE-010 adapter regression | 5/5 PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved real
HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 26 to 25
- direct `integration_passed`: 20 to 21
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-011 gains static `semantic_reopen`, sibling `formula_readback` and `page_split` evidence. It
still lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

The native profile accepts only formula-free tables with no caption, zero repeat-header rows and the
same supported page-split policy. It does not claim that different junction edges, formulas,
repeat-header ownership or caption ownership can be losslessly joined. The domain formula rebase plan
remains component evidence only. Synthetic XML/package evidence is not licensed Hangul or renderer
evidence. Automation remains unverified and differential state remains `not_run`. P06-09, P06,
production and the product remain in progress.

The next exact step is to lower another unit-only table row while keeping all target-build/render and
automation/differential fields false until their own evidence exists. Recommended reasoning remains
`max`.
