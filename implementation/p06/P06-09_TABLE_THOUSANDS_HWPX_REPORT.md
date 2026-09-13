# P06-09 table thousands HWPX report

- Generated: 2026-09-13
- Adapter schema: `hwpx-agent.table-thousands-hwpx/v1`
- Native profile: `hwpx-agent.table-thousands-hwpx.hancom-2020/1`
- Exact target: Hangul 2020 `11.0.0.9136` x86 `ko-KR`
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-032 and TABLE-033 now have one exact preserving HWPX adapter. It admits only a complete
unmerged grid and explicitly selected native `=SUM(LEFT)` formula fields with the current-target
grouping grammar. It changes only visible formula-result text, while preserving native formula
metadata, numeric cache, formula AST, selected owner, decimal places, complete grid and all unowned
section bytes.

Request construction binds section, selected state, grid, document flow and plan digests. Lowering
rechecks all five bindings, performs bounded edits, and returns no bytes unless typed semantic
readback and unowned-byte preservation both pass. Strict JSON rejects duplicate and unknown keys;
Debug for readback, draft, request and receipt is redacted.

## Exact-source evidence

Attempt `20260913-11` passed the licensed target watchdog with 22 ordered progress events and a
terminal `pass`. The target authored and saved three separate HWPX files after the documented
`TableDeleteComma` and `TableInsertComma` actions. The run opened no user document, invoked no
Computer Use click/type, used no network, changed no registry/system setting, and left zero Hwp
processes.

The offline oracle found the same 11 package entries and the same document flow in all three files.
Baseline and added sections are identical. Removed differs from baseline only at the selected
formula field's visible result. Direct remove and add output sections each exactly equal their
corresponding native section. Formula AST, numeric cache and grid digests remain exact.

Attempt 10 is not promoted: all native saves completed, but the old watchdog rejected the valid
`formula_cell_select` phase because its allowlist was incomplete. The allowlist and static guard were
fixed, while attempt 10 and earlier failures remain preserved.

## Verification

| Check | Result |
|---|---:|
| Dedicated HWPX adapter tests | 6/6 PASS |
| Source harness static tests | 23/23 PASS |
| PSScriptAnalyzer | 0 findings |
| Exact native remove section differential | PASS |
| Exact native add section differential | PASS |
| Request/build state-grid-flow-plan drift | fail closed |
| Malformed/ambiguous native format | fail closed |
| Bounded strict JSON and redacted Debug | PASS |

## Conformance impact

The direct-stage matrix changes only as follows:

- `unit_passed`: 4 to 2
- `integration_passed`: 32 to 34
- `cataloged`: remains 0
- `oracle_verified`: remains 25
- green rows: remains 0/61

Direct-output package save/reopen, PDF/render, rollback/retry, product automation runtime and release
differential are not run. No P06-09, P06, production or product-complete claim is made.
