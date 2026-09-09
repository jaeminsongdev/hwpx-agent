# P06-09 TABLE-012/013/014/015 exact structure HWPX report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-structure-hwpx.hancom-2020-wrapper/1`
- Model profile: `hwpx-agent.table-structure/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-012 through TABLE-015 now use one complete structural model and one preserving direct-HWPX
adapter. All four operations bind and recompute the same exact grid, geometry, master-cell, ordered
payload, complete property, formula/cache, edge and document-flow transition. Insertion creates only
explicit empty 1x1 masters at a legal whole-grid boundary. Deletion removes only fully contained
masters and rejects a partial merged span or the last remaining dimension.

The edge model duplicates the source boundary around an inserted band and validates all caller-bound
internal edges. Deletion maps surviving edges structurally and rejects any unequal pair that would
collapse into one native shared edge. Surviving formulas use the exact grid edit for owner and
references, with explicit cache policy; owner deletion is counted and reference-endpoint deletion
fails closed. A merged two-column formula cell was reopened after row insertion with its span,
native `SUM(LEFT)` envelope and cache intact and its owner/reference coordinates exactly rebased.

The native lowerer preserves the top-level wrapper/table IDs, page-split and caption. Repeat-header
rows transform as a prefix when the flag remains enabled, while a zero/nonzero transition is rejected.
The final state reopens through ruling, formula and pagination readers before publication. Closed ZIP
fixtures prove that every non-target part and spine entry remains exact.

## Verification

| Check | Result |
|---|---:|
| Dedicated domain structure tests | 7/7 PASS |
| Dedicated TABLE-012/013/014/015 HWPX tests | 8/8 PASS |
| All four insert/delete row/column operations | static lower/reopen PASS |
| Merged formula span plus owner/reference rebase | exact reopen PASS |
| Formula-owner deletion and native envelope removal | exact PASS |
| Insertion through merged span and partial-span deletion | fail closed |
| Final row/column deletion | fail closed |
| Unequal edges collapsing onto one boundary | fail closed |
| Geometry, payload, property, inserted-cell and edge drift | fail closed |
| Source part/wrapper/state/grid/flow and plan drift | fail closed |
| Repeat-header prefix, page-split, caption and native IDs | exact preservation PASS |
| Repeat-header zero/nonzero transition | fail closed |
| Unknown and recursive duplicate-key JSON | fail closed |
| Closed package non-section parts and spine | exact preservation PASS |
| Debug redaction, deterministic JSON and finite output | PASS |
| Private contract/tamper tests | 4/4 PASS |
| P06 Python suite | 178/178 PASS |
| Workspace all-target/all-feature locked offline tests | PASS; existing isolated P17 PostgreSQL qualification test is the sole ignored test |
| Workspace Clippy `-D warnings`, `cargo fmt --check`, `git diff --check` | PASS |
| Conformance source locks | 217/217 PASS |
| STRICT preservation/privacy/non-promotion self-audit | PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved real
HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 25 to 21
- direct `integration_passed`: 21 to 25
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

All four rows gain static `semantic_reopen`, supported native `formula_readback` and `page_split`
evidence. They still lack render-diff, target-build, rollback/retry, automation runtime and
direct/automation differential evidence.

## Preserved boundaries

The admitted native formula profile is an existing single `SUM(LEFT)` left-prefix formula with an
explicit decimal cache; no general native formula creation is claimed. Insertion through a merged
span, partial-span deletion and repeat-header enable/disable remain unsupported. Caption is preserved,
not regenerated. Synthetic XML/package evidence is not licensed Hangul or renderer evidence.
Automation remains unverified and differential state remains `not_run`. P06-09, P06, production and
the product remain in progress.

P06-07 target-v2 licensed Hangul 2020 lifecycle evidence is already complete and remains separately
scoped. The next P06-09 step is to lower the remaining 21 unit-only rows and then close the 25
integration-only rows with exact current-target oracles. Recommended reasoning remains `max`.
