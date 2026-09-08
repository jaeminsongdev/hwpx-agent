# P06-09 table placement HWPX adapter report

- Generated: 2026-09-09
- Evidence profile: `hwpx-agent.table-placement-hwpx.hancom-2020/1`
- Model profile: `hwpx-agent.table-placement/v1`
- Scope: current repository, static Hancom 2020 HWPX XML integration
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

`TABLE-034`, `TABLE-036`, `TABLE-037` and `TABLE-038` now have preserving direct-HWPX evidence.
The adapter reads and lowers the complete table placement surface while binding the caller's exact
source and target states to the selected table's admitted grid/cell content digest.

Position coverage exercises every reference frame and alignment plus negative and positive native
offsets and all three floating flags. Attachment coverage proves both floating-to-inline and
inline-to-floating transitions without losing inactive native fields. Wrap coverage exercises the
Cartesian product of four table wrap styles and four side-flow modes. Outer margins have exact
four-side HWPUNIT readback.

## Verification

| Check | Result |
|---|---:|
| Dedicated placement HWPX tests | 7/7 PASS |
| All position references, alignments, offsets and flags | exact static readback PASS |
| Inline/floating transitions and inactive values | exact preservation PASS |
| Four wrap by four side-flow combinations | 16/16 exact readback PASS |
| Four outside margins | exact readback PASS |
| Source/target state identity and native drift | fail closed |
| Canonical enum/boolean/number and finite limits | fail closed |
| Closed full-package reopen for all five operations | PASS |
| Formula AST/cache and pagination policy | preserved by exact semantic readback |
| Merged sibling and non-section package parts | exact preservation PASS |
| Determinism, idempotence, source immutability and Debug redaction | PASS |

The tests use only synthetic in-memory table, section and closed-package bytes. They do not use a
user document, a real saved HWPX, Hangul UI or a renderer.

## Conformance impact

After hash admission, the strict matrix changes only as follows:

- direct `cataloged`: remains 0
- direct `unit_passed`: 40 to 36
- direct `integration_passed`: 6 to 10
- direct `oracle_verified`: remains 15
- green rows: remains 0/61

The four rows gain static `semantic_reopen`, `formula_readback` and `page_split` evidence. They
still lack render-diff, target-build, rollback/retry, automation runtime and direct/automation
differential evidence.

## Preserved boundaries

No real HWPX package or user document was modified. No Hangul process, COM/HAction call, access
prompt, save/reopen, PDF render or other PC/version was used. The receipt Debug surface omits
source/output/state/content hashes and document values. P06-09, P06, production and the product
remain in progress.

The next exact step is another bounded unit-only semantic group or a licensed current-target oracle
for remaining integration-only rows. Recommended reasoning remains `max`.
