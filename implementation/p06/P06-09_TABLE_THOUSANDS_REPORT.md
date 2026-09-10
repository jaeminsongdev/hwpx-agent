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

## Exact-source qualifier status — 2026-09-11

The repository now contains a fail-closed Hangul 2020 source worker, watchdog and 23-case static
test for the native thousands-separator transition. PowerShell parsing passes, PSScriptAnalyzer
reports zero findings, and the static contract passes 23/23. The worker creates only a disposable
1-by-3 table and never guesses or emits native field grammar itself.

Runtime qualification is not complete. Attempt 01 was manually interrupted after no output or
progress receipt and its exact owned Hwp process was identity-checked and cleaned. Attempt 02 found
a preflight defect in the new progress-file extension check; its failed watchdog receipt remains.
Attempts 03 through 07 reached the licensed target but timed out awaiting the baseline `SaveAs`
access approval. Their bounded journals and watchdog receipts remain preserved. In attempt 08 the
user approved the baseline save; the exact target produced the baseline HWPX, then failed because
the worker used the installed UI macro alias `DeleteThousandsSeparator`, which is not an enabled
automation Action ID in the formula-cell context. That baseline, inner trace, journal and failed
watchdog receipt also remain preserved without promotion.

The official Action Table identifies `TableDeleteComma` and `TableInsertComma` as the automation
Action IDs. A bounded in-memory probe on the exact installed build proved that selecting the result
cell with `TableCellBlock` enables both actions and performs the exact visible transition
`4,600 -> 4600 -> 4,600`. The source worker and static guard now use that sequence, reject the UI
macro aliases, require exact grouped/plain/grouped visible states and bind formula-cell selection in
the v2 receipt. This probe does not create HWPX evidence and does not promote either row.

Attempt 09 used that corrected worker and reached the exact licensed build, but no baseline-save
access approval was received before the 900-second watchdog. Its 10-event journal terminates at
`baseline_save/running`; the failed v2 watchdog receipt reports
`TABLE_THOUSANDS_SOURCE_TIMEOUT`, cleaned exactly one owned `-Automation -Embedding` Hwp process,
and left zero Hwp processes. The run directory
`fixtures/target-build/p06-09-table-thousands-source-20260911-09` remains preserved as failed
evidence. It is not relabeled or promoted.

No baseline/removed/added HWPX source triple exists yet, so the exact `ResultFormat` mapping remains
unknown and no direct adapter or conformance-row promotion is claimed. The next run requires the
user to click only Hangul's access `허용` button on each access dialog while the watchdog is active,
followed by offline structural comparison of the three outputs.
