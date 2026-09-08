# P06-09 table layout modes HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-layout-modes-hwpx.hancom-2020/1`
- Lowerer profile: `hwpx-agent.table-layout-hwpx.hancom-2020/2`
- Scope: current repository, static Hancom 2020 HWPX XML integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

`TABLE-051`, `TABLE-052` and `TABLE-053` now have operation-specific preserving direct-HWPX
evidence. The fixed-column case proves that only the automatic neighbor absorbs the remaining exact
target width. Fit-content and fit-page start from identical automatic constraints but produce
distinct, exact expected results: 38,100 micrometers preferred-content width versus the full
50,800 micrometer page-body width.

## Verification

| Check | Result |
|---|---:|
| Dedicated mode tests | 7/7 PASS |
| Fixed plus automatic column allocation | exact static readback PASS |
| Fit-content versus fit-page distinction | exact plan and HWP-unit readback PASS |
| Closed full-package reopen | all three modes PASS |
| Formula AST/cache and pagination policy | preserved by exact semantic readback |
| Non-section package parts | exact expanded-byte SHA-256 |
| Merged-cell track sum and sibling table | exact preservation PASS |
| Determinism, idempotence and source immutability | PASS |
| Estimated metric and finite-output negatives | fail closed |

The tests use only synthetic in-memory package bytes. They exercise standalone, section and closed
package paths, verify the exact fixed/content/page allocations, require verified font evidence,
preserve merged spans and an unselected table, and reopen both formula and pagination readers after
each mode.

## Conformance impact

After the report is hash-admitted, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 43 to 40
- direct `integration_passed`: 3 to 6
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

The static package fixture admits `formula_readback` and `page_split` alongside
`semantic_reopen`. The three rows still lack render-diff, target-build, rollback/retry, automation
runtime and direct/automation differential evidence.

## Preserved boundaries

No real HWPX package or user document was modified. No Hangul process, COM/HAction call, access
prompt, save/reopen, PDF render or other PC/version was used. The existing receipt Debug surface
contains no visible cell text, but this evidence does not newly claim digest or dimension
redaction. P06-09, P06, production and the product remain in progress.

The next exact step is another bounded unit-only semantic group or a licensed current-target oracle
for the remaining integration-only rows. Recommended reasoning remains `max`.
