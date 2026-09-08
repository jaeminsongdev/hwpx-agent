# P06-09 table geometry HWPX adapter report

- Generated: 2026-09-08
- Adapter profile: `hwpx-agent.table-geometry-hwpx.hancom-2020/1`
- Scope: current repository, static Hancom 2020 HWPX XML integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

`TABLE-018`, `TABLE-019` and `TABLE-050` now have a preserving direct-HWPX lowering path. A
validated geometry state is quantized to HWP units, projected through merged-cell spans, written
only into the selected table's size attributes and reparsed for exact semantic readback before the
output is returned.

## Verification

| Check | Result |
|---|---:|
| Dedicated adapter tests | 9/9 PASS |
| All three geometry operations | exact static readback PASS |
| Closed full-package reopen | all three operations PASS |
| Formula AST/cache and pagination policy | preserved by exact semantic readback |
| Non-section package parts | exact expanded-byte SHA-256 |
| Merged-cell span sums | PASS |
| Cell text/comment digest | preserved |
| Inner margins | preserved |
| Unselected section table | byte-identical |
| Determinism and idempotence | PASS |
| Grid/shape/limit negatives | fail closed |
| Receipt Debug hashes/dimensions | redacted |

The dedicated tests cover standalone, section-part and closed-package HWPX, exact
source/output/state receipt digests, all three operation results, formula AST/cache and pagination
policy readback, non-section part hashes, source immutability, content and margin preservation,
merged spans, a same-shape wrong-grid identity, malformed source coverage, output/dimension limits
and stable public errors.
The full locked `hwpx-package --all-targets` test suite, Clippy with `-D warnings`, and repository
format check also pass before evidence admission.

## Conformance impact

After the report is hash-admitted, the strict matrix changes only as follows:

- direct `cataloged`: remains 30
- direct `unit_passed`: 16 to 13
- direct `integration_passed`: 4 to 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

The package test admits `formula_readback` and `page_split` alongside static `semantic_reopen`, but
it is not a licensed desktop application oracle. The three rows still lack render-diff,
target-build, rollback/retry, automation runtime and direct/automation differential evidence.

## Preserved boundaries

No real HWPX package or user document was modified. No Hangul process, COM/HAction call, access
prompt, save/reopen, PDF render or other PC/version was used. The adapter does not serialize the
internal minimum constraint separately; it lowers the validated effective row height and binds the
full geometry state in the receipt. P06-09, P06, production and the product remain in progress.

The next exact step is the next bounded catalog-only semantic group, followed later by licensed
Hangul 2020 target-build save/reopen and renderer evidence. Recommended reasoning remains `max`.
