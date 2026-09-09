# P06-09 TABLE-056 table sort HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-sort-hwpx.hancom-2020-plain-unmerged/1`
- Model profile: `hwpx-agent.table-sort/v1`
- Scope: current repository, synthetic static Hancom 2020 HWPX XML/package integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-056 now has preserving direct-HWPX integration evidence for its complete admitted native
profile. Exact row and column permutations move whole cell identities, ordered payload bytes and
non-ruling properties inside an arbitrary rectangular region while leaving the complete physical
grid, edge lattice, table properties, unselected cells, page policy, repeat headers and caption
unchanged. The output is reopened through the same full reader and must equal the planned target
ruling state, grid and text grid.

Comparison values are derived from lifted plain cell text, not caller labels. The exact classifier
admits blank, lowercase boolean, canonical `i64`, scale-18 fixed decimal and NFC text. It does not
infer native dates or locale collation. The selected table must be unmerged and formula-free;
formulas and rich or ambiguous cell content fail closed without being dropped or approximated.

The request, builder and lowerer independently recheck source parts, table content, ruling state,
grid, payload identities, text grid, pagination and current flow. The builder binds target state,
grid and text-grid digests. A STRICT self-review found and corrected one no-op flow defect: unchanged
sorts now require an unchanged flow digest and return byte-identical parts, while real permutations
require a distinct target flow.

## Verification

| Check | Result |
|---|---:|
| Dedicated TABLE-056 adapter tests | 7/7 PASS |
| Existing domain sort tests | 14/14 PASS |
| Existing transpose adapter regression | 7/7 PASS |
| Complete row and column relocation | exact static readback PASS |
| Master IDs, ordered payloads and non-ruling properties | move together |
| Physical dimensions, boundaries, edges and unselected cells | preserved |
| Target text grid and payload-bound ruling state | exact reopen PASS |
| Page-split policy, repeat headers and caption | preserved |
| No-op parts and document flow | byte exact / unchanged |
| Part/state/grid/text/pagination/current-flow/plan drift | fail closed |
| Merged, formula, multi-paragraph, opaque and unsupported-policy input | fail closed |
| Duplicate/unknown/oversized JSON and Debug privacy | fail closed / redacted |
| Closed package graph and opaque non-target part | exact preservation PASS |

The fixtures are bounded synthetic in-memory HWPX XML and ZIP packages. No user document, saved
real HWPX, Hangul process, UI, COM/HAction call, PDF renderer or automation route was used.

## Conformance impact

After source-lock admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 9 to 8
- direct `integration_passed`: 37 to 38
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

TABLE-056 gains static `semantic_reopen`, formula-free `formula_readback` and `page_split` evidence.
It still lacks render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence. Aggregate missing validation instances fall from 95 to 92; direct backend
unbound rows fall from 9 to 8.

## Preserved boundaries

The domain policies for verbatim formula movement and relative-reference rebasing remain component
semantics only; the v1 native adapter supports only explicit rejection and formula-free readback.
Synthetic XML/package success is not licensed Hangul or render evidence. Automation remains
unverified and differential state remains `not_run`. P06-09, P06, production and the product remain
in progress.

The next exact step is another remaining unit-only row or a licensed current-target oracle for an
integration row. Recommended reasoning remains `max`.
