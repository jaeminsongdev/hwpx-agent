# P06-09 TABLE-007/008/009/047 table properties HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-properties-hwpx.hancom-2020/1`
- Model profile: `hwpx-agent.table-properties/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-007, TABLE-008, TABLE-009 and TABLE-047 now have preserving direct-HWPX integration evidence
for the complete admitted domain operation family. The adapter reads complete table/cell properties,
four independent border sides, backgrounds and explicit diagonal intent while retaining exact grid,
payload and formula/cache identities.

Lowering accepts only typed values, prevalidates the whole supplied catalog, relifts the source
immediately before mutation, verifies part/state/grid/plan/document-flow receipts, and returns
coordinated header/section bytes only after exact semantic readback. Native cell spacing remains
geometry-bound and preserved rather than being misrepresented as an independent property.

## Verification

| Check | Result |
|---|---:|
| Dedicated table-properties HWPX tests | 12/12 PASS |
| Complete typed table/cell/border/background reader | PASS |
| Independent four-side border and background edits | exact static readback PASS |
| Unified outer/inner border mapping on merged grid | PASS |
| Each-cell, unified and clear diagonal intent | exact binding/readback PASS |
| Typed table and cell properties without raw XML | PASS |
| Typed table border-fill interning | PASS |
| Source parts/state/grid/flow and catalog drift | fail closed |
| Malformed cells and missing/ambiguous diagonal intent | fail closed |
| Unused invalid catalog values | fail closed |
| Payload and zero/one supported formula preservation | PASS |
| Closed package graph, sibling formula/cache and pagination | preserved |
| Non-header/section parts, unselected table and source bytes | exact preservation PASS |
| Determinism and Debug redaction | PASS |
| Focused package Clippy with `-D warnings` | PASS |
| Private contract validator and tamper tests | 4/4 PASS |
| P06 Python suite | 158/158 PASS |
| Workspace all-target/all-feature locked offline tests | PASS; existing isolated P17 PostgreSQL qualification test 1 ignored |
| Workspace Clippy with `-D warnings` | PASS |
| `cargo fmt --all -- --check` and `git diff --check` | PASS |
| Strict matrix/ledger/nonclaim audit | PASS; 61 rows, green 0/61, 120-line ledger |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 34 to 30
- direct `integration_passed`: 12 to 16
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

The four rows gain static `semantic_reopen`, `formula_readback` and `page_split` evidence. They still
lack render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

Independent native cell-spacing lowering and multiple-formula native admission remain unsupported.
No synthetic result is promoted to licensed Hangul 2020 or renderer evidence. Automation projection
remains unverified for all 61 rows and all differential states remain `not_run`. P06-09, P06,
production and the product remain in progress.

The next exact step is another bounded unit-only semantic group or a licensed current-target oracle
for an integration-only row. Recommended reasoning remains `max`.
