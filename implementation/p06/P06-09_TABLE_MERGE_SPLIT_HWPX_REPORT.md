# P06-09 TABLE-016/017 merge/split HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-merge-split-hwpx.hancom-2020/1`
- Model profile: `hwpx-agent.table-merge-split/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-016 and TABLE-017 now have preserving direct-HWPX integration evidence for the complete
admitted merge/split model. The adapter executes the domain-authoritative grid/content result and
derives every physical edge change from exact before/after slot ownership rather than a local
coordinate shortcut.

All merge content policies and split keep/distribute policies are represented. Paragraph blocks
retain exact bytes and deterministic ownership/order; `First` records intentional discards and
`RejectIfMultiple` fails before output. Split line identity is bound to the source edge-line catalog.
Selected formulas, diagonals and incompatible complete merge-cell properties fail closed.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-016/017 adapter tests | 6/6 PASS |
| 2x2 split with balanced four-paragraph distribution | exact static reopen PASS |
| Merge concatenate/distribute/first/reject policies | PASS |
| Top-left identity, retired/created IDs and normalized edges | PASS |
| Request source state/grid/content and document-flow drift | fail closed |
| Header/section/request/plan part-binding drift | fail closed |
| Selected property, formula and diagonal incompatibility | fail closed |
| Missing split-line catalog identity and inverse topology | fail closed |
| Unselected same-table formula owner/AST/cache | exact preservation PASS |
| Pagination, sibling table and closed package non-target parts | exact preservation PASS |
| Bounded JSON, unknown-field rejection and Debug redaction | PASS |
| `table_ruling_hwpx` complete regression | 21/21 PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 29 to 27
- direct `integration_passed`: 17 to 19
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-016/017 gain static `semantic_reopen`, `formula_readback` and `page_split` evidence. They still
lack render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

The public native formula mutation profile remains the exact supported formula shape and does not
gain merged-cell mutation authority. Synthetic XML/package evidence is not licensed Hangul or
render evidence. Automation remains unverified and differential state remains `not_run`. P06-09,
P06, production and the product remain in progress.

The next exact step is another bounded unit-only semantic group or a licensed current-target oracle
for an integration-only row. Recommended reasoning remains `max`.
