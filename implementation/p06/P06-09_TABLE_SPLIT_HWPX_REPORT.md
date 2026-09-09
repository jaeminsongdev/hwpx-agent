# P06-09 TABLE-010 whole-table split HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-split-hwpx.hancom-2020-wrapper/1`
- Model profile: `hwpx-agent.table-partition/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-010 now has a preserving direct-HWPX adapter for the exact admitted whole-table split profile.
The cursor row becomes row zero of the second table, while the first table keeps its original logical
and native identity. The second table and separator receive distinct caller-bound logical identities
and collision-free native IDs. Both partitions retain the exact column lattice and width, and row
geometry is sliced and rebased without approximating coordinates.

Every master cell, span, ordered paragraph payload, complete cell property, physical edge and diagonal
identity is transferred from the source state to exactly one output table. The adapter independently
renders both partitions, requires one identical header catalog, replaces only the selected top-level
wrapper, and reopens both outputs through strict ruling, partition and pagination readers.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-010 adapter tests | 5/5 PASS |
| 4x2 split into exact 2x2 + separator + 2x2 | static reopen PASS |
| Source table identity and three collision-free native IDs | PASS |
| Row/column geometry, edge, payload and property preservation | PASS |
| Crossing merged boundary, first row and wrapper mismatch | fail closed |
| Selected formula/rebase, repeat-header and caption profiles | fail closed |
| Request part/wrapper/state/flow and plan drift | fail closed |
| Empty, unknown and duplicate-key JSON | fail closed |
| Sibling formula owner/AST/cache and pagination page-split | exact preservation PASS |
| Closed package non-section parts and spine | exact preservation PASS |
| Debug redaction and finite output | PASS |
| Existing ruling adapter regression | 21/21 PASS |
| Domain partition regression | 13/13 PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved real
HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 27 to 26
- direct `integration_passed`: 19 to 20
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-010 gains static `semantic_reopen`, sibling `formula_readback` and `page_split` evidence. It
still lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence. TABLE-011 remains at component/unit evidence.

## Preserved boundaries

The profile accepts only formula-free tables with no caption and zero repeat-header rows. This is an
explicit fail-closed boundary, not evidence for formula rebasing, repeat-header ownership or caption
ownership after native splitting. Synthetic XML/package evidence is not licensed Hangul or renderer
evidence. Automation remains unverified and differential state remains `not_run`. P06-09, P06,
production and the product remain in progress.

The next exact step is TABLE-011 `table.join_table`, using two complete wrapper/state inputs and an
exact whitespace separator over the authoritative common-column lattice. Recommended reasoning
remains `max`.
