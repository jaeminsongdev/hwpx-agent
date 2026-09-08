# P06-09 table placement component report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-placement/v1`
- Scope: current repository, pure local table-placement component
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now validates complete placement state and produces immutable state+receipt results
for table position, inline/floating attachment, text wrap/flow and outer margins. Operations retain
the logical table identity and every unrelated placement field exactly.

Position and wrap changes require an already floating table and therefore cannot silently convert
an inline table. Attachment conversion is explicit and preserves inactive wrap/flow and margins.
Offsets use signed micrometers; margins are nonnegative. Both use separate finite bounds.

## Verification

| Check | Result |
|---|---:|
| Dedicated placement tests | 13/13 PASS |
| Position-only mutation and preservation | PASS |
| Explicit inline/floating conversion | PASS |
| Wrap/flow pair mutation | PASS |
| Outer-margin-only mutation | PASS |
| Inline inactive-operation negatives | fail closed |
| Offset, margin, input and output bounds | fail closed |
| Strict JSON duplicate/unknown/version negatives | fail closed |
| Determinism, idempotence and 256-seed corpus | PASS |
| Debug identifier/value/hash disclosure | redacted |

## Conformance impact

After exact evidence hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 18 to 14
- direct `unit_passed`: 25 to 29
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX package, user document or Hangul process was touched. Native
XML lowering/readback, formula/page preservation, rendering, target-build save/reopen, automation
and differential evidence remain open. P06-09, P06, production and the product remain in progress.
