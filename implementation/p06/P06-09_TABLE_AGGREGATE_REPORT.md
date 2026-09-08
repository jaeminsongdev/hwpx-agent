# P06-09 table aggregate planner report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-aggregate/v1`
- Scope: current repository, pure local formula-planning component
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now converts exact block, horizontal and vertical selections into bounded
locale-neutral `SUM`, `AVG` and `PRODUCT` formula plans. All nine axis/function combinations have
exact canonical A1 output, including the existing horizontal-sum regression path. The eight rows
listed in the policy gain unit evidence; `TABLE-025` keeps its stronger existing oracle evidence.

Requests bind exact table dimensions and reject reversed/out-of-bounds ranges, self-reference and
horizontal/vertical direction drift. Plans always start with an absent cache and general number
format, so this component cannot counterfeit a calculated or current-target result.

## Verification

| Check | Result |
|---|---:|
| Dedicated planner tests | 8/8 PASS |
| Axis/function combinations | 9/9 exact canonical formulas |
| Strict JSON duplicate/unknown/version negatives | fail closed |
| Range/order/bounds/self-reference negatives | fail closed |
| Canonical JSON and SHA-256 determinism | PASS |
| Debug formula disclosure | redacted |
| Full `domain-ir --all-targets` tests | PASS |
| `domain-ir --all-targets` Clippy `-D warnings` | PASS |

## Conformance impact

After hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 30 to 22
- direct `unit_passed`: 13 to 21
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX XML, user document or Hangul process was touched. Formula
lowering/readback, pagination/rendering, target-build save/reopen, automation and differentials
remain open. P06-09, P06, production and the product remain in progress.
