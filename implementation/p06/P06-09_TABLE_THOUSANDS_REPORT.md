# P06-09 table thousands-format planner report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-thousands/v1`
- Scope: current repository, pure local formula-cell format component
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now produces bounded plans for adding or removing thousands grouping on an exact
selection of numeric formula-cell formats. Plans change only `use_grouping`; decimal places, formula
owner, formula AST and absent or explicitly unverified cache remain exact.

Requests canonicalize selection order and reject empty, duplicate, oversized or out-of-bounds
coordinates. The builder requires the supplied cell owner set to equal the request exactly and
revalidates every formula against the bound dimensions. Unsupported formats and any late output
limit fail without returning a partial plan.

## Verification

| Check | Result |
|---|---:|
| Dedicated planner tests | 9/9 PASS |
| Add/remove exact grouping flag | PASS |
| Decimal places, formula AST and cache preservation | PASS |
| Idempotence and deterministic JSON/SHA-256 | PASS |
| Selection/order/bounds/mismatch negatives | fail closed |
| Unsupported number formats | fail closed |
| Strict JSON duplicate/unknown/version negatives | fail closed |
| Debug formatted-cell disclosure | redacted |

## Conformance impact

After hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 22 to 20
- direct `unit_passed`: 21 to 23
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX XML, user document or Hangul process was touched. Native
number-format lowering/readback, pagination/rendering, target-build save/reopen, automation and
differentials remain open. P06-09, P06, production and the product remain in progress.

## Exact-source qualifier status — 2026-09-10

The repository now contains a fail-closed Hangul 2020 source worker, watchdog and 20-case static
test for the native thousands-separator transition. PowerShell parsing passes, PSScriptAnalyzer
reports zero findings, and the static contract passes 20/20. The worker creates only a disposable
1-by-3 table and never guesses or emits native field grammar itself.

Runtime qualification is not complete. Attempt 01 was manually interrupted after no output or
progress receipt and its exact owned Hwp process was identity-checked and cleaned. Attempt 02 found
a preflight defect in the new progress-file extension check; its failed watchdog receipt remains.
Attempts 03 through 06 reached the licensed target but timed out awaiting the baseline `SaveAs`
access approval. Attempt 06's bounded journal also ends at `baseline_save/running`; its watchdog
cleaned one exact owned process, refused no cleanup target and left zero Hwp processes. The available
Computer Use surface exposed browsers only, so it could not capture the Hangul dialog and no click
or typing was automated. None of these failures is promoted.

No baseline/removed/added HWPX source triple exists yet, so the exact `ResultFormat` mapping remains
unknown and no direct adapter or conformance-row promotion is claimed. The next run requires the
user to click only Hangul's access `허용` button on each access dialog while the watchdog is active,
followed by offline structural comparison of the three outputs.
